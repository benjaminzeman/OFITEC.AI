#!/usr/bin/env python3
"""
Script para probar la API REST del módulo OFITEC AI
"""
import requests
import json
import sys

# Ensure UTF-8 stdout to avoid Windows console encode errors
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def test_api_endpoints():
    """Prueba los endpoints de la API REST"""
    base_url = "http://localhost:8069"
    print(f"🔍 Probando API REST en {base_url}...")

    # Headers para la API
    headers = {"Content-Type": "application/json", "Accept": "application/json"}

    try:
        # Endpoint de login para obtener token (si existe)
        login_data = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "service": "common",
                "method": "login",
                "args": ["ofitec", "admin", "admin"],
            },
            "id": 1,
        }

        response = requests.post(
            f"{base_url}/web/session/authenticate", json=login_data, headers=headers
        )
        print(f"✅ Endpoint de autenticación: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            if "result" in result and result["result"]:
                session_id = response.cookies.get("session_id")
                print("✅ Autenticación exitosa")
                headers["Cookie"] = f"session_id={session_id}"
            else:
                print("⚠️  Autenticación fallida, continuando sin sesión")

        # Probar endpoint de AI Analytics (si existe)
        ai_endpoints = [
            "/api/v1/ai/models",
            "/api/v1/ai/predict",
            "/api/v1/ai/train",
            "/web/api/ai/analytics",
        ]

        for endpoint in ai_endpoints:
            try:
                response = requests.get(
                    f"{base_url}{endpoint}", headers=headers, timeout=5
                )
                print(f"Endpoint {endpoint}: {response.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"Endpoint {endpoint}: Error - {str(e)}")

        # Probar endpoint de health check
        try:
            response = requests.get(
                f"{base_url}/web/health", headers=headers, timeout=5
            )
            print(f"✅ Health check: {response.status_code}")
        except requests.exceptions.RequestException:
            print("⚠️  Health check no disponible (normal en Odoo)")

        print("\n🎉 ¡Pruebas de API completadas!")
        return True

    except Exception as e:
        print(f"❌ Error probando API: {e}")
        return False


if __name__ == "__main__":
    success = test_api_endpoints()
    sys.exit(0 if success else 1)
