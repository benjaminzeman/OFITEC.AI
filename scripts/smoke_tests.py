#!/usr/bin/env python3
"""
OFITEC.AI - Smoke tests básicos

Ejecuta validaciones mínimas contra una instancia local de Odoo con addons OFITEC:
- Health API JSON
- Endpoint Dashboard (si autenticado, opcional)
- Verificación webhook WhatsApp (GET)

Uso:
    python scripts/smoke_tests.py --host http://localhost:8069 --challenge abc --token test

Nota: Para rutas autenticadas se recomienda probar desde el cliente web o
usar cookies de sesión. Este script sólo hace checks públicos/simples.
"""
import argparse
import sys
import requests


def check_health(base):
    url = f"{base.rstrip('/')}/ofitec/api/health"
    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        print("[OK] Health:", r.json())
        return True
    except Exception as e:
        # fallback a endpoint http plano
        try:
            url2 = f"{base.rstrip('/')}/ofitec/health"
            r2 = requests.get(url2, timeout=5)
            r2.raise_for_status()
            print("[OK] Health (fallback):", r2.json())
            return True
        except Exception as e2:
            print("[FAIL] Health:", e, "| Fallback:", e2)
            return False


def check_whatsapp_webhook(base, challenge, token):
    # Nota: requiere una configuración con ID válido para devolver el challenge.
    # Aquí sólo validamos que el endpoint responda (404 esperado si no existe config).
    url = (
        f"{base.rstrip('/')}/webhooks/whatsapp/1?hub.mode=subscribe"
        f"&hub.verify_token={token}&hub.challenge={challenge}"
    )
    try:
        r = requests.get(url, timeout=5)
        print(f"[INFO] WhatsApp webhook status: {r.status_code}")
        return r.status_code in (200, 403, 404)
    except Exception as e:
        print("[FAIL] WhatsApp webhook:", e)
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="http://localhost:8069")
    ap.add_argument("--challenge", default="challenge123")
    ap.add_argument("--token", default="test_token")
    args = ap.parse_args()

    ok = True
    ok &= check_health(args.host)
    ok &= check_whatsapp_webhook(args.host, args.challenge, args.token)

    print("\nSmoke tests:", "OK" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
