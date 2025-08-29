odoo.define('ofitec_theme.theme_switch', function (require) {
  "use strict";
  const { whenReady } = require('web.dom_ready');

  function applyTheme() {
    const saved = localStorage.getItem('ofitec_theme') || 'dark';
    document.body.classList.remove('light-mode', 'dark-mode');
    document.body.classList.add(saved + '-mode');
  }

  whenReady(applyTheme);

  window.ofitecToggleTheme = function () {
    const current = document.body.classList.contains('light-mode') ? 'light' : 'dark';
    const next = current === 'light' ? 'dark' : 'light';
    localStorage.setItem('ofitec_theme', next);
    applyTheme();
    try {
      window.dispatchEvent(new CustomEvent('ofitec:theme-changed', { detail: { mode: next } }));
    } catch (e) {}
  };

  // Optional: inject a small floating toggle if not present in user menu
  whenReady(() => {
    try {
      const id = 'ofitec-theme-toggle';
      if (document.getElementById(id)) return;
      const btn = document.createElement('button');
      btn.id = id;
      btn.title = 'Cambiar tema OFITEC';
      btn.textContent = '🌓';
      btn.style.position = 'fixed';
      btn.style.right = '16px';
      btn.style.bottom = '16px';
      btn.style.zIndex = 10000;
      btn.style.border = 'none';
      btn.style.borderRadius = '999px';
      btn.style.width = '44px';
      btn.style.height = '44px';
      btn.style.cursor = 'pointer';
      btn.style.fontSize = '20px';
      btn.style.boxShadow = '0 4px 12px rgba(0,0,0,.2)';
      btn.style.background = '#00c896';
      btn.style.color = '#fff';
      btn.addEventListener('click', () => window.ofitecToggleTheme());
      document.body.appendChild(btn);
    } catch (e) {
      // ignore failures, the user can still toggle via user menu binding
    }
  });
});
