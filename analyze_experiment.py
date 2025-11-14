"""
🔬 ANALIZADOR DEL EXPERIMENTO
==============================

Analiza los resultados del experimento de aumento de RAM
"""

import sys

# Configurar encoding para Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def analyze_experiment(ram_total_gb, ram_used_gb):
    """
    Analiza el experimento de aumento de RAM
    
    Args:
        ram_total_gb: RAM total actual (4 GB)
        ram_used_gb: RAM usada actualmente
    """
    print("=" * 80)
    print("🔬 ANÁLISIS DEL EXPERIMENTO")
    print("=" * 80)
    
    # Datos del experimento
    batch_size_constant = 15  # Variable de control
    ram_before = 2.0  # RAM antes del experimento
    ram_used_before = 1.8  # Uso observado con 2 GB
    
    print(f"\n📊 DATOS DEL EXPERIMENTO:")
    print(f"   batch_size (constante): {batch_size_constant}")
    print(f"   RAM antes: {ram_before} GB → Uso: {ram_used_before} GB (90%)")
    print(f"   RAM ahora: {ram_total_gb} GB → Uso: {ram_used_gb} GB")
    
    # Calcular ratios
    usage_percent = (ram_used_gb / ram_total_gb) * 100
    ratio_before = ram_used_before / ram_before
    ratio_now = ram_used_gb / ram_total_gb
    
    print(f"\n📈 RATIOS:")
    print(f"   Ratio antes: {ram_used_before}/{ram_before} = {ratio_before:.2f} ({ratio_before*100:.1f}%)")
    print(f"   Ratio ahora: {ram_used_gb}/{ram_total_gb} = {ratio_now:.2f} ({ratio_now*100:.1f}%)")
    
    # Análisis de la hipótesis
    print(f"\n🔬 ANÁLISIS DE LA HIPÓTESIS:")
    
    # Si el uso subió proporcionalmente
    expected_usage_proportional = ram_used_before * (ram_total_gb / ram_before)  # 1.8 * 2 = 3.6 GB
    difference = abs(ram_used_gb - expected_usage_proportional)
    
    if difference <= 0.2:  # Dentro de 200 MB del esperado
        print(f"   ✅ CONFIRMADO: Uso subió proporcionalmente")
        print(f"      Esperado: ~{expected_usage_proportional:.2f} GB")
        print(f"      Observado: {ram_used_gb:.2f} GB")
        print(f"      Diferencia: {difference:.2f} GB (dentro del margen)")
        print(f"\n   🎯 CONCLUSIÓN:")
        print(f"      ✅ El margen de seguridad ES REAL")
        print(f"      ✅ Supabase está reteniendo ~10% de RAM intencionalmente")
        print(f"      ✅ Debemos respetar el margen y cuidar el batch_size")
        
        margin_is_real = True
        
    elif ram_used_gb <= ram_used_before * 1.1:  # Se mantuvo similar (dentro del 10%)
        print(f"   ✅ CONFIRMADO: Uso se mantuvo similar")
        print(f"      Antes: {ram_used_before:.2f} GB")
        print(f"      Ahora: {ram_used_gb:.2f} GB")
        print(f"      Diferencia: {ram_used_gb - ram_used_before:.2f} GB")
        print(f"\n   🎯 CONCLUSIÓN:")
        print(f"      ✅ El margen NO era real")
        print(f"      ✅ Había más capacidad disponible")
        print(f"      ✅ Podemos ser más agresivos con el batch_size")
        
        margin_is_real = False
        
    else:
        print(f"   ⚠️  Resultado intermedio")
        print(f"      Esperado proporcional: ~{expected_usage_proportional:.2f} GB")
        print(f"      Observado: {ram_used_gb:.2f} GB")
        print(f"      Diferencia: {difference:.2f} GB")
        print(f"\n   🎯 CONCLUSIÓN:")
        print(f"      ⚠️  Necesitamos más observación")
        print(f"      💡 El uso cambió pero no proporcionalmente")
        
        margin_is_real = None
    
    # Calcular batch_size óptimo según resultado
    print(f"\n" + "=" * 80)
    print(f"💡 CÁLCULO DE BATCH_SIZE ÓPTIMO")
    print("=" * 80)
    
    # Factor: cuánta RAM por archivo
    ram_per_file = ram_used_gb / batch_size_constant
    print(f"\n📊 Factor de uso:")
    print(f"   Con batch_size={batch_size_constant}: {ram_used_gb:.2f} GB usados")
    print(f"   RAM por archivo: {ram_per_file:.3f} GB = {ram_per_file*1024:.1f} MB")
    
    if margin_is_real:
        # Margen real: usar 85% del RAM efectivamente disponible
        margin_gb = ram_total_gb * 0.10
        effective_ram = ram_total_gb - margin_gb
        safe_ram = effective_ram * 0.85
        
        print(f"\n🔒 Estrategia (Margen Real):")
        print(f"   Margen de seguridad: {margin_gb:.2f} GB (10%)")
        print(f"   RAM efectiva: {effective_ram:.2f} GB")
        print(f"   RAM segura (85%): {safe_ram:.2f} GB")
        
        optimal_batch = int(safe_ram / ram_per_file)
        
    elif margin_is_real == False:
        # Margen no real: podemos usar más
        safe_ram = ram_used_gb * 1.5  # 50% más que el uso actual
        
        print(f"\n🚀 Estrategia (Margen NO Real):")
        print(f"   Uso actual: {ram_used_gb:.2f} GB")
        print(f"   RAM segura (150% del uso): {safe_ram:.2f} GB")
        
        optimal_batch = int(safe_ram / ram_per_file)
        
    else:
        # Zona intermedia: ser conservador
        safe_ram = ram_total_gb * 0.75  # 75% del total
        
        print(f"\n⚠️  Estrategia (Zona Intermedia):")
        print(f"   RAM segura (75% del total): {safe_ram:.2f} GB")
        
        optimal_batch = int(safe_ram / ram_per_file)
    
    # Limitar a rangos razonables
    optimal_batch = max(15, min(optimal_batch, 100))
    
    print(f"\n📦 RESULTADO:")
    print(f"   batch_size óptimo: {optimal_batch} archivos")
    print(f"   batch_size actual: {batch_size_constant}")
    
    if optimal_batch > batch_size_constant:
        increment = optimal_batch - batch_size_constant
        print(f"   ✅ Aumento recomendado: +{increment} archivos")
    elif optimal_batch < batch_size_constant:
        print(f"   ⚠️  Reducción recomendada (aunque el actual funciona)")
    else:
        print(f"   ✅ Mantener batch_size actual")
    
    # Estimación de velocidad
    print(f"\n⚡ ESTIMACIÓN DE RENDIMIENTO:")
    time_per_batch = 2 + (optimal_batch / 10)  # minutos
    files_per_hour = (optimal_batch * 60) / time_per_batch
    
    print(f"   Con batch_size={optimal_batch}:")
    print(f"   • Tiempo por lote: ~{time_per_batch:.1f} minutos")
    print(f"   • Velocidad: ~{files_per_hour:.0f} archivos/hora")
    
    # Comparación
    current_time_per_batch = 2 + (batch_size_constant / 10)
    current_files_per_hour = (batch_size_constant * 60) / current_time_per_batch
    speedup = files_per_hour / current_files_per_hour
    
    print(f"\n   Comparación con batch_size={batch_size_constant}:")
    print(f"   • Velocidad actual: ~{current_files_per_hour:.0f} archivos/hora")
    print(f"   • Mejora estimada: {speedup:.2f}x más rápido")
    
    print("\n" + "=" * 80)
    
    return optimal_batch, margin_is_real

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        try:
            ram_total = float(sys.argv[1])
            ram_used = float(sys.argv[2])
            optimal, margin_real = analyze_experiment(ram_total, ram_used)
            
            print(f"\n✅ Para aplicar el batch_size óptimo:")
            print(f"   python update_batch_size.py {optimal}")
            
        except ValueError:
            print("❌ Error: Los valores deben ser números")
            print("Uso: python analyze_experiment.py <ram_total_gb> <ram_used_gb>")
            print("Ejemplo: python analyze_experiment.py 4 3.6")
    else:
        print("Uso: python analyze_experiment.py <ram_total_gb> <ram_used_gb>")
        print("Ejemplo: python analyze_experiment.py 4 3.6")
        print("\nO simplemente dime los datos y yo ejecuto el análisis")




