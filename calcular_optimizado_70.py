"""
📊 CÁLCULO OPTIMIZADO AL 70% DE CAPACIDAD TIER 3
==================================================
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
print("📊 CÁLCULO OPTIMIZADO AL 70% DE CAPACIDAD TIER 3")
print("=" * 80)
print()

print(f"🎯 OBJETIVO (70% de capacidad):")
print(f"   • RPM objetivo: {RPM_TARGET:,} (70% de {TIER3_RPM_LIMIT:,})")
print(f"   • TPM objetivo: {TPM_TARGET:,} (70% de {TIER3_TPM_LIMIT:,})")
print()

# Parámetros reales
avg_requests_per_file = 100  # ~100 chunks/requests por archivo
avg_tokens_per_file = 50000  # ~50,000 tokens por archivo
time_per_batch_minutes = 2.0  # ~2 minutos por batch (conservador)

print(f"📐 PARÁMETROS:")
print(f"   • Requests por archivo: ~{avg_requests_per_file}")
print(f"   • Tokens por archivo: ~{avg_tokens_per_file:,}")
print(f"   • Tiempo por batch: ~{time_per_batch_minutes} minutos")
print()

# Calcular diferentes configuraciones
configs = []

# Probar diferentes combinaciones de batch_size y workers
for batch_size in [20, 30, 38, 50]:
    for workers in [5, 7, 10, 15, 20]:
        requests_per_batch = batch_size * avg_requests_per_file
        tokens_per_batch = batch_size * avg_tokens_per_file
        
        # Con workers paralelos, procesamos múltiples batches simultáneamente
        # Pero cada batch tarda ~2 minutos, así que en 1 minuto procesamos workers/2 batches
        batches_per_minute = workers / time_per_batch_minutes
        total_rpm = batches_per_minute * requests_per_batch
        total_tpm = batches_per_minute * tokens_per_batch
        
        # Verificar si está dentro del 70% (con margen del 5%)
        rpm_usage = (total_rpm / RPM_TARGET) * 100
        tpm_usage = (total_tpm / TPM_TARGET) * 100
        
        if rpm_usage <= 75 and tpm_usage <= 75:  # 70% + 5% margen
            files_per_minute = batches_per_minute * batch_size
            configs.append({
                'workers': workers,
                'batch_size': batch_size,
                'rpm': total_rpm,
                'tpm': total_tpm,
                'rpm_usage': rpm_usage,
                'tpm_usage': tpm_usage,
                'files_per_min': files_per_minute
            })

# Ordenar por velocidad (files_per_min)
configs.sort(key=lambda x: x['files_per_min'], reverse=True)

print("✅ CONFIGURACIONES ÓPTIMAS (dentro del 70%):")
print()
print(f"{'Workers':<10} {'Batch':<10} {'RPM':<12} {'TPM':<15} {'% RPM':<10} {'% TPM':<10} {'Arch/min':<10}")
print("-" * 80)

for config in configs[:10]:  # Top 10
    print(f"{config['workers']:<10} {config['batch_size']:<10} "
          f"{config['rpm']:>10,.0f}  {config['tpm']:>12,.0f}  "
          f"{config['rpm_usage']:>6.1f}%  {config['tpm_usage']:>6.1f}%  "
          f"{config['files_per_min']:>8.1f}")

print()
print("=" * 80)

# Recomendación
if configs:
    best = configs[0]
    print(f"💡 RECOMENDACIÓN ÓPTIMA:")
    print(f"   • Workers: {best['workers']}")
    print(f"   • Batch size: {best['batch_size']}")
    print(f"   • Velocidad: ~{best['files_per_min']:.0f} archivos/minuto")
    print(f"   • Uso de capacidad: {best['rpm_usage']:.1f}% RPM, {best['tpm_usage']:.1f}% TPM")
    print()
    print("=" * 80)



