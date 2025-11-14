"""
🚀 MONITOR MAESTRO INTELIGENTE DE INGESTIÓN
===========================================

Este script combina las mejores características de smart_monitor.py y optimize_and_monitor.py:
- Detecta si el proceso se detiene y lo reinicia automáticamente
- Ajusta el batch_size dinámicamente según progreso Y recursos
- Optimizado para aprovechar los nuevos recursos de Supabase (CPU/RAM aumentados)
- Monitorea progreso en tiempo real
- Previene duplicados y conflictos
"""

import os
import sys
import time
import subprocess
import re
import psutil
from datetime import datetime
from urllib.parse import quote_plus
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
import config

# Configurar encoding para Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

def get_env(key):
    """Obtiene una variable de entorno"""
    value = os.getenv(key, "")
    if not value:
        for env_key in os.environ.keys():
            if env_key.strip().lstrip('\ufeff') == key:
                value = os.environ[env_key]
                break
    return value.strip('"').strip("'").strip()

# ============================================================================
# FUNCIONES DE MONITOREO DE PROGRESO
# ============================================================================

def get_indexed_count():
    """Obtiene el número de archivos indexados desde la base de datos"""
    try:
        SUPABASE_URL = get_env("SUPABASE_URL")
        SUPABASE_DB_PASSWORD = get_env("SUPABASE_DB_PASSWORD")
        
        if not SUPABASE_URL or not SUPABASE_DB_PASSWORD:
            return None
        
        project_ref = SUPABASE_URL.replace("https://", "").replace(".supabase.co", "")
        encoded_password = quote_plus(SUPABASE_DB_PASSWORD)
        postgres_connection_string = f"postgresql://postgres:{encoded_password}@db.{project_ref}.supabase.co:5432/postgres"
        
        conn = psycopg2.connect(postgres_connection_string, connect_timeout=10)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Timeout corto para evitar esperas largas
        cur.execute("SET statement_timeout = '15s'")
        
        cur.execute(f"""
            SELECT COUNT(DISTINCT metadata->>'file_name') as count
            FROM vecs.{config.VECTOR_COLLECTION_NAME} 
            WHERE metadata->>'file_name' IS NOT NULL
        """)
        result = cur.fetchone()
        count = result['count'] if result else 0
        cur.close()
        conn.close()
        return count
    except (psycopg2.errors.QueryCanceled, psycopg2.OperationalError):
        # Si hay timeout, significa que hay MUCHOS datos (buena señal)
        return None
    except Exception as e:
        print(f"⚠️  Error obteniendo conteo: {e}")
        return None

def get_total_files():
    """Obtiene el total de archivos a procesar"""
    try:
        total = 0
        if os.path.exists(config.DATA_DIRECTORY):
            supported_extensions = {'.pdf', '.epub', '.txt', '.docx', '.md'}
            for root, dirs, files in os.walk(config.DATA_DIRECTORY):
                for file in files:
                    if os.path.splitext(file)[1].lower() in supported_extensions:
                        total += 1
        return total
    except Exception as e:
        print(f"⚠️  Error contando archivos: {e}")
        return None

# ============================================================================
# FUNCIONES DE GESTIÓN DE BATCH_SIZE
# ============================================================================

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

