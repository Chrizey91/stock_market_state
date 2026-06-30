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
      renderHeroSection(marketData);
      renderPriceTrendTab(marketData.indicators);
      renderSentimentTab(marketData.indicators);
      renderMonetaryTab(marketData.indicators);
      renderEconomyTab(marketData.indicators);
      renderFundamentalsTab(marketData.indicators);
      
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

  // Price & Trend Tab Rendering
  function renderPriceTrendTab(indicators) {
    const trendData = indicators.sp500_trend || [];
    if (trendData.length > 0) {
      const latest = trendData[trendData.length - 1];
      const currentVal = latest.value;
      const ma50 = latest.ma50;
      const ma200 = latest.ma200;
      
      const valEl = document.getElementById('sp500-current-val');
      const trendStatusEl = document.getElementById('sp500-trend-status');
      const momentumStatusEl = document.getElementById('sp500-momentum-status');
      
      if (valEl) valEl.textContent = currentVal.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
      
      if (trendStatusEl) {
        trendStatusEl.className = 'stat-status';
        if (currentVal > ma200) {
          trendStatusEl.textContent = 'ABOVE 200-DAY SMA (BULLISH)';
          trendStatusEl.classList.add('status-complacent');
        } else {
          trendStatusEl.textContent = 'BELOW 200-DAY SMA (BEARISH)';
          trendStatusEl.classList.add('status-panic');
        }
      }
      
      if (momentumStatusEl) {
        momentumStatusEl.className = 'stat-status';
        if (ma50 > ma200) {
          momentumStatusEl.textContent = 'GOLDEN CROSS';
          momentumStatusEl.classList.add('status-complacent');
        } else {
          momentumStatusEl.textContent = 'DEATH CROSS';
          momentumStatusEl.classList.add('status-panic');
        }
      }

      const closeSeries = trendData.map(item => [new Date(item.date).getTime(), item.value]);
      const ma50Series = trendData.map(item => [new Date(item.date).getTime(), item.ma50]);
      const ma200Series = trendData.map(item => [new Date(item.date).getTime(), item.ma200]);
      
      const options = {
        series: [
          {
            name: 'S&P 500 Close',
            type: 'area',
            data: closeSeries
          },
          {
            name: '50-day SMA',
            type: 'line',
            data: ma50Series
          },
          {
            name: '200-day SMA',
            type: 'line',
            data: ma200Series
          }
        ],
        chart: {
          height: 450,
          type: 'line',
          background: 'transparent',
          foreColor: '#a1a1aa',
          toolbar: { show: false },
          animations: {
            enabled: true,
            easing: 'easeinout',
            speed: 800
          }
        },
        colors: ['#3b82f6', '#f59e0b', '#ef4444'], // Blue close, Yellow 50 SMA, Red 200 SMA
        fill: {
          type: ['gradient', 'solid', 'solid'],
          gradient: {
            shadeIntensity: 1,
            opacityFrom: 0.2,
            opacityTo: 0.0,
            stops: [0, 90]
          }
        },
        stroke: {
          width: [3, 2, 2],
          curve: 'smooth'
        },
        grid: {
          borderColor: 'rgba(255, 255, 255, 0.05)',
          strokeDashArray: 4
        },
        xaxis: {
          type: 'datetime',
          axisBorder: { show: false },
          axisTicks: { show: false }
        },
        yaxis: {
          tickAmount: 6,
          labels: {
            formatter: (value) => value.toLocaleString('en-US', { maximumFractionDigits: 0 })
          }
        },
        legend: {
          show: true,
          position: 'top',
          horizontalAlign: 'right',
          labels: { colors: '#a1a1aa' }
        },
        tooltip: {
          x: { format: 'yyyy-MM-dd' },
          theme: 'dark',
          y: {
            formatter: (value) => value !== null ? value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : 'N/A'
          }
        }
      };

      if (charts.sp500Trend) charts.sp500Trend.destroy();
      charts.sp500Trend = new ApexCharts(document.querySelector("#sp500-trend-chart"), options);
      charts.sp500Trend.render();
    }

    // 2. Equal-Weight vs Cap-Weight Chart
    const eqCapData = indicators.equal_vs_cap_weight || [];
    if (eqCapData.length > 0) {
      const latest = eqCapData[eqCapData.length - 1];
      const latestSpread = latest.spread;
      
      const valEl = document.getElementById('equal-vs-cap-val');
      const statusEl = document.getElementById('equal-vs-cap-status');
      
      if (valEl) {
        valEl.textContent = `${latestSpread > 0 ? '+' : ''}${latestSpread.toFixed(2)}%`;
      }
      
      if (statusEl) {
        statusEl.className = 'stat-status';
        if (latestSpread >= -5.0 && latestSpread <= 5.0) {
          statusEl.textContent = 'HEALTHY (BALANCED BREADTH)';
          statusEl.style.backgroundColor = 'rgba(16, 185, 129, 0.1)';
          statusEl.style.color = 'var(--accent-green)';
        } else {
          statusEl.textContent = `UNHEALTHY (${latestSpread < -5.0 ? 'CONCENTRATED IN MEGA-CAPS' : 'EQUAL-WEIGHT OUTPERFORMING'})`;
          statusEl.style.backgroundColor = 'rgba(239, 68, 68, 0.1)';
          statusEl.style.color = 'var(--accent-red)';
        }
      }

      const rspSeries = eqCapData.map(item => [new Date(item.date).getTime(), item.rsp_return]);
      const spySeries = eqCapData.map(item => [new Date(item.date).getTime(), item.spy_return]);
      const spreadSeries = eqCapData.map(item => [new Date(item.date).getTime(), item.spread]);

      const options = {
        series: [
          {
            name: 'RSP (Equal-Weight) Return',
            type: 'line',
            data: rspSeries
          },
          {
            name: 'SPY (Cap-Weighted) Return',
            type: 'line',
            data: spySeries
          },
          {
            name: 'Spread (RSP - SPY)',
            type: 'area',
            data: spreadSeries
          }
        ],
        chart: {
          height: 450,
          type: 'line',
          background: 'transparent',
          foreColor: '#a1a1aa',
          toolbar: { show: false },
          animations: {
            enabled: true,
            easing: 'easeinout',
            speed: 800
          }
        },
        colors: ['#10b981', '#3b82f6', '#8b5cf6'], // Emerald, Blue, Purple
        fill: {
          type: ['solid', 'solid', 'gradient'],
          gradient: {
            shadeIntensity: 1,
            opacityFrom: 0.15,
            opacityTo: 0.0,
            stops: [0, 90]
          }
        },
        stroke: {
          width: [3, 3, 1.5],
          curve: 'smooth'
        },
        grid: {
          borderColor: 'rgba(255, 255, 255, 0.05)',
          strokeDashArray: 4
        },
        xaxis: {
          type: 'datetime',
          axisBorder: { show: false },
          axisTicks: { show: false }
        },
        yaxis: {
          tickAmount: 6,
          labels: {
            formatter: (value) => `${value.toFixed(1)}%`
          }
        },
        legend: {
          show: true,
          position: 'top',
          horizontalAlign: 'right',
          labels: { colors: '#a1a1aa' }
        },
        tooltip: {
          x: { format: 'yyyy-MM-dd' },
          theme: 'dark',
          y: {
            formatter: (value) => value !== null ? `${value.toFixed(2)}%` : 'N/A'
          }
        }
      };

      if (charts.equalVsCap) charts.equalVsCap.destroy();
      charts.equalVsCap = new ApexCharts(document.querySelector("#equal-vs-cap-chart"), options);
      charts.equalVsCap.render();
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

    // Render S&P 500 A/D Line Chart
    const sp500AdLine = indicators.sp500_ad_line || [];
    if (sp500AdLine.length > 0) {
      const adSeries = sp500AdLine.map(item => [new Date(item.date).getTime(), item.value]);
      const opts = {
        series: [{
          name: 'S&P 500 A/D Line',
          data: adSeries
        }],
        chart: {
          type: 'line',
          height: '100%',
          background: 'transparent',
          foreColor: '#a1a1aa',
          toolbar: { show: false },
          animations: { enabled: true, easing: 'easeinout', speed: 800 }
        },
        colors: ['#06b6d4'],
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
            formatter: (value) => value.toLocaleString('en-US', { maximumFractionDigits: 0 })
          }
        },
        tooltip: {
          x: { format: 'yyyy-MM-dd' },
          theme: 'dark'
        }
      };
      if (charts.sp500AdLine) charts.sp500AdLine.destroy();
      charts.sp500AdLine = new ApexCharts(document.querySelector("#sp500-ad-line-chart"), opts);
      charts.sp500AdLine.render();
    }

    // Render S&P 500 New Highs/Lows Chart
    const sp500HighsLows = indicators.sp500_new_highs_lows || [];
    if (sp500HighsLows.length > 0) {
      const highsSeries = sp500HighsLows.map(item => [new Date(item.date).getTime(), item.highs]);
      const lowsSeries = sp500HighsLows.map(item => [new Date(item.date).getTime(), item.lows]);
      
      const opts = {
        series: [
          {
            name: 'New Highs',
            data: highsSeries
          },
          {
            name: 'New Lows',
            data: lowsSeries
          }
        ],
        chart: {
          type: 'bar',
          height: '100%',
          background: 'transparent',
          foreColor: '#a1a1aa',
          toolbar: { show: false },
          animations: { enabled: true, easing: 'easeinout', speed: 800 }
        },
        colors: ['#10b981', '#ef4444'], // Green for Highs, Red for Lows
        plotOptions: {
          bar: {
            horizontal: false,
            columnWidth: '55%'
          },
        },
        dataLabels: {
          enabled: false
        },
        stroke: {
          show: true,
          width: 2,
          colors: ['transparent']
        },
        grid: { borderColor: 'rgba(255, 255, 255, 0.05)', strokeDashArray: 4 },
        xaxis: {
          type: 'datetime',
          axisBorder: { show: false },
          axisTicks: { show: false }
        },
        yaxis: {
          tickAmount: 5,
          labels: {
            formatter: (value) => value.toFixed(0)
          }
        },
        legend: {
          show: true,
          position: 'top',
          horizontalAlign: 'right',
          labels: { colors: '#a1a1aa' }
        },
        tooltip: {
          x: { format: 'yyyy-MM-dd' },
          theme: 'dark'
        }
      };
      if (charts.sp500HighsLows) charts.sp500HighsLows.destroy();
      charts.sp500HighsLows = new ApexCharts(document.querySelector("#sp500-highs-lows-chart"), opts);
      charts.sp500HighsLows.render();
    }

    // Render Sector MA Breadth Chart
    const sectorLead = indicators.sector_leadership || {};
    const sectors = sectorLead.sectors || [];
    if (sectors.length > 0) {
      const summaryEl = document.getElementById('sector-breadth-summary');
      if (summaryEl) {
        summaryEl.textContent = `${sectorLead.above_200d} of ${sectorLead.total} sectors above 200-day MA`;
      }

      const categories = sectors.map(s => s.name);
      const data = sectors.map(s => s.above ? 1 : -1);

      const opts = {
        series: [{
          name: 'Status',
          data: data
        }],
        chart: {
          type: 'bar',
          height: 300,
          background: 'transparent',
          foreColor: '#a1a1aa',
          toolbar: { show: false }
        },
        plotOptions: {
          bar: {
            horizontal: true,
            barHeight: '75%',
            colors: {
              ranges: [
                { from: -1, to: -1, color: '#ef4444' }, // Red for Below
                { from: 1, to: 1, color: '#10b981' }   // Green for Above
              ]
            }
          }
        },
        dataLabels: {
          enabled: true,
          formatter: (val) => val === 1 ? 'ABOVE' : 'BELOW',
          style: {
            colors: ['#fff'],
            fontSize: '10px',
            fontWeight: 'bold'
          }
        },
        grid: {
          borderColor: 'rgba(255, 255, 255, 0.05)',
          strokeDashArray: 4,
          xaxis: { lines: { show: false } }
        },
        xaxis: {
          categories: categories,
          labels: { show: false },
          axisBorder: { show: false },
          axisTicks: { show: false },
          min: -1.2,
          max: 1.2
        },
        yaxis: {
          labels: {
            style: {
              colors: '#a1a1aa',
              fontSize: '12px',
              fontWeight: 600
            }
          }
        },
        tooltip: {
          theme: 'dark',
          y: {
            formatter: (val) => val === 1 ? 'Above 200-day MA' : 'Below 200-day MA'
          }
        }
      };

      if (charts.sectorLeadership) charts.sectorLeadership.destroy();
      charts.sectorLeadership = new ApexCharts(document.querySelector("#sector-leadership-chart"), opts);
      charts.sectorLeadership.render();
    }

    // Render Sector Performance Heatmap
    const sectorHeatmap = indicators.sector_heatmap || [];
    if (sectorHeatmap.length > 0) {
      const series = [
        {
          name: '3-Month',
          data: sectorHeatmap.map(item => ({ x: item.sector, y: item['3m'] }))
        },
        {
          name: '1-Month',
          data: sectorHeatmap.map(item => ({ x: item.sector, y: item['1m'] }))
        },
        {
          name: '1-Week',
          data: sectorHeatmap.map(item => ({ x: item.sector, y: item['1w'] }))
        }
      ];

      const opts = {
        series: series,
        chart: {
          type: 'heatmap',
          height: 300,
          background: 'transparent',
          foreColor: '#a1a1aa',
          toolbar: { show: false }
        },
        dataLabels: {
          enabled: true,
          style: {
            colors: ['#fff'],
            fontSize: '11px',
            fontWeight: 'bold'
          },
          formatter: (val) => val !== null ? (val > 0 ? '+' : '') + val.toFixed(1) + '%' : ''
        },
        plotOptions: {
          heatmap: {
            shadeIntensity: 0.5,
            radius: 4,
            useDirectColors: false,
            colorScale: {
              ranges: [
                { from: -100, to: -5, name: 'Very Weak (<-5%)', color: '#991b1b' },
                { from: -5, to: -2, name: 'Weak (-5% to -2%)', color: '#ef4444' },
                { from: -2, to: -0.001, name: 'Slightly Weak (-2% to 0%)', color: '#f87171' },
                { from: 0, to: 0, name: 'Flat', color: '#27272a' },
                { from: 0.001, to: 2, name: 'Slightly Strong (0% to 2%)', color: '#10b981' },
                { from: 2, to: 5, name: 'Strong (2% to 5%)', color: '#059669' },
                { from: 5, to: 100, name: 'Very Strong (>5%)', color: '#065f46' }
              ]
            }
          }
        },
        grid: {
          show: false
        },
        xaxis: {
          labels: {
            style: {
              colors: '#a1a1aa',
              fontSize: '11px',
              fontWeight: 600
            }
          }
        },
        yaxis: {
          labels: {
            style: {
              colors: '#a1a1aa',
              fontSize: '12px',
              fontWeight: 600
            }
          }
        },
        tooltip: {
          theme: 'dark',
          y: {
            formatter: (val) => val !== null ? val.toFixed(2) + '%' : 'N/A'
          }
        }
      };

      if (charts.sectorHeatmap) charts.sectorHeatmap.destroy();
      charts.sectorHeatmap = new ApexCharts(document.querySelector("#sector-heatmap-chart"), opts);
      charts.sectorHeatmap.render();
    }
  }

  // Fundamentals Tab Rendering
  function renderFundamentalsTab(indicators) {
    const epsData = indicators.eps_growth || [];
    const revData = indicators.revenue_growth || [];

    // Render EPS Growth
    const epsValEl = document.getElementById('eps-growth-val');
    const epsStatusEl = document.getElementById('eps-growth-status');
    const epsChartEl = document.getElementById('eps-growth-chart');
    const epsFallbackEl = document.getElementById('eps-growth-fallback');

    if (epsData.length > 0) {
      if (epsChartEl) epsChartEl.style.display = 'block';
      if (epsFallbackEl) epsFallbackEl.style.display = 'none';

      const latest = epsData[epsData.length - 1];
      const latestVal = latest.value;

      if (epsValEl) {
        epsValEl.textContent = `${latestVal > 0 ? '+' : ''}${latestVal.toFixed(2)}%`;
      }

      if (epsStatusEl) {
        epsStatusEl.className = 'stat-status';
        if (latestVal > 0) {
          epsStatusEl.textContent = 'EXPANSION (BULLISH)';
          epsStatusEl.classList.add('status-complacent');
        } else {
          epsStatusEl.textContent = 'CONTRACTION (BEARISH)';
          epsStatusEl.classList.add('status-panic');
        }
      }

      const epsSeries = epsData.map(item => [new Date(item.date).getTime(), item.value]);

      const options = {
        series: [{
          name: 'EPS Growth (YoY)',
          data: epsSeries
        }],
        chart: {
          type: 'area',
          height: 400,
          background: 'transparent',
          foreColor: '#a1a1aa',
          toolbar: { show: false },
          animations: { enabled: true, easing: 'easeinout', speed: 800 }
        },
        colors: ['#a78bfa'], // Purple
        fill: {
          type: 'gradient',
          gradient: {
            shadeIntensity: 1,
            opacityFrom: 0.35,
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
          labels: { formatter: (value) => `${value.toFixed(1)}%` }
        },
        tooltip: {
          x: { format: 'yyyy-MM-dd' },
          theme: 'dark',
          y: { formatter: (value) => `${value.toFixed(2)}%` }
        },
        annotations: {
          yaxis: [{
            y: 0,
            borderColor: '#ef4444',
            strokeDashArray: 4,
            width: '100%',
            label: {
              borderColor: '#ef4444',
              style: { color: '#fff', background: '#ef4444', fontWeight: 600 },
              text: 'Growth Threshold (0.00%)'
            }
          }]
        }
      };

      if (charts.epsGrowth) charts.epsGrowth.destroy();
      charts.epsGrowth = new ApexCharts(document.querySelector("#eps-growth-chart"), options);
      charts.epsGrowth.render();
    } else {
      if (epsValEl) epsValEl.textContent = 'N/A';
      if (epsStatusEl) {
        epsStatusEl.className = 'stat-status status-normal';
        epsStatusEl.textContent = 'UNAVAILABLE';
      }
      if (epsChartEl) epsChartEl.style.display = 'none';
      if (epsFallbackEl) epsFallbackEl.style.display = 'flex';
    }

    // Render Revenue Growth
    const revValEl = document.getElementById('revenue-growth-val');
    const revStatusEl = document.getElementById('revenue-growth-status');
    const revChartEl = document.getElementById('revenue-growth-chart');
    const revFallbackEl = document.getElementById('revenue-growth-fallback');

    if (revData.length > 0) {
      if (revChartEl) revChartEl.style.display = 'block';
      if (revFallbackEl) revFallbackEl.style.display = 'none';

      const latest = revData[revData.length - 1];
      const latestVal = latest.value;

      if (revValEl) {
        revValEl.textContent = `${latestVal > 0 ? '+' : ''}${latestVal.toFixed(2)}%`;
      }

      if (revStatusEl) {
        revStatusEl.className = 'stat-status';
        if (latestVal > 0) {
          revStatusEl.textContent = 'EXPANSION (BULLISH)';
          revStatusEl.classList.add('status-complacent');
        } else {
          revStatusEl.textContent = 'CONTRACTION (BEARISH)';
          revStatusEl.classList.add('status-panic');
        }
      }

      const revSeries = revData.map(item => [new Date(item.date).getTime(), item.value]);

      const options = {
        series: [{
          name: 'Revenue Growth (YoY)',
          data: revSeries
        }],
        chart: {
          type: 'area',
          height: 400,
          background: 'transparent',
          foreColor: '#a1a1aa',
          toolbar: { show: false },
          animations: { enabled: true, easing: 'easeinout', speed: 800 }
        },
        colors: ['#06b6d4'], // Cyan
        fill: {
          type: 'gradient',
          gradient: {
            shadeIntensity: 1,
            opacityFrom: 0.35,
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
          labels: { formatter: (value) => `${value.toFixed(1)}%` }
        },
        tooltip: {
          x: { format: 'yyyy-MM-dd' },
          theme: 'dark',
          y: { formatter: (value) => `${value.toFixed(2)}%` }
        },
        annotations: {
          yaxis: [{
            y: 0,
            borderColor: '#ef4444',
            strokeDashArray: 4,
            width: '100%',
            label: {
              borderColor: '#ef4444',
              style: { color: '#fff', background: '#ef4444', fontWeight: 600 },
              text: 'Growth Threshold (0.00%)'
            }
          }]
        }
      };

      if (charts.revenueGrowth) charts.revenueGrowth.destroy();
      charts.revenueGrowth = new ApexCharts(document.querySelector("#revenue-growth-chart"), options);
      charts.revenueGrowth.render();
    } else {
      if (revValEl) revValEl.textContent = 'N/A';
      if (revStatusEl) {
        revStatusEl.className = 'stat-status status-normal';
        revStatusEl.textContent = 'UNAVAILABLE';
      }
      if (revChartEl) revChartEl.style.display = 'none';
      if (revFallbackEl) revFallbackEl.style.display = 'flex';
    }
  }

  // Hero Section Rendering (Market Regime Score & Sidebar Summary)
  function renderHeroSection(data) {
    const score = data.market_regime_score !== undefined ? data.market_regime_score : 50.0;
    const indicators = data.indicators || {};

    // 1. Update Gauge Card Info
    const scoreEl = document.getElementById('regime-score-val');
    if (scoreEl) scoreEl.textContent = score.toFixed(1);

    const statusLabelEl = document.getElementById('regime-status-label');
    if (statusLabelEl) {
      statusLabelEl.className = 'regime-status-badge'; // Reset classes
      if (score >= 70) {
        statusLabelEl.textContent = 'Risk-On / Expansion';
        statusLabelEl.style.backgroundColor = 'rgba(16, 185, 129, 0.1)';
        statusLabelEl.style.color = 'var(--accent-green)';
      } else if (score >= 45) {
        statusLabelEl.textContent = 'Neutral / Transition';
        statusLabelEl.style.backgroundColor = 'rgba(245, 158, 11, 0.1)';
        statusLabelEl.style.color = 'var(--accent-yellow)';
      } else {
        statusLabelEl.textContent = 'Risk-Off / Panic';
        statusLabelEl.style.backgroundColor = 'rgba(239, 68, 68, 0.1)';
        statusLabelEl.style.color = 'var(--accent-red)';
      }
    }

    // 2. Render Gauge Chart (ApexCharts)
    renderRegimeGauge(score);

    // 3. Update VIX Sidebar Card
    const vixData = indicators.vix || [];
    if (vixData.length > 0) {
      const latestVix = vixData[vixData.length - 1].value;
      const vixValEl = document.getElementById('summary-vix-val');
      const vixBadgeEl = document.getElementById('summary-vix-badge');
      const vixDescEl = document.getElementById('summary-vix-desc');

      if (vixValEl) vixValEl.textContent = latestVix.toFixed(2);
      if (vixBadgeEl) {
        vixBadgeEl.className = 'badge-pill';
        if (latestVix < 15) {
          vixBadgeEl.textContent = 'Calm';
          vixBadgeEl.classList.add('status-complacent');
        } else if (latestVix < 25) {
          vixBadgeEl.textContent = 'Normal';
          vixBadgeEl.classList.add('status-normal');
        } else if (latestVix < 35) {
          vixBadgeEl.textContent = 'Elevated';
          vixBadgeEl.classList.add('status-elevated');
        } else {
          vixBadgeEl.textContent = 'Panic';
          vixBadgeEl.classList.add('status-panic');
        }
      }
      if (vixDescEl) {
        if (latestVix < 15) {
          vixDescEl.textContent = 'Market environment is calm and complacent.';
        } else if (latestVix < 25) {
          vixDescEl.textContent = 'Standard volatility and risk levels.';
        } else if (latestVix < 35) {
          vixDescEl.textContent = 'Elevated market fear and price swings.';
        } else {
          vixDescEl.textContent = 'High market panic! Risk conditions severe.';
        }
      }
    }

    // 4. Update Bond Market (Yield Curve 10Y-2Y) Sidebar Card
    const ycData = indicators.yield_curve || [];
    if (ycData.length > 0) {
      const latestYc = ycData[ycData.length - 1].value;
      const bondValEl = document.getElementById('summary-bond-val');
      const bondBadgeEl = document.getElementById('summary-bond-badge');
      const bondDescEl = document.getElementById('summary-bond-desc');

      if (bondValEl) bondValEl.textContent = `${latestYc.toFixed(2)}%`;
      if (bondBadgeEl) {
        bondBadgeEl.className = 'badge-pill';
        if (latestYc < 0) {
          bondBadgeEl.textContent = 'Inverted';
          bondBadgeEl.classList.add('status-panic');
        } else if (latestYc < 0.5) {
          bondBadgeEl.textContent = 'Flat';
          bondBadgeEl.classList.add('status-elevated');
        } else {
          bondBadgeEl.textContent = 'Normal';
          bondBadgeEl.classList.add('status-complacent');
        }
      }
      if (bondDescEl) {
        if (latestYc < 0) {
          bondDescEl.textContent = 'Yield curve is inverted, signaling recession risk.';
        } else if (latestYc < 0.5) {
          bondDescEl.textContent = 'Curve is flattening. Monitor closely.';
        } else {
          bondDescEl.textContent = 'Curve is upward-sloping and healthy.';
        }
      }
    }

    // 5. Update Retail Sentiment (Fear & Greed) Sidebar Card
    const fgData = indicators.fear_greed || [];
    if (fgData.length > 0) {
      const latestFg = fgData[fgData.length - 1].value;
      const fgValEl = document.getElementById('summary-sentiment-val');
      const fgBadgeEl = document.getElementById('summary-sentiment-badge');
      const fgDescEl = document.getElementById('summary-sentiment-desc');

      if (fgValEl) fgValEl.textContent = latestFg.toFixed(0);
      if (fgBadgeEl) {
        fgBadgeEl.className = 'badge-pill';
        if (latestFg < 25) {
          fgBadgeEl.textContent = 'Extreme Fear';
          fgBadgeEl.classList.add('status-panic');
        } else if (latestFg < 45) {
          fgBadgeEl.textContent = 'Fear';
          fgBadgeEl.classList.add('status-elevated');
        } else if (latestFg < 55) {
          fgBadgeEl.textContent = 'Neutral';
          fgBadgeEl.classList.add('status-normal');
        } else if (latestFg < 75) {
          fgBadgeEl.textContent = 'Greed';
          fgBadgeEl.classList.add('status-complacent');
        } else {
          fgBadgeEl.textContent = 'Extreme Greed';
          fgBadgeEl.classList.add('status-complacent');
        }
      }
      if (fgDescEl) {
        if (latestFg < 25) {
          fgDescEl.textContent = 'Extreme pessimism. Potential buying zone.';
        } else if (latestFg < 45) {
          fgDescEl.textContent = 'Retail investors are cautious and fearful.';
        } else if (latestFg < 55) {
          fgDescEl.textContent = 'Sentiment is balanced and neutral.';
        } else if (latestFg < 75) {
          fgDescEl.textContent = 'Retail investors are optimistic and greedy.';
        } else {
          fgDescEl.textContent = 'Extreme optimism. Precedes market tops.';
        }
      }
    }
  }

  // Render ApexCharts radial gauge chart for regime score
  function renderRegimeGauge(score) {
    // Pick color based on score
    let gaugeColor = '#3b82f6'; // Blue default
    if (score >= 70) {
      gaugeColor = '#10b981'; // Green (Expansion)
    } else if (score >= 45) {
      gaugeColor = '#f59e0b'; // Yellow (Neutral)
    } else {
      gaugeColor = '#ef4444'; // Red (Panic)
    }

    const options = {
      series: [score],
      chart: {
        type: 'radialBar',
        height: '100%',
        offsetY: -10,
        sparkline: { enabled: true }
      },
      plotOptions: {
        radialBar: {
          startAngle: -135,
          endAngle: 135,
          hollow: {
            margin: 0,
            size: '70%',
            background: 'transparent',
            image: undefined,
            imageWidth: 150,
            imageHeight: 150,
            imageOffsetY: 0,
            imageClipped: true,
            position: 'front',
            dropShadow: {
              enabled: true,
              top: 3,
              left: 0,
              blur: 4,
              opacity: 0.24
            }
          },
          track: {
            background: 'rgba(255, 255, 255, 0.05)',
            strokeWidth: '67%',
            margin: 0, // a parameter of track margin
            dropShadow: {
              enabled: true,
              top: -3,
              left: 0,
              blur: 4,
              opacity: 0.35
            }
          },
          dataLabels: {
            show: true,
            name: {
              show: false
            },
            value: {
              offsetY: 8,
              color: '#f4f4f5',
              fontSize: '2rem',
              fontWeight: 800,
              fontFamily: 'Plus Jakarta Sans',
              show: true,
              formatter: function (val) {
                return val.toFixed(1);
              }
            }
          }
        }
      },
      fill: {
        type: 'solid',
        colors: [gaugeColor]
      },
      stroke: {
        lineCap: 'round'
      },
      labels: ['Regime Score']
    };

    if (charts.regimeGauge) charts.regimeGauge.destroy();
    charts.regimeGauge = new ApexCharts(document.querySelector("#regime-gauge-chart"), options);
    charts.regimeGauge.render();
  }

  // Load Data on Initial Page Load
  loadMarketData();
});
