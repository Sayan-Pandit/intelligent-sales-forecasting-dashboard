// State variables
let activeTab = 'dashboard';
let config = { min_date: '2023-01-01', max_date: '2026-06-30', regions: [], categories: [] };
let activeFilters = {
    start_date: '',
    end_date: '',
    regions: [],
    categories: []
};
let dashboardData = null;

// DOM Elements
const menuItems = document.querySelectorAll('.menu-item');
const panels = document.querySelectorAll('.tab-panel');
const pageTitle = document.getElementById('page-title');

const startDateInput = document.getElementById('filter-start-date');
const endDateInput = document.getElementById('filter-end-date');
const regionSelect = document.getElementById('filter-region');
const categorySelect = document.getElementById('filter-category');
const repSelect = document.getElementById('filter-rep');
const btnResetFilters = document.getElementById('btn-reset-filters');
const displayDateRange = document.getElementById('display-date-range');

// Data Source Elements
const dataSourceSelect = document.getElementById('data-source-select');
const uploadContainer = document.getElementById('upload-container');
const fileUploader = document.getElementById('file-uploader');
const mappingContainer = document.getElementById('mapping-container');
const mappingDate = document.getElementById('mapping-date');
const mappingSales = document.getElementById('mapping-sales');


// Forecast simulator sliders
const simDiscount = document.getElementById('sim-discount');
const simMarketing = document.getElementById('sim-marketing');
const simPrice = document.getElementById('sim-price');
const valSimDiscount = document.getElementById('val-sim-discount');
const valSimMarketing = document.getElementById('val-sim-marketing');
const valSimPrice = document.getElementById('val-sim-price');
const simPredictedVal = document.getElementById('sim-predicted-sales');
const simPredictedChange = document.getElementById('sim-predicted-change');

// Page Navigation
menuItems.forEach(item => {
    item.addEventListener('click', () => {
        menuItems.forEach(mi => mi.classList.remove('active'));
        item.classList.add('active');
        
        const tab = item.getAttribute('data-tab');
        activeTab = tab;
        
        // Update Title
        pageTitle.textContent = tab.charAt(0).toUpperCase() + tab.slice(1);
        
        // Show panel
        panels.forEach(p => p.classList.remove('active'));
        
        let targetPanel = document.getElementById(`panel-${tab}`);
        if (!targetPanel) {
            targetPanel = document.getElementById('panel-placeholder');
            document.getElementById('placeholder-title').textContent = tab.charAt(0).toUpperCase() + tab.slice(1);
        }
        targetPanel.classList.add('active');
        
        if (tab === 'dashboard') {
            loadDashboard();
        } else if (tab === 'analytics') {
            // Trigger Plotly charts resize to fit layout correctly
            setTimeout(() => {
                window.dispatchEvent(new Event('resize'));
            }, 100);
        } else if (tab === 'products') {
            loadProductsPanel();
        }
    });
});

// Initial load
window.addEventListener('DOMContentLoaded', async () => {
    await fetchConfig();
    setupFilters();
    loadDashboard();
});

