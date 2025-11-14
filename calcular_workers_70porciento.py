"""
📊 CALCULAR WORKERS ÓPTIMOS AL 70% DE CAPACIDAD TIER 3
=======================================================
"""

import sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Límites Tier 3
TIER3_RPM_LIMIT = 5000
TIER3_TPM_LIMIT = 5000000

# Objetivo: 70% de capacidad
RPM_TARGET = int(TIER3_RPM_LIMIT * 0.7)  # 3,500 RPM
TPM_TARGET = int(TIER3_TPM_LIMIT * 0.7)  # 3,500,000 TPM

print("=" * 80)
print("📊 CÁLCULO DE WORKERS AL 70% DE CAPACIDAD TIER 3")
print("=" * 80)
print()

print(f"🎯 OBJETIVO (70% de capacidad):")
print(f"   • RPM objetivo: {RPM_TARGET:,} (70% de {TIER3_RPM_LIMIT:,})")
print(f"   • TPM objetivo: {TPM_TARGET:,} (70% de {TIER3_TPM_LIMIT:,})")
print()

# Estimaciones por archivo
avg_requests_per_file = 100  # ~100 chunks/requests por archivo promedio
avg_tokens_per_file = 50000  # ~50,000 tokens por archivo promedio

print(f"📐 ESTIMACIONES POR ARCHIVO:")
print(f"   • Requests promedio: ~{avg_requests_per_file}")
print(f"   • Tokens promedio: ~{avg_tokens_per_file:,}")
print()

# Calcular workers basado en RPM
# Si cada worker procesa 1 archivo a la vez y genera ~100 requests
# RPM por worker = requests por archivo / tiempo por archivo
# Asumiendo ~2-3 segundos por archivo (con embeddings)
time_per_file_seconds = 2.5  # Conservador
requests_per_second_per_worker = avg_requests_per_file / time_per_file_seconds

# Workers basados en RPM
max_workers_rpm = int(RPM_TARGET / (requests_per_second_per_worker * 60))

# Workers basados en TPM
tokens_per_second_per_worker = avg_tokens_per_file / time_per_file_seconds
max_workers_tpm = int(TPM_TARGET / (tokens_per_second_per_worker * 60))

# Tomar el menor para respetar ambos límites
optimal_workers = min(max_workers_rpm, max_workers_tpm)

# Ajustar al rango práctico (5-20 workers)
optimal_workers = max(5, min(optimal_workers, 20))

print(f"📈 CÁLCULOS:")
print(f"   • Requests/segundo por worker: ~{requests_per_second_per_worker:.1f}")
print(f"   • Tokens/segundo por worker: ~{tokens_per_second_per_worker:.0f}")
print()
print(f"   • Workers basados en RPM: {max_workers_rpm}")
print(f"   • Workers basados en TPM: {max_workers_tpm}")
print()
print(f"✅ WORKERS ÓPTIMOS AL 70%: {optimal_workers}")
print()

# Calcular capacidad real con este número de workers
total_requests_per_minute = optimal_workers * requests_per_second_per_worker * 60
total_tokens_per_minute = optimal_workers * tokens_per_second_per_worker * 60

print(f"📊 CAPACIDAD CON {optimal_workers} WORKERS:")
print(f"   • Requests/minuto: ~{total_requests_per_minute:.0f} ({total_requests_per_minute/RPM_TARGET*100:.1f}% del objetivo)")
print(f"   • Tokens/minuto: ~{total_tokens_per_minute:,.0f} ({total_tokens_per_minute/TPM_TARGET*100:.1f}% del objetivo)")
print()

# Velocidad estimada
files_per_minute = optimal_workers * (60 / time_per_file_seconds)
print(f"⚡ VELOCIDAD ESTIMADA:")
print(f"   • Archivos/minuto: ~{files_per_minute:.0f}")
print(f"   • Archivos/hora: ~{files_per_minute * 60:.0f}")
print()

print("=" * 80)
print(f"💡 RECOMENDACIÓN: Usar {optimal_workers} workers para aprovechar 70% de Tier 3")
print("=" * 80)

