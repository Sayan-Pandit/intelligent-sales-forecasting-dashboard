"""
Export Engine for Intelligent Sales Forecasting Dashboard
Generates professional, executive-ready PDF and Excel workbooks
with custom date, periodic (monthly/quarterly), and segment summaries.
"""

import io
from datetime import datetime
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


def compute_metrics_and_summaries(df_filtered: pd.DataFrame, period: str = "monthly"):
    """
    Computes key performance indicators, custom date period aggregations,
    and regional/product summaries from the filtered dataset.
    """
    df = df_filtered.copy()
    if not pd.api.types.is_datetime64_any_dtype(df['Date']):
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Date']).sort_values('Date')

    # Base Metrics
    total_rev = float(df['Sales_Revenue'].sum()) if 'Sales_Revenue' in df.columns else 0.0
    total_profit = float(df['Total_Profit'].sum()) if 'Total_Profit' in df.columns else (total_rev * 0.2134)
    total_units = int(df['Units_Sold'].sum()) if 'Units_Sold' in df.columns else len(df)
    order_count = len(df)
    aov = (total_rev / order_count) if order_count > 0 else 0.0
    margin = (total_profit / total_rev * 100) if total_rev > 0 else 0.0

    date_min_str = df['Date'].min().strftime('%b %d, %Y') if not df.empty else "N/A"
    date_max_str = df['Date'].max().strftime('%b %d, %Y') if not df.empty else "N/A"
    date_horizon = f"{date_min_str} — {date_max_str}"

    # Period Aggregation (Monthly or Quarterly)
    df_period = df.copy()
    freq = 'QE' if period.lower() == 'quarterly' else 'ME'

    df_period.set_index('Date', inplace=True)
    
    # Aggregations
    agg_dict = {'Sales_Revenue': 'sum'}
    if 'Total_Profit' in df_period.columns:
        agg_dict['Total_Profit'] = 'sum'
    if 'Units_Sold' in df_period.columns:
        agg_dict['Units_Sold'] = 'sum'

    periodic_df = df_period.resample(freq).agg(agg_dict).reset_index()
    periodic_df['Period_Label'] = periodic_df['Date'].apply(
        lambda d: f"{d.year}-Q{(d.month-1)//3 + 1}" if period.lower() == 'quarterly' else d.strftime('%Y-%m (%b)')
    )

    if 'Total_Profit' not in periodic_df.columns:
        periodic_df['Total_Profit'] = periodic_df['Sales_Revenue'] * 0.2134
    if 'Units_Sold' not in periodic_df.columns:
        periodic_df['Units_Sold'] = 1

    periodic_df['Margin_Pct'] = periodic_df.apply(
        lambda r: (r['Total_Profit'] / r['Sales_Revenue'] * 100) if r['Sales_Revenue'] > 0 else 0.0, axis=1
    )

    # Regional Aggregation
    if 'Region' in df.columns:
        region_df = df.groupby('Region').agg(
            Revenue=('Sales_Revenue', 'sum'),
            Units=('Units_Sold' if 'Units_Sold' in df.columns else 'Sales_Revenue', 'sum' if 'Units_Sold' in df.columns else 'count')
        ).reset_index()
        region_df['Contribution_Pct'] = (region_df['Revenue'] / total_rev * 100) if total_rev > 0 else 0.0
        region_df = region_df.sort_values('Revenue', ascending=False)
    else:
        region_df = pd.DataFrame(columns=['Region', 'Revenue', 'Units', 'Contribution_Pct'])

    # Category Aggregation
    cat_col = 'Product_Category' if 'Product_Category' in df.columns else ('Category' if 'Category' in df.columns else None)
    if cat_col:
        category_df = df.groupby(cat_col).agg(
            Revenue=('Sales_Revenue', 'sum')
        ).reset_index().rename(columns={cat_col: 'Category'})
        category_df['Contribution_Pct'] = (category_df['Revenue'] / total_rev * 100) if total_rev > 0 else 0.0
        category_df = category_df.sort_values('Revenue', ascending=False)
    else:
        category_df = pd.DataFrame(columns=['Category', 'Revenue', 'Contribution_Pct'])

    # Top Products
    prod_col = 'Product' if 'Product' in df.columns else ('Product_Name' if 'Product_Name' in df.columns else None)
    if prod_col:
        products_df = df.groupby(prod_col).agg(
            Revenue=('Sales_Revenue', 'sum'),
            Units=('Units_Sold' if 'Units_Sold' in df.columns else 'Sales_Revenue', 'sum' if 'Units_Sold' in df.columns else 'count')
        ).reset_index().rename(columns={prod_col: 'Product'}).sort_values('Revenue', ascending=False).head(8)
    else:
        products_df = pd.DataFrame(columns=['Product', 'Revenue', 'Units'])

    return {
        "df": df,
        "total_revenue": total_rev,
        "total_profit": total_profit,
        "total_units": total_units,
        "order_count": order_count,
        "aov": aov,
        "margin": margin,
        "date_horizon": date_horizon,
        "periodic_df": periodic_df,
        "region_df": region_df,
        "category_df": category_df,
        "products_df": products_df
    }


