import os
import sys
import time
import subprocess
import re
import psutil
from datetime import datetime

# Configurar encoding para Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def get_system_resources():
    """Obtiene información de recursos del sistema"""
    try:
        # Memoria total y disponible
        mem = psutil.virtual_memory()
        total_gb = mem.total / (1024**3)
        available_gb = mem.available / (1024**3)
        used_gb = mem.used / (1024**3)
        percent_used = mem.percent
        
        # CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        
        return {
            'total_ram_gb': total_gb,
            'available_ram_gb': available_gb,
            'used_ram_gb': used_gb,
            'ram_percent': percent_used,
            'cpu_percent': cpu_percent
        }
    except Exception as e:
        print(f"⚠️  Error obteniendo recursos: {e}")
        return None

def get_ingest_process_info():
    """Obtiene información del proceso de ingest"""
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_info', 'cpu_percent']):
            try:
                if proc.info['name'] == 'python.exe' and proc.info['cmdline']:
                    cmdline = ' '.join(proc.info['cmdline'])
                    if 'ingest_improved.py' in cmdline:
                        proc_obj = psutil.Process(proc.info['pid'])
                        return {
                            'pid': proc.info['pid'],
                            'memory_mb': proc.info['memory_info'].rss / (1024**2),
                            'cpu_percent': proc_obj.cpu_percent(interval=0.5),
                            'status': proc_obj.status()
                        }
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return None
    except Exception as e:
        print(f"⚠️  Error obteniendo info del proceso: {e}")
        return None

def get_current_batch_size():
    """Lee el batch_size actual del archivo"""
    try:
        with open('ingest_improved.py', 'r', encoding='utf-8') as f:
            content = f.read()
            match = re.search(r'batch_size\s*=\s*(\d+)', content)
            if match:
                return int(match.group(1))
    except Exception as e:
        print(f"⚠️  Error leyendo batch_size: {e}")
    return None

