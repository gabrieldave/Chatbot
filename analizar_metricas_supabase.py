"""
📊 ANÁLISIS DE MÉTRICAS DE SUPABASE
===================================

Analiza CPU, IOPS y RAM para determinar si podemos aumentar batch_size
"""

import sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

print("=" * 80)
print("📊 ANÁLISIS DE MÉTRICAS DE SUPABASE")
print("=" * 80)

# Datos observados
cpu_total = 6.49
cpu_user = 4.97
cpu_system = 1.22
cpu_other = 0.20 + 0.08  # Other + IOwait

iops_max = 3000
iops_read = 0
iops_write = 1.31
iops_total = 1.31
iops_percent = 0.04

ram_total_gb = 3.74
ram_used_mb = 287.64
ram_used_gb = ram_used_mb / 1024
ram_free_gb = 1.97
ram_cache_gb = 1.49
ram_available_gb = ram_free_gb + ram_cache_gb  # Cache puede liberarse

print(f"\n📊 MÉTRICAS OBSERVADAS:")
print(f"\n💻 CPU:")
print(f"   Total: {cpu_total}%")
print(f"   • User: {cpu_user}%")
print(f"   • System: {cpu_system}%")
print(f"   • Otros: {cpu_other}%")
print(f"   Disponible: {100 - cpu_total:.1f}%")

print(f"\n💾 IOPS (Input/Output Operations Per Second):")
print(f"   Máximo: {iops_max}")
print(f"   Read: {iops_read} ({iops_read/iops_max*100:.2f}%)")
print(f"   Write: {iops_write} ({iops_write/iops_max*100:.2f}%)")
print(f"   Total: {iops_total} ({iops_percent}%)")
print(f"   Disponible: {iops_max - iops_total:.0f} IOPS ({100 - iops_percent:.2f}%)")

print(f"\n🧠 RAM:")
print(f"   Total: {ram_total_gb} GB")
print(f"   Usada: {ram_used_gb:.2f} GB ({ram_used_mb:.0f} MB)")
print(f"   Libre: {ram_free_gb} GB")
print(f"   Cache + Buffers: {ram_cache_gb} GB (puede liberarse)")
print(f"   Disponible: {ram_available_gb} GB")

# Análisis
print(f"\n" + "=" * 80)
print("🔍 ANÁLISIS")
print("=" * 80)

print(f"\n✅ CPU:")
if cpu_total < 20:
    print(f"   ✅ MUY BAJO - Solo usando {cpu_total}% de {100}%")
    print(f"   ✅ Hay {100 - cpu_total:.1f}% de capacidad disponible")
    print(f"   ✅ Podemos aumentar significativamente la carga")
    cpu_status = "excellent"
elif cpu_total < 50:
    print(f"   ⚠️  BAJO - Usando {cpu_total}%")
    print(f"   ✅ Hay espacio para aumentar")
    cpu_status = "good"
else:
    print(f"   ⚠️  MODERADO - Usando {cpu_total}%")
    cpu_status = "moderate"

print(f"\n✅ IOPS:")
if iops_percent < 1:
    print(f"   ✅ MUY BAJO - Solo usando {iops_percent}% de capacidad")
    print(f"   ✅ Hay {iops_max - iops_total:.0f} IOPS disponibles")
    print(f"   ✅ No hay cuello de botella en I/O")
    iops_status = "excellent"
elif iops_percent < 10:
    print(f"   ✅ BAJO - Usando {iops_percent}%")
    print(f"   ✅ Hay espacio para aumentar")
    iops_status = "good"
else:
    print(f"   ⚠️  MODERADO - Usando {iops_percent}%")
    iops_status = "moderate"

print(f"\n✅ RAM:")
ram_usage_percent = (ram_used_gb / ram_total_gb) * 100
if ram_usage_percent < 20:
    print(f"   ✅ MUY BAJO - Solo usando {ram_usage_percent:.1f}%")
    print(f"   ✅ Hay {ram_available_gb:.2f} GB disponibles")
    print(f"   ✅ Podemos aumentar significativamente el batch_size")
    ram_status = "excellent"
elif ram_usage_percent < 50:
    print(f"   ✅ BAJO - Usando {ram_usage_percent:.1f}%")
    print(f"   ✅ Hay espacio para aumentar")
    ram_status = "good"
else:
    print(f"   ⚠️  MODERADO - Usando {ram_usage_percent:.1f}%")
    ram_status = "moderate"