// Setup filter listeners
function setupFilters() {
    startDateInput.addEventListener('change', (e) => {
        activeFilters.start_date = e.target.value;
        loadDashboard();
    });
    endDateInput.addEventListener('change', (e) => {
        activeFilters.end_date = e.target.value;
        loadDashboard();
    });
    regionSelect.addEventListener('change', (e) => {
        activeFilters.regions = e.target.value === 'All Regions' ? [] : [e.target.value];
        loadDashboard();
    });
    categorySelect.addEventListener('change', (e) => {
        activeFilters.categories = e.target.value === 'All Categories' ? [] : [e.target.value];
        loadDashboard();
    });
    
    btnResetFilters.addEventListener('click', () => {
        startDateInput.value = config.min_date;
        endDateInput.value = config.max_date;
        regionSelect.value = 'All Regions';
        categorySelect.value = 'All Categories';
        repSelect.value = 'All Representatives';
        
        activeFilters.start_date = config.min_date;
        activeFilters.end_date = config.max_date;
        activeFilters.regions = [];
        activeFilters.categories = [];
        
        loadDashboard();
    });
    
    // Simulator controls
    simDiscount.addEventListener('input', (e) => {
        valSimDiscount.textContent = `${e.target.value}%`;
        runSimulator();
    });
    simMarketing.addEventListener('input', (e) => {
        valSimMarketing.textContent = `$${e.target.value}K`;
        runSimulator();
    });
    simPrice.addEventListener('input', (e) => {
        valSimPrice.textContent = `${e.target.value}%`;
        runSimulator();
    });

    // Data Source Handlers
    dataSourceSelect.addEventListener('change', async (e) => {
        const val = e.target.value;
        if (val === 'sample') {
            try {
                await fetch('/api/reset-datasource', { method: 'POST' });
            } catch (err) {
                console.error('Error resetting datasource:', err);
            }
            uploadContainer.style.display = 'none';
            mappingContainer.style.display = 'none';
            
            delete activeFilters.date_col;
            delete activeFilters.sales_col;
            
            await fetchConfig();
            loadDashboard();
        } else {
            uploadContainer.style.display = 'block';
        }
    });

    fileUploader.addEventListener('change', async (e) => {
        const file = e.target.files[0];
        if (!file) return;
        
        const formData = new FormData();
        formData.append('file', file);
        
        try {
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                const err = await response.json();
                alert(`Upload failed: ${err.detail || 'Server error'}`);
                return;
            }
            
            const data = await response.json();
            if (data.success) {
                mappingContainer.style.display = 'block';
                
                mappingDate.innerHTML = '';
                mappingSales.innerHTML = '';
                
                data.columns.forEach(col => {
                    const optDate = document.createElement('option');
                    optDate.value = col;
                    optDate.textContent = col;
                    if (col === data.suggested_date) optDate.selected = true;
                    mappingDate.appendChild(optDate);
                    
                    const optSales = document.createElement('option');
                    optSales.value = col;
                    optSales.textContent = col;
                    if (col === data.suggested_sales) optSales.selected = true;
                    mappingSales.appendChild(optSales);
                });
                
                activeFilters.date_col = mappingDate.value;
                activeFilters.sales_col = mappingSales.value;
                
                await fetchConfig();
                loadDashboard();
            }
        } catch (err) {
            console.error('Error uploading file:', err);
            alert('Failed to upload file. Please try again.');
        }
    });

    mappingDate.addEventListener('change', async () => {
        activeFilters.date_col = mappingDate.value;
        await fetchConfig();
        loadDashboard();
    });

    mappingSales.addEventListener('change', async () => {
        activeFilters.sales_col = mappingSales.value;
        await fetchConfig();
        loadDashboard();
    });
}

// Fetch Initial Configs
async function fetchConfig() {
    try {
        let url = '/api/config';
        const params = [];
        if (activeFilters.date_col) params.push(`date_col=${encodeURIComponent(activeFilters.date_col)}`);
        if (activeFilters.sales_col) params.push(`sales_col=${encodeURIComponent(activeFilters.sales_col)}`);
        if (params.length > 0) {
            url += '?' + params.join('&');
        }
        
        const response = await fetch(url);
        config = await response.json();
        
        startDateInput.value = config.min_date;
        endDateInput.value = config.max_date;
        
        activeFilters.start_date = config.min_date;
        activeFilters.end_date = config.max_date;
        
        // Populate Regions Select
        regionSelect.innerHTML = '<option value="All Regions">All Regions</option>';
        config.regions.forEach(r => {
            const opt = document.createElement('option');
            opt.value = r;
            opt.textContent = r;
            regionSelect.appendChild(opt);
        });
        
        // Populate Categories Select
        categorySelect.innerHTML = '<option value="All Categories">All Categories</option>';
        config.categories.forEach(c => {
            const opt = document.createElement('option');
            opt.value = c;
            opt.textContent = c;
            categorySelect.appendChild(opt);
        });
    } catch (e) {
        console.error('Error fetching config:', e);
    }
}