def update_batch_size(new_size):
    """Actualiza el batch_size en el archivo"""
    try:
        with open('ingest_improved.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Reemplazar batch_size
        new_content = re.sub(
            r'batch_size\s*=\s*\d+',
            f'batch_size = {new_size}',
            content
        )
        
        with open('ingest_improved.py', 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        return True
    except Exception as e:
        print(f"❌ Error actualizando batch_size: {e}")
        return False

def calculate_optimal_batch_size(resources, ingest_info):
    """Calcula el batch_size óptimo basado en recursos disponibles"""
    if not resources or not ingest_info:
        return None
    
    available_ram_gb = resources['available_ram_gb']
    cpu_percent = resources['cpu_percent']
    ingest_memory_mb = ingest_info['memory_mb']
    ingest_cpu = ingest_info['cpu_percent']
    
    # Estrategia de optimización:
    # - Si hay mucha RAM disponible (>15 GB) y CPU bajo (<50%), aumentar batch
    # - Si RAM está limitada (<5 GB) o CPU alto (>80%), reducir batch
    # - Batch base: 2000 archivos
    
    current_batch = get_current_batch_size() or 2000
    
    # Calcular batch óptimo basado en RAM disponible
    # Asumimos ~10-20 MB por archivo en memoria durante procesamiento
    # Con 15 GB disponibles, podríamos procesar ~750,000 archivos teóricamente
    # Pero usamos un factor conservador de seguridad
    
    if available_ram_gb > 15 and cpu_percent < 50:
        # Mucha capacidad disponible - aumentar agresivamente
        optimal = min(10000, int(available_ram_gb * 500))  # ~500 archivos por GB disponible
        if optimal > current_batch:
            return optimal
    elif available_ram_gb > 10 and cpu_percent < 70:
        # Buena capacidad - aumentar moderadamente
        optimal = min(5000, int(available_ram_gb * 300))
        if optimal > current_batch:
            return optimal
    elif available_ram_gb < 5 or cpu_percent > 85:
        # Recursos limitados - reducir
        optimal = max(500, int(available_ram_gb * 200))
        if optimal < current_batch:
            return optimal
    
    return current_batch  # Mantener actual si está bien

def restart_ingest():
    """Detiene y reinicia el proceso de ingest"""
    print("\n🔄 Reiniciando proceso de ingest...")
    
    # Detener procesos de Python
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['name'] == 'python.exe' and proc.info['cmdline']:
                    cmdline = ' '.join(proc.info['cmdline'])
                    if 'ingest_improved.py' in cmdline:
                        proc_obj = psutil.Process(proc.info['pid'])
                        proc_obj.terminate()
                        proc_obj.wait(timeout=5)
                        print(f"   ✓ Proceso {proc.info['pid']} detenido")
            except (psutil.NoSuchProcess, psutil.TimeoutExpired, psutil.AccessDenied):
                continue
    except Exception as e:
        print(f"   ⚠️  Error deteniendo procesos: {e}")
    
    # Esperar un momento
    time.sleep(2)
    
    # Reiniciar
    try:
        subprocess.Popen(
            [sys.executable, 'ingest_improved.py'],
            creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
        )
        print("   ✓ Proceso reiniciado")
        time.sleep(3)  # Dar tiempo para que inicie
        return True
    except Exception as e:
        print(f"   ❌ Error reiniciando: {e}")
        return False

def main():
    print("=" * 80)
    print("🚀 OPTIMIZADOR Y MONITOR DE INGESTIÓN")
    print("=" * 80)
    print(f"Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nEste script monitorea y optimiza automáticamente el batch_size")
    print("para aprovechar al máximo los recursos de tu computadora.\n")
    print("Presiona Ctrl+C para detener\n")
    
    check_count = 0
    last_batch_size = get_current_batch_size()
    last_restart_time = 0
    restart_cooldown = 300  # 5 minutos entre reinicios
    
    try:
        while True:
            check_count += 1
            current_time = time.time()
            
            # Obtener recursos del sistema
            resources = get_system_resources()
            ingest_info = get_ingest_process_info()
            
            # Limpiar pantalla cada 10 checks
            if check_count % 10 == 1:
                os.system('cls' if os.name == 'nt' else 'clear')
                print("=" * 80)
                print("🚀 OPTIMIZADOR Y MONITOR DE INGESTIÓN")
                print("=" * 80)
                print(f"Check #{check_count} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            
            # Mostrar recursos del sistema
            if resources:
                print("📊 RECURSOS DEL SISTEMA:")
                print(f"   RAM Total: {resources['total_ram_gb']:.2f} GB")
                print(f"   RAM Disponible: {resources['available_ram_gb']:.2f} GB ({100-resources['ram_percent']:.1f}% libre)")
                print(f"   RAM Usada: {resources['used_ram_gb']:.2f} GB ({resources['ram_percent']:.1f}%)")
                print(f"   CPU: {resources['cpu_percent']:.1f}%")
                print()
            
            # Mostrar info del proceso de ingest
            if ingest_info:
                print("🔄 PROCESO DE INGEST:")
                print(f"   PID: {ingest_info['pid']}")
                print(f"   Memoria: {ingest_info['memory_mb']:.2f} MB")
                print(f"   CPU: {ingest_info['cpu_percent']:.1f}%")
                print(f"   Estado: {ingest_info['status']}")
                print()
            else:
                print("⚠️  No se detectó proceso de ingest corriendo")
                print()
            
            # Calcular batch_size óptimo
            current_batch = get_current_batch_size()
            if resources and ingest_info:
                optimal_batch = calculate_optimal_batch_size(resources, ingest_info)
                
                print(f"📦 CONFIGURACIÓN ACTUAL:")
                print(f"   batch_size: {current_batch}")
                
                if optimal_batch and optimal_batch != current_batch:
                    print(f"\n💡 OPTIMIZACIÓN DETECTADA:")
                    print(f"   batch_size recomendado: {optimal_batch}")
                    
                    if optimal_batch > current_batch:
                        print(f"   ⬆️  Aumento sugerido: +{optimal_batch - current_batch} archivos por lote")
                    else:
                        print(f"   ⬇️  Reducción sugerida: {optimal_batch - current_batch} archivos por lote")
                    
                    # Aplicar optimización si ha pasado suficiente tiempo desde último reinicio
                    if (current_time - last_restart_time) > restart_cooldown:
                        print(f"\n🔄 Aplicando optimización...")
                        if update_batch_size(optimal_batch):
                            print(f"   ✓ batch_size actualizado a {optimal_batch}")
                            if restart_ingest():
                                last_batch_size = optimal_batch
                                last_restart_time = current_time
                                print(f"   ✅ Proceso reiniciado con batch_size = {optimal_batch}")
                        else:
                            print(f"   ❌ Error actualizando batch_size")
                    else:
                        remaining = int((restart_cooldown - (current_time - last_restart_time)) / 60)
                        print(f"\n⏳ Esperando {remaining} minutos antes de aplicar cambios (cooldown)")
                else:
                    print(f"   ✅ batch_size actual es óptimo para los recursos disponibles")
            else:
                current_batch = get_current_batch_size()
                if current_batch:
                    print(f"📦 batch_size actual: {current_batch}")
            
            print(f"\n{'='*80}")
            print(f"Próxima verificación en 30 segundos...")
            print(f"(Presiona Ctrl+C para detener)\n")
            
            time.sleep(30)
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Monitoreo detenido por el usuario")
        print(f"\n📊 Resumen final:")
        final_batch = get_current_batch_size()
        if final_batch:
            print(f"   batch_size final: {final_batch}")
        if ingest_info:
            print(f"   Proceso de ingest: PID {ingest_info['pid']}")

if __name__ == "__main__":
    # Verificar que psutil esté instalado
    try:
        import psutil
    except ImportError:
        print("❌ Error: psutil no está instalado")
        print("   Instálalo con: pip install psutil")
        sys.exit(1)
    
    main()







