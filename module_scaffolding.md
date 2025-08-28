# 🗂 Scaffolding de Addons de OFITEC

A modo de avance, aquí quedan los archivos `__init__.py` y `__manifest__.py` para cada módulo, listos para copiar en `custom_addons/`:

---

## ofitec\_core

**init****.py**

```python
from . import models
from . import controllers
```

**manifest****.py**

```python
{
    'name': 'OFITEC Core',
    'version': '16.0.1.0.0',
    'category': 'Base',
    'summary': 'API central y modelos de datos compartidos',
    'depends': ['base', 'project', 'res_users'],
    'data': [
        'security/ir.model.access.csv',
        'security/core_security.xml',
        'data/core_data.xml',
    ],
    'installable': True,
    'application': False,
}
```

---

## ofitec\_security

**init****.py**

```python
from . import models
from . import controllers
```

**manifest****.py**

```python
{
    'name': 'OFITEC Security',
    'version': '16.0.1.0.0',
    'category': 'Settings',
    'summary': 'Roles, permisos y autenticación avanzada',
    'depends': ['base', 'ofitec_core'],
    'data': [
        'security/ir.model.access.csv',
        'data/security_groups.xml',
        'data/record_rules.xml',
        'data/sso_data.xml',
        'views/security_settings_views.xml',
        'views/groups_views.xml',
        'views/record_rules_views.xml',
    ],
    'installable': True,
    'application': False,
}
```

---

## site\_management

**init****.py**

```python
from . import models
```

**manifest****.py**

```python
{
    'name': 'Site Management',
    'version': '16.0.1.0.0',
    'category': 'Project',
    'summary': 'Gestión de reportes diarios de obra',
    'depends': ['project'],
    'data': [
        'views/daily_report_views.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': False,
}
```

---

## project\_financials

**init****.py**

```python
from . import models
```

**manifest****.py**

```python
{
    'name': 'Project Financials',
    'version': '16.0.1.0.0',
    'category': 'Accounting/Project',
    'summary': 'Presupuestos y órdenes de cambio de proyectos',
    'depends': ['project', 'account'],
    'data': [],  # Agregar vistas y security
    'installable': True,
    'application': False,
}
```

---

## flow\_management

**init****.py**

```python
from . import models
```

**manifest****.py**

```python
{
    'name': 'Flow Management',
    'version': '16.0.1.0.0',
    'category': 'Accounting/Reporting',
    'summary': 'Flujo de caja interactivo semanal',
    'depends': ['project', 'purchase', 'account', 'sale_management', 'ofitec_theme'],
    'data': [
        'data/ir_cron.xml',
        'views/cashflow_views.xml',
    ],
    'installable': True,
    'application': False,
}
```

---

## bank\_connector\_openbanking

**init****.py**

```python
from . import models
```

**manifest****.py**

```python
{
    'name': 'Bank Connector (OpenBanking)',
    'version': '16.0.1.0.0',
    'category': 'Accounting/Integration',
    'summary': 'Importa extractos bancarios vía OFX, SFTP y APIs Open Banking',
    'depends': ['account', 'ofitec_security'],
    'data': [
        'views/bank_views.xml',
        'data/ir_cron_bank.xml',
    ],
    'installable': True,
    'application': False,
}
```

---

## site\_performance

**init****.py**

```python
from . import models
```

**manifest****.py**

```python
{
    'name': 'Site Performance',
    'version': '16.0.1.0.0',
    'category': 'Project/Reporting',
    'summary': 'KPIs y alertas de rendimiento de obra',
    'depends': ['site_management', 'ofitec_theme'],
    'data': [
        'views/performance_views.xml',
    ],
    'installable': True,
    'application': False,
}
```

---

## payroll

**init****.py**

```python
# Se asume uso de módulo existente hr_payroll
```

**manifest****.py**

```python
{
    'name': 'Payroll Integration',
    'version': '16.0.1.0.0',
    'category': 'Human Resources',
    'summary': 'Integración de nómina al flujo de caja',
    'depends': ['hr_payroll_account_move', 'flow_management'],
    'data': [],
    'installable': True,
    'application': False,
}
```

---

## subcontractor\_management

**init****.py**

```python
from . import models
```

**manifest****.py**

```python
{
    'name': 'Subcontractor Management',
    'version': '16.0.1.0.0',
    'category': 'Project',
    'summary': 'Control de subcontratistas, contratos y pagos',
    'depends': ['project', 'site_management', 'flow_management', 'ofitec_theme'],
    'data': [],
    'installable': True,
    'application': False,
}
```

---

## sii\_connector

**init****.py**

```python
from . import models
```

**manifest****.py**

```python
{
    'name': 'SII Connector',
    'version': '16.0.1.0.0',
    'category': 'Accounting/Integration',
    'summary': 'Conexión con Web Services del SII',
    'depends': ['ofitec_security', 'flow_management'],
    'data': [],  # Agregar data/sii_menu.xml y ir_cron_sii.xml
    'installable': True,
    'application': False,
}
```

---

Estos archivos marcan el punto de partida para cada addon. Cuando tengas acceso a Codespaces, podrás copiarlos y comenzar a incorporar el código detallado en cada chat de módulo.

