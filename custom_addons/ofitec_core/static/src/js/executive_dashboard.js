/** @odoo-module */
import { whenReady } from 'web.dom_ready';

function loadChartJs() {
  return new Promise((resolve) => {
    if (window.Chart) return resolve();
    const s = document.createElement('script');
    s.src = 'https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js';
    s.async = true;
    s.onload = () => resolve();
    s.onerror = () => resolve(); // continue even if CDN blocked
    document.head.appendChild(s);
  });
}

function parseCurrentId() {
  try {
    const hash = window.location.hash || '';
    const m = /[?&#]id=(\d+)/.exec(hash);
    return m ? parseInt(m[1], 10) : null;
  } catch (e) { return null; }
}

function makeSeries() {
  // Generate 12 points resembling a cumulative cost trend
  const labels = [];
  const now = new Date();
  for (let i = 11; i >= 0; i--) {
    const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
    labels.push(d.toLocaleDateString(undefined, { month: 'short' }));
  }
  let base = 100;
  const real = labels.map(() => (base += Math.round(Math.random() * 40 + 20)));
  const budget = real.map((v, idx) => Math.round((idx + 8) * 25));
  return { labels, real, budget };
}

async function rpcCall(model, method, args = [], kwargs = {}) {
  try {
    const r = await fetch('/web/dataset/call_kw', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ model, method, args, kwargs })
    });
    const j = await r.json();
    return j && j.result;
  } catch (e) { return null; }
}

async function renderExecutiveChart() {
  await loadChartJs();
  if (!window.Chart) return;
  const canvas = document.getElementById('costTrendChart');
  if (!canvas) return;

  const palette = window.ofitecChartPalette || ['#22D3EE', '#10B981', '#93C5FD'];
  let labels, real, budget;
  const id = parseCurrentId();
  if (id) {
    // Call record method with a recordset argument [[id]]
    const data = await rpcCall('ofitec.project.financials', 'get_cost_trend_data', [[id]], {});
    if (data && data.labels) {
      labels = data.labels; real = data.real; budget = data.budget;
    }
  }
  if (!labels) {
    const demo = makeSeries();
    labels = demo.labels; real = demo.real; budget = demo.budget;
  }

  const ctx = canvas.getContext('2d');
  // Destroy previous chart if any
  if (canvas.__ofitecChart) {
    try { canvas.__ofitecChart.destroy(); } catch (e) {}
  }
  canvas.__ofitecChart = new window.Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [
        {
          label: 'Costo Real',
          data: real,
          borderColor: palette[0],
          backgroundColor: palette[0] + '33',
          fill: true,
          tension: 0.35,
        },
        {
          label: 'Presupuesto',
          data: budget,
          borderColor: palette[1],
          backgroundColor: 'transparent',
          borderDash: [6, 6],
          tension: 0.3,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: { legend: { position: 'bottom' } },
      scales: {
        y: { beginAtZero: true },
      },
    },
  });
}

function setupObserver() {
  const obs = new MutationObserver(() => {
    // Render when canvas appears or URL changes
    if (document.getElementById('costTrendChart')) {
      renderExecutiveChart();
    }
  });
  obs.observe(document.body, { childList: true, subtree: true });
  window.addEventListener('hashchange', renderExecutiveChart);
  window.addEventListener('ofitec:theme-changed', renderExecutiveChart);
}

whenReady(() => {
  // Quick attempt immediately, then observe changes
  renderExecutiveChart();
  setupObserver();
});