# Recomendación de batch_size
print(f"\n" + "=" * 80)
print("💡 RECOMENDACIÓN DE BATCH_SIZE")
print("=" * 80)

current_batch = 80
ram_per_file_mb = ram_used_mb / current_batch  # Asumiendo que el batch actual está usando esta RAM

print(f"\n📊 CÁLCULO:")
print(f"   batch_size actual: {current_batch}")
print(f"   RAM por archivo (estimado): {ram_per_file_mb:.1f} MB")

# Calcular batch_size óptimo basado en recursos disponibles
# Usar 70% de la RAM disponible de forma segura
safe_ram_gb = ram_available_gb * 0.70
safe_ram_mb = safe_ram_gb * 1024

# También considerar que podemos usar más si el CPU e IOPS están bajos
if cpu_status == "excellent" and iops_status == "excellent":
    # Si CPU e IOPS están muy bajos, podemos ser más agresivos
    safe_ram_mb = safe_ram_mb * 1.2  # 20% más agresivo

optimal_batch = int(safe_ram_mb / ram_per_file_mb)

# Límites razonables
optimal_batch = max(current_batch, min(optimal_batch, 150))  # Entre 80 y 150

print(f"\n💡 BATCH_SIZE ÓPTIMO:")
print(f"   RAM disponible segura (70%): {safe_ram_gb:.2f} GB = {safe_ram_mb:.0f} MB")
print(f"   Con {ram_per_file_mb:.1f} MB por archivo:")
print(f"   batch_size recomendado: {optimal_batch} archivos")

if optimal_batch > current_batch:
    increment = optimal_batch - current_batch
    print(f"\n✅ RECOMENDACIÓN: Aumentar batch_size de {current_batch} a {optimal_batch}")
    print(f"   Aumento: +{increment} archivos")
    print(f"\n📊 JUSTIFICACIÓN:")
    print(f"   • CPU: {cpu_total}% (muy bajo, hay {100-cpu_total:.1f}% disponible)")
    print(f"   • IOPS: {iops_percent}% (muy bajo, hay {iops_max-iops_total:.0f} IOPS disponibles)")
    print(f"   • RAM: {ram_usage_percent:.1f}% usado, {ram_available_gb:.2f} GB disponibles")
    print(f"   • Todos los recursos están muy por debajo de su capacidad")
    
    # Estimación de mejora
    current_speed = 1383.8  # archivos/hora (del análisis anterior)
    # Asumiendo que la velocidad aumenta proporcionalmente al batch_size
    # Pero con rendimientos decrecientes
    speed_improvement = 1 + (increment / current_batch) * 0.5  # 50% de eficiencia
    new_speed = current_speed * speed_improvement
    
    print(f"\n⚡ ESTIMACIÓN DE MEJORA:")
    print(f"   Velocidad actual: ~{current_speed:.0f} archivos/hora")
    print(f"   Velocidad estimada: ~{new_speed:.0f} archivos/hora")
    print(f"   Mejora: {speed_improvement:.2f}x más rápido")
    
elif optimal_batch == current_batch:
    print(f"\n✅ RECOMENDACIÓN: Mantener batch_size en {current_batch}")
    print(f"   El batch_size actual está bien optimizado")
    print(f"   Los recursos están siendo utilizados eficientemente")
else:
    print(f"\n⚠️  RECOMENDACIÓN: Reducir batch_size")
    print(f"   Aunque los recursos están disponibles, el batch_size actual puede ser óptimo")

print(f"\n" + "=" * 80)
print("🎯 CONCLUSIÓN")
print("=" * 80)

if cpu_status == "excellent" and iops_status == "excellent" and ram_status == "excellent":
    print(f"\n✅ TODOS LOS RECURSOS ESTÁN MUY BAJOS:")
    print(f"   • CPU: {cpu_total}% (puede manejar mucho más)")
    print(f"   • IOPS: {iops_percent}% (puede manejar mucho más)")
    print(f"   • RAM: {ram_usage_percent:.1f}% (puede manejar mucho más)")
    print(f"\n💡 CONCLUSIÓN: SÍ, podemos aumentar el batch_size significativamente")
    print(f"   Recomendación: Aumentar a {optimal_batch} archivos")
    print(f"   Esto aprovechará mejor los recursos disponibles")
else:
    print(f"\n⚠️  Algunos recursos están en niveles moderados")
    print(f"   Recomendación: Aumentar gradualmente y monitorear")

print("\n" + "=" * 80)




