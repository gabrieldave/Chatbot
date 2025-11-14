"""
🧠 MONITOR INTELIGENTE CON AJUSTE AUTOMÁTICO DE WORKERS
========================================================

Monitorea el progreso de la ingestión paralela y ajusta workers automáticamente
"""

import os
import sys
import time
import re
import psutil
import subprocess
from datetime import datetime
from urllib.parse import quote_plus
from dotenv import load_dotenv
import psycopg2
import config

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

SUPABASE_URL = get_env("SUPABASE_URL")
SUPABASE_DB_PASSWORD = get_env("SUPABASE_DB_PASSWORD")

if not SUPABASE_URL or not SUPABASE_DB_PASSWORD:
    print("❌ Error: Faltan variables de entorno")
    sys.exit(1)

project_ref = SUPABASE_URL.replace("https://", "").replace(".supabase.co", "")
encoded_password = quote_plus(SUPABASE_DB_PASSWORD)
postgres_connection_string = f"postgresql://postgres:{encoded_password}@db.{project_ref}.supabase.co:5432/postgres"

# ============================================================================
# FUNCIONES DE MONITOREO
# ============================================================================

def get_indexed_count():
    """Obtiene número de archivos indexados"""
    try:
        conn = psycopg2.connect(postgres_connection_string, connect_timeout=10)
        cur = conn.cursor()
        cur.execute("SET statement_timeout = '15s'")
        
        cur.execute(f"""
            SELECT COUNT(DISTINCT metadata->>'file_name') as count
            FROM vecs.{config.VECTOR_COLLECTION_NAME}
            WHERE metadata->>'file_name' IS NOT NULL
        """)
        
        count = cur.fetchone()[0]
        cur.close()
        conn.close()
        return count
    except Exception as e:
        print(f"⚠️  Error obteniendo conteo: {e}")
        return None

def get_total_files():
    """Cuenta archivos totales en data/"""
    data_dir = "./data"
    total = 0
    if os.path.exists(data_dir):
        supported_extensions = {'.pdf', '.epub', '.txt', '.docx', '.md', '.doc'}
        for root, dirs, files in os.walk(data_dir):
            for file in files:
                if os.path.splitext(file)[1].lower() in supported_extensions:
                    total += 1
    return total

def get_ingest_processes():
    """Obtiene procesos de ingestión paralela"""
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['name'] == 'python.exe' and proc.info['cmdline']:
                cmdline = ' '.join(proc.info['cmdline'])
                if 'ingest_parallel_tier3.py' in cmdline.lower():
                    proc_obj = psutil.Process(proc.info['pid'])
                    processes.append({
                        'pid': proc.info['pid'],
                        'memory_mb': proc_obj.memory_info().rss / (1024**2),
                        'cpu': proc_obj.cpu_percent(interval=0.5),
                        'status': proc_obj.status()
                    })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return processes

def get_current_workers():
    """Lee el número de workers del script"""
    try:
        with open('ingest_parallel_tier3.py', 'r', encoding='utf-8') as f:
            content = f.read()
            # Buscar MAX_WORKERS
            match = re.search(r'MAX_WORKERS\s*=\s*(\d+)', content)
            if match:
                return int(match.group(1))
    except Exception as e:
        print(f"⚠️  Error leyendo workers: {e}")
    return None

