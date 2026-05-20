/* ═══════════════════════════════════════════
   每日贵金属投资日报 — 交互脚本
   ═══════════════════════════════════════════ */

(function () {
  'use strict';

  // ── 状态 ──
  var store = JSON.parse(document.getElementById('data-store').textContent);
  var defaultSelected = store.defaultSelected;
  var CATEGORY_ICONS = store.categoryIcons || {};
  var chartInstance = null;
  var currentPeriod = 'day';
  var isLoading = false;

  // ── 工具函数 ──

  function getSelected() {
    var cbs = document.querySelectorAll('.product-checkbox:checked');
    var sel = Array.from(cbs).map(function (el) { return el.value; });
    return sel.length ? sel : defaultSelected;
  }

  function saveSelection() {
    var cbs = document.querySelectorAll('.product-checkbox');
    var sel = [];
    for (var i = 0; i < cbs.length; i++) {
      if (cbs[i].checked) sel.push(cbs[i].value);
    }
    try { localStorage.setItem('pm_selected', JSON.stringify(sel)); } catch (e) { /* ignore */ }
  }

  function restoreSelection() {
    try {
      var saved = localStorage.getItem('pm_selected');
      if (!saved) return false;
      var sel = JSON.parse(saved);
      if (!Array.isArray(sel) || sel.length === 0) return false;
      var cbs = document.querySelectorAll('.product-checkbox');
      for (var i = 0; i < cbs.length; i++) {
        cbs[i].checked = sel.indexOf(cbs[i].value) >= 0;
      }
      return true;
    } catch (e) { return false; }
  }

  function showError(msg, permanent) {
    var banner = document.getElementById('errorBanner');
    if (!banner) return;
    banner.textContent = msg;
    banner.classList.add('visible');
    if (!permanent) {
      setTimeout(function () { banner.classList.remove('visible'); }, 8000);
    }
  }

  function clearError() {
    var banner = document.getElementById('errorBanner');
    if (banner) banner.classList.remove('visible');
  }

  function setLoading(on) {
    isLoading = on;
    var btn = document.getElementById('refreshButton');
    if (btn) {
      btn.disabled = on;
      btn.innerHTML = on ? '<span class="spinner"></span>刷新中...' : '🔄 刷新行情';
    }
  }

  function setStatus(msg) {
    var el = document.getElementById('refreshStatus');
    if (el) el.textContent = msg;
  }

  // ── 数据渲染 ──

  function renderTable(metals) {
    var tbody = document.getElementById('priceTableBody');
    var html = '';
    for (var i = 0; i < metals.length; i++) {
      var m = metals[i];
      var icon = CATEGORY_ICONS[m.category] || '📊';
      var cls = m.change_pct > 0 ? 'change-positive' : m.change_pct < 0 ? 'change-negative' : 'change-neutral';
      var clsM = m.mom_pct > 0 ? 'change-positive' : m.mom_pct < 0 ? 'change-negative' : 'change-neutral';
      var clsY = m.yoy_pct > 0 ? 'change-positive' : m.yoy_pct < 0 ? 'change-negative' : 'change-neutral';
      var sig = m.signal || '--';
      var tagCls = 'tag-neutral';
      if (sig.indexOf('超卖') >= 0 || sig.indexOf('偏强') >= 0 || sig.indexOf('买入') >= 0) tagCls = 'tag-buy';
      else if (sig.indexOf('超买') >= 0) tagCls = 'tag-warning';
      else if (sig.indexOf('偏弱') >= 0) tagCls = 'tag-bearish';
      html += '<tr>';
      html += '<td><div class="metal-name">' + icon + ' ' + m.full_name + '</div><span class="metal-symbol">' + m.symbol + '</span></td>';
      html += '<td><div class="price">' + m.price + '</div><span class="unit">' + m.unit + '</span></td>';
      html += '<td>' + (m.open || '--') + '</td><td>' + (m.high || '--') + '</td><td>' + (m.low || '--') + '</td>';
      html += '<td class="' + cls + '">' + (m.change || '--') + '</td>';
      html += '<td class="' + cls + '">' + (m.change_pct != null ? m.change_pct + '%' : '--') + '</td>';
      html += '<td class="' + clsM + '">' + (m.mom_pct != null ? m.mom_pct + '%' : '--') + '</td>';
      html += '<td class="' + clsY + '">' + (m.yoy_pct != null ? m.yoy_pct + '%' : '--') + '</td>';
      html += '<td><span class="tag ' + tagCls + '">' + sig + '</span></td>';
      html += '<td><button class="ai-button" data-product="' + m.name + '">AI 分析</button></td>';
      html += '</tr>';
    }
    tbody.innerHTML = html;
  }

  function renderTechGrid(metals) {
    var grid = document.getElementById('technicalAnalysisGrid');
    var html = '';
    for (var i = 0; i < metals.length; i++) {
      var m = metals[i];
      var icon = CATEGORY_ICONS[m.category] || '📊';
      html += '<div class="tech-card">';
      html += '<div class="card-title">' + icon + ' ' + m.full_name + ' - 技术分析</div>';
      html += '<div class="tech-row"><span class="label">趋势</span><span>' + (m.trend || '--') + '</span></div>';
      html += '<div class="tech-row"><span class="label">RSI</span><span>' + (m.rsi != null ? m.rsi : '--') + '</span></div>';
      html += '<div class="tech-row"><span class="label">MA5</span><span>' + (m.sma_5 != null ? m.sma_5 : '--') + '</span></div>';
      html += '<div class="tech-row"><span class="label">MA20</span><span>' + (m.sma_20 != null ? m.sma_20 : '--') + '</span></div>';
      html += '<div class="tech-row"><span class="label">阻力</span><span>' + (m.resistance_level != null ? m.resistance_level : '--') + '</span></div>';
      html += '<div class="tech-row"><span class="label">支撑</span><span>' + (m.support_level != null ? m.support_level : '--') + '</span></div>';
      html += '<div class="tech-row"><span class="label">波动率</span><span>' + (m.volatility != null ? m.volatility : '--') + '</span></div>';
      html += '<div class="tech-row"><span class="label">环比</span><span>' + (m.mom_direction || '--') + '</span></div>';
      html += '<div class="tech-row"><span class="label">同比</span><span>' + (m.yoy_direction || '--') + '</span></div>';
      html += '</div>';
    }
    grid.innerHTML = html;
  }

  function updateBanner(market) {
    document.getElementById('marketSentiment').textContent = market.overall_sentiment || '--';
    document.getElementById('gainCount').textContent = market.total_gainers != null ? market.total_gainers : 0;
    document.getElementById('lossCount').textContent = market.total_losers != null ? market.total_losers : 0;
    document.getElementById('avgChangePct').textContent = (market.avg_change_pct != null ? market.avg_change_pct : 0) + '%';
    if (market.strongest) {
      document.getElementById('strongestName').textContent = market.strongest.name;
      document.getElementById('strongestSub').textContent = '涨幅: ' + market.strongest.change_pct + '%';
    }
    if (market.weakest) {
      document.getElementById('weakestName').textContent = market.weakest.name;
      document.getElementById('weakestSub').textContent = '涨幅: ' + market.weakest.change_pct + '%';
    }
    document.getElementById('gainLossCount').textContent = (market.total_gainers || 0) + '/' + (market.total_losers || 0);
  }

  function updateSummary(text) {
    document.getElementById('summaryText').textContent = text || '当前暂无摘要信息。';
  }

  var _lastFetchTime = null;

  function updateMeta(d, t, source) {
    var displayTime = document.getElementById('fetchTimeDisplay');
    if (displayTime) displayTime.textContent = t || '--';
    var badge = document.getElementById('dataSourceBadge');
    if (badge) {
      var sourceText = source || '模拟行情';
      badge.style.color = sourceText.indexOf('实时') >= 0 ? '#8efc7f' : '#ffd700';
      badge.textContent = '数据源: ' + sourceText;
    }
    if (t) _lastFetchTime = t;
  }

  // 每分钟更新数据年龄指示
  function updateDataAge() {
    var badge = document.getElementById('dataAgeBadge');
    if (!badge) return;
    if (!_lastFetchTime) {
      badge.textContent = '● 未知';
      badge.style.color = '#ff8d8d';
      return;
    }
    var now = new Date();
    var fetchDate = new Date(_lastFetchTime.replace(/-/g, '/'));
    var diffMs = now - fetchDate;
    var diffMin = Math.floor(diffMs / 60000);
    if (diffMin < 1) {
      badge.textContent = '● 刚刚';
      badge.style.color = '#8efc7f';
    } else if (diffMin < 3) {
      badge.textContent = '● ' + diffMin + '分钟前';
      badge.style.color = '#8efc7f';
    } else if (diffMin < 6) {
      badge.textContent = '● ' + diffMin + '分钟前';
      badge.style.color = '#ffd700';
    } else if (diffMin < 15) {
      badge.textContent = '● ' + diffMin + '分钟前 (数据可能过时)';
      badge.style.color = '#ff8d8d';
    } else {
      badge.textContent = '⚠️ ' + diffMin + '分钟前 (请刷新)';
      badge.style.color = '#ff6b6b';
    }
  }

  // ── 表格列排序 ──

  function setupTableSorting() {
    var ths = document.querySelectorAll('#priceTable thead th');
    var sortState = { col: -1, asc: true };

    for (var i = 0; i < ths.length; i++) {
      (function (idx) {
        ths[idx].addEventListener('click', function () {
          var tbody = document.getElementById('priceTableBody');
          var rows = Array.from(tbody.querySelectorAll('tr'));
          if (rows.length === 0) return;

          // Update sort state
          if (sortState.col === idx) {
            sortState.asc = !sortState.asc;
          } else {
            sortState.col = idx;
            sortState.asc = true;
          }

          // Update arrow indicators
          for (var j = 0; j < ths.length; j++) {
            ths[j].classList.remove('sorted-asc', 'sorted-desc');
          }
          ths[idx].classList.add(sortState.asc ? 'sorted-asc' : 'sorted-desc');

          // Sort rows based on cell content
          rows.sort(function (a, b) {
            var aVal = a.cells[idx] ? a.cells[idx].textContent.trim() : '';
            var bVal = b.cells[idx] ? b.cells[idx].textContent.trim() : '';
            var aNum = parseFloat(aVal.replace(/[^0-9.-]/g, ''));
            var bNum = parseFloat(bVal.replace(/[^0-9.-]/g, ''));
            if (!isNaN(aNum) && !isNaN(bNum)) {
              return sortState.asc ? aNum - bNum : bNum - aNum;
            }
            return sortState.asc ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
          });

          // Re-append sorted rows
          for (var k = 0; k < rows.length; k++) {
            tbody.appendChild(rows[k]);
          }
        });
      })(i);
    }
  }

  // ── Chart.js 图表 ──

  function switchPeriod(period) {
    currentPeriod = period;
    var btns = document.querySelectorAll('.period-btn');
    for (var i = 0; i < btns.length; i++) {
      var b = btns[i];
      if (b.getAttribute('data-period') === period) {
        b.classList.add('active');
        b.classList.remove('inactive');
      } else {
        b.classList.remove('active');
        b.classList.add('inactive');
      }
    }
    loadChart();
  }

  function renderChart(data) {
    var canvas = document.getElementById('monthlyChart');
    if (!canvas) return;
    if (chartInstance) { chartInstance.destroy(); chartInstance = null; }
    var entries = Object.entries(data);
    if (entries.length === 0) return;
    var datasets = [];
    var colors = ['#FFD700', '#C0C0C0', '#E5E4E2', '#AAA', '#4ECDC4', '#FF6B6B', '#45B7D1'];
    var allDates = [];
    for (var i = 0; i < entries.length; i++) {
      var key = entries[i][0];
      var hd = entries[i][1];
      var color = colors[i % colors.length];
      datasets.push({
        label: hd.name || key,
        data: hd.closes,
        borderColor: color,
        borderWidth: 2,
        pointRadius: 2,
        tension: 0.3,
        fill: false
      });
      if (hd.dates.length > allDates.length) allDates = hd.dates;
    }
    var isMobile = window.innerWidth < 720;
    chartInstance = new Chart(canvas.getContext('2d'), {
      type: 'line',
      data: { labels: allDates, datasets: datasets },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            labels: { color: '#eef2ff', boxWidth: isMobile ? 8 : 12, font: { size: isMobile ? 9 : 12 } }
          }
        },
        scales: {
          x: {
            ticks: { color: '#9bb4ff', maxTicksLimit: isMobile ? 6 : 12, font: { size: isMobile ? 8 : 11 } }
          },
          y: {
            ticks: { color: '#9bb4ff', font: { size: isMobile ? 8 : 11 } }
          }
        },
        interaction: { mode: 'index', intersect: false }
      }
    });
  }

  // ── API 调用 ──

  function loadData() {
    clearError();
    var selected = getSelected();
    var params = new URLSearchParams();
    for (var i = 0; i < selected.length; i++) params.append('selected', selected[i]);
    setStatus('正在加载最新行情...');
    fetch('/api/data?' + params.toString())
      .then(function (r) {
        if (!r.ok) throw new Error('HTTP ' + r.status);
        return r.json();
      })
      .then(function (data) {
        if (data.error) { showError(data.error); return; }
        if (data.metals) {
          renderTable(data.metals);
          renderTechGrid(data.metals);
        }
        attachAIButtons();
        updateBanner(data.market_trends || {});
        updateSummary(data.summary);
        updateMeta(data.fetch_date, data.fetch_time, data.data_source);
        setStatus('行情已刷新：' + (data.fetch_time || new Date().toLocaleTimeString()));
      })
      .catch(function (err) {
        showError('数据加载失败: ' + err.message);
        setStatus('❌ 请求失败');
      });

    // Verification (delayed)
    setTimeout(function () {
      fetch('/api/verify')
        .then(function (r) { return r.json(); })
        .then(function (d) {
          var el = document.getElementById('verifyContent');
          if (!el || !d.verification) return;
          var html = '';
          for (var i = 0; i < d.verification.length; i++) {
            var v = d.verification[i];
            var ms = v.multi_sources;
            html += '<div style="display:inline-block;margin:4px 8px 4px 0;padding:6px 12px;background:rgba(255,255,255,0.03);border-radius:8px;">';
            html += '<span style="color:#ffd700;">' + v.name + '</span> ';
            html += '<span style="color:#eef2ff;">' + v.current_price + '</span> ';
            html += '<span style="color:#9bb4ff;">(ref:' + v.reference_price + ', 偏差' + v.deviation_pct + '%)</span>';
            if (ms) {
              html += ' <span style="color:#8efc7f;font-size:0.85em;">[路透:' + ms.source_a.price + ' 彭博:' + ms.source_b.price + ' 新浪:' + ms.source_c.price + ']</span>';
            }
            html += '</div>';
          }
          el.innerHTML = html;
        })
        .catch(function () { /* silently fail */ });
    }, 2000);
  }

  function loadChart() {
    var selected = getSelected();
    var params = new URLSearchParams();
    for (var i = 0; i < selected.length; i++) params.append('selected', selected[i]);
    params.append('period', currentPeriod);
    fetch('/api/history?' + params.toString())
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (data.history) renderChart(data.history);
      })
      .catch(function () { /* silently fail */ });
  }

  function refreshData() {
    setLoading(true);
    setStatus('正在刷新数据，请稍候...');
    fetch('/api/refresh')
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (data.error) { showError(data.error); setLoading(false); return; }
        loadData();
        setTimeout(loadChart, 500);
        setLoading(false);
      })
      .catch(function (err) {
        showError('刷新失败: ' + err.message);
        setStatus('❌ 刷新失败');
        setLoading(false);
      });
  }

  // ── AI 分析 ──

  function showAIDetailRow(button, data) {
    // Remove any existing detail rows
    var existing = document.querySelectorAll('.ai-detail-row');
    for (var i = 0; i < existing.length; i++) existing[i].remove();

    var tr = button.closest('tr');
    var detailRow = document.createElement('tr');
    detailRow.className = 'ai-detail-row';
    var cell = document.createElement('td');
    cell.className = 'ai-detail-cell';
    cell.setAttribute('colspan', '11');

    var pred = data.prediction || {};
    var advice = data.advice || {};
    var momentum = data.momentum || {};

    var scoreColor = data.score >= 70 ? '#8efc7f' : data.score >= 40 ? '#ffd700' : '#ff8d8d';
    var scoreLabel = data.score >= 70 ? '偏多' : data.score >= 40 ? '中性' : '偏空';

    var futuresRec = '';
    if (data.prediction && data.advice) {
      var isPositive = data.score >= 45 && (data.advice.action || '').indexOf('买入') >= 0;
      var dir = (pred.direction || '').indexOf('涨') >= 0 ? '看涨' : (pred.direction || '').indexOf('跌') >= 0 ? '看跌' : '震荡';
      var conf = pred.confidence || '中';
      futuresRec = '近期该品种期货' + dir + '信号' + (conf === '高' ? '强烈' : '一般') + '，' +
        (isPositive ? '建议关注逢低布局机会，适合短线交易者关注。' : '建议观望为主，等待趋势进一步明朗。');
    }

    cell.innerHTML =
      '<div class="ai-detail-box">' +
        '<button class="ai-detail-close" onclick="this.closest(\'.ai-detail-row\').remove()">✕ 关闭</button>' +
        '<div class="d-title">🤖 ' + data.product_name + ' — AI 深度分析</div>' +
        '<div style="margin-bottom:14px;display:flex;gap:12px;flex-wrap:wrap;align-items:center;">' +
          '<span class="ai-detail-score" style="color:' + scoreColor + '">综合评分 ' + (data.score || '--') + ' / 100 (' + scoreLabel + ')</span>' +
          '<span class="ai-detail-score" style="background:rgba(255,255,255,0.06);color:#eef2ff;font-size:0.9em;">当前价: ' + (data.current_price || '--') + '</span>' +
          '<span class="ai-detail-score" style="background:rgba(255,255,255,0.06);color:#eef2ff;font-size:0.9em;">预测: ' + (pred.direction || '--') + '</span>' +
        '</div>' +
        '<div style="margin-bottom:14px;padding:12px;background:rgba(255,215,0,0.08);border-radius:12px;border:1px solid rgba(255,215,0,0.15);">' +
          '<span style="color:#ffd700;font-weight:600;">📌 期货投资建议</span>' +
          '<span style="color:#d8dff3;margin-left:10px;font-size:0.92em;">' + futuresRec + '</span>' +
        '</div>' +
        '<div class="ai-detail-grid">' +
          '<div class="ai-detail-col">' +
            '<div class="ai-detail-item"><span class="d-label">📊 趋势分析</span><span class="d-value">' + (data.trend_analysis || '--') + '</span></div>' +
            '<div class="ai-detail-item"><span class="d-label">📈 RSI 分析</span><span class="d-value">' + (data.rsi_analysis || '--') + '</span></div>' +
            '<div class="ai-detail-item"><span class="d-label">📉 价格区间</span><span class="d-value">' + (data.range_analysis || '--') + '</span></div>' +
          '</div>' +
          '<div class="ai-detail-col">' +
            '<div class="ai-detail-item"><span class="d-label">⚡ 动量</span><span class="d-value">' + (momentum.summary || '--') + '</span></div>' +
            '<div class="ai-detail-item"><span class="d-label">🎯 预测详情</span><span class="d-value">' + (pred.detail || '--') + '</span></div>' +
            '<div class="ai-detail-item"><span class="d-label">💡 建议操作</span><span class="d-value">' + (advice.action || '--') + '</span></div>' +
            '<div class="ai-detail-item"><span class="d-label">📝 建议理由</span><span class="d-value">' + (advice.reason || '') + '</span></div>' +
          '</div>' +
        '</div>' +
      '</div>';

    detailRow.appendChild(cell);
    tr.parentNode.insertBefore(detailRow, tr.nextSibling);
    setStatus('已加载 ' + data.product_name + ' 的 AI 分析。');
  }

  function attachAIButtons() {
    var buttons = document.querySelectorAll('.ai-button');
    for (var i = 0; i < buttons.length; i++) {
      buttons[i].onclick = function () {
        var name = this.getAttribute('data-product');
        if (!name) return;
        setStatus('正在分析 ' + name + '...');
        var btn = this;
        fetch('/api/analyze/' + encodeURIComponent(name))
          .then(function (r) {
            if (!r.ok) throw new Error('HTTP ' + r.status);
            return r.json();
          })
          .then(function (data) {
            if (data.error) { showError(data.error); return; }
            showAIDetailRow(btn, data);
            document.getElementById('aiAnalysisEmpty').style.display = 'none';
            document.getElementById('aiScore').style.display = 'block';
            document.getElementById('aiScore').textContent = 'AI 评分：' + (data.score || '--');
            document.getElementById('aiDirection').textContent = '预测方向：' + (data.prediction ? data.prediction.direction || '--' : '--');
            document.getElementById('aiAdvice').textContent = '投资建议：' + (data.advice ? data.advice.action || '--' : '--');
            document.getElementById('aiDetail').textContent = data.prediction ? data.prediction.detail || '--' : '--';
            setStatus('已更新 ' + name + ' 的AI分析结果。');
          })
          .catch(function (err) {
            showError('AI分析请求失败: ' + err.message);
            setStatus('❌ AI分析失败');
          });
      };
    }
  }

  // ── 折叠面板（localStorage 持久化） ──

  function initCollapsible() {
    var headers = document.querySelectorAll('.collapsible-header');
    for (var i = 0; i < headers.length; i++) {
      (function (header) {
        var body = header.nextElementSibling;
        if (!body) return;

        // Restore saved state
        var key = 'pm_collapse_' + i;
        try {
          var saved = localStorage.getItem(key);
          if (saved === 'collapsed') {
            body.classList.add('collapsed');
            header.classList.add('collapsed');
          }
        } catch (e) { /* ignore */ }

        header.onclick = function (e) {
          // 点击内部按钮（period-btn / AI分析）时不触发折叠
          if (e.target.closest('.period-btn') || e.target.closest('button') || e.target.closest('a')) return;
          var isCollapsed = body.classList.contains('collapsed');
          if (isCollapsed) {
            body.classList.remove('collapsed');
            header.classList.remove('collapsed');
            try { localStorage.setItem(key, 'expanded'); } catch (e) { /* ignore */ }
          } else {
            body.classList.add('collapsed');
            header.classList.add('collapsed');
            try { localStorage.setItem(key, 'collapsed'); } catch (e) { /* ignore */ }
          }
        };
      })(headers[i]);
    }
  }

  // ── 初始化 ──

  document.addEventListener('DOMContentLoaded', function () {
    // Checkbox selection
    var checkboxes = document.querySelectorAll('.product-checkbox');
    for (var i = 0; i < checkboxes.length; i++) {
      checkboxes[i].addEventListener('change', function () {
        saveSelection();
        loadData();
        setTimeout(loadChart, 500);
      });
    }

    // Buttons
    document.getElementById('refreshButton').addEventListener('click', refreshData);
    document.getElementById('selectDefaultButton').addEventListener('click', function () {
      var cbs = document.querySelectorAll('.product-checkbox');
      for (var i = 0; i < cbs.length; i++) cbs[i].checked = defaultSelected.indexOf(cbs[i].value) >= 0;
      saveSelection();
      loadData();
      setTimeout(loadChart, 500);
    });
    document.getElementById('clearSelectionButton').addEventListener('click', function () {
      var cbs = document.querySelectorAll('.product-checkbox');
      for (var i = 0; i < cbs.length; i++) cbs[i].checked = false;
      saveSelection();
      loadData();
      setTimeout(loadChart, 500);
    });

    // Restore or apply default selection
    if (!restoreSelection()) {
      var cbs = document.querySelectorAll('.product-checkbox');
      for (var i = 0; i < cbs.length; i++) {
        cbs[i].checked = defaultSelected.indexOf(cbs[i].value) >= 0;
      }
    }

    // Period buttons
    var periodBtns = document.querySelectorAll('.period-btn');
    for (var i = 0; i < periodBtns.length; i++) {
      periodBtns[i].addEventListener('click', function () {
        switchPeriod(this.getAttribute('data-period'));
      });
    }

    // Setup table sorting
    setupTableSorting();

    // Collapsible panels
    initCollapsible();

    // Initial load
    setTimeout(loadData, 300);
    setTimeout(loadChart, 1000);

    // Data age indicator — update every 30s
    updateDataAge();
    setInterval(updateDataAge, 30000);

    // Auto-refresh every 5 min (frontend pulls fresh data via API)
    setInterval(function () { loadData(); setTimeout(loadChart, 500); }, 300000);

    // Resize handler
    var resizeTimer;
    window.addEventListener('resize', function () {
      clearTimeout(resizeTimer);
      resizeTimer = setTimeout(function () {
        if (chartInstance) chartInstance.resize();
      }, 300);
    });
  });

})();
