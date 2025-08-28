# 🗂 Chat del módulo ofitec\_theme (Capa Estética)

> **Objetivo:** Proveer componentes UI, variables de estilo y layouts globales para todos los módulos de Ofitec, garantizando consistencia visual y facilidad de desarrollo.

## 1. Estructura del addon

```
ofitec_theme/
├── __init__.py
├── __manifest__.py
├── scss/
│   ├── _variables.scss
│   ├── _mixins.scss
│   └── _theme.scss
├── static/
│   ├── src/
│   │   ├── js/
│   │   │   └── components/
│   │   │       ├── Card.js
│   │   │       ├── Badge.js
│   │   │       ├── Modal.js
│   │   │       └── ChartWrapper.js
│   │   └── css/
│   │       └── ofitec.css
│   └── description/
│       └── icon.png
├── views/
│   └── assets.xml
└── tests/
    └── test_styles.py
```

## 2. Variables SCSS (`_variables.scss`)

```scss
// Colores
$color-primary: #0052CC;
$color-secondary: #00B8D9;
$color-success: #36B37E;
$color-warning: #FFAB00;
$color-danger:  #DE350B;
$color-neutral: #A5ADBA;

// Tipografía
type-scale:
  (xs: 0.75rem,
   sm: 0.875rem,
   base: 1rem,
   lg: 1.125rem,
   xl: 1.25rem,
   '2xl': 1.5rem);

// Espaciados
$space-unit: 0.5rem;
```

## 3. Mixins y utilidades (`_mixins.scss`)

```scss
@import 'variables';

@mixin card-style {
  background: white;
  border-radius: 0.5rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  padding: $space-unit * 2;
}

@mixin button($bg-color) {
  background-color: $bg-color;
  color: white;
  padding: $space-unit 2*$space-unit;
  border: none;
  border-radius: 0.375rem;
  cursor: pointer;
}
```

## 4. Componentes JS OWL (`static/src/js/components`)

### 4.1 Card.js

```js
/** @odoo-module */
import { Component } from '@odoo/owl';
export class Card extends Component {
    static template = 'ofitec_theme.Card';
}
```

### 4.2 Badge.js

```js
/** @odoo-module */
import { Component, useRef } from '@odoo/owl';
export class Badge extends Component {
    static props = ['state'];
    get badgeClass() {
        return `badge-${this.props.state}`;
    }
}
```

### 4.3 Modal.js

```js
/** @odoo-module */
import { Component, useState } from '@odoo/owl';
export class Modal extends Component {
    static props = ['title'];
    state = useState({ open: false });
    toggle() { this.state.open = !this.state.open; }
}
```

### 4.4 ChartWrapper.js

```js
/** @odoo-module */
import { Component } from '@odoo/owl';
import { LineChart } from 'recharts';
export class ChartWrapper extends Component {
    static props = ['data','options'];
}
```

## 5. Assets (`views/assets.xml`)

```xml
<odoo>
  <template id="assets_backend" name="ofitec_theme assets" inherit_id="web.assets_backend">
    <xpath expr=".
" position="inside">
      <link rel="stylesheet" href="/ofitec_theme/static/src/css/ofitec.css"/>
      <script type="module" src="/ofitec_theme/static/src/js/components/Card.js"/>
      <script type="module" src="/ofitec_theme/static/src/js/components/Badge.js"/>
      <script type="module" src="/ofitec_theme/static/src/js/components/Modal.js"/>
      <script type="module" src="/ofitec_theme/static/src/js/components/ChartWrapper.js"/>
    </xpath>
  </template>
</odoo>
```

## 6. Tests de estilos (`tests/test_styles.py`)

```python
from odoo.tests.common import TransactionCase

class TestStyles(TransactionCase):
    def test_scss_variables_loaded(self):
        # Verificar que los archivos SCSS se incluyan en assets
        assets = self.env['ir.ui.view'].search([('arch','ilike','ofitec.css')])
        self.assertTrue(assets, 'ofitec.css no está en assets')
```

---

Con esta capa estética en `ofitec_theme`, todos los módulos podrán:

- Reutilizar variables de color, tipografía y espaciados.
- Incluir componentes OWL consistentes (Cards, Badges, Modals, Charts).
- Mantener una apariencia homogénea en formularios, kanbans y dashboards.

Los manifests de cada módulo deben declarar dependencia de `ofitec_theme` para acceder a estos assets y componentes.