def update_workers(new_workers):
    """Actualiza el número de workers en el script"""
    try:
        with open('ingest_parallel_tier3.py', 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Buscar y reemplazar MAX_WORKERS
        updated = False
        for i, line in enumerate(lines):
            if 'MAX_WORKERS' in line and '=' in line:
                # Reemplazar el valor
                new_line = re.sub(r'MAX_WORKERS\s*=\s*\d+', f'MAX_WORKERS = {new_workers}', line)
                lines[i] = new_line
                updated = True
                break
        
        if updated:
            with open('ingest_parallel_tier3.py', 'w', encoding='utf-8') as f:
                f.writelines(lines)
            return True
    except Exception as e:
        print(f"❌ Error actualizando workers: {e}")
    return False

def kill_ingest_processes():
    """Detiene todos los procesos de ingestión"""
    processes = get_ingest_processes()
    for proc_info in processes:
        try:
            proc = psutil.Process(proc_info['pid'])
            proc.terminate()
            proc.wait(timeout=5)
        except (psutil.NoSuchProcess, psutil.TimeoutExpired):
            try:
                proc.kill()
            except:
                pass
        except Exception as e:
            print(f"⚠️  Error terminando proceso {proc_info['pid']}: {e}")

def restart_ingest():
    """Reinicia el proceso de ingestión"""
    print("🔄 Reiniciando proceso de ingestión...")
    kill_ingest_processes()
    time.sleep(2)
    
    # Iniciar nuevo proceso
    try:
        subprocess.Popen(
            [sys.executable, 'ingest_parallel_tier3.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        )
        print("✅ Proceso reiniciado")
        return True
    except Exception as e:
        print(f"❌ Error reiniciando: {e}")
        return False

# ============================================================================
# LÓGICA DE AJUSTE
# ============================================================================

def calculate_optimal_workers(current_workers, files_per_minute, remaining_files):
    """Calcula número óptimo de workers basado en velocidad (objetivo: 70% de Tier 3)"""
    # Objetivo: usar ~70% de capacidad Tier 3 (3,500 RPM, 3.5M TPM)
    # Con 15 workers podemos procesar ~30-40 archivos/minuto
    
    if files_per_minute < 10:
        # Muy lento, aumentar workers hacia objetivo de 70%
        if current_workers < 15:
            return min(current_workers + 2, 15)
        elif current_workers < 20:
            return min(current_workers + 1, 20)
    elif files_per_minute < 20:
        # Lento, aumentar moderadamente
        if current_workers < 15:
            return min(current_workers + 1, 15)
    elif files_per_minute > 50:
        # Muy rápido, podemos reducir si hay pocos archivos
        if remaining_files < 100 and current_workers > 10:
            return max(current_workers - 1, 10)
    
    # Si quedan muchos archivos y tenemos capacidad, aumentar hacia 70%
    if remaining_files > 500 and current_workers < 15:
        return min(current_workers + 1, 15)
    
    # Mantener cerca de 15 workers para usar ~70% de capacidad
    if current_workers < 15 and remaining_files > 200:
        return min(current_workers + 1, 15)
    
    return current_workers  # Mantener actual

# ============================================================================
# FUNCIÓN PRINCIPAL
# ============================================================================

def main():
    print("=" * 80)
    print("🧠 MONITOR INTELIGENTE CON AJUSTE AUTOMÁTICO DE WORKERS")
    print("=" * 80)
    print(f"Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n✨ Características:")
    print("   • Monitorea progreso cada 30 segundos")
    print("   • Ajusta workers automáticamente según velocidad")
    print("   • Reinicia proceso si se detiene")
    print("   • Respeta límites de OpenAI (máx 20 workers)")
    print("\nPresiona Ctrl+C para detener\n")
    
    check_interval = 30  # Verificar cada 30 segundos
    last_indexed = None
    last_time = None
    last_workers = None
    restart_cooldown = 0
    last_restart_time = 0
    
    try:
        while True:
            current_time = time.time()
            
            # Obtener estado actual
            indexed_count = get_indexed_count()
            total_files = get_total_files()
            processes = get_ingest_processes()
            current_workers = get_current_workers()
            
            if indexed_count is None:
                print("⚠️  No se pudo obtener conteo, reintentando...")
                time.sleep(check_interval)
                continue
            
            remaining = total_files - indexed_count
            progress = (indexed_count / total_files * 100) if total_files > 0 else 0
            
            # Calcular velocidad
            files_per_minute = 0
            if last_indexed is not None and last_time is not None:
                elapsed_minutes = (current_time - last_time) / 60
                if elapsed_minutes > 0:
                    files_per_minute = (indexed_count - last_indexed) / elapsed_minutes
            
            # Mostrar estado
            print(f"\n{'='*80}")
            print(f"📊 ESTADO: {datetime.now().strftime('%H:%M:%S')}")
            print(f"{'='*80}")
            print(f"Archivos indexados: {indexed_count}/{total_files} ({progress:.2f}%)")
            print(f"Pendientes: {remaining}")
            print(f"Procesos activos: {len(processes)}")
            print(f"Workers configurados: {current_workers}")
            
            if files_per_minute > 0:
                print(f"Velocidad: {files_per_minute:.2f} archivos/minuto")
                eta_minutes = remaining / files_per_minute if files_per_minute > 0 else 0
                print(f"ETA: {int(eta_minutes)} minutos")
            
            # Verificar si el proceso está corriendo
            if not processes:
                print("\n⚠️  No hay procesos activos")
                if current_time - last_restart_time > 60:  # Cooldown de 1 minuto
                    print("🔄 Reiniciando proceso...")
                    if restart_ingest():
                        last_restart_time = current_time
                        time.sleep(5)  # Esperar a que inicie
                        continue
                else:
                    print("⏳ Esperando cooldown antes de reiniciar...")
            else:
                # Proceso está corriendo, verificar si necesitamos ajustar workers
                if current_workers and files_per_minute > 0:
                    optimal_workers = calculate_optimal_workers(
                        current_workers, 
                        files_per_minute, 
                        remaining
                    )
                    
                    if optimal_workers != current_workers:
                        print(f"\n💡 Ajuste recomendado:")
                        print(f"   Workers actuales: {current_workers}")
                        print(f"   Workers óptimos: {optimal_workers}")
                        
                        if optimal_workers > current_workers:
                            print(f"   🚀 Aumentando workers para mejorar velocidad...")
                        else:
                            print(f"   ⬇️  Reduciendo workers (velocidad suficiente)...")
                        
                        # Actualizar y reiniciar
                        if update_workers(optimal_workers):
                            print(f"   ✅ Workers actualizados a {optimal_workers}")
                            if current_time - last_restart_time > 120:  # Cooldown de 2 minutos
                                print("   🔄 Reiniciando para aplicar cambios...")
                                if restart_ingest():
                                    last_restart_time = current_time
                                    last_workers = optimal_workers
                                    time.sleep(5)
                                    continue
                            else:
                                print("   ⏳ Esperando cooldown antes de reiniciar...")
            
            # Actualizar valores para próxima iteración
            last_indexed = indexed_count
            last_time = current_time
            last_workers = current_workers
            
            # Esperar antes de siguiente verificación
            print(f"\n⏳ Próxima verificación en {check_interval} segundos...")
            time.sleep(check_interval)
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Monitor detenido por el usuario")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

