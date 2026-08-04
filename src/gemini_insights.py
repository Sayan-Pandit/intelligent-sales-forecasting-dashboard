import os
import json
import time
import re
import requests
from dotenv import load_dotenv

# Auto-load .env from the project root (two levels up from src/)
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

# In-memory cache: {cache_key: (timestamp, insights_list)}
_insights_cache: dict = {}
CACHE_TTL_SECONDS = 300  # 5 minutes — respects the free-tier 5 req/min limit


def _make_cache_key(df_filtered) -> str:
    """Creates a lightweight cache key from the data summary."""
    total_revenue = round(float(df_filtered['Sales_Revenue'].sum()), -3)  # round to nearest 1000
    total_units = int(df_filtered['Units_Sold'].sum())
    num_rows = len(df_filtered)
    return f"{total_revenue}_{total_units}_{num_rows}"


def _clean_json_text(raw_text: str) -> str:
    """Strips markdown code fences and cleans the text for JSON parsing."""
    raw_text = raw_text.strip()
    # Remove ```json ... ``` or ``` ... ``` wrappers
    raw_text = re.sub(r'^```(?:json)?\s*', '', raw_text)
    raw_text = re.sub(r'\s*```$', '', raw_text)
    return raw_text.strip()


def generate_gemini_insights_helper(df_filtered):
    """
    Attempts to generate insights using the Gemini API (gemini-3.5-flash).
    - Caches results for 5 minutes to avoid rate limit errors.
    - Gracefully returns None on any failure, triggering the rule-based fallback.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return None

    # --- Cache check ---
    cache_key = _make_cache_key(df_filtered)
    if cache_key in _insights_cache:
        ts, cached = _insights_cache[cache_key]
        if time.time() - ts < CACHE_TTL_SECONDS:
            return cached
        else:
            del _insights_cache[cache_key]

    try:
        # Build compact data summary for the prompt
        total_revenue = float(df_filtered['Sales_Revenue'].sum())
        total_profit = float(
            df_filtered['Total_Profit'].sum()
            if 'Total_Profit' in df_filtered.columns
            else total_revenue * 0.2134
        )
        total_units = int(df_filtered['Units_Sold'].sum())

        region_sales = df_filtered.groupby('Region')['Sales_Revenue'].sum().reset_index()
        region_summary = {row['Region']: float(row['Sales_Revenue']) for _, row in region_sales.iterrows()}

        cat_sales = df_filtered.groupby('Product_Category')['Sales_Revenue'].sum().reset_index()
        cat_summary = {row['Product_Category']: float(row['Sales_Revenue']) for _, row in cat_sales.iterrows()}

        prompt = (
            "You are a professional business intelligence analyst.\n"
            "Analyze the sales data below and return EXACTLY 4 concise actionable insights as a JSON array.\n\n"
            f"Total Revenue: ${total_revenue:,.0f}\n"
            f"Total Profit: ${total_profit:,.0f}\n"
            f"Units Sold: {total_units:,}\n"
            f"Regional Sales: {json.dumps(region_summary)}\n"
            f"Category Sales: {json.dumps(cat_summary)}\n\n"
            "Return ONLY a raw JSON array (no markdown, no code fences). Each element must have:\n"
            '  "icon": one emoji\n'
            '  "text": 1-2 sentence plain text insight (no HTML tags, no apostrophes inside strings)\n'
            "Example: "
            '[{"icon":"📈","text":"Revenue grew strongly this quarter."},{"icon":"🔻","text":"South region lags others."}]'
        )

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.4,
                "maxOutputTokens": 512
            }
        }

        response = requests.post(url, headers=headers, json=payload, timeout=12.0)

        if response.status_code == 200:
            res_json = response.json()
            raw_text = res_json['candidates'][0]['content']['parts'][0]['text']
            raw_text = _clean_json_text(raw_text)

            parsed = json.loads(raw_text)
            if isinstance(parsed, list) and len(parsed) > 0:
                validated = []
                for item in parsed[:4]:
                    icon = item.get("icon", "💡")
                    text = str(item.get("text", "")).strip()
                    if text:
                        # Wrap numbers in colored bold spans for visual consistency
                        text = re.sub(
                            r'\$[\d,]+(?:\.\d+)?[KMB]?',
                            lambda m: f"<b style='color:#00CC96;'>{m.group()}</b>",
                            text
                        )
                        validated.append({"icon": icon, "text": text})
                if validated:
                    _insights_cache[cache_key] = (time.time(), validated)
                    return validated

        elif response.status_code == 429:
            print("Gemini rate limit hit (429). Falling back to rule-based insights.")
        else:
            print(f"Gemini API returned status {response.status_code}: {response.text[:200]}")

    except Exception as e:
        print(f"Gemini API call failed, falling back to rule-based insights: {e}")

    return None
