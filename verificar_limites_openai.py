"""
🔍 VERIFICAR LÍMITES REALES DE OPENAI TIER 2
=============================================

Verifica los límites reales de OpenAI desde la API o documentación
"""

import os
import sys
import requests
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

print("=" * 80)
print("🔍 VERIFICACIÓN DE LÍMITES DE OPENAI TIER 2")
print("=" * 80)
print()

if not OPENAI_API_KEY:
    print("❌ Error: OPENAI_API_KEY no está configurada")
    print()
    print("💡 Para verificar tus límites reales:")
    print("   1. Ve a: https://platform.openai.com/settings/organization/limits")
    print("   2. Busca los límites para 'text-embedding-3-small'")
    print("   3. Verifica el RPM (Requests Per Minute) de tu Tier 2")
    sys.exit(1)

print("📋 INFORMACIÓN SOBRE LÍMITES DE OPENAI")
print()
print("⚠️  IMPORTANTE: Los límites exactos de Tier 2 varían según:")
print("   • Tu plan de OpenAI")
print("   • Tu historial de uso")
print("   • Tu organización específica")
print()
print("📊 LÍMITES TÍPICOS SEGÚN DOCUMENTACIÓN:")
print()
print("1️⃣  TIER 1 (Básico/Pay-as-you-go):")
print("   • RPM: 3,500 - 10,000 (varía por modelo)")
print("   • TPM: 1,000,000 - 10,000,000")
print()
print("2️⃣  TIER 2 (Scale/Enterprise):")
print("   • RPM: 10,000 - 20,000+ (varía por modelo)")
print("   • TPM: 10,000,000+")
print()
print("3️⃣  TIER 3 (Enterprise Plus):")
print("   • RPM: Personalizado (muy alto)")
print("   • TPM: Personalizado (muy alto)")
print()
print("=" * 80)
print("🔍 INTENTANDO VERIFICAR LÍMITES DESDE API")
print("=" * 80)
print()

# Intentar obtener información de la organización
try:
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Intentar obtener información de la organización
    print("📡 Intentando obtener información de la organización...")
    org_response = requests.get(
        "https://api.openai.com/v1/organizations",
        headers=headers,
        timeout=10
    )
    
    if org_response.status_code == 200:
        orgs = org_response.json()
        if orgs.get('data'):
            print(f"   ✅ Organizaciones encontradas: {len(orgs['data'])}")
            for org in orgs['data']:
                print(f"      • {org.get('name', 'Sin nombre')} (ID: {org.get('id', 'N/A')})")
        else:
            print("   ⚠️  No se encontraron organizaciones")
    else:
        print(f"   ⚠️  No se pudo obtener organizaciones: {org_response.status_code}")
        print(f"      {org_response.text[:200]}")
    
    print()
    
    # Intentar hacer una llamada de prueba para ver headers de rate limit
    print("📡 Haciendo llamada de prueba para ver headers de rate limit...")
    test_response = requests.post(
        "https://api.openai.com/v1/embeddings",
        headers=headers,
        json={
            "model": "text-embedding-3-small",
            "input": "test"
        },
        timeout=10
    )
    
    # Los headers de rate limit suelen estar en las respuestas
    rate_limit_headers = {
        'x-ratelimit-limit-requests': test_response.headers.get('x-ratelimit-limit-requests'),
        'x-ratelimit-limit-tokens': test_response.headers.get('x-ratelimit-limit-tokens'),
        'x-ratelimit-remaining-requests': test_response.headers.get('x-ratelimit-remaining-requests'),
        'x-ratelimit-remaining-tokens': test_response.headers.get('x-ratelimit-remaining-tokens'),
        'x-ratelimit-reset-requests': test_response.headers.get('x-ratelimit-reset-requests'),
        'x-ratelimit-reset-tokens': test_response.headers.get('x-ratelimit-reset-tokens'),
    }
    
    if any(rate_limit_headers.values()):
        print("   ✅ Headers de rate limit encontrados:")
        for key, value in rate_limit_headers.items():
            if value:
                print(f"      • {key}: {value}")
    else:
        print("   ⚠️  No se encontraron headers de rate limit en la respuesta")
        print(f"      Status code: {test_response.status_code}")
        if test_response.status_code == 200:
            print("      ✅ La llamada fue exitosa, pero no hay headers de rate limit")
    
    print()
    
except Exception as e:
    print(f"   ⚠️  Error al verificar límites: {e}")
    print()

print("=" * 80)
print("📋 CÓMO VERIFICAR TUS LÍMITES REALES")
print("=" * 80)
print()
print("1️⃣  MÉTODO RECOMENDADO - Panel de OpenAI:")
print("   • Ve a: https://platform.openai.com/settings/organization/limits")
print("   • Busca la sección de 'Rate Limits'")
print("   • Encuentra 'text-embedding-3-small'")
print("   • Verifica el valor de 'Requests per minute (RPM)'")
print()
print("2️⃣  MÉTODO ALTERNATIVO - Headers de respuesta:")
print("   • Haz una llamada a la API de embeddings")
print("   • Revisa los headers de respuesta:")
print("     - x-ratelimit-limit-requests: Límite de RPM")
print("     - x-ratelimit-remaining-requests: RPM restantes")
print()
print("3️⃣  MÉTODO MANUAL - Documentación:")
print("   • Revisa: https://platform.openai.com/docs/guides/rate-limits")
print("   • Los límites pueden variar según tu cuenta específica")
print()
print("=" * 80)
print("💡 RECOMENDACIÓN")
print("=" * 80)
print()
print("Para obtener los límites EXACTOS de tu cuenta Tier 2:")
print("   1. Ve a: https://platform.openai.com/settings/organization/limits")
print("   2. Busca 'text-embedding-3-small'")
print("   3. Anota el RPM máximo")
print("   4. Ejecuta: python calcular_batch_tier2.py --rpm <TU_RPM>")
print()
print("O modifica manualmente el script calcular_batch_tier2.py")
print("   cambiando la línea:")
print("   rpm_limit_tier2 = 10000  # Cambia este valor por tu RPM real")
print()




