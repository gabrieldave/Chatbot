"""
🧮 CALCULADOR DE BATCH_SIZE ÓPTIMO
===================================

Este script calcula el batch_size óptimo basado en:
- RAM total de Supabase
- Uso actual de RAM
- batch_size actual
- Progreso observado

Uso: Ejecuta y proporciona los datos de Supabase cuando se te pida.
"""

import sys

# Configurar encoding para Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def calculate_batch_size(ram_total_gb, ram_used_gb, current_batch, observation=""):
    """
    Calcula el batch_size óptimo basado en los recursos de Supabase
    
    Args:
        ram_total_gb: RAM total en Supabase (ej: 2, 4, 8)
        ram_used_gb: RAM usada actualmente (ej: 1.8, 3.6)
        current_batch: batch_size actual
        observation: Observación adicional (opcional)
    """
    print("=" * 80)
    print("🧮 CÁLCULO DE BATCH_SIZE ÓPTIMO")
    print("=" * 80)
    
    # Calcular porcentaje de uso
    usage_percent = (ram_used_gb / ram_total_gb) * 100
    available_gb = ram_total_gb - ram_used_gb
    
    print(f"\n📊 RECURSOS DE SUPABASE:")
    print(f"   RAM Total: {ram_total_gb} GB")
    print(f"   RAM Usada: {ram_used_gb} GB ({usage_percent:.1f}%)")
    print(f"   RAM Disponible: {available_gb:.2f} GB")
    print(f"   batch_size actual: {current_batch}")
    
    if observation:
        print(f"\n📝 Observación: {observation}")
    
    # Análisis del margen de seguridad
    margin_gb = ram_total_gb * 0.10  # 10% típico
    effective_available = ram_total_gb - margin_gb
    
    print(f"\n🔍 ANÁLISIS:")
    print(f"   Margen de seguridad estimado: {margin_gb:.2f} GB (10%)")
    print(f"   RAM efectivamente disponible: {effective_available:.2f} GB")
    
    # Determinar si el margen es real
    # HIPÓTESIS: Si con batch_size=15 el uso sube proporcionalmente al aumentar RAM,
    # entonces el margen de seguridad es REAL y debemos respetarlo
    
    usage_ratio = ram_used_gb / ram_total_gb
    
    if usage_ratio >= 0.88:  # 88% o más (cerca del 90% esperado)
        print(f"   ✅ Uso cerca del límite ({usage_ratio*100:.1f}%) → Margen de seguridad es REAL")
        print(f"   💡 Supabase está reteniendo RAM intencionalmente por seguridad")
        margin_is_real = True
    elif usage_ratio < 0.70:  # Menos del 70%
        print(f"   ⚠️  Uso por debajo del límite ({usage_ratio*100:.1f}%) → Puede haber más capacidad disponible")
        print(f"   💡 El proceso no está usando todo lo disponible")
        margin_is_real = False
    else:
        print(f"   ⚠️  Uso en zona intermedia ({usage_ratio*100:.1f}%) → Necesitamos más datos")
        margin_is_real = None
    
    # Análisis específico del experimento
    if current_batch == 15:
        print(f"\n🔬 ANÁLISIS DEL EXPERIMENTO:")
        print(f"   batch_size constante: 15 (variable de control)")
        expected_usage_2gb = 1.8  # Lo que observamos con 2 GB
        expected_usage_4gb = expected_usage_2gb * 2  # Proporcional si margen es real
        
        if ram_total_gb == 4:
            if ram_used_gb >= expected_usage_4gb * 0.9:  # Cerca de 3.6 GB
                print(f"   ✅ CONFIRMADO: Uso subió proporcionalmente ({ram_used_gb:.2f} GB)")
                print(f"   ✅ El margen de seguridad ES REAL - Supabase retiene RAM intencionalmente")
                print(f"   ✅ Debemos respetar el margen y cuidar el batch_size")
            elif ram_used_gb <= expected_usage_2gb * 1.1:  # Se mantiene cerca de 1.8 GB
                print(f"   ✅ CONFIRMADO: Uso se mantuvo similar ({ram_used_gb:.2f} GB)")
                print(f"   ✅ El margen NO era real - Había más capacidad disponible")
                print(f"   ✅ Podemos ser más agresivos con el batch_size")
    
    # Calcular batch_size óptimo
    print(f"\n💡 CÁLCULO DE BATCH_SIZE ÓPTIMO:")
    
    # Factor de seguridad basado en RAM disponible
    # Asumimos ~20-30 MB por archivo en memoria durante procesamiento
    mb_per_file = 25  # MB promedio por archivo
    
    if margin_is_real:
        # Si el margen es real, usar solo el 85% de la RAM efectivamente disponible
        safe_ram_gb = effective_available * 0.85
        print(f"   Usando 85% de RAM efectiva (margen real): {safe_ram_gb:.2f} GB")
    elif margin_is_real == False:
        # Si el margen no es real, podemos usar más
        safe_ram_gb = ram_used_gb * 1.2  # 20% más que el uso actual
        print(f"   Usando 120% del uso actual (margen no real): {safe_ram_gb:.2f} GB")
    else:
        # Zona intermedia, ser conservador
        safe_ram_gb = effective_available * 0.75
        print(f"   Usando 75% de RAM efectiva (zona intermedia): {safe_ram_gb:.2f} GB")
    
    # Calcular batch_size teórico
    safe_ram_mb = safe_ram_gb * 1024
    theoretical_batch = int(safe_ram_mb / mb_per_file)
    
    print(f"   Capacidad teórica: {theoretical_batch} archivos")
    
    # Ajustar según el batch_size actual y progreso
    if current_batch > 0:
        # Si el batch_size actual funciona bien, podemos aumentar gradualmente
        if usage_percent < 85:
            # Hay espacio, podemos aumentar
            optimal_batch = min(theoretical_batch, current_batch * 1.5)
            recommendation = "AUMENTAR"
        elif usage_percent > 95:
            # Muy cerca del límite, reducir
            optimal_batch = max(current_batch * 0.7, 10)
            recommendation = "REDUCIR"
        else:
            # Zona segura, mantener o aumentar ligeramente
            optimal_batch = min(theoretical_batch, current_batch * 1.2)
            recommendation = "MANTENER/AUMENTAR LIGERAMENTE"
    else:
        optimal_batch = min(theoretical_batch, 20)  # Inicio conservador
        recommendation = "INICIO CONSERVADOR"
    
    # Limitar a rangos razonables
    optimal_batch = max(10, min(optimal_batch, 100))  # Entre 10 y 100
    
    print(f"\n📦 RECOMENDACIÓN:")
    print(f"   batch_size óptimo: {int(optimal_batch)} archivos")
    print(f"   Acción: {recommendation}")
    
    if optimal_batch > current_batch:
        increment = optimal_batch - current_batch
        print(f"   Aumento sugerido: +{int(increment)} archivos")
    elif optimal_batch < current_batch:
        decrement = current_batch - optimal_batch
        print(f"   Reducción sugerida: -{int(decrement)} archivos")
    else:
        print(f"   Mantener batch_size actual")
    
    # Estimación de velocidad
    print(f"\n⚡ ESTIMACIÓN DE RENDIMIENTO:")
    time_per_batch_minutes = 2 + (optimal_batch / 10)  # ~2 min base + tiempo por archivo
    files_per_hour = (optimal_batch * 60) / time_per_batch_minutes
    print(f"   Tiempo por lote: ~{time_per_batch_minutes:.1f} minutos")
    print(f"   Velocidad estimada: ~{files_per_hour:.0f} archivos/hora")
    
    # Comparación con actual
    if current_batch > 0:
        current_time_per_batch = 2 + (current_batch / 10)
        current_files_per_hour = (current_batch * 60) / current_time_per_batch
        speedup = files_per_hour / current_files_per_hour if current_files_per_hour > 0 else 1
        print(f"   Velocidad actual: ~{current_files_per_hour:.0f} archivos/hora")
        print(f"   Mejora estimada: {speedup:.2f}x")
    
    print("\n" + "=" * 80)
    
    return int(optimal_batch)