// Load Dashboard data
async function loadDashboard() {
    try {
        const response = await fetch('/api/dashboard', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(activeFilters)
        });
        
        dashboardData = await response.json();
        if (dashboardData.error) {
            alert(dashboardData.error);
            return;
        }
        
        // Update header dates
        const sDate = new Date(activeFilters.start_date);
        const eDate = new Date(activeFilters.end_date);
        displayDateRange.textContent = `${sDate.toLocaleDateString('en-US', {month:'short', day:'numeric', year:'numeric'})} - ${eDate.toLocaleDateString('en-US', {month:'short', day:'numeric', year:'numeric'})}`;
        
        updateKPIs(dashboardData.kpis);
        renderSalesTrendChart(dashboardData.trend);
        renderRegionalMap(dashboardData.map);
        renderTopProducts(dashboardData.products);
        renderInsights(dashboardData.insights);
        renderCategoryDonut(dashboardData.categories);
        renderModelComparison(dashboardData.performance);
        updateSidebarForecast(dashboardData.sidebar_forecast);
        updateDataSummary(dashboardData.summary);
        runSimulator(); // trigger initial simulator render
        
        // Resize charts to fit viewport container
        window.dispatchEvent(new Event('resize'));
    } catch (e) {
        console.error('Error loading dashboard:', e);
    }
}

// Update KPI cards UI
function updateKPIs(kpis) {
    document.getElementById('kpi-revenue').textContent = `$${(kpis.revenue / 1e6).toFixed(2)}M`;
    document.getElementById('kpi-revenue-growth').innerHTML = `▲ +${kpis.revenue_growth.toFixed(1)}% <span style='color:#8C8C9A; font-weight:normal;'>vs last year</span>`;
    
    document.getElementById('kpi-profit').textContent = `$${(kpis.profit / 1e3).toFixed(1)}K`;
    document.getElementById('kpi-profit-growth').innerHTML = `▲ +${kpis.profit_growth.toFixed(1)}% <span style='color:#8C8C9A; font-weight:normal;'>vs last year</span>`;
    
    document.getElementById('kpi-units').textContent = kpis.units.toLocaleString();
    document.getElementById('kpi-units-growth').innerHTML = `▲ +${kpis.units_growth.toFixed(1)}% <span style='color:#8C8C9A; font-weight:normal;'>vs last year</span>`;
    
    document.getElementById('kpi-aov').textContent = `$${kpis.aov.toFixed(2)}`;
    document.getElementById('kpi-aov-growth').innerHTML = `▲ +${kpis.aov_growth.toFixed(1)}% <span style='color:#8C8C9A; font-weight:normal;'>vs last year</span>`;
    
    document.getElementById('kpi-margin').textContent = `${kpis.margin.toFixed(2)}%`;
    document.getElementById('kpi-margin-growth').innerHTML = `▲ +${kpis.margin_growth.toFixed(1)}% <span style='color:#8C8C9A; font-weight:normal;'>vs last year</span>`;
}

// Update sidebar forecast
function updateSidebarForecast(fc) {
    document.getElementById('sb-fc-value').textContent = `$${(fc.val / 1e6).toFixed(2)}M`;
    document.getElementById('sb-fc-growth').innerHTML = `▲ +${fc.growth.toFixed(1)}% <span style="color:#8C8C9A; font-weight:normal;">from last 3m</span>`;
    
    // Render sidebar sparkline (plotly style)
    const trace = {
        x: Array.from({length: fc.sparkline.length}, (_, i) => i),
        y: fc.sparkline,
        type: 'scatter',
        mode: 'lines',
        line: { color: '#AB63FA', width: 2 },
        fill: 'tozeroy',
        fillcolor: 'rgba(171, 99, 250, 0.1)'
    };
    const layout = {
        xaxis: { visible: false },
        yaxis: { visible: false },
        margin: { l: 0, r: 0, t: 0, b: 0 },
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        height: 35
    };
    Plotly.newPlot('sb-sparkline-chart', [trace], layout, {displayModeBar: false});
}

