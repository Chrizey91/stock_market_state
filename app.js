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
    const vixData = indicators.vix || [];
    if (vixData.length === 0) return;

    // Get current VIX info
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

    // Render VIX Chart
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
        toolbar: {
          show: false
        },
        animations: {
          enabled: true,
          easing: 'easeinout',
          speed: 800,
          animateGradually: {
            enabled: true,
            delay: 150
          },
          dynamicAnimation: {
            enabled: true,
            speed: 350
          }
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
      stroke: {
        curve: 'smooth',
        width: 2.5
      },
      dataLabels: {
        enabled: false
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
          formatter: (value) => value.toFixed(1)
        }
      },
      tooltip: {
        x: {
          format: 'yyyy-MM-dd'
        },
        theme: 'dark'
      }
    };

    if (charts.vix) {
      charts.vix.destroy();
    }
    charts.vix = new ApexCharts(document.querySelector("#vix-chart"), options);
    charts.vix.render();
  }

  // Monetary & Liquidity Tab Rendering
  function renderMonetaryTab(indicators) {
    const fedFunds = indicators.fed_funds || [];
    const treasury10y = indicators.treasury_10y || [];
    const yieldCurve = indicators.yield_curve || [];

    // Helper to build line charts
    const buildChartOptions = (containerId, name, dataPoints, color, isSpread = false) => {
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

      // Add inversion line annotation for 10Y-2Y Treasury spread
      if (isSpread) {
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
              text: 'Inversion (0.00%)'
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
      const opts = buildChartOptions("#t10y2y-chart", "10Y - 2Y Yield Spread", yieldCurve, "#fbbf24", true);
      if (charts.yieldCurve) charts.yieldCurve.destroy();
      charts.yieldCurve = new ApexCharts(document.querySelector("#t10y2y-chart"), opts);
      charts.yieldCurve.render();
    }
  }

  // Load Data on Initial Page Load
  loadMarketData();
});
