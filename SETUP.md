# OFITEC.AI - Guía de Instalación y Desarrollo

## Requisitos Previos

- Docker y Docker Compose
- Python 3.8+
- Git

## Configuración del Entorno

### 1. Clonar el repositorio
```bash
git clone https://github.com/benjaminzeman/OFITEC.AI.git
cd OFITEC.AI
```

### 2. Configurar ramas de desarrollo
```bash
git checkout -b develop
git push -u origin develop
```

### 3. Instalar dependencias Python
```bash
pip install -r requirements.txt
```

### 4. Levantar el entorno con Docker
```bash
docker-compose up -d
```

### 5. Acceder a Odoo
- URL: http://localhost:8069
- Usuario: admin
- Contraseña: admin (cambiar en producción)

## Instalación de Módulos

1. Iniciar sesión en Odoo
2. Ir a **Apps** > **Actualizar lista de apps**
3. Buscar e instalar los módulos OFITEC en orden:
   - ofitec_core
   - ofitec_security
   - ofitec_theme
   - site_management
   - project_financials
   - project_risk
   - ai_bridge
   - docuchat_ai
   - of_command_palette

## Desarrollo

### Estructura del proyecto
```
OFITEC.AI/
├── custom_addons/          # Módulos personalizados
│   ├── ofitec_core/       # Núcleo del sistema
│   ├── ofitec_security/   # Seguridad avanzada
│   ├── site_management/   # Gestión de obra
│   └── ...
├── docker-compose.yml     # Configuración Docker
├── requirements.txt       # Dependencias Python
└── implementation_plan.md # Plan de desarrollo
```

### Crear un nuevo módulo
```bash
cd custom_addons
odoo scaffold nuevo_modulo
```

### Ejecutar pruebas
```bash
python -m pytest custom_addons/ -v
```

## Configuración de Producción

### Variables de entorno
Crear archivo `.env`:
```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=ofitec_prod
DB_USER=odoo
DB_PASSWORD=secure_password
ODOO_ADMIN_PASSWORD=admin_secure
```

### Despliegue con Docker
```bash
docker-compose -f docker-compose.prod.yml up -d
```

## Solución de Problemas

### Error de conexión a base de datos
```bash
docker-compose logs db
docker-compose restart db
```

### Módulos no aparecen
1. Reiniciar contenedor Odoo
2. Verificar dependencias en `__manifest__.py`
3. Revisar logs: `docker-compose logs odoo`

### Problemas de permisos
```bash
sudo chown -R 101:101 custom_addons/
```

## Siguientes Pasos

1. Completar Fase 1 del plan de implementación
2. Configurar CI/CD básico
3. Implementar logging y monitoreo básico
4. Crear documentación de API

## Soporte

Para soporte técnico o preguntas:
- Revisar issues en GitHub
- Consultar documentación de Odoo 16
- Revisar logs del contenedor