// Render Sales Trend Chart
function renderSalesTrendChart(trend) {
    const dates = trend.map(t => t.date);
    const revs = trend.map(t => t.revenue);
    
    const trace = {
        x: dates,
        y: revs,
        type: 'scatter',
        mode: 'lines+markers',
        name: 'Actual Sales',
        line: { color: '#636EFA', width: 3 },
        marker: { size: 6, color: '#636EFA' }
    };
    
    const layout = {
        title: { text: 'Sales Trend Overview', font: { color: '#FFFFFF', size: 14, family: 'Outfit' } },
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: { color: '#E0E0E6', family: 'Outfit' },
        xaxis: { gridcolor: '#2B2B3D', linecolor: '#2B2B3D', tickfont: {color:'#8C8C9A'} },
        yaxis: { gridcolor: '#2B2B3D', linecolor: '#2B2B3D', tickfont: {color:'#8C8C9A'} },
        margin: { l: 40, r: 20, t: 40, b: 30 },
        height: 230
    };
    
    Plotly.newPlot('chart-sales-trend', [trace], layout, {displayModeBar: false});
}

// Render Regional Map (Natural Earth World Projection)
function renderRegionalMap(map) {
    const locations = map.map(m => m.country);
    const sales = map.map(m => m.sales);
    const hover = map.map(m => `${m.region}: $${(m.sales).toLocaleString()}`);
    
    const trace = {
        type: 'choropleth',
        locations: locations,
        z: sales,
        text: hover,
        hoverinfo: 'text',
        colorscale: [
            [0, '#121225'],
            [0.5, '#636EFA'],
            [1.0, '#AB63FA']
        ],
        showscale: false
    };
    
    const layout = {
        title: { text: 'Sales by Region', font: { color: '#FFFFFF', size: 14, family: 'Outfit' } },
        geo: {
            showframe: false,
            showcoastlines: true,
            coastlinecolor: '#2B2B3D',
            projection: { type: 'equirectangular' },
            backgroundcolor: 'rgba(0,0,0,0)',
            landcolor: '#16162B',
            lakecolor: '#0F0F1A',
            showland: true
        },
        paper_bgcolor: 'rgba(0,0,0,0)',
        margin: { l: 0, r: 0, t: 40, b: 0 },
        height: 250
    };
    
    Plotly.newPlot('chart-regional-map', [trace], layout, {displayModeBar: false});
}

// Render Top Products List
function renderTopProducts(products) {
    const container = document.getElementById('top-products-list');
    container.innerHTML = '';
    
    products.forEach(p => {
        const valStr = p.revenue >= 1e6 ? `$${(p.revenue/1e6).toFixed(2)}M` : `$${(p.revenue/1e3).toFixed(1)}K`;
        const item = document.createElement('div');
        item.className = 'product-item';
        item.innerHTML = `
            <div class="product-info">
                <span style="color:#E0E0E6; font-weight:500;">${p.rank}. ${p.name}</span>
                <span style="color:#FFFFFF; font-weight:600;">${valStr}</span>
            </div>
            <div class="progress-bar-container">
                <div class="progress-bar-fill" style="width: ${p.percentage}%;"></div>
            </div>
        `;
        container.appendChild(item);
    });
}

// Render Insights
function renderInsights(insights) {
    const container = document.getElementById('ai-insights-list');
    container.innerHTML = '';
    
    insights.forEach(ins => {
        const item = document.createElement('div');
        item.className = 'insight-item';
        item.innerHTML = `
            <div class="insight-icon-box" style="background:rgba(255, 255, 255, 0.04);">
                ${ins.icon}
            </div>
            <div style="color:#E0E0E6;">
                ${ins.text}
            </div>
        `;
        container.appendChild(item);
    });
}

