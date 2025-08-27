#!/usr/bin/env python3
"""
Script para asignar permisos de administrador al usuario admin
"""
import os
import sys
sys.path.insert(0, '/usr/lib/python3/dist-packages')

def assign_admin_permissions():
    """Asignar permisos de administrador al usuario admin"""
    try:
        # Configurar variables de entorno
        os.environ['DB_HOST'] = 'db'
        os.environ['DB_USER'] = 'odoo'
        os.environ['DB_PASSWORD'] = 'odoo'
        os.environ['DB_NAME'] = 'ofitec'

        from odoo import api, SUPERUSER_ID
        from odoo.sql_db import db_connect

        db = db_connect('ofitec')
        with db.cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, {})

            # Buscar usuario admin
            user = env['res.users'].search([('login', '=', 'admin')])
            if not user:
                print("❌ Usuario admin no encontrado")
                return False

            print(f"✅ Usuario encontrado: {user.name} (ID: {user.id})")

            # Buscar grupos importantes
            group_names = [
                'Administrator',
                'Internal User',
                'Settings',
                'Access Rights'
            ]

            groups = env['res.groups'].search([('name', 'in', group_names)])

            if groups:
                print(f"✅ Grupos encontrados: {[g.name for g in groups]}")

                # Asignar grupos al usuario
                for group in groups:
                    if group not in user.groups_id:
                        user.write({'groups_id': [(4, group.id)]})
                        print(f"✅ Grupo asignado: {group.name}")
                    else:
                        print(f"ℹ️  Grupo ya asignado: {group.name}")
            else:
                print("⚠️  No se encontraron grupos específicos")

            # También intentar asignar permisos de contabilidad si existen
            try:
                accounting_groups = env['res.groups'].search([('name', 'ilike', '%account%')])
                if accounting_groups:
                    print(f"📊 Grupos de contabilidad encontrados: {len(accounting_groups)}")
                    for group in accounting_groups:
                        if group not in user.groups_id:
                            user.write({'groups_id': [(4, group.id)]})
                            print(f"✅ Grupo de contabilidad asignado: {group.name}")
            except Exception as e:
                print(f"⚠️  Error asignando grupos de contabilidad: {e}")

            return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = assign_admin_permissions()
    sys.exit(0 if success else 1)
