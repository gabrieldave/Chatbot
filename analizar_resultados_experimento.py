"""
🔬 ANÁLISIS DETALLADO DEL EXPERIMENTO
======================================

Analiza los resultados del experimento de aumento de RAM
"""

import sys

# Configurar encoding para Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

print("=" * 80)
print("🔬 ANÁLISIS DETALLADO DEL EXPERIMENTO")
print("=" * 80)

# Datos del experimento
batch_size_constant = 15
ram_before = 2.0
ram_used_before = 1.8
ram_now = 5.59  # Parece que aumentó a más de 4 GB (tal vez 6 GB?)
ram_used_now = 3.74

print(f"\n📊 DATOS DEL EXPERIMENTO:")
print(f"   batch_size (constante): {batch_size_constant}")
print(f"   RAM antes: {ram_before} GB → Uso: {ram_used_before} GB ({ram_used_before/ram_before*100:.1f}%)")
print(f"   RAM ahora: {ram_now} GB → Uso: {ram_used_now} GB ({ram_used_now/ram_now*100:.1f}%)")

# Análisis de proporcionalidad
expected_proportional = ram_used_before * (ram_now / ram_before)  # 1.8 * (5.59/2) = ~5.03 GB
actual_increase = ram_used_now - ram_used_before  # 3.74 - 1.8 = 1.94 GB
proportional_increase = expected_proportional - ram_used_before  # 5.03 - 1.8 = 3.23 GB

print(f"\n📈 ANÁLISIS DE PROPORCIONALIDAD:")
print(f"   Si fuera proporcional (90%): {expected_proportional:.2f} GB")
print(f"   Uso observado: {ram_used_now:.2f} GB")
print(f"   Diferencia: {abs(ram_used_now - expected_proportional):.2f} GB")
print(f"\n   Aumento esperado (proporcional): +{proportional_increase:.2f} GB")
print(f"   Aumento observado: +{actual_increase:.2f} GB")
print(f"   Ratio de aumento: {actual_increase/proportional_increase*100:.1f}% del esperado")

# Análisis de ratios
ratio_before = ram_used_before / ram_before  # 0.90 (90%)
ratio_now = ram_used_now / ram_now  # 0.67 (67%)

print(f"\n🔍 ANÁLISIS DE RATIOS:")
print(f"   Ratio antes: {ratio_before:.2f} ({ratio_before*100:.1f}%)")
print(f"   Ratio ahora: {ratio_now:.2f} ({ratio_now*100:.1f}%)")
print(f"   Cambio en ratio: {ratio_now - ratio_before:.2f} ({((ratio_now/ratio_before)-1)*100:.1f}% relativo)")

# Factor de RAM por archivo
ram_per_file_before = ram_used_before / batch_size_constant  # 1.8 / 15 = 0.12 GB
ram_per_file_now = ram_used_now / batch_size_constant  # 3.74 / 15 = 0.249 GB

print(f"\n💾 FACTOR DE RAM POR ARCHIVO:")
print(f"   Con 2 GB RAM: {ram_per_file_before:.3f} GB/archivo = {ram_per_file_before*1024:.1f} MB/archivo")
print(f"   Con {ram_now} GB RAM: {ram_per_file_now:.3f} GB/archivo = {ram_per_file_now*1024:.1f} MB/archivo")
print(f"   Aumento: {((ram_per_file_now/ram_per_file_before)-1)*100:.1f}% más RAM por archivo")

# Conclusiones
print(f"\n" + "=" * 80)
print(f"🎯 CONCLUSIONES")
print("=" * 80)

if actual_increase >= proportional_increase * 0.8:  # Al menos 80% del aumento esperado
    print(f"\n✅ CONCLUSIÓN PRINCIPAL:")
    print(f"   El uso de RAM SÍ aumentó significativamente (+{actual_increase:.2f} GB)")
    print(f"   Esto indica que el proceso está usando más RAM cuando hay más disponible")
    print(f"   El margen de seguridad probablemente ES REAL")
    print(f"\n💡 INTERPRETACIÓN:")
    print(f"   • Con más RAM disponible, el proceso puede usar más memoria")
    print(f"   • El ratio bajó de 90% a 67% porque hay más RAM total")
    print(f"   • Pero el uso absoluto aumentó, confirmando que había límite antes")
    print(f"   • Supabase probablemente SÍ retiene ~10% por seguridad")
    
    margin_is_real = True
    