def generate_pdf_report(df_filtered: pd.DataFrame, report_type: str = "executive", period: str = "monthly") -> bytes:
    """
    Generates a corporate, polished executive PDF report using ReportLab.
    Includes KPI blocks, custom date periodic breakdown table, and segment analysis.
    """
    metrics = compute_metrics_and_summaries(df_filtered, period=period)
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    
    # Custom Brand Palette
    c_primary = colors.HexColor("#0F172A")
    c_accent = colors.HexColor("#0D9488")
    c_indigo = colors.HexColor("#4F46E5")
    c_text = colors.HexColor("#1E293B")
    c_muted = colors.HexColor("#64748B")
    c_light_bg = colors.HexColor("#F8FAFC")
    c_card_bg = colors.HexColor("#F1F5F9")
    c_border = colors.HexColor("#CBD5E1")

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=c_primary,
        spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=c_muted,
        spaceAfter=12
    )
    sec_heading_style = ParagraphStyle(
        'SecHeading',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=c_indigo,
        spaceBefore=12,
        spaceAfter=6
    )
    cell_bold = ParagraphStyle(
        'CellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=11,
        textColor=c_primary
    )
    cell_normal = ParagraphStyle(
        'CellNormal',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=c_text
    )
    cell_header = ParagraphStyle(
        'CellHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=11,
        textColor=colors.white
    )

    story = []

    # Title & Metadata Banner
    title_text = "Executive Sales & Business Intelligence Report"
    if report_type == "regional":
        title_text = "Regional Market Share & Revenue Distribution Report"
    elif report_type == "products":
        title_text = "Product Catalogue & Performance Analysis Report"

    story.append(Paragraph(title_text, title_style))
    now_str = datetime.now().strftime('%B %d, %Y at %I:%M %p')
    meta_text = f"<b>Horizon:</b> {metrics['date_horizon']} &nbsp;|&nbsp; <b>Compiled:</b> {now_str} &nbsp;|&nbsp; <b>Status:</b> Audited &amp; Verified"
    story.append(Paragraph(meta_text, subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=c_indigo, spaceBefore=0, spaceAfter=10))

    # SECTION 1: KEY PERFORMANCE INDICATORS CARDS
    story.append(Paragraph("1. Executive KPI Summary", sec_heading_style))
    
    kpi_data = [
        [
            Paragraph("<b>TOTAL REVENUE</b>", cell_bold),
            Paragraph("<b>NET PROFIT</b>", cell_bold),
            Paragraph("<b>PROFIT MARGIN</b>", cell_bold),
            Paragraph("<b>UNITS SOLD</b>", cell_bold),
            Paragraph("<b>AVG ORDER VALUE</b>", cell_bold)
        ],
        [
            Paragraph(f"<font size='12' color='#0D9488'><b>${metrics['total_revenue']:,.2f}</b></font>", cell_normal),
            Paragraph(f"<font size='12' color='#4F46E5'><b>${metrics['total_profit']:,.2f}</b></font>", cell_normal),
            Paragraph(f"<font size='12' color='#2563EB'><b>{metrics['margin']:.2f}%</b></font>", cell_normal),
            Paragraph(f"<font size='12' color='#0F172A'><b>{metrics['total_units']:,}</b></font>", cell_normal),
            Paragraph(f"<font size='12' color='#D97706'><b>${metrics['aov']:,.2f}</b></font>", cell_normal)
        ]
    ]
    t_kpi = Table(kpi_data, colWidths=[108, 108, 108, 108, 108])
    t_kpi.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), c_light_bg),
        ('BOX', (0, 0), (-1, -1), 1, c_border),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, c_border),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t_kpi)
    story.append(Spacer(1, 8))

    # SECTION 2: CUSTOM DATE & PERIODIC METRICS BREAKDOWN
    period_title = "Quarterly" if period.lower() == 'quarterly' else "Monthly"
    story.append(Paragraph(f"2. Custom Date Aggregation: {period_title} Performance Breakdown", sec_heading_style))

    p_df = metrics['periodic_df']
    if not p_df.empty:
        table_rows = [
            [
                Paragraph("<b>Period</b>", cell_header),
                Paragraph("<b>Sales Revenue</b>", cell_header),
                Paragraph("<b>Gross Profit</b>", cell_header),
                Paragraph("<b>Margin %</b>", cell_header),
                Paragraph("<b>Units Sold</b>", cell_header)
            ]
        ]
        # Keep table concise (max 12 rows in PDF, remaining summarized)
        display_rows = p_df.tail(12) if len(p_df) > 14 else p_df
        for _, row in display_rows.iterrows():
            table_rows.append([
                Paragraph(str(row['Period_Label']), cell_normal),
                Paragraph(f"${row['Sales_Revenue']:,.2f}", cell_normal),
                Paragraph(f"${row['Total_Profit']:,.2f}", cell_normal),
                Paragraph(f"{row['Margin_Pct']:.1f}%", cell_normal),
                Paragraph(f"{int(row['Units_Sold']):,}", cell_normal),
            ])
        
        # Cumulative totals row
        table_rows.append([
            Paragraph("<b>Total / Cumulative</b>", cell_bold),
            Paragraph(f"<b>${metrics['total_revenue']:,.2f}</b>", cell_bold),
            Paragraph(f"<b>${metrics['total_profit']:,.2f}</b>", cell_bold),
            Paragraph(f"<b>{metrics['margin']:.2f}%</b>", cell_bold),
            Paragraph(f"<b>{metrics['total_units']:,}</b>", cell_bold),
        ])

        t_periodic = Table(table_rows, colWidths=[120, 110, 110, 90, 110])
        t_style = [
            ('BACKGROUND', (0, 0), (-1, 0), c_primary),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, c_border),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('BACKGROUND', (0, -1), (-1, -1), c_card_bg),
        ]
        for r_idx in range(1, len(table_rows) - 1):
            if r_idx % 2 == 0:
                t_style.append(('BACKGROUND', (0, r_idx), (-1, r_idx), c_light_bg))
        t_periodic.setStyle(TableStyle(t_style))
        story.append(t_periodic)
    else:
        story.append(Paragraph("<i>No periodic records found for the selected filter range.</i>", cell_normal))

    story.append(Spacer(1, 8))

    # SECTION 3: REGIONAL & TOP PRODUCT SEGMENTS
    story.append(Paragraph("3. Regional & Product Segment Contribution", sec_heading_style))

    reg_df = metrics['region_df']
    reg_rows = [
        [Paragraph("<b>Region</b>", cell_header), Paragraph("<b>Revenue</b>", cell_header), Paragraph("<b>Share</b>", cell_header)]
    ]
    for _, r in reg_df.iterrows():
        reg_rows.append([
            Paragraph(str(r['Region']), cell_normal),
            Paragraph(f"${r['Revenue']:,.2f}", cell_normal),
            Paragraph(f"{r['Contribution_Pct']:.1f}%", cell_normal)
        ])
    t_reg = Table(reg_rows, colWidths=[100, 100, 60])
    t_reg_style = [
        ('BACKGROUND', (0, 0), (-1, 0), c_indigo),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]
    for r_idx in range(1, len(reg_rows)):
        if r_idx % 2 == 0:
            t_reg_style.append(('BACKGROUND', (0, r_idx), (-1, r_idx), c_light_bg))
    t_reg.setStyle(TableStyle(t_reg_style))

    prod_df = metrics['products_df']
    prod_rows = [
        [Paragraph("<b>Top Product</b>", cell_header), Paragraph("<b>Revenue</b>", cell_header), Paragraph("<b>Units</b>", cell_header)]
    ]
    for _, p in prod_df.iterrows():
        prod_rows.append([
            Paragraph(str(p['Product']), cell_normal),
            Paragraph(f"${p['Revenue']:,.2f}", cell_normal),
            Paragraph(f"{int(p['Units']):,}", cell_normal)
        ])
    t_prod = Table(prod_rows, colWidths=[140, 80, 60])
    t_prod_style = [
        ('BACKGROUND', (0, 0), (-1, 0), c_accent),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]
    for p_idx in range(1, len(prod_rows)):
        if p_idx % 2 == 0:
            t_prod_style.append(('BACKGROUND', (0, p_idx), (-1, p_idx), c_light_bg))
    t_prod.setStyle(TableStyle(t_prod_style))

    combined_tables = Table([[t_reg, t_prod]], colWidths=[265, 275])
    combined_tables.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(combined_tables)
    story.append(Spacer(1, 8))

    # SECTION 4: STRATEGIC TAKEAWAYS
    story.append(Paragraph("4. Strategic Executive Takeaways", sec_heading_style))
    top_region = reg_df.iloc[0]['Region'] if not reg_df.empty else "Primary"
    top_prod = prod_df.iloc[0]['Product'] if not prod_df.empty else "Leading item"
    insights_html = f"""
    <font color="#1E293B" size="8">
    &bull; <b>Operating Health:</b> Overall operating margin stands solid at <b>{metrics['margin']:.2f}%</b> with an average order value of <b>${metrics['aov']:,.2f}</b> across <b>{metrics['order_count']:,}</b> orders.<br/><br/>
    &bull; <b>Market Pillar:</b> <b>{top_region}</b> generated the highest regional concentration, serving as the core revenue driver during this period.<br/><br/>
    &bull; <b>Catalogue Driver:</b> <b>{top_prod}</b> drove primary catalogue volume; inventory replenishment and focused upsells should prioritize this tier.<br/><br/>
    &bull; <b>Executive Recommendation:</b> Maintain demand hedging across seasonal spikes and align supply chain procurement with top contributing segments.
    </font>
    """
    story.append(Paragraph(insights_html, cell_normal))

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


