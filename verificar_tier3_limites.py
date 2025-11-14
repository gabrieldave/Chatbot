"""
🔍 VERIFICACIÓN DE LÍMITES TIER 3
==================================

Verifica los límites reales de OpenAI para Tier 3
y calcula el batch_size óptimo
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
print("🔍 VERIFICACIÓN DE LÍMITES TIER 3")
print("=" * 80)
print()

# Hacer llamada real y ver headers
print("📡 HACIENDO LLAMADA A OPENAI PARA VERIFICAR LÍMITES...")
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
    
    # Extraer headers de rate limit
    rate_limit_info = {}
    for key, value in response.headers.items():
        if 'ratelimit' in key.lower():
            rate_limit_info[key] = value
    
    if rate_limit_info:
        print("\n✅ HEADERS DE RATE LIMIT ENCONTRADOS:")
        for key, value in sorted(rate_limit_info.items()):
            print(f"   • {key}: {value}")
    
    # Analizar límites
    rpm_limit = None
    tpm_limit = None
    
    for key, value in rate_limit_info.items():
        if 'limit-requests' in key.lower():
            rpm_limit = int(value)
        elif 'limit-tokens' in key.lower():
            tpm_limit = int(value)
    
    print("\n" + "=" * 80)
    print("📊 ANÁLISIS DE LÍMITES")
    print("=" * 80)
    print()
    
    if rpm_limit:
        print(f"✅ RPM (Requests Per Minute): {rpm_limit:,}")
    else:
        print("⚠️  RPM: No detectado en headers")
        rpm_limit = 5000  # Asumir Tier 3
    
    if tpm_limit:
        print(f"✅ TPM (Tokens Per Minute): {tpm_limit:,}")
        # Verificar si es Tier 3 (5M TPM)
        if tpm_limit >= 5000000:
            print("   🎯 ¡Confirmado Tier 3! (5M+ TPM)")
        elif tpm_limit >= 1000000:
            print("   📊 Tier 2 detectado (1M+ TPM)")
        else:
            print("   📊 Tier 1 o inferior")
    else:
        print("⚠️  TPM: No detectado en headers")
        tpm_limit = 5000000  # Asumir Tier 3
    
    print()
    print("=" * 80)
    print("💡 CÁLCULO DE BATCH_SIZE ÓPTIMO")
    print("=" * 80)
    print()
    
    # Cálculos para Tier 3
    print("📐 PARÁMETROS:")
    print(f"   • RPM límite: {rpm_limit:,}")
    print(f"   • TPM límite: {tpm_limit:,}")
    print(f"   • TPD límite: 100,000,000 (Tier 3)")
    print()
    
    # Asumir promedio de tokens por archivo
    # Un libro promedio puede tener 50,000-200,000 tokens
    # Para chunks pequeños (512 tokens cada uno), un archivo puede generar ~100-400 chunks
    # Cada chunk = 1 request a embeddings
    
    avg_tokens_per_file = 50000  # Conservador
    avg_chunks_per_file = 100    # ~100 requests por archivo promedio
    
    print("📊 ESTIMACIONES POR ARCHIVO:")
    print(f"   • Tokens promedio: ~{avg_tokens_per_file:,}")
    print(f"   • Chunks promedio: ~{avg_chunks_per_file}")
    print(f"   • Requests promedio: ~{avg_chunks_per_file}")
    print()
    
    # Calcular batch_size óptimo
    # Usar 80% del límite para seguridad
    rpm_target = int(rpm_limit * 0.8)
    tpm_target = int(tpm_limit * 0.8)
    
    print(f"🎯 OBJETIVO (80% de capacidad):")
    print(f"   • RPM objetivo: {rpm_target:,}")
    print(f"   • TPM objetivo: {tpm_target:,}")
    print()
    
    # Batch size basado en RPM
    batch_size_rpm = rpm_target // avg_chunks_per_file
    # Batch size basado en TPM
    batch_size_tpm = tpm_target // avg_tokens_per_file
    
    # Tomar el menor para respetar ambos límites
    batch_size_optimal = min(batch_size_rpm, batch_size_tpm)
    
    # Ajustar al rango recomendado (32-64)
    if batch_size_optimal < 32:
        batch_size_optimal = 32
    elif batch_size_optimal > 64:
        batch_size_optimal = 64
    
    print(f"📦 BATCH_SIZE ÓPTIMO:")
    print(f"   • Basado en RPM: {batch_size_rpm}")
    print(f"   • Basado en TPM: {batch_size_tpm}")
    print(f"   • Óptimo final: {batch_size_optimal} (rango recomendado: 32-64)")
    print()
    
    # Calcular capacidad con batch actual (38)
    batch_current = 38
    requests_current = batch_current * avg_chunks_per_file
    tokens_current = batch_current * avg_tokens_per_file
    
    print(f"📊 ANÁLISIS CON BATCH ACTUAL ({batch_current}):")
    print(f"   • Requests por batch: ~{requests_current:,}")
    print(f"   • Tokens por batch: ~{tokens_current:,}")
    print(f"   • % de RPM límite: {(requests_current/rpm_limit)*100:.2f}%")
    print(f"   • % de TPM límite: {(tokens_current/tpm_limit)*100:.2f}%")
    print()
    
    if requests_current < rpm_target * 0.5:
        print("   ⚠️  Estás usando menos del 50% de tu capacidad RPM")
        print("   💡 Puedes aumentar el batch_size significativamente")
    elif requests_current < rpm_target:
        print("   ✅ Estás dentro del rango óptimo")
    else:
        print("   ⚠️  Estás cerca del límite, considera reducir")
    
    print()
    print("=" * 80)
    print("🚀 RECOMENDACIONES")
    print("=" * 80)
    print()
    print(f"✅ Batch size recomendado: {batch_size_optimal}")
    print(f"✅ Puedes procesar en paralelo: hasta 10 workers")
    print(f"✅ Con {batch_size_optimal} archivos/batch:")
    print(f"   • Requests: ~{batch_size_optimal * avg_chunks_per_file:,} por batch")
    print(f"   • Tokens: ~{batch_size_optimal * avg_tokens_per_file:,} por batch")
    print(f"   • Velocidad: ~{batch_size_optimal * 60 / 2:.0f} archivos/hora (estimado)")
    print()
    print("💡 VENTAJAS DE TIER 3:")
    print("   • Límites muy altos (5M TPM, 5K RPM)")
    print("   • Puedes procesar cientos de libros sin problemas")
    print("   • Procesamiento paralelo seguro")
    print("   • No necesitas preocuparte por límites diarios")
    print()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("=" * 80)



