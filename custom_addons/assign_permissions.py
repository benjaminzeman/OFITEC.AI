#!/usr/bin/env python3
"""
Script para asignar permisos de contabilidad al usuario admin
"""
import sys
import os

sys.path.insert(0, "/usr/lib/python3/dist-packages")


def assign_accounting_permissions():
    """Asignar permisos de contabilidad al usuario admin"""
    try:
        # Configurar Odoo
        os.environ["DB_HOST"] = "db"
        os.environ["DB_USER"] = "odoo"
        os.environ["DB_PASSWORD"] = "odoo"
        os.environ["DB_NAME"] = "ofitec"

        from odoo import api, SUPERUSER_ID
        from odoo.service.db import exp_db_exists

        # Verificar conexión a BD
        if not exp_db_exists("ofitec"):
            print("❌ Base de datos no encontrada")
            return False

        # Conectar
        from odoo.sql_db import db_connect

        db = db_connect("ofitec")

        with db.cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, {})

            # Buscar usuario admin
            user = env["res.users"].search([("login", "=", "admin")])
            if not user:
                print("❌ Usuario admin no encontrado")
                return False

            print(f"✅ Usuario encontrado: {user.name} (ID: {user.id})")

            # Buscar grupos de contabilidad
            group_names = [
                "Invoicing/Billing",
                "Invoicing/Billing Administrator",
                "Technical/Show Accounting Features - Readonly",
                "User types/Internal User",
            ]

            groups = env["res.groups"].search([("name", "in", group_names)])

            if groups:
                print(f"✅ Grupos encontrados: {[g.name for g in groups]}")

                # Asignar grupos al usuario
                user.write({"groups_id": [(4, g.id) for g in groups]})
                print("✅ Permisos de contabilidad asignados correctamente")
            else:
                print(
                    "⚠️  No se encontraron grupos específicos, asignando grupos básicos"
                )

                # Asignar grupos básicos
                basic_groups = env["res.groups"].search(
                    [
                        (
                            "name",
                            "in",
                            [
                                "User types/Internal User",
                                "Technical/Show Accounting Features - Readonly",
                            ],
                        )
                    ]
                )
                if basic_groups:
                    user.write({"groups_id": [(4, g.id) for g in basic_groups]})
                    print("✅ Grupos básicos asignados")

            return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    success = assign_accounting_permissions()
    sys.exit(0 if success else 1)


def create_custom_module_access(model_name, group_name="Internal User"):
    """Crear reglas de acceso para módulos custom"""
    try:
        import psycopg2

        conn = psycopg2.connect(
            host="db", database="ofitec", user="odoo", password="odoo"
        )
        conn.autocommit = True
        cur = conn.cursor()

        print(f"🔧 Creando regla de acceso para {model_name}...")

        # Obtener el ID del modelo
        cur.execute("SELECT id FROM ir_model WHERE model = %s", (model_name,))
        model_result = cur.fetchone()
        if not model_result:
            print(f"❌ Modelo {model_name} no encontrado")
            return False

        model_id = model_result[0]

        # Obtener el ID del grupo
        cur.execute("SELECT id FROM res_groups WHERE id = 1")  # Internal User
        group_result = cur.fetchone()
        if not group_result:
            print(f"❌ Grupo {group_name} no encontrado")
            return False

        group_id = group_result[0]

        # Crear regla de acceso con permisos completos
        insert_query = (
            "INSERT INTO ir_model_access "
            "(model_id, group_id, perm_read, perm_write, perm_create, perm_unlink, name) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s)"
        )
        cur.execute(
            insert_query,
            (
                model_id,
                group_id,
                True,
                True,
                True,
                True,
                f"{model_name}.access_{model_name.replace('.', '_')}_internal_user",
            ),
        )

        print(f"✅ Regla de acceso creada para {model_name}")
        conn.close()
        return True

    except Exception as e:
        print(f"❌ Error creando acceso para {model_name}: {e}")
        return False