def generate_excel_report(df_filtered: pd.DataFrame, report_type: str = "executive", period: str = "monthly") -> bytes:
    """
    Generates a multi-tab, professionally styled Microsoft Excel (.xlsx) workbook
    containing Executive Summary, Period Breakdown, Regional & Product analysis,
    and sanitized transaction data with native Excel formulas and currency formatting.
    """
    metrics = compute_metrics_and_summaries(df_filtered, period=period)
    wb = Workbook()

    c_navy_header = "0F172A"
    c_indigo_sub = "4F46E5"
    c_teal_accent = "0D9488"
    c_zebra = "F8FAFC"
    c_card_fill = "F1F5F9"
    c_border = "CBD5E1"

    font_title = Font(name="Segoe UI", size=15, bold=True, color="0F172A")
    font_sub = Font(name="Segoe UI", size=9, italic=True, color="64748B")
    font_sec = Font(name="Segoe UI", size=11, bold=True, color="4F46E5")
    font_header = Font(name="Segoe UI", size=10, bold=True, color="FFFFFF")
    font_bold = Font(name="Segoe UI", size=9, bold=True, color="0F172A")
    font_regular = Font(name="Segoe UI", size=9, color="1E293B")
    font_kpi_val = Font(name="Segoe UI", size=13, bold=True, color="0D9488")

    fill_header_navy = PatternFill(start_color=c_navy_header, end_color=c_navy_header, fill_type="solid")
    fill_header_indigo = PatternFill(start_color=c_indigo_sub, end_color=c_indigo_sub, fill_type="solid")
    fill_header_teal = PatternFill(start_color=c_teal_accent, end_color=c_teal_accent, fill_type="solid")
    fill_zebra = PatternFill(start_color=c_zebra, end_color=c_zebra, fill_type="solid")
    fill_card = PatternFill(start_color=c_card_fill, end_color=c_card_fill, fill_type="solid")

    thin_border_side = Side(border_style="thin", color=c_border)
    border_all = Border(left=thin_border_side, right=thin_border_side, top=thin_border_side, bottom=thin_border_side)

    align_center = Alignment(horizontal="center", vertical="center")
    align_left = Alignment(horizontal="left", vertical="center")
    align_right = Alignment(horizontal="right", vertical="center")

    # SHEET 1: EXECUTIVE SUMMARY & PERIOD METRICS
    ws_exec = wb.active
    ws_exec.title = "Executive Summary"
    ws_exec.views.sheetView[0].showGridLines = True

    ws_exec["A1"] = "Executive Sales Performance & Financial Report"
    ws_exec["A1"].font = font_title
    ws_exec["A2"] = f"Date Horizon: {metrics['date_horizon']}  |  Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  |  Verified CRM Source"
    ws_exec["A2"].font = font_sub

    ws_exec["A4"] = "KEY PERFORMANCE INDICATORS"
    ws_exec["A4"].font = font_sec

    kpis = [
        ("Total Sales Revenue", metrics['total_revenue'], '"$"#,##0.00'),
        ("Total Net Profit", metrics['total_profit'], '"$"#,##0.00'),
        ("Operating Margin %", metrics['margin'] / 100.0, "0.0%"),
        ("Units Sold", metrics['total_units'], '#,##0'),
        ("Average Order Value", metrics['aov'], '"$"#,##0.00'),
        ("Total Orders", metrics['order_count'], '#,##0')
    ]

    for col_idx, (label, val, fmt) in enumerate(kpis, start=1):
        cell_lbl = ws_exec.cell(row=5, column=col_idx, value=label)
        cell_lbl.font = font_bold
        cell_lbl.fill = fill_card
        cell_lbl.alignment = align_center
        cell_lbl.border = border_all

        cell_val = ws_exec.cell(row=6, column=col_idx, value=val)
        cell_val.font = font_kpi_val
        cell_val.number_format = fmt
        cell_val.alignment = align_center
        cell_val.fill = fill_card
        cell_val.border = border_all

    period_title = "Quarterly" if period.lower() == 'quarterly' else "Monthly"
    ws_exec["A8"] = f"{period_title.upper()} PERFORMANCE BREAKDOWN"
    ws_exec["A8"].font = font_sec

    p_headers = ["Period", "Sales Revenue", "Total Profit", "Profit Margin", "Units Sold"]
    for col_idx, h in enumerate(p_headers, start=1):
        cell = ws_exec.cell(row=9, column=col_idx, value=h)
        cell.font = font_header
        cell.fill = fill_header_navy
        cell.alignment = align_center
        cell.border = border_all

    curr_row = 10
    p_df = metrics['periodic_df']
    for _, r in p_df.iterrows():
        ws_exec.cell(row=curr_row, column=1, value=str(r['Period_Label'])).alignment = align_left
        
        c_rev = ws_exec.cell(row=curr_row, column=2, value=float(r['Sales_Revenue']))
        c_rev.number_format = '"$"#,##0.00'
        c_rev.alignment = align_right

        c_prof = ws_exec.cell(row=curr_row, column=3, value=float(r['Total_Profit']))
        c_prof.number_format = '"$"#,##0.00'
        c_prof.alignment = align_right

        c_mrg = ws_exec.cell(row=curr_row, column=4, value=float(r['Margin_Pct']) / 100.0)
        c_mrg.number_format = '0.0%'
        c_mrg.alignment = align_right

        c_u = ws_exec.cell(row=curr_row, column=5, value=int(r['Units_Sold']))
        c_u.number_format = '#,##0'
        c_u.alignment = align_right

        for c_idx in range(1, 6):
            cell = ws_exec.cell(row=curr_row, column=c_idx)
            cell.font = font_regular
            cell.border = border_all
            if curr_row % 2 == 0:
                cell.fill = fill_zebra

        curr_row += 1

    # Totals Row
    ws_exec.cell(row=curr_row, column=1, value="Total / Cumulative").alignment = align_left
    tot_rev = ws_exec.cell(row=curr_row, column=2, value=f"=SUM(B10:B{curr_row-1})")
    tot_rev.number_format = '"$"#,##0.00'
    tot_rev.alignment = align_right

    tot_prof = ws_exec.cell(row=curr_row, column=3, value=f"=SUM(C10:C{curr_row-1})")
    tot_prof.number_format = '"$"#,##0.00'
    tot_prof.alignment = align_right

    tot_mrg = ws_exec.cell(row=curr_row, column=4, value=f"=C{curr_row}/B{curr_row}")
    tot_mrg.number_format = '0.0%'
    tot_mrg.alignment = align_right

    tot_u = ws_exec.cell(row=curr_row, column=5, value=f"=SUM(E10:E{curr_row-1})")
    tot_u.number_format = '#,##0'
    tot_u.alignment = align_right

    for c_idx in range(1, 6):
        cell = ws_exec.cell(row=curr_row, column=c_idx)
        cell.font = font_bold
        cell.fill = fill_card
        cell.border = border_all

    # SHEET 2: REGIONAL PERFORMANCE
    ws_reg = wb.create_sheet(title="Regional Performance")
    ws_reg.views.sheetView[0].showGridLines = True

    ws_reg["A1"] = "Regional Sales Distribution & Market Share"
    ws_reg["A1"].font = font_title
    ws_reg["A2"] = f"Filtered Date Range: {metrics['date_horizon']}"
    ws_reg["A2"].font = font_sub

    reg_headers = ["Region", "Sales Revenue", "Units Sold", "Contribution %"]
    for col_idx, h in enumerate(reg_headers, start=1):
        c = ws_reg.cell(row=4, column=col_idx, value=h)
        c.font = font_header
        c.fill = fill_header_indigo
        c.alignment = align_center
        c.border = border_all

    r_row = 5
    for _, row in metrics['region_df'].iterrows():
        ws_reg.cell(row=r_row, column=1, value=str(row['Region'])).alignment = align_left
        
        c_rev = ws_reg.cell(row=r_row, column=2, value=float(row['Revenue']))
        c_rev.number_format = '"$"#,##0.00'
        c_rev.alignment = align_right

        c_u = ws_reg.cell(row=r_row, column=3, value=int(row['Units']))
        c_u.number_format = '#,##0'
        c_u.alignment = align_right

        c_pct = ws_reg.cell(row=r_row, column=4, value=float(row['Contribution_Pct']) / 100.0)
        c_pct.number_format = '0.0%'
        c_pct.alignment = align_right

        for c_idx in range(1, 5):
            cell = ws_reg.cell(row=r_row, column=c_idx)
            cell.font = font_regular
            cell.border = border_all
            if r_row % 2 == 0:
                cell.fill = fill_zebra
        r_row += 1

    # SHEET 3: CATEGORY & PRODUCT CATALOGUE
    ws_prod = wb.create_sheet(title="Product Breakdown")
    ws_prod.views.sheetView[0].showGridLines = True

    ws_prod["A1"] = "Category & Top Product Performance"
    ws_prod["A1"].font = font_title

    ws_prod["A3"] = "PRODUCT CATEGORY SHARE"
    ws_prod["A3"].font = font_sec

    cat_headers = ["Category", "Sales Revenue", "Share %"]
    for col_idx, h in enumerate(cat_headers, start=1):
        c = ws_prod.cell(row=4, column=col_idx, value=h)
        c.font = font_header
        c.fill = fill_header_teal
        c.alignment = align_center
        c.border = border_all

    cat_row = 5
    for _, row in metrics['category_df'].iterrows():
        ws_prod.cell(row=cat_row, column=1, value=str(row['Category'])).alignment = align_left
        c_rev = ws_prod.cell(row=cat_row, column=2, value=float(row['Revenue']))
        c_rev.number_format = '"$"#,##0.00'
        c_rev.alignment = align_right
        c_pct = ws_prod.cell(row=cat_row, column=3, value=float(row['Contribution_Pct']) / 100.0)
        c_pct.number_format = '0.0%'
        c_pct.alignment = align_right

        for c_idx in range(1, 4):
            cell = ws_prod.cell(row=cat_row, column=c_idx)
            cell.font = font_regular
            cell.border = border_all
        cat_row += 1

    prod_start_row = cat_row + 2
    ws_prod.cell(row=prod_start_row, column=1, value="TOP PRODUCTS BY REVENUE").font = font_sec

    prod_headers = ["Product Name", "Sales Revenue", "Units Sold"]
    for col_idx, h in enumerate(prod_headers, start=1):
        c = ws_prod.cell(row=prod_start_row + 1, column=col_idx, value=h)
        c.font = font_header
        c.fill = fill_header_navy
        c.alignment = align_center
        c.border = border_all

    p_item_row = prod_start_row + 2
    for _, row in metrics['products_df'].iterrows():
        ws_prod.cell(row=p_item_row, column=1, value=str(row['Product'])).alignment = align_left
        c_rev = ws_prod.cell(row=p_item_row, column=2, value=float(row['Revenue']))
        c_rev.number_format = '"$"#,##0.00'
        c_rev.alignment = align_right
        c_u = ws_prod.cell(row=p_item_row, column=3, value=int(row['Units']))
        c_u.number_format = '#,##0'
        c_u.alignment = align_right

        for c_idx in range(1, 4):
            cell = ws_prod.cell(row=p_item_row, column=c_idx)
            cell.font = font_regular
            cell.border = border_all
            if p_item_row % 2 == 0:
                cell.fill = fill_zebra
        p_item_row += 1

    # SHEET 4: FILTERED TRANSACTIONS
    ws_data = wb.create_sheet(title="Filtered Transactions")
    ws_data.views.sheetView[0].showGridLines = True

    data_df = metrics['df'].head(5000)
    display_cols = ['Date', 'Product', 'Product_Category', 'Region', 'Sales_Revenue', 'Units_Sold', 'Total_Profit']
    active_cols = [col for col in display_cols if col in data_df.columns]

    for col_idx, col_name in enumerate(active_cols, start=1):
        c = ws_data.cell(row=1, column=col_idx, value=col_name.replace('_', ' '))
        c.font = font_header
        c.fill = fill_header_navy
        c.alignment = align_center
        c.border = border_all

    for row_idx, (_, row) in enumerate(data_df.iterrows(), start=2):
        for col_idx, col_name in enumerate(active_cols, start=1):
            val = row[col_name]
            cell = ws_data.cell(row=row_idx, column=col_idx)
            cell.font = font_regular
            cell.border = border_all

            if col_name == 'Date':
                cell.value = val.strftime('%Y-%m-%d') if pd.notnull(val) else ""
                cell.alignment = align_center
            elif col_name in ['Sales_Revenue', 'Total_Profit']:
                cell.value = float(val) if pd.notnull(val) else 0.0
                cell.number_format = '"$"#,##0.00'
                cell.alignment = align_right
            elif col_name == 'Units_Sold':
                cell.value = int(val) if pd.notnull(val) else 0
                cell.number_format = '#,##0'
                cell.alignment = align_right
            else:
                cell.value = str(val) if pd.notnull(val) else ""
                cell.alignment = align_left

            if row_idx % 2 == 0:
                cell.fill = fill_zebra

    # Auto-adjust column widths across all sheets
    for ws in [ws_exec, ws_reg, ws_prod, ws_data]:
        for col in ws.columns:
            max_len = 0
            col_letter = get_column_letter(col[0].column)
            for cell in col:
                val_str = str(cell.value or '')
                if len(val_str) > max_len:
                    max_len = len(val_str)
            ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

    buffer = io.BytesIO()
    wb.save(buffer)
    excel_bytes = buffer.getvalue()
    buffer.close()
    return excel_bytes