// Render Category Donut
function renderCategoryDonut(categories) {
    const values = categories.map(c => c.revenue);
    const labels = categories.map(c => c.category);
    const total = values.reduce((a, b) => a + b, 0);
    
    const trace = {
        values: values,
        labels: labels,
        type: 'pie',
        hole: 0.6,
        marker: {
            colors: ['#636EFA', '#AB63FA', '#00CC96', '#FFA15A', '#19D3F3']
        },
        textposition: 'inside',
        textinfo: 'percent',
        hoverinfo: 'label+value+percent'
    };
    
    const layout = {
        title: { text: 'Sales by Category', font: { color: '#FFFFFF', size: 14, family: 'Outfit' } },
        paper_bgcolor: 'rgba(0,0,0,0)',
        font: { color: '#E0E0E6', family: 'Outfit' },
        annotations: [{
            text: `<span style='font-size:10px;color:#8C8C9A;'>Total</span><br><b style='font-size:14px;color:#FFFFFF;'>$${(total/1e6).toFixed(2)}M</b>`,
            x: 0.5, y: 0.5,
            showarrow: false
        }],
        legend: {
            orientation: 'v',
            yanchor: 'middle', y: 0.5,
            xanchor: 'left', x: 0.95,
            font: { size: 10, color: '#8C8C9A' }
        },
        margin: { l: 0, r: 80, t: 40, b: 0 },
        height: 250
    };
    
    Plotly.newPlot('chart-category-donut', [trace], layout, {displayModeBar: false});
}

// Render Model Comparison Table
function renderModelComparison(perf) {
    const tbody = document.querySelector('#model-comparison-table tbody');
    tbody.innerHTML = '';
    
    perf.forEach(r => {
        const row = document.createElement('tr');
        if (r.is_best) {
            row.className = 'best-row';
        }
        row.innerHTML = `
            <td>${r.model}${r.is_best ? ' 🏆' : ''}</td>
            <td>${r.mae}</td>
            <td>${r.rmse}</td>
            <td>${r.r2}</td>
        `;
        tbody.appendChild(row);
    });
}

// Update Data Summary
function updateDataSummary(sum) {
    document.getElementById('summary-orders').textContent = sum.orders.toLocaleString();
    document.getElementById('summary-customers').textContent = sum.customers.toLocaleString();
    document.getElementById('summary-quality').textContent = `${sum.quality}%`;
}

// Simulator computations
function runSimulator() {
    if (!dashboardData) return;
    
    const discVal = parseFloat(simDiscount.value);
    const mktgVal = parseFloat(simMarketing.value);
    const priceVal = parseFloat(simPrice.value);
    
    const baseRev = dashboardData.kpis.revenue;
    const uniqueMonths = new Set(dashboardData.trend.map(t => t.date.substring(0, 7))).size;
    const baseMonthly = baseRev / (uniqueMonths || 1);
    
    // Simulate multipliers
    const discMult = 1.0 + (0.15 - discVal/100) * 0.4;
    const mktgMult = 1.0 + Math.log1p((mktgVal*1000 - 50000)/50000) * 0.15;
    const priceMult = 1.0 - (priceVal/100.0) * 0.8;
    
    const predictedMonthly = baseMonthly * disc_multiplier(discVal) * mktg_multiplier(mktgVal) * price_multiplier(priceVal);
    const growth = ((predictedMonthly - baseMonthly) / baseMonthly * 100);
    
    simPredictedVal.textContent = `$${(predictedMonthly / 1e3).toFixed(1)}K`;
    
    if (growth >= 0) {
        simPredictedChange.className = 'sim-result-change text-success';
        simPredictedChange.textContent = `▲ +${growth.toFixed(1)}% change`;
    } else {
        simPredictedChange.className = 'sim-result-change text-error';
        simPredictedChange.textContent = `▼ ${growth.toFixed(1)}% change`;
    }
}

