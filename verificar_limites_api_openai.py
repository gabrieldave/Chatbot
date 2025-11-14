"""
🔍 VERIFICAR LÍMITES DE OPENAI DESDE API
=========================================

Intenta obtener límites usando diferentes endpoints de OpenAI
"""

import os
import sys
import requests
import json
from dotenv import load_dotenv

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

def get_env(key):
    value = os.getenv(key, "")
    if not value:
        for env_key in os.environ.keys():
            if env_key.strip().lstrip('\ufeff') == key:
                value = os.environ[env_key]
                break
    return value.strip('"').strip("'").strip()

OPENAI_API_KEY = get_env("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    print("❌ Error: OPENAI_API_KEY no está configurada")
    sys.exit(1)

headers = {
    "Authorization": f"Bearer {OPENAI_API_KEY}",
    "Content-Type": "application/json"
}

print("=" * 80)
print("🔍 VERIFICACIÓN DE LÍMITES DE OPENAI DESDE API")
print("=" * 80)
print()

# 1. Intentar endpoint de fine-tuning model limits
print("1️⃣  INTENTANDO: /v1/fine_tuning/model_limits")
print("-" * 80)
try:
    response = requests.get(
        "https://api.openai.com/v1/fine_tuning/model_limits",
        headers=headers,
        timeout=10
    )
    
    if response.status_code == 200:
        data = response.json()
        print("   ✅ Respuesta exitosa:")
        print(f"   {json.dumps(data, indent=2)}")
        print()
        print("   ⚠️  NOTA: Este endpoint es para límites de fine-tuning,")
        print("      no para rate limits (RPM/TPM) de embeddings")
    else:
        print(f"   ⚠️  Error {response.status_code}: {response.text[:200]}")
except Exception as e:
    print(f"   ❌ Error: {e}")

print()

# 2. Intentar hacer una llamada real a embeddings y ver headers
print("2️⃣  INTENTANDO: Llamada real a embeddings (ver headers)")
print("-" * 80)
try:
    response = requests.post(
        "https://api.openai.com/v1/embeddings",
        headers=headers,
        json={
            "model": "text-embedding-3-small",
            "input": "test"
        },
        timeout=10
    )
    
    print(f"   Status code: {response.status_code}")
    
    # Buscar headers de rate limit
    rate_limit_headers = {}
    for key, value in response.headers.items():
        if 'ratelimit' in key.lower():
            rate_limit_headers[key] = value
    
    if rate_limit_headers:
        print("   ✅ Headers de rate limit encontrados:")
        for key, value in sorted(rate_limit_headers.items()):
            print(f"      • {key}: {value}")
    else:
        print("   ⚠️  No se encontraron headers de rate limit")
    
    if response.status_code == 200:
        print("   ✅ Llamada exitosa")
    else:
        print(f"   ⚠️  Error: {response.text[:200]}")
        
except Exception as e:
    print(f"   ❌ Error: {e}")

print()

# 3. Intentar endpoint de modelos
print("3️⃣  INTENTANDO: /v1/models (listar modelos)")
print("-" * 80)
try:
    response = requests.get(
        "https://api.openai.com/v1/models",
        headers=headers,
        timeout=10
    )
    
    if response.status_code == 200:
        data = response.json()
        models = data.get('data', [])
        embedding_models = [m for m in models if 'embedding' in m.get('id', '').lower()]
        
        print(f"   ✅ Encontrados {len(embedding_models)} modelos de embedding:")
        for model in embedding_models[:5]:  # Mostrar primeros 5
            print(f"      • {model.get('id')}")
        
        if len(embedding_models) > 5:
            print(f"      ... y {len(embedding_models) - 5} más")
    else:
        print(f"   ⚠️  Error {response.status_code}: {response.text[:200]}")
except Exception as e:
    print(f"   ❌ Error: {e}")

print()

# 4. Intentar endpoint de organización
print("4️⃣  INTENTANDO: /v1/organizations")
print("-" * 80)
try:
    response = requests.get(
        "https://api.openai.com/v1/organizations",
        headers=headers,
        timeout=10
    )
    
    if response.status_code == 200:
        data = response.json()
        print("   ✅ Organizaciones encontradas:")
        if data.get('data'):
            for org in data['data']:
                print(f"      • {org.get('name', 'Sin nombre')} (ID: {org.get('id', 'N/A')})")
        else:
            print("      ⚠️  No se encontraron organizaciones")
    else:
        print(f"   ⚠️  Error {response.status_code}")
        if response.status_code == 401:
            print("      (Requiere permisos de organización)")
        else:
            print(f"      {response.text[:200]}")
except Exception as e:
    print(f"   ❌ Error: {e}")

print()

# 5. Resumen y recomendaciones
print("=" * 80)
print("📋 RESUMEN Y RECOMENDACIONES")
print("=" * 80)
print()

print("✅ MÉTODO MÁS CONFIABLE:")
print("   Los headers de rate limit en las respuestas de la API son la forma")
print("   más precisa de conocer tus límites reales:")
print()
print("   • x-ratelimit-limit-requests: Tu límite de RPM")
print("   • x-ratelimit-limit-tokens: Tu límite de TPM")
print()

print("📊 SOBRE TIER 2:")
print("   • Tier 2 significa: $50 pagados + 7+ días desde primer pago")
print("   • Límite de uso: $500/mes")
print("   • Los rate limits (RPM/TPM) varían por modelo y organización")
print("   • Tier 2 generalmente tiene límites más altos que Tier 1")
print()

print("💡 PARA VERIFICAR TUS LÍMITES EXACTOS:")
print("   1. Ve a: https://platform.openai.com/settings/organization/limits")
print("   2. Busca 'text-embedding-3-small'")
print("   3. Verifica RPM y TPM mostrados")
print("   4. O usa los headers de las respuestas de la API (método más preciso)")
print()

print("🔧 EL ENDPOINT DE FINE-TUNING:")
print("   • /v1/fine_tuning/model_limits muestra límites de fine-tuning")
print("   • NO muestra rate limits (RPM/TPM) para embeddings")
print("   • Útil solo si planeas hacer fine-tuning")
print()




