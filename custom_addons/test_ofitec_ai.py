#!/usr/bin/env python3
"""
Script para probar las funcionalidades del módulo OFITEC AI desde dentro de Odoo
"""
import sys
import os

sys.path.insert(0, "/usr/lib/python3/dist-packages")


def test_ofitec_ai_module():
    """Prueba las funcionalidades del módulo OFITEC AI"""
    print("🔍 Probando módulo OFITEC AI...")

    try:
        # Importar Odoo
        import odoo
        from odoo import api, fields, models
        from odoo.api import Environment

        print("✅ Odoo importado correctamente")
    except ImportError as e:
        print("❌ Error importando Odoo:", e)
        return False

    try:
        # Conectar a la base de datos usando SQLAlchemy
        import psycopg2

        conn = psycopg2.connect(
            host="db", database="ofitec", user="odoo", password="odoo"
        )
        conn.close()
        print("✅ Conexión a base de datos 'ofitec' exitosa")
    except Exception as e:
        print("❌ Error conectando a la base de datos:", e)
        return False

    try:
        # Probar importar el módulo ofitec_ai_advanced
        from odoo.addons.ofitec_ai_advanced.models import ai_advanced

        print("✅ Módulo ofitec_ai_advanced importado correctamente")

        # Verificar que la clase AIAnalyticsEngine existe
        if hasattr(ai_advanced, "AIAnalyticsEngine"):
            print("✅ Clase AIAnalyticsEngine encontrada")
        else:
            print("❌ Clase AIAnalyticsEngine no encontrada")
            return False

    except ImportError as e:
        print("❌ Error importando ofitec_ai_advanced:", e)
        return False
    except Exception as e:
        print("❌ Error general:", e)
        return False

    try:
        # Crear una instancia del motor de IA para probar
        engine = ai_advanced.AIAnalyticsEngine()
        print("✅ Instancia de AIAnalyticsEngine creada")

        # Probar métodos básicos
        if hasattr(engine, "get_available_algorithms"):
            algorithms = engine.get_available_algorithms()
            print(f"✅ Algoritmos disponibles: {algorithms}")

        if hasattr(engine, "validate_model_parameters"):
            # Probar validación de parámetros
            test_params = {"n_estimators": 100, "max_depth": 10}
            is_valid = engine.validate_model_parameters("xgboost", test_params)
            print(f"✅ Validación de parámetros XGBoost: {is_valid}")

    except Exception as e:
        print("❌ Error probando funcionalidades:", e)
        return False

    print("\n🎉 ¡Módulo OFITEC AI funciona correctamente!")
    return True


if __name__ == "__main__":
    success = test_ofitec_ai_module()
    sys.exit(0 if success else 1)