// Helper multiplier functions
function disc_multiplier(disc) {
    return 1.0 + (0.15 - disc/100.0) * 0.4;
}
function mktg_multiplier(mktg) {
    return 1.0 + Math.log1p((mktg*1000 - 50000)/50000) * 0.15;
}
function price_multiplier(price) {
    return 1.0 - (price/100.0) * 0.8;
}

// FORECASTING PANEL TAB LOGIC
const btnRunForecast = document.getElementById('btn-run-forecast');
const fcAlgorithm = document.getElementById('fc-algorithm');
const fcHorizon = document.getElementById('fc-horizon');
const fcHorizonVal = document.getElementById('fc-horizon-val');
const fcLoading = document.getElementById('fc-loading');
const fcResultsContainer = document.getElementById('fc-results-container');
const fcMetricsGrid = document.getElementById('fc-metrics-grid');
const btnDownloadForecast = document.getElementById('btn-download-forecast');
let generatedForecastCsvData = null;
let generatedForecastFilename = "forecast.csv";

fcHorizon.addEventListener('input', (e) => {
    fcHorizonVal.textContent = `${e.target.value} Months`;
});

btnRunForecast.addEventListener('click', async () => {
    fcLoading.style.display = 'block';
    fcResultsContainer.style.display = 'none';
    
    const requestData = {
        ...activeFilters,
        model_choice: fcAlgorithm.value,
        horizon: parseInt(fcHorizon.value)
    };
    
    try {
        const response = await fetch('/api/forecast', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestData)
        });
        
        if (!response.ok) {
            const err = await response.json();
            alert(`Forecasting Error: ${err.detail || 'Failed to train models'}`);
            fcLoading.style.display = 'none';
            return;
        }
        
        const data = await response.json();
        fcLoading.style.display = 'none';
        fcResultsContainer.style.display = 'block';
        
        // Show metrics if regression-based
        if (data.metrics) {
            fcMetricsGrid.style.display = 'grid';
            document.getElementById('fc-metric-mae').textContent = `$${data.metrics.MAE.toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2})}`;
            document.getElementById('fc-metric-rmse').textContent = `$${data.metrics.RMSE.toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2})}`;
            document.getElementById('fc-metric-r2').textContent = data.metrics.R2.toFixed(4);
        } else {
            fcMetricsGrid.style.display = 'none';
        }
        
        // Render plot
        renderForecastPlot(data.historical, data.forecasted, data.model_name);
        
        // Render predictions table
        renderForecastTable(data.forecasted);
        
        // Prepare download CSV
        prepareForecastDownload(data.forecasted, data.model_name);
    } catch (e) {
        console.error('Error generating forecast:', e);
        fcLoading.style.display = 'none';
        alert('An unexpected server error occurred during ML training.');
    }
});

