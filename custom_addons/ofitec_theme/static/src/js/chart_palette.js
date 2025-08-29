/** @odoo-module **/
odoo.define('ofitec_theme.chart_palette', function (require) {
  'use strict';
  const { whenReady } = require('web.dom_ready');

  function css(name, fallback) {
    try { return getComputedStyle(document.documentElement).getPropertyValue(name).trim() || fallback; }
    catch (e) { return fallback; }
  }

  function getPalette() {
    return [
      css('--of-chart-1', '#22D3EE'),
      css('--of-chart-2', '#10B981'),
      css('--of-chart-3', '#93C5FD'),
      css('--of-chart-4', '#F59E0B'),
      css('--of-chart-5', '#EF4444'),
    ];
  }

  function getMode() {
    return document.body.classList.contains('light-mode') ? 'light' : 'dark';
  }

  function applyApex() {
    if (!window.Apex) return;
    const colors = getPalette();
    const mode = getMode();
    window.Apex = Object.assign({}, window.Apex, {
      theme: { mode },
      colors,
      stroke: { width: 2 },
      grid: { borderColor: mode === 'dark' ? 'rgba(255,255,255,.08)' : 'rgba(0,0,0,.08)' },
      dataLabels: { enabled: false },
      tooltip: { theme: mode },
    });
  }

  function applyChartJs() {
    if (!window.Chart) return;
    const colors = getPalette();
    const mode = getMode();
    const text = mode === 'dark' ? '#E5E7EB' : '#111827';
    const grid = mode === 'dark' ? 'rgba(255,255,255,.12)' : 'rgba(0,0,0,.12)';
    // Global defaults
    window.Chart.defaults.color = text;
    window.Chart.defaults.borderColor = grid;
    // Provide helper palette
    window.ofitecChartPalette = colors;
  }

  function applyAll() {
    applyApex();
    applyChartJs();
  }

  whenReady(applyAll);
  window.addEventListener('ofitec:theme-changed', applyAll);
});

