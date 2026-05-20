import re

with open('templates/report.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Replace old media queries with new responsive CSS
old1 = """@media (max-width:980px) { .controls-panel { grid-template-columns:1fr; } table { min-width:100%; } .ai-detail-grid { grid-template-columns:1fr; } }
@media (max-width:720px) { body { padding:12px; } .header h1 { font-size:1.7em; } .sentiment-banner { grid-template-columns:1fr; } }"""

new1 = """/* ===== 响应式设计 - 手机端适配 (兼容微信小程序) ===== */
@media (max-width:980px) {
  .controls-panel { grid-template-columns:1fr; }
  table { min-width:100%; }
  .ai-detail-grid { grid-template-columns:1fr; }
  .categories-grid { grid-template-columns:repeat(auto-fit,minmax(140px,1fr)); }
}
@media (max-width:720px) {
  body { padding:10px; }
  .header { padding:18px 14px; }
  .header h1 { font-size:1.3em; letter-spacing:1px; }
  .header .subtitle { font-size:0.82em; }
  .header .meta { font-size:0.78em; }
  .panel { padding:14px; }
  .panel-title { font-size:0.95em; }
  .sentiment-banner { grid-template-columns:1fr 1fr; gap:10px; padding:12px; }
  .sentiment-item { padding:10px; }
  .sentiment-item .value { font-size:1.1em; }
  .stats-grid { grid-template-columns:1fr; gap:10px; padding:12px; }
  .stat-card .value { font-size:1.2em; }
  .categories-grid { grid-template-columns:repeat(2,1fr); gap:10px; }
  .category-group { padding:10px; }
  .checkbox-label { font-size:0.85em; margin-bottom:8px; }
  .action-group button, .ai-button { padding:12px 14px; font-size:0.9em; }
  .tech-grid { grid-template-columns:1fr; gap:12px; }
  .chart-section { padding:14px; }
  .chart-wrapper { height:220px; }
  .summary-box { padding:16px; font-size:0.88em; }
  .disclaimer { font-size:0.72em; padding:12px 10px; }
  .ai-panel { padding:14px; }
  .ai-detail-cell { padding:12px 14px; }
  .ai-detail-box { padding:14px; }
  .ai-detail-box .d-title { font-size:0.9em; }
  .ai-detail-item { font-size:0.82em; padding:6px 10px; }
  .ai-detail-score { font-size:0.9em; padding:8px 12px; }
  .ai-detail-grid { gap:10px; }
  .ai-detail-text { font-size:0.82em; }
  .notice-box { font-size:0.82em; padding:10px 12px; }
  .table-container { overflow-x:auto; -webkit-overflow-scrolling:touch; }
  .table-container table { min-width:650px; font-size:0.82em; }
  .table-container thead th { padding:8px 6px; font-size:0.75em; white-space:nowrap; }
  .table-container tbody td { padding:8px 6px; font-size:0.82em; white-space:nowrap; }
  .chart-header { flex-wrap:wrap; gap:8px; }
  .chart-header button { padding:6px 12px !important; font-size:0.72em !important; }
}
@media (max-width:420px) {
  body { padding:6px; }
  .header { padding:12px 10px; margin-bottom:14px; }
  .header h1 { font-size:1.05em; }
  .header .subtitle { font-size:0.75em; }
  .header .meta { font-size:0.7em; }
  .panel { padding:10px; }
  .categories-grid { grid-template-columns:1fr 1fr; gap:6px; }
  .category-group { padding:8px; }
  .category-title { font-size:0.85em; }
  .checkbox-label { font-size:0.78em; margin-bottom:6px; }
  .checkbox-label input { width:14px; height:14px; }
  .sentiment-banner { grid-template-columns:1fr 1fr; gap:6px; padding:8px; }
  .sentiment-item { padding:8px; }
  .sentiment-item .label { font-size:0.72em; }
  .sentiment-item .value { font-size:1em; }
  .stats-grid { gap:8px; padding:8px; }
  .stat-card .label { font-size:0.78em; }
  .action-group button, .ai-button { padding:10px; font-size:0.82em; border-radius:10px; }
  .table-container table { min-width:550px; font-size:0.72em; }
  .table-container thead th { padding:6px 4px; font-size:0.68em; }
  .table-container tbody td { padding:6px 4px; font-size:0.72em; }
  .chart-section { padding:10px; }
  .chart-wrapper { height:180px; }
  .tech-grid { gap:8px; }
  .tech-card { padding:12px; }
  .tech-card .card-title { font-size:0.85em; }
  .tech-row { font-size:0.78em; }
  .summary-box { padding:12px; font-size:0.8em; line-height:1.6; }
  .ai-panel { padding:10px; }
  .ai-detail-cell { padding:8px 10px; }
  .ai-detail-box { padding:10px; }
  .ai-detail-box .d-title { font-size:0.82em; }
  .ai-detail-item { font-size:0.75em; padding:4px 8px; }
  .ai-detail-score { font-size:0.82em; padding:6px 10px; }
  .ai-detail-grid { gap:8px; }
  .chart-header button { padding:4px 10px !important; font-size:0.68em !important; }
  .disclaimer { font-size:0.65em; }
  .notice-box { font-size:0.75em; padding:8px 10px; }
}
.chart-wrapper canvas { max-width:100%; max-height:100%; }
@media (hover:none) and (pointer:coarse) {
  .ai-button, .action-group button, .period-btn { min-height:44px; }
  .checkbox-label { padding:4px 0; }
  .checkbox-label input { width:18px; height:18px; }
}"""

assert old1 in content, 'OLD1 NOT FOUND'
content = content.replace(old1, new1)
print('OK - media queries replaced')

# 2. Add touch-action and period-btn CSS
old2 = """.disclaimer { text-align:center; padding:18px 16px; font-size:0.82em; color:#a9b3d7; }
.ai-detail-row"""

new2 = """button, .checkbox-label, .product-checkbox, .period-btn, .ai-button { touch-action:manipulation; }
.disclaimer { text-align:center; padding:18px 16px; font-size:0.82em; color:#a9b3d7; }
.period-btn { padding:4px 14px; border-radius:8px; cursor:pointer; font-size:0.78em; transition:all 0.2s; }
.period-btn.active { background:rgba(255,215,0,0.2); border:1px solid rgba(255,215,0,0.3); color:#ffd700; }
.period-btn.inactive { background:transparent; border:1px solid rgba(255,255,255,0.15); color:#ccc; }
.period-btn:hover { opacity:0.8; }
@media (hover:none) and (pointer:coarse) { .period-btn { min-height:44px; padding:8px 16px !important; } }
.ai-detail-row"""

assert old2 in content, 'OLD2 NOT FOUND'
content = content.replace(old2, new2)
print('OK - period-btn classes added')

with open('templates/report.html', 'w', encoding='utf-8') as f:
    f.write(content)
print('OK - file saved')