// Render the detailed prediction curve (Plotly style)
function renderForecastPlot(hist, fc, modelName) {
    const histDates = hist.map(h => h.date);
    const histVals = hist.map(h => h.value);
    
    const fcDates = fc.map(f => f.date);
    const fcVals = fc.map(f => f.yhat);
    const fcLower = fc.map(f => f.yhat_lower);
    const fcUpper = fc.map(f => f.yhat_upper);
    
    const traces = [];
    
    // Historical Line
    traces.push({
        x: histDates,
        y: histVals,
        type: 'scatter',
        mode: 'lines+markers',
        name: 'Historical Sales',
        line: { color: '#E0E0E6', width: 2 },
        marker: { size: 4 }
    });
    
    if (fcDates.length > 0) {
        // Connect historical and predicted line
        const lastHistDate = histDates[histDates.length - 1];
        const lastHistVal = histVals[histVals.length - 1];
        
        const connDates = [lastHistDate, ...fcDates];
        const connVals = [lastHistVal, ...fcVals];
        const connLower = [lastHistVal, ...fcLower];
        const connUpper = [lastHistVal, ...fcUpper];
        
        // 95% Confidence Band
        traces.push({
            x: [...connDates, ...[...connDates].reverse()],
            y: [...connUpper, ...[...connLower].reverse()],
            fill: 'toself',
            fillcolor: 'rgba(99, 110, 250, 0.15)',
            line: { color: 'rgba(255,255,255,0)' },
            hoverinfo: 'skip',
            name: '95% Confidence Interval'
        });
        
        // Prediction Line
        traces.push({
            x: connDates,
            y: connVals,
            type: 'scatter',
            mode: 'lines+markers',
            name: `${modelName} Forecast`,
            line: { color: '#636EFA', width: 3, dash: 'dash' },
            marker: { size: 6, color: '#00CC96' }
        });
    }
    
    const layout = {
        title: { text: `Sales Forecast Projections using ${modelName}`, font: { color: '#FFFFFF', size: 16, family: 'Outfit' } },
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: { color: '#E0E0E6', family: 'Outfit' },
        xaxis: { gridcolor: '#2B2B3D', linecolor: '#2B2B3D', tickfont: {color:'#8C8C9A'} },
        yaxis: { gridcolor: '#2B2B3D', linecolor: '#2B2B3D', tickfont: {color:'#8C8C9A'} },
        margin: { l: 40, r: 20, t: 40, b: 30 },
        height: 380
    };
    
    Plotly.newPlot('chart-fc-results', traces, layout, {displayModeBar: false});
}

// Populates forecast values summary
function renderForecastTable(fc) {
    const tbody = document.querySelector('#forecast-summary-table tbody');
    tbody.innerHTML = '';
    
    fc.forEach(row => {
        const tr = document.createElement('tr');
        const fMonth = new Date(row.date).toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
        tr.innerHTML = `
            <td>${fMonth}</td>
            <td>$${row.yhat.toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2})}</td>
            <td>$${row.yhat_lower.toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2})}</td>
            <td>$${row.yhat_upper.toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2})}</td>
        `;
        tbody.appendChild(tr);
    });
}

// Download Helper
function prepareForecastDownload(fc, modelName) {
    let csv = "Forecasted Month,Predicted Sales ($),Lower Bound ($),Upper Bound ($)\n";
    fc.forEach(row => {
        const fMonth = new Date(row.date).toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
        csv += `"${fMonth}",${row.yhat},${row.yhat_lower},${row.yhat_upper}\n`;
    });
    
    generatedForecastCsvData = csv;
    generatedForecastFilename = `sales_forecast_${modelName.toLowerCase().replace(/\s+/g, '_')}.csv`;
}

btnDownloadForecast.addEventListener('click', () => {
    if (!generatedForecastCsvData) return;
    const blob = new Blob([generatedForecastCsvData], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement("a");
    const url = URL.createObjectURL(blob);
    link.setAttribute("href", url);
    link.setAttribute("download", generatedForecastFilename);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
});

// PRODUCTS TABLE PAGE LISTING
async function loadProductsPanel() {
    if (!dashboardData) return;
    
    try {
        const response = await fetch('/api/dashboard', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(activeFilters)
        });
        const data = await response.json();
        
        const tbody = document.querySelector('#full-products-table tbody');
        tbody.innerHTML = '';
        
        // Use aggregated products listings for display
        data.products.forEach(p => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${p.name}</td>
                <td>Electronics</td> <!-- default category tag mapping -->
                <td>${Math.round(p.revenue / 500)}</td>
                <td>$${valStr(p.revenue)}</td>
            `;
            tbody.appendChild(tr);
        });
    } catch(e) {
        console.error('Error loading products list:', e);
    }
}

function valStr(val) {
    return val.toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2});
}
