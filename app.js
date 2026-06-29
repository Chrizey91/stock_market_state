document.addEventListener('DOMContentLoaded', () => {
  // Global State for Charts
  const charts = {};
  let marketData = null;

  // Initialize Lucide Icons
  lucide.createIcons();

  // Tab Switching Logic
  const tabButtons = document.querySelectorAll('.tab-btn');
  const tabPanes = document.querySelectorAll('.tab-pane');

  tabButtons.forEach(button => {
    button.addEventListener('click', () => {
      const targetTab = button.getAttribute('data-tab');

      // Update active button
      tabButtons.forEach(btn => btn.classList.remove('active'));
      button.classList.add('active');

      // Update active pane
      tabPanes.forEach(pane => pane.classList.remove('active'));
      const activePane = document.getElementById(`${targetTab}-tab`);
      if (activePane) {
        activePane.classList.add('active');
      }

      // ApexCharts require a resize/reflow event to display correctly if they were initialized inside a hidden container
      window.dispatchEvent(new Event('resize'));
    });
  });

  // Fetch Market Data
  async function loadMarketData() {
    try {
      const response = await fetch('data/market_data.json');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      marketData = await response.json();
      
      updateUIHeader(marketData.last_updated);
      renderSentimentTab(marketData.indicators);
      renderMonetaryTab(marketData.indicators);
      renderEconomyTab(marketData.indicators);
      
    } catch (error) {
      console.error("Error loading market data:", error);
      document.querySelector('.status-pill').style.borderColor = 'var(--accent-red)';
      document.querySelector('.status-label').textContent = 'ERROR LOADING DATA';
      document.querySelector('.status-label').style.color = 'var(--accent-red)';
      document.querySelector('.pulse-indicator').style.backgroundColor = 'var(--accent-red)';
    }
  }

  // Update navbar metadata
  function updateUIHeader(lastUpdated) {
    const timeEl = document.getElementById('last-updated-time');
    if (timeEl && lastUpdated) {
      const date = new Date(lastUpdated);
      // Format as "YYYY-MM-DD HH:MM UTC"
      const formattedDate = date.toISOString().replace('T', ' ').substring(0, 16) + ' UTC';
      timeEl.textContent = `UPDATED: ${formattedDate}`;
    }
  }

  // Sentiment & Volatility Tab Rendering
  function renderSentimentTab(indicators) {
    // 1. VIX Chart & Indicator
    const vixData = indicators.vix || [];
    if (vixData.length > 0) {
      const latestVix = vixData[vixData.length - 1];
      const currentVal = latestVix.value;
      
      const valEl = document.getElementById('vix-current-val');
      const statusEl = document.getElementById('vix-current-status');
      
      if (valEl) valEl.textContent = currentVal.toFixed(2);
      
      if (statusEl) {
        statusEl.className = 'stat-status'; // Reset classes
        if (currentVal < 15) {
          statusEl.textContent = 'COMPLACENCY';
          statusEl.classList.add('status-complacent');
        } else if (currentVal < 25) {
          statusEl.textContent = 'NORMAL';
          statusEl.classList.add('status-normal');
        } else if (currentVal < 35) {
          statusEl.textContent = 'ELEVATED RISK';
          statusEl.classList.add('status-elevated');
        } else {
          statusEl.textContent = 'PANIC';
          statusEl.classList.add('status-panic');
        }
      }

      const vixChartSeries = vixData.map(item => [new Date(item.date).getTime(), item.value]);
      
      const options = {
        series: [{
          name: 'VIX Close',
          data: vixChartSeries
        }],
        chart: {
          type: 'area',
          height: '100%',
          background: 'transparent',
          foreColor: '#a1a1aa',
          toolbar: { show: false },
          animations: {
            enabled: true,
            easing: 'easeinout',
            speed: 800,
            animateGradually: { enabled: true, delay: 150 },
            dynamicAnimation: { enabled: true, speed: 350 }
          }
        },
        colors: ['#3b82f6'],
        fill: {
          type: 'gradient',
          gradient: {
            shadeIntensity: 1,
            opacityFrom: 0.45,
            opacityTo: 0.05,
            stops: [0, 95]
          }
        },
        stroke: { curve: 'smooth', width: 2.5 },
        dataLabels: { enabled: false },
        grid: { borderColor: 'rgba(255, 255, 255, 0.05)', strokeDashArray: 4 },
        xaxis: {
          type: 'datetime',
          axisBorder: { show: false },
          axisTicks: { show: false }
        },
        yaxis: {
          tickAmount: 5,
          labels: { formatter: (value) => value.toFixed(1) }
        },
        tooltip: {
          x: { format: 'yyyy-MM-dd' },
          theme: 'dark'
        }
      };

      if (charts.vix) charts.vix.destroy();
      charts.vix = new ApexCharts(document.querySelector("#vix-chart"), options);
      charts.vix.render();
    }

    // 2. CNN Fear & Greed Chart & Indicator
    const fgData = indicators.fear_greed || [];
    if (fgData.length > 0) {
      const latestFg = fgData[fgData.length - 1];
      const currentVal = latestFg.value;
      
      const valEl = document.getElementById('fear-greed-current-val');
      const statusEl = document.getElementById('fear-greed-current-status');
      
      if (valEl) valEl.textContent = currentVal.toFixed(1);
      
      if (statusEl) {
        statusEl.className = 'stat-status';
        if (currentVal < 25) {
          statusEl.textContent = 'EXTREME FEAR';
          statusEl.classList.add('status-panic');
        } else if (currentVal < 45) {
          statusEl.textContent = 'FEAR';
          statusEl.classList.add('status-elevated');
        } else if (currentVal < 55) {
          statusEl.textContent = 'NEUTRAL';
          statusEl.classList.add('status-normal');
        } else if (currentVal < 75) {
          statusEl.textContent = 'GREED';
          statusEl.classList.add('status-complacent');
        } else {
          statusEl.textContent = 'EXTREME GREED';
          statusEl.classList.add('status-complacent');
        }
      }

      const fgChartSeries = fgData.map(item => [new Date(item.date).getTime(), item.value]);
      
      const options = {
        series: [{
          name: 'Fear & Greed Index',
          data: fgChartSeries
        }],
        chart: {
          type: 'area',
          height: '100%',
          background: 'transparent',
          foreColor: '#a1a1aa',
          toolbar: { show: false },
          animations: {
            enabled: true,
            easing: 'easeinout',
            speed: 800,
            animateGradually: { enabled: true, delay: 150 },
            dynamicAnimation: { enabled: true, speed: 350 }
          }
        },
        colors: ['#f59e0b'],
        fill: {
          type: 'gradient',
          gradient: {
            shadeIntensity: 1,
            opacityFrom: 0.45,
            opacityTo: 0.05,
            stops: [0, 95]
          }
        },
        stroke: { curve: 'smooth', width: 2.5 },
        dataLabels: { enabled: false },
        grid: { borderColor: 'rgba(255, 255, 255, 0.05)', strokeDashArray: 4 },
        xaxis: {
          type: 'datetime',
          axisBorder: { show: false },
          axisTicks: { show: false }
        },
        yaxis: {
          tickAmount: 5,
          min: 0,
          max: 100,
          labels: { formatter: (value) => value.toFixed(0) }
        },
        tooltip: {
          x: { format: 'yyyy-MM-dd' },
          theme: 'dark'
        },
        annotations: {
          yaxis: [
            {
              y: 75,
              borderColor: '#10b981',
              strokeDashArray: 4,
              width: '100%',
              label: {
                borderColor: '#10b981',
                style: { color: '#fff', background: '#10b981', fontWeight: 600 },
                text: 'Extreme Greed (75)'
              }
            },
            {
              y: 25,
              borderColor: '#ef4444',
              strokeDashArray: 4,
              width: '100%',
              label: {
                borderColor: '#ef4444',
                style: { color: '#fff', background: '#ef4444', fontWeight: 600 },
                text: 'Extreme Fear (25)'
              }
            }
          ]
        }
      };

      if (charts.fearGreed) charts.fearGreed.destroy();
      charts.fearGreed = new ApexCharts(document.querySelector("#fear-greed-chart"), options);
      charts.fearGreed.render();
    }

    // 3. Insider Buy/Sell Ratio Chart & Indicator
    const insiderData = indicators.insider_ratio || [];
    if (insiderData.length > 0) {
      const latestInsider = insiderData[insiderData.length - 1];
      const currentVal = latestInsider.value;
      
      const valEl = document.getElementById('insider-ratio-current-val');
      const statusEl = document.getElementById('insider-ratio-current-status');
      
      if (valEl) valEl.textContent = currentVal.toFixed(3);
      
      if (statusEl) {
        statusEl.className = 'stat-status';
        if (currentVal > 0.5) {
          statusEl.textContent = 'HIGH CONFIDENCE';
          statusEl.classList.add('status-complacent');
        } else if (currentVal >= 0.15) {
          statusEl.textContent = 'NORMAL';
          statusEl.classList.add('status-normal');
        } else {
          statusEl.textContent = 'LOW BUYING';
          statusEl.classList.add('status-normal');
        }
      }

      const insiderChartSeries = insiderData.map(item => [new Date(item.date).getTime(), item.value]);
      
      const options = {
        series: [{
          name: 'Insider Buy/Sell Ratio',
          data: insiderChartSeries
        }],
        chart: {
          type: 'area',
          height: '100%',
          background: 'transparent',
          foreColor: '#a1a1aa',
          toolbar: { show: false },
          animations: {
            enabled: true,
            easing: 'easeinout',
            speed: 800,
            animateGradually: { enabled: true, delay: 150 },
            dynamicAnimation: { enabled: true, speed: 350 }
          }
        },
        colors: ['#10b981'],
        fill: {
          type: 'gradient',
          gradient: {
            shadeIntensity: 1,
            opacityFrom: 0.45,
            opacityTo: 0.05,
            stops: [0, 95]
          }
        },
        stroke: { curve: 'smooth', width: 2.5 },
        dataLabels: { enabled: false },
        grid: { borderColor: 'rgba(255, 255, 255, 0.05)', strokeDashArray: 4 },
        xaxis: {
          type: 'datetime',
          axisBorder: { show: false },
          axisTicks: { show: false }
        },
        yaxis: {
          tickAmount: 5,
          labels: { formatter: (value) => value.toFixed(2) }
        },
        tooltip: {
          x: { format: 'yyyy-MM-dd' },
          theme: 'dark'
        },
        annotations: {
          yaxis: [
            {
              y: 0.5,
              borderColor: '#10b981',
              strokeDashArray: 4,
              width: '100%',
              label: {
                borderColor: '#10b981',
                style: { color: '#fff', background: '#10b981', fontWeight: 600 },
                text: 'High Confidence (0.50)'
              }
            }
          ]
        }
      };

      if (charts.insiderRatio) charts.insiderRatio.destroy();
      charts.insiderRatio = new ApexCharts(document.querySelector("#insider-ratio-chart"), options);
      charts.insiderRatio.render();
    }
  }

  // Monetary & Liquidity Tab Rendering
  function renderMonetaryTab(indicators) {
    const fedFunds = indicators.fed_funds || [];
    const treasury10y = indicators.treasury_10y || [];
    const yieldCurve = indicators.yield_curve || [];

    // Helper to build line charts
    const buildChartOptions = (containerId, name, dataPoints, color, zeroLineLabel = null) => {
      const chartSeries = dataPoints.map(item => [new Date(item.date).getTime(), item.value]);
      
      const options = {
        series: [{
          name: name,
          data: chartSeries
        }],
        chart: {
          type: 'line',
          height: '100%',
          background: 'transparent',
          foreColor: '#a1a1aa',
          toolbar: {
            show: false
          },
          animations: {
            enabled: true,
            easing: 'easeinout',
            speed: 800
          }
        },
        colors: [color],
        stroke: {
          curve: 'smooth',
          width: 2.5
        },
        grid: {
          borderColor: 'rgba(255, 255, 255, 0.05)',
          strokeDashArray: 4
        },
        xaxis: {
          type: 'datetime',
          axisBorder: {
            show: false
          },
          axisTicks: {
            show: false
          }
        },
        yaxis: {
          tickAmount: 5,
          labels: {
            formatter: (value) => value.toFixed(2) + '%'
          }
        },
        tooltip: {
          x: {
            format: 'yyyy-MM-dd'
          },
          theme: 'dark'
        }
      };

      // Add inversion/contraction line annotation if specified
      if (zeroLineLabel) {
        options.annotations = {
          yaxis: [{
            y: 0,
            borderColor: '#ef4444',
            strokeDashArray: 4,
            width: '100%',
            label: {
              borderColor: '#ef4444',
              style: {
                color: '#fff',
                background: '#ef4444',
                fontWeight: 600
              },
              text: zeroLineLabel
            }
          }]
        };
      }

      return options;
    };

    // Render Fed Funds Rate Chart
    if (fedFunds.length > 0) {
      const opts = buildChartOptions("#fedfunds-chart", "Fed Funds Rate", fedFunds, "#818cf8");
      if (charts.fedFunds) charts.fedFunds.destroy();
      charts.fedFunds = new ApexCharts(document.querySelector("#fedfunds-chart"), opts);
      charts.fedFunds.render();
    }

    // Render 10Y Treasury Yield Chart
    if (treasury10y.length > 0) {
      const opts = buildChartOptions("#dgs10-chart", "10-Year Treasury Yield", treasury10y, "#34d399");
      if (charts.treasury10y) charts.treasury10y.destroy();
      charts.treasury10y = new ApexCharts(document.querySelector("#dgs10-chart"), opts);
      charts.treasury10y.render();
    }

    // Render Yield Curve Spread Chart
    if (yieldCurve.length > 0) {
      const opts = buildChartOptions("#t10y2y-chart", "10Y - 2Y Yield Spread", yieldCurve, "#fbbf24", "Inversion (0.00%)");
      if (charts.yieldCurve) charts.yieldCurve.destroy();
      charts.yieldCurve = new ApexCharts(document.querySelector("#t10y2y-chart"), opts);
      charts.yieldCurve.render();
    }

    // Render M2 Growth Chart
    const m2Growth = indicators.m2_growth || [];
    if (m2Growth.length > 0) {
      const opts = buildChartOptions("#m2growth-chart", "M2 YoY Growth", m2Growth, "#f43f5e", "Contraction (0.00%)");
      if (charts.m2Growth) charts.m2Growth.destroy();
      charts.m2Growth = new ApexCharts(document.querySelector("#m2growth-chart"), opts);
      charts.m2Growth.render();
    }
  }

  // Economy & Internals Tab Rendering
  function renderEconomyTab(indicators) {
    const ismPmi = indicators.ism_pmi || [];
    const highYieldSpread = indicators.high_yield_spread || [];

    // Render ISM Manufacturing PMI Chart
    if (ismPmi.length > 0) {
      const pmiSeries = ismPmi.map(item => [new Date(item.date).getTime(), item.value]);
      const opts = {
        series: [{
          name: 'ISM Manufacturing PMI',
          data: pmiSeries
        }],
        chart: {
          type: 'line',
          height: '100%',
          background: 'transparent',
          foreColor: '#a1a1aa',
          toolbar: { show: false },
          animations: { enabled: true, easing: 'easeinout', speed: 800 }
        },
        colors: ['#a78bfa'],
        stroke: { curve: 'smooth', width: 2.5 },
        grid: { borderColor: 'rgba(255, 255, 255, 0.05)', strokeDashArray: 4 },
        xaxis: {
          type: 'datetime',
          axisBorder: { show: false },
          axisTicks: { show: false }
        },
        yaxis: {
          tickAmount: 5,
          labels: {
            formatter: (value) => value.toFixed(1)
          }
        },
        tooltip: {
          x: { format: 'yyyy-MM-dd' },
          theme: 'dark'
        },
        annotations: {
          yaxis: [{
            y: 50,
            borderColor: '#fbbf24',
            strokeDashArray: 4,
            width: '100%',
            label: {
              borderColor: '#fbbf24',
              style: { color: '#000', background: '#fbbf24', fontWeight: 600 },
              text: 'Expansion Threshold (50)'
            }
          }]
        }
      };
      if (charts.ismPmi) charts.ismPmi.destroy();
      charts.ismPmi = new ApexCharts(document.querySelector("#ism-pmi-chart"), opts);
      charts.ismPmi.render();
    }

    // Render High Yield Credit Spread Chart
    if (highYieldSpread.length > 0) {
      const hySeries = highYieldSpread.map(item => [new Date(item.date).getTime(), item.value]);
      const opts = {
        series: [{
          name: 'High Yield Credit Spread',
          data: hySeries
        }],
        chart: {
          type: 'line',
          height: '100%',
          background: 'transparent',
          foreColor: '#a1a1aa',
          toolbar: { show: false },
          animations: { enabled: true, easing: 'easeinout', speed: 800 }
        },
        colors: ['#f87171'],
        stroke: { curve: 'smooth', width: 2.5 },
        grid: { borderColor: 'rgba(255, 255, 255, 0.05)', strokeDashArray: 4 },
        xaxis: {
          type: 'datetime',
          axisBorder: { show: false },
          axisTicks: { show: false }
        },
        yaxis: {
          tickAmount: 5,
          labels: {
            formatter: (value) => value.toFixed(2) + '%'
          }
        },
        tooltip: {
          x: { format: 'yyyy-MM-dd' },
          theme: 'dark'
        },
        annotations: {
          yaxis: [
            {
              y: 4.0,
              borderColor: '#fbbf24',
              strokeDashArray: 4,
              width: '100%',
              label: {
                borderColor: '#fbbf24',
                style: { color: '#000', background: '#fbbf24', fontWeight: 600 },
                text: 'Moderate Stress (4.0%)'
              }
            },
            {
              y: 6.0,
              borderColor: '#ef4444',
              strokeDashArray: 4,
              width: '100%',
              label: {
                borderColor: '#ef4444',
                style: { color: '#fff', background: '#ef4444', fontWeight: 600 },
                text: 'High Stress (6.0%)'
              }
            }
          ]
        }
      };
      if (charts.highYieldSpread) charts.highYieldSpread.destroy();
      charts.highYieldSpread = new ApexCharts(document.querySelector("#highyield-chart"), opts);
      charts.highYieldSpread.render();
    }

    // Render S&P 500 Breadth Chart
    const sp500Breadth = indicators.sp500_breadth || [];
    if (sp500Breadth.length > 0) {
      const breadthSeries = sp500Breadth.map(item => [new Date(item.date).getTime(), item.value]);
      const opts = {
        series: [{
          name: 'S&P 500 Breadth (% > 200 SMA)',
          data: breadthSeries
        }],
        chart: {
          type: 'area',
          height: '100%',
          background: 'transparent',
          foreColor: '#a1a1aa',
          toolbar: { show: false },
          animations: { enabled: true, easing: 'easeinout', speed: 800 }
        },
        colors: ['#60a5fa'],
        fill: {
          type: 'gradient',
          gradient: {
            shadeIntensity: 1,
            opacityFrom: 0.3,
            opacityTo: 0.05,
            stops: [0, 95]
          }
        },
        stroke: { curve: 'smooth', width: 2.5 },
        grid: { borderColor: 'rgba(255, 255, 255, 0.05)', strokeDashArray: 4 },
        xaxis: {
          type: 'datetime',
          axisBorder: { show: false },
          axisTicks: { show: false }
        },
        yaxis: {
          tickAmount: 5,
          min: 0,
          max: 100,
          labels: {
            formatter: (value) => value.toFixed(0) + '%'
          }
        },
        tooltip: {
          x: { format: 'yyyy-MM-dd' },
          theme: 'dark'
        },
        annotations: {
          yaxis: [
            {
              y: 70,
              borderColor: '#10b981',
              strokeDashArray: 4,
              width: '100%',
              label: {
                borderColor: '#10b981',
                style: { color: '#fff', background: '#10b981', fontWeight: 600 },
                text: 'Bullish Support (70%)'
              }
            },
            {
              y: 30,
              borderColor: '#ef4444',
              strokeDashArray: 4,
              width: '100%',
              label: {
                borderColor: '#ef4444',
                style: { color: '#fff', background: '#ef4444', fontWeight: 600 },
                text: 'Capitulation (30%)'
              }
            }
          ]
        }
      };
      if (charts.sp500Breadth) charts.sp500Breadth.destroy();
      charts.sp500Breadth = new ApexCharts(document.querySelector("#sp500-breadth-chart"), opts);
      charts.sp500Breadth.render();
    }
  }

  // Load Data on Initial Page Load
  loadMarketData();
});