def interactive_calculation():
    """Modo interactivo para calcular batch_size"""
    print("=" * 80)
    print("🧮 CALCULADOR INTERACTIVO DE BATCH_SIZE")
    print("=" * 80)
    print("\nProporciona los datos de Supabase cuando se te pida.")
    print("Presiona Enter sin valor para usar valores por defecto.\n")
    
    try:
        # RAM Total
        ram_total_input = input("RAM Total en Supabase (GB) [2]: ").strip()
        ram_total = float(ram_total_input) if ram_total_input else 2.0
        
        # RAM Usada
        ram_used_input = input("RAM Usada actualmente (GB) [1.8]: ").strip()
        ram_used = float(ram_used_input) if ram_used_input else 1.8
        
        # Batch Size Actual
        batch_current_input = input("batch_size actual [15]: ").strip()
        batch_current = int(batch_current_input) if batch_current_input else 15
        
        # Observación opcional
        observation = input("Observación adicional (opcional): ").strip()
        
        # Calcular
        optimal = calculate_batch_size(ram_total, ram_used, batch_current, observation)
        
        print(f"\n✅ RESULTADO FINAL:")
        print(f"   batch_size recomendado: {optimal}")
        print(f"\n💡 Para aplicar este batch_size, ejecuta:")
        print(f"   python update_batch_size.py {optimal}")
        
    except ValueError as e:
        print(f"\n❌ Error: Valor inválido - {e}")
    except KeyboardInterrupt:
        print("\n\n⏹️  Cancelado por el usuario")

if __name__ == "__main__":
    interactive_calculation()