def update_batch_size(new_size, reason=""):
    """Actualiza el batch_size en el archivo"""
    try:
        with open('ingest_improved.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Reemplazar batch_size y actualizar comentario
        new_content = re.sub(
            r'batch_size\s*=\s*\d+\s*#.*',
            f'batch_size = {new_size}  # Ajustado automáticamente por master_monitor.py',
            content
        )
        
        # Si no hay comentario, agregarlo
        if new_content == content:
            new_content = re.sub(
                r'batch_size\s*=\s*\d+',
                f'batch_size = {new_size}  # Ajustado automáticamente por master_monitor.py',
                content
            )
        
        with open('ingest_improved.py', 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        return True
    except Exception as e:
        print(f"❌ Error actualizando batch_size: {e}")
        return False

# ============================================================================
# FUNCIONES DE GESTIÓN DE PROCESOS
# ============================================================================

def get_ingest_processes():
    """Obtiene todos los procesos de ingest corriendo"""
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['name'] == 'python.exe' and proc.info['cmdline']:
                cmdline = ' '.join(proc.info['cmdline'])
                if 'ingest_improved.py' in cmdline.lower():
                    processes.append(psutil.Process(proc.info['pid']))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return processes

def restart_ingest():
    """Detiene TODOS los procesos de ingest y reinicia uno limpio"""
    print("\n" + "="*80)
    print("🔄 REINICIANDO PROCESO DE INGEST...")
    print("="*80)
    
    # Detener TODOS los procesos de ingest (evitar duplicados)
    ingest_processes = get_ingest_processes()
    if ingest_processes:
        print(f"   Deteniendo {len(ingest_processes)} proceso(s) de ingest...")
        for proc in ingest_processes:
            try:
                proc.terminate()
                proc.wait(timeout=3)
                print(f"      ✅ Proceso {proc.pid} detenido")
            except (psutil.NoSuchProcess, psutil.TimeoutExpired):
                try:
                    proc.kill()
                    print(f"      ✅ Proceso {proc.pid} forzado a cerrar")
                except:
                    pass
    else:
        print("   No hay procesos de ingest corriendo")
    
    time.sleep(3)  # Esperar a que se cierren completamente
    
    # Reiniciar un solo proceso limpio
    try:
        subprocess.Popen(
            [sys.executable, 'ingest_improved.py'],
            creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
        )
        print("   ✅ Proceso reiniciado (un solo proceso limpio)")
        time.sleep(5)  # Dar tiempo para que inicie
        return True
    except Exception as e:
        print(f"   ❌ Error reiniciando: {e}")
        return False

# ============================================================================
# FUNCIONES DE OPTIMIZACIÓN BASADA EN RECURSOS
# ============================================================================

def get_system_resources():
    """Obtiene información de recursos del sistema"""
    try:
        mem = psutil.virtual_memory()
        return {
            'total_ram_gb': mem.total / (1024**3),
            'available_ram_gb': mem.available / (1024**3),
            'used_ram_gb': mem.used / (1024**3),
            'ram_percent': mem.percent,
            'cpu_percent': psutil.cpu_percent(interval=1)
        }
    except Exception as e:
        print(f"⚠️  Error obteniendo recursos: {e}")
        return None

def get_ingest_process_info():
    """Obtiene información del proceso de ingest"""
    try:
        processes = get_ingest_processes()
        if not processes:
            return None
        
        proc = processes[0]  # Tomar el primero
        return {
            'pid': proc.pid,
            'memory_mb': proc.memory_info().rss / (1024**2),
            'cpu_percent': proc.cpu_percent(interval=0.5),
            'status': proc.status()
        }
    except Exception as e:
        return None

def calculate_optimal_batch_size(resources, ingest_info, current_batch, progress_rate=None):
    """
    Calcula el batch_size óptimo basado en:
    - Recursos del sistema (RAM/CPU)
    - Estado del proceso de ingest
    - Tasa de progreso (si está disponible)
    
    NOTA: Supabase tiene 2 GB RAM y 2-core ARM CPU (instancia actualizada)
    """
    if not resources:
        return current_batch
    
    available_ram_gb = resources['available_ram_gb']
    cpu_percent = resources['cpu_percent']
    
    # RECURSOS DE SUPABASE: 2 GB RAM, 2-core ARM CPU
    # Estrategia optimizada para aprovechar al máximo los recursos aumentados
    
    # El servidor de Supabase tiene 2 GB RAM, podemos ser más agresivos
    # Procesar más archivos localmente ayuda, y el servidor puede manejar más
    
    # IMPORTANTE: Supabase reserva ~10% de RAM (200 MB) como margen de seguridad
    # Solo tenemos ~1.8 GB realmente disponibles para evitar OOM kills
    # Por lo tanto, debemos ser más conservadores con los aumentos
    
    # Si hay mucha RAM local disponible (>15 GB) y CPU bajo (<50%)
    # Podemos procesar más localmente, pero el servidor tiene límites
    if available_ram_gb > 15 and cpu_percent < 50:
        # Aumentar moderadamente: servidor tiene 1.8 GB disponible (respetando margen)
        optimal = min(50, int(available_ram_gb * 2.5))  # ~2.5 archivos por GB local
        if optimal > current_batch:
            return optimal
    
    # Si hay buena capacidad local (10-15 GB RAM) y CPU moderado (<70%)
    elif available_ram_gb > 10 and cpu_percent < 70:
        # Aumentar conservadoramente
        optimal = min(40, int(available_ram_gb * 2))  # ~2 archivos por GB local
        if optimal > current_batch:
            return optimal
    
    # Si hay capacidad moderada (5-10 GB RAM) y CPU <80%
    elif available_ram_gb > 5 and cpu_percent < 80:
        # Mantener o aumentar ligeramente
        optimal = min(30, int(available_ram_gb * 1.8))  # ~1.8 archivos por GB local
        if optimal > current_batch:
            return optimal
    
    # Si recursos están limitados (<5 GB RAM o CPU >85%)
    elif available_ram_gb < 5 or cpu_percent > 85:
        # Reducir conservadoramente
        optimal = max(15, int(available_ram_gb * 1.5))
        if optimal < current_batch:
            return optimal
    
    # Límite máximo basado en recursos de Supabase (2 GB RAM)
    # IMPORTANTE: Supabase deja ~10% de RAM libre (200 MB) como margen de seguridad
    # para evitar que el proceso sea "asesinado" (OOM kill) como pasó antes
    # Por lo tanto, solo tenemos ~1.8 GB realmente disponibles
    # Con 1.8 GB disponibles, podemos procesar ~40-50 archivos por lote de forma segura
    max_safe_batch = 50  # Límite seguro considerando el margen de seguridad de Supabase
    
    if current_batch > max_safe_batch:
        return max_safe_batch
    
    return current_batch  # Mantener actual si está bien

# ============================================================================
# FUNCIÓN PRINCIPAL
# ============================================================================

def main():
    print("=" * 80)
    print("🚀 MONITOR MAESTRO INTELIGENTE DE INGESTIÓN")
    print("=" * 80)
    print(f"Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n✨ Características:")
    print("   • Detecta y reinicia procesos detenidos automáticamente")
    print("   • Ajusta batch_size dinámicamente según progreso Y recursos")
    print("   • Optimizado para Supabase con 2 GB RAM (respeta margen de seguridad)")
    print("   • Previene duplicados y conflictos")
    print("\nPresiona Ctrl+C para detener\n")
    
    # Valores iniciales
    last_indexed_count = get_indexed_count()
    total_files = get_total_files()
    current_batch = get_current_batch_size() or 10
    no_progress_count = 0
    check_interval = 60  # Verificar cada 60 segundos
    last_check_time = time.time()
    last_restart_time = 0
    restart_cooldown = 180  # 3 minutos entre reinicios (más corto para respuesta rápida)
    
    # Historial de ajustes
    adjustment_history = []
    min_batch = 15  # Mínimo seguro
    max_batch = 50  # Máximo seguro considerando margen de seguridad de Supabase (1.8 GB disponible)
    
    print(f"📊 Configuración inicial:")
    print(f"   Total de archivos: {total_files}")
    print(f"   Archivos indexados: {last_indexed_count if last_indexed_count else 'calculando...'}")
    print(f"   batch_size actual: {current_batch}")
    print(f"   Rango de batch_size: {min_batch} - {max_batch}")
    print("\n" + "="*80 + "\n")
    
    try:
        while True:
            current_time = time.time()
            
            # Obtener estado actual
            indexed_count = get_indexed_count()
            ingest_processes = get_ingest_processes()
            resources = get_system_resources()
            ingest_info = get_ingest_process_info()
            
            # Verificar procesos duplicados
            if len(ingest_processes) > 1:
                print(f"\n⚠️  ADVERTENCIA: Se detectaron {len(ingest_processes)} procesos de ingest!")
                print(f"   Deteniendo duplicados y reiniciando...")
                restart_ingest()
                time.sleep(5)
                continue
            
            # Verificar si el proceso está corriendo
            if not ingest_processes:
                print(f"\n⚠️  No se detecta proceso de ingest corriendo")
                print(f"   Reiniciando...")
                restart_ingest()
                no_progress_count = 0
                time.sleep(5)
                continue
            
            ingest_proc = ingest_processes[0]
            
            # Verificar estado del proceso
            try:
                proc_status = ingest_proc.status()
                if proc_status in ['zombie', 'stopped']:
                    print(f"\n⚠️  Proceso en estado anormal ({proc_status}), reiniciando...")
                    restart_ingest()
                    no_progress_count = 0
                    time.sleep(5)
                    continue
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                print(f"\n⚠️  Proceso ya no existe, reiniciando...")
                restart_ingest()
                no_progress_count = 0
                time.sleep(5)
                continue
            
            # Mostrar estado actual
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Estado actual:")
            if indexed_count is not None:
                print(f"   📚 Archivos indexados: {indexed_count}/{total_files if total_files else '?'}")
                if total_files:
                    progress_pct = (indexed_count / total_files * 100)
                    print(f"   📈 Progreso: {progress_pct:.1f}%")
            else:
                print(f"   📚 Archivos indexados: calculando... (hay muchos datos)")
            
            if resources:
                print(f"   💻 RAM disponible: {resources['available_ram_gb']:.1f} GB | CPU: {resources['cpu_percent']:.1f}%")
            
            if ingest_info:
                print(f"   🔄 Proceso: PID {ingest_info['pid']} | Mem: {ingest_info['memory_mb']:.1f} MB | CPU: {ingest_info['cpu_percent']:.1f}%")
            
            print(f"   📦 batch_size: {current_batch}")
            
            # Verificar progreso
            if indexed_count is not None and indexed_count > last_indexed_count:
                # ¡Hay progreso!
                progress = indexed_count - last_indexed_count
                no_progress_count = 0
                print(f"\n✅ PROGRESO DETECTADO: +{progress} archivos")
                
                # Calcular tasa de progreso
                elapsed = current_time - last_check_time
                progress_rate = progress / elapsed if elapsed > 0 else 0
                
                # Si hay buen progreso y recursos disponibles, aumentar batch_size
                if progress >= 3 and (current_time - last_restart_time) > restart_cooldown:
                    if resources and ingest_info:
                        optimal_batch = calculate_optimal_batch_size(
                            resources, ingest_info, current_batch, progress_rate
                        )
                        
                        if optimal_batch > current_batch:
                            increment = optimal_batch - current_batch
                            # Limitar incrementos grandes a pasos graduales (conservador por margen de seguridad)
                            if increment > 10:
                                optimal_batch = current_batch + 10  # Aumentar de a 10 en 10 (conservador)
                            
                            print(f"\n💡 Buen progreso detectado (+{progress} archivos)")
                            print(f"   Aumentando batch_size: {current_batch} -> {optimal_batch} (+{optimal_batch - current_batch})")
                            
                            if update_batch_size(optimal_batch, "progreso positivo"):
                                current_batch = optimal_batch
                                adjustment_history.append(('increase', optimal_batch, datetime.now()))
                                restart_ingest()
                                last_restart_time = current_time
                                time.sleep(10)
                                continue
                
                last_indexed_count = indexed_count
                
            elif indexed_count is not None and indexed_count == last_indexed_count:
                # No hay progreso
                no_progress_count += 1
                print(f"\n⏳ Sin progreso ({no_progress_count} checks)")
                
                # Si no hay progreso por varios checks, reducir batch_size
                if no_progress_count >= 3 and (current_time - last_restart_time) > restart_cooldown:
                    if current_batch > min_batch:
                        # Reducir gradualmente (ajustado para 2 GB RAM)
                        if current_batch <= 50:
                            decrement = 10
                        elif current_batch <= 80:
                            decrement = 15
                        else:
                            decrement = 20
                        
                        new_batch = max(current_batch - decrement, min_batch)
                        print(f"\n⚠️  Sin progreso por {no_progress_count} checks")
                        print(f"   Reduciendo batch_size: {current_batch} -> {new_batch} (-{decrement})")
                        
                        if update_batch_size(new_batch, "sin progreso"):
                            current_batch = new_batch
                            adjustment_history.append(('decrease', new_batch, datetime.now()))
                            restart_ingest()
                            last_restart_time = current_time
                            no_progress_count = 0
                            time.sleep(10)
                            continue
            
            # Mostrar historial reciente
            if adjustment_history:
                print(f"\n📋 Historial de ajustes (últimos 3):")
                for adj_type, batch, adj_time in adjustment_history[-3:]:
                    print(f"   {adj_time.strftime('%H:%M:%S')}: {adj_type} -> batch_size = {batch}")
            
            print(f"\n⏱️  Próxima verificación en {check_interval} segundos...")
            print("="*80)
            
            last_check_time = current_time
            time.sleep(check_interval)
            
    except KeyboardInterrupt:
        print("\n\n" + "="*80)
        print("⏹️  MONITOR DETENIDO POR EL USUARIO")
        print("="*80)
        final_count = get_indexed_count()
        if final_count is not None:
            print(f"\n📊 Estado final:")
            print(f"   Archivos indexados: {final_count}/{total_files if total_files else '?'}")
            if total_files:
                percentage = (final_count / total_files * 100)
                print(f"   Progreso: {percentage:.1f}%")
        print(f"   batch_size final: {current_batch}")
        
        if adjustment_history:
            print(f"\n📋 Historial completo de ajustes:")
            for adj_type, batch, adj_time in adjustment_history:
                print(f"   {adj_time.strftime('%Y-%m-%d %H:%M:%S')}: {adj_type} -> {batch}")

if __name__ == "__main__":
    main()

