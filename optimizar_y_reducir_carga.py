"""
🔧 OPTIMIZAR Y REDUCIR CARGA EN SUPABASE
=========================================

Reduce la carga en Supabase optimizando workers y pausando si es necesario.
"""

import os
import sys
import psutil
import time
import signal
from datetime import datetime

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def get_ingest_processes():
    """Obtiene procesos de ingesta"""
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['name'] and 'python' in proc.info['name'].lower():
                cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                if any(keyword in cmdline.lower() for keyword in ['ingest_parallel_tier3', 'ingest_optimized_rag', 'ingest_optimized_tier3']) and 'monitor' not in cmdline.lower():
                    processes.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return processes

def reducir_workers():
    """Reduce el número de procesos de ingesta"""
    print("="*80)
    print("🔧 REDUCIENDO CARGA EN SUPABASE")
    print("="*80)
    print()
    
    procesos = get_ingest_processes()
    
    if not procesos:
        print("⚠️  No se encontraron procesos de ingesta")
        return
    
    print(f"📊 Procesos encontrados: {len(procesos)}")
    print()
    print("💡 Opciones:")
    print("   1. Detener TODOS los procesos (recomendado si hay sobrecarga)")
    print("   2. Detener solo algunos procesos (reducir carga gradualmente)")
    print("   3. Pausar temporalmente (suspender procesos)")
    print("   4. Cancelar")
    print()
    
    opcion = input("Selecciona opción (1-4): ").strip()
    
    if opcion == "1":
        print("\n🛑 Deteniendo TODOS los procesos de ingesta...")
        for proc in procesos:
            try:
                print(f"   Deteniendo PID {proc.pid}...")
                proc.terminate()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        print("\n✅ Procesos detenidos. Espera 5 segundos...")
        time.sleep(5)
        
        # Verificar si aún están corriendo
        procesos_restantes = get_ingest_processes()
        if procesos_restantes:
            print("⚠️  Algunos procesos aún están activos, forzando cierre...")
            for proc in procesos_restantes:
                try:
                    proc.kill()
                except:
                    pass
        
        print("✅ Todos los procesos han sido detenidos")
        
    elif opcion == "2":
        print(f"\n🛑 Deteniendo {len(procesos) // 2} de {len(procesos)} procesos...")
        for i, proc in enumerate(procesos):
            if i < len(procesos) // 2:
                try:
                    print(f"   Deteniendo PID {proc.pid}...")
                    proc.terminate()
                except:
                    pass
        print("✅ Procesos reducidos")
        
    elif opcion == "3":
        print("\n⏸️  Pausando procesos (suspender)...")
        for proc in procesos:
            try:
                print(f"   Pausando PID {proc.pid}...")
                proc.suspend()
            except:
                pass
        print("✅ Procesos pausados")
        print("💡 Para reanudar, ejecuta: python reanudar_ingesta.py")
        
    else:
        print("❌ Operación cancelada")

def verificar_estado_actual():
    """Verifica el estado actual antes de actuar"""
    print("="*80)
    print("📊 ESTADO ACTUAL")
    print("="*80)
    print()
    
    procesos = get_ingest_processes()
    print(f"🔄 Procesos de ingesta: {len(procesos)}")
    
    for proc in procesos:
        try:
            cpu = proc.cpu_percent(interval=0.1)
            mem_mb = proc.memory_info().rss / (1024 * 1024)
            print(f"   PID {proc.pid}: CPU {cpu:.1f}%, RAM {mem_mb:.0f} MB")
        except:
            pass
    
    print()
    print("💡 Basado en la imagen de Supabase que compartiste:")
    print("   - Memory: 1.8 GB total, solo 77.95 MB libre (CRÍTICO)")
    print("   - CPU I/O Wait: 75.87% (muy alto, indica sobrecarga de disco)")
    print("   - IOPS: 751.96 / 3000 (25%, pero con mucho I/O wait)")
    print()
    print("🔴 RECOMENDACIÓN: Reducir carga inmediatamente")
    print()

def main():
    verificar_estado_actual()
    reducir_workers()
    
    print("\n" + "="*80)
    print("📝 PRÓXIMOS PASOS:")
    print("="*80)
    print("1. Espera unos minutos para que Supabase se estabilice")
    print("2. Verifica el estado en el dashboard de Supabase")
    print("3. Si decides continuar, reduce workers:")
    print("   - Edita config_ingesta.py: MAX_WORKERS = 5 (en lugar de 15)")
    print("   - O ejecuta solo 1 proceso en lugar de 3")
    print("4. Monitorea el uso de memoria en Supabase")
    print("="*80)

if __name__ == "__main__":
    main()



