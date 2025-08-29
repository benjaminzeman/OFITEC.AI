# ofitec\_theme — módulo Odoo listo (Light/Dark DeFi)

Copia estas carpetas y archivos tal cual dentro de `custom_addons/ofitec_theme/`.

## Árbol

```
ofitec_theme/
├── __init__.py
├── __manifest__.py
├── static/
│   ├── description/
│   │   └── icon.png (place‑holder)
│   ├── src/
│   │   ├── js/
│   │   │   └── theme_switch.js
│   │   └── scss/
│   │       ├── variables.scss
│   │       ├── light_theme.scss
│   │       └── dark_theme.scss
│   └── xml/
│       └── assets.xml
└── views/
    └── theme_templates.xml
```

---

## `__init__.py`

```python
# empty on purpose
```

## `__manifest__.py`

```python
{
    "name": "OFITEC Theme",
    "version": "1.0.0",
    "category": "Theme/Backend",
    "summary": "Tema corporativo OFITEC con modo claro y oscuro (estética DeFi)",
    "author": "OFITEC",
    "license": "LGPL-3",
    "depends": ["web"],
    "data": [
        "views/theme_templates.xml"
    ],
    "assets": {
        "web.assets_backend": [
            "ofitec_theme/static/src/scss/variables.scss",
            "ofitec_theme/static/src/scss/light_theme.scss",
            "ofitec_theme/static/src/scss/dark_theme.scss",
            "ofitec_theme/static/src/js/theme_switch.js"
        ]
    },
    "installable": True,
    "application": False
}
```

---

## `static/xml/assets.xml`

```xml
<odoo>
  <template id="assets_backend" inherit_id="web.assets_backend" name="OFITEC Theme Assets">
    <xpath expr="." position="inside">
      <link rel="stylesheet" type="text/scss" href="/ofitec_theme/static/src/scss/variables.scss"/>
      <link rel="stylesheet" type="text/scss" href="/ofitec_theme/static/src/scss/light_theme.scss"/>
      <link rel="stylesheet" type="text/scss" href="/ofitec_theme/static/src/scss/dark_theme.scss"/>
      <script type="text/javascript" src="/ofitec_theme/static/src/js/theme_switch.js"></script>
    </xpath>
  </template>
</odoo>
```

---

## `views/theme_templates.xml`

```xml
<odoo>
  <!-- Botón de cambio de tema en el menú de usuario -->
  <template id="theme_switch_button" inherit_id="web.user_menu" name="OFITEC Theme Switch Button">
    <xpath expr="//div[contains(@class,'o_user_menu')]" position="inside">
      <button type="button" class="btn btn-sm ofitec-theme-switch" onclick="window.ofitecToggleTheme()">
        Cambiar tema
      </button>
    </xpath>
  </template>
</odoo>
```

---

## `static/src/js/theme_switch.js`

```javascript
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
  };
});
```

---

## `static/src/scss/variables.scss`

```scss
// Paleta base DeFi Verde OFITEC
$primary-color: #00c896;
$secondary-color: #046C54;
$accent-color: #A6F5E1;
$warning-color: #F5F749;
$error-color: #FF4D4F;

// Tipografía
$font-family-base: 'Inter', 'Poppins', system-ui, -apple-system, sans-serif;
$border-radius-base: 14px;

:root {
  --of-primary: #00c896;
  --of-secondary: #046C54;
  --of-bg-dark: #121212;
  --of-bg-light: #f8f9fa;
  --of-text-dark: #1A1A1A;
  --of-text-light: #E1E1E1;
}
```

---

## `static/src/scss/light_theme.scss`

```scss
body.light-mode {
  background-color: var(--of-bg-light);
  color: var(--of-text-dark);
  font-family: $font-family-base;

  .o_main_navbar {
    background: linear-gradient(90deg, $primary-color 0%, lighten($primary-color, 10%) 100%);
    color: #fff;
  }

  .btn-primary {
    background-color: $primary-color;
    border-radius: $border-radius-base;
    border: none;
    &:hover { background-color: darken($primary-color, 5%); }
  }

  .o_form_view, .o_list_view, .o_kanban_view {
    .o_form_sheet_bg, .o_content, .o_kanban_group, table.o_list_view {
      background: #ffffffaa;
      backdrop-filter: blur(6px);
      border-radius: $border-radius-base;
      box-shadow: 0 8px 24px rgba(0,0,0,0.06);
    }
  }

  .card, .o_stat_info, .o_statusbar_buttons {
    background: #fff;
    border-radius: $border-radius-base;
    box-shadow: 0 6px 16px rgba(0,0,0,0.07);
  }
}
```

---

## `static/src/scss/dark_theme.scss`

```scss
body.dark-mode {
  background-color: var(--of-bg-dark);
  color: var(--of-text-light);
  font-family: $font-family-base;

  .o_main_navbar {
    background: linear-gradient(90deg, $secondary-color 0%, darken($secondary-color, 10%) 100%);
    color: #fff;
  }

  .btn-primary {
    background-color: $primary-color;
    border-radius: $border-radius-base;
    border: none;
    &:hover { background-color: lighten($primary-color, 6%); }
  }

  .o_form_view, .o_list_view, .o_kanban_view {
    .o_form_sheet_bg, .o_content, .o_kanban_group, table.o_list_view {
      background: rgba(30,30,30,0.8);
      backdrop-filter: blur(8px);
      border-radius: $border-radius-base;
      box-shadow: 0 12px 28px rgba(0,0,0,0.35);
    }
  }

  .card, .o_stat_info, .o_statusbar_buttons {
    background: rgba(35,35,35,0.9);
    border-radius: $border-radius-base;
    box-shadow: 0 10px 24px rgba(0,0,0,0.35);
  }
}
```

---

## `static/description/icon.png`

> Usa cualquier PNG de 128×128 como ícono (place‑holder). Si lo dejas vacío igualmente instala.

---

## Instalación rápida

1. Crea la carpeta `custom_addons/ofitec_theme/` y pega estos archivos.
2. Actualiza lista de Apps en Odoo → instala **OFITEC Theme**.
3. En el menú de usuario, usa **Cambiar tema** para alternar **claro/oscuro**.

> Compatible con Odoo Community y módulos OCA; sólo afecta presentación (SCSS/QWeb/JS), no la lógica de negocio ni los datos.