elif actual_increase <= ram_used_before * 0.2:  # Aumento menor al 20%
    print(f"\n✅ CONCLUSIÓN PRINCIPAL:")
    print(f"   El uso de RAM se mantuvo similar (+{actual_increase:.2f} GB)")
    print(f"   Esto indica que NO había límite real antes")
    print(f"   El margen de seguridad NO era restrictivo")
    print(f"\n💡 INTERPRETACIÓN:")
    print(f"   • El proceso solo necesita ~{ram_used_before:.2f} GB")
    print(f"   • Con 2 GB tenía espacio suficiente")
    print(f"   • Podemos ser más agresivos con el batch_size")
    
    margin_is_real = False
    
else:
    print(f"\n✅ CONCLUSIÓN PRINCIPAL:")
    print(f"   Resultado intermedio: uso aumentó pero no proporcionalmente")
    print(f"   Aumento observado: +{actual_increase:.2f} GB")
    print(f"   Aumento esperado (proporcional): +{proportional_increase:.2f} GB")
    print(f"\n💡 INTERPRETACIÓN:")
    print(f"   • El proceso está usando más RAM ({ram_used_now:.2f} GB vs {ram_used_before:.2f} GB)")
    print(f"   • Pero no está usando todo lo disponible (solo {ratio_now*100:.1f}% vs {ratio_before*100:.1f}% antes)")
    print(f"   • Esto sugiere que:")
    print(f"     - El margen de seguridad puede ser real")
    print(f"     - Pero el proceso puede optimizarse mejor")
    print(f"     - Hay espacio para aumentar el batch_size")
    
    margin_is_real = "partial"

# Calcular batch_size óptimo
print(f"\n" + "=" * 80)
print(f"💡 CÁLCULO DE BATCH_SIZE ÓPTIMO")
print("=" * 80)

if margin_is_real == True:
    # Margen real: usar 85% del RAM efectivamente disponible
    margin_gb = ram_now * 0.10
    effective_ram = ram_now - margin_gb
    safe_ram = effective_ram * 0.85
    
    print(f"\n🔒 Estrategia (Margen Real Confirmado):")
    print(f"   Margen de seguridad: {margin_gb:.2f} GB (10%)")
    print(f"   RAM efectiva: {effective_ram:.2f} GB")
    print(f"   RAM segura (85%): {safe_ram:.2f} GB")
    
    optimal_batch = int(safe_ram / ram_per_file_now)
    
elif margin_is_real == False:
    # Margen no real: podemos usar más
    safe_ram = ram_used_now * 1.5
    
    print(f"\n🚀 Estrategia (Margen NO Real):")
    print(f"   Uso actual: {ram_used_now:.2f} GB")
    print(f"   RAM segura (150% del uso): {safe_ram:.2f} GB")
    
    optimal_batch = int(safe_ram / ram_per_file_now)
    
else:
    # Resultado intermedio: usar 75% del total
    safe_ram = ram_now * 0.75
    
    print(f"\n⚠️  Estrategia (Resultado Intermedio):")
    print(f"   RAM segura (75% del total): {safe_ram:.2f} GB")
    
    optimal_batch = int(safe_ram / ram_per_file_now)

# Limitar a rangos razonables
optimal_batch = max(15, min(optimal_batch, 100))

print(f"\n📦 RESULTADO:")
print(f"   batch_size óptimo: {optimal_batch} archivos")
print(f"   batch_size actual: {batch_size_constant}")

if optimal_batch > batch_size_constant:
    increment = optimal_batch - batch_size_constant
    print(f"   ✅ Aumento recomendado: +{increment} archivos")
    print(f"\n💡 RECOMENDACIÓN:")
    print(f"   Podemos aumentar el batch_size de {batch_size_constant} a {optimal_batch}")
    print(f"   Esto aprovechará mejor los {ram_now} GB de RAM disponibles")
elif optimal_batch < batch_size_constant:
    print(f"   ⚠️  El batch_size actual es adecuado")
else:
    print(f"   ✅ Mantener batch_size actual")

# Estimación de velocidad
print(f"\n⚡ ESTIMACIÓN DE RENDIMIENTO:")
time_per_batch = 2 + (optimal_batch / 10)
files_per_hour = (optimal_batch * 60) / time_per_batch

print(f"   Con batch_size={optimal_batch}:")
print(f"   • Tiempo por lote: ~{time_per_batch:.1f} minutos")
print(f"   • Velocidad: ~{files_per_hour:.0f} archivos/hora")

current_time_per_batch = 2 + (batch_size_constant / 10)
current_files_per_hour = (batch_size_constant * 60) / current_time_per_batch
speedup = files_per_hour / current_files_per_hour

print(f"\n   Comparación con batch_size={batch_size_constant}:")
print(f"   • Velocidad actual: ~{current_files_per_hour:.0f} archivos/hora")
print(f"   • Mejora estimada: {speedup:.2f}x más rápido")

print("\n" + "=" * 80)




