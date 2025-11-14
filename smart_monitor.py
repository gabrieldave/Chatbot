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

def get_indexed_count():
    """Obtiene el número de archivos indexados"""
    try:
        SUPABASE_URL = get_env("SUPABASE_URL")
        SUPABASE_DB_PASSWORD = get_env("SUPABASE_DB_PASSWORD")
        
        if not SUPABASE_URL or not SUPABASE_DB_PASSWORD:
            return None
        
        project_ref = SUPABASE_URL.replace("https://", "").replace(".supabase.co", "")
        encoded_password = quote_plus(SUPABASE_DB_PASSWORD)
        postgres_connection_string = f"postgresql://postgres:{encoded_password}@db.{project_ref}.supabase.co:5432/postgres"
        
        conn = psycopg2.connect(postgres_connection_string)
        cur = conn.cursor(cursor_factory=RealDictCursor)
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
    except Exception as e:
        print(f"Error obteniendo conteo: {e}")
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
        print(f"Error contando archivos: {e}")
        return None

def get_current_batch_size():
    """Lee el batch_size actual"""
    try:
        with open('ingest_improved.py', 'r', encoding='utf-8') as f:
            content = f.read()
            match = re.search(r'batch_size\s*=\s*(\d+)', content)
            if match:
                return int(match.group(1))
    except Exception as e:
        print(f"Error leyendo batch_size: {e}")
    return None

def update_batch_size(new_size):
    """Actualiza el batch_size"""
    try:
        with open('ingest_improved.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        new_content = re.sub(
            r'batch_size\s*=\s*\d+',
            f'batch_size = {new_size}',
            content
        )
        
        with open('ingest_improved.py', 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        return True
    except Exception as e:
        print(f"Error actualizando batch_size: {e}")
        return False

def get_ingest_processes():
    """Obtiene todos los procesos de ingest"""
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

def get_ingest_process():
    """Obtiene el primer proceso de ingest (para compatibilidad)"""
    processes = get_ingest_processes()
    return processes[0] if processes else None

def restart_ingest():
    """Detiene TODOS los procesos de ingest y reinicia uno limpio"""
    print("\n" + "="*80)
    print("REINICIANDO PROCESO DE INGEST...")
    print("="*80)
    
    # Detener TODOS los procesos de ingest (evitar duplicados)
    ingest_processes = get_ingest_processes()
    if ingest_processes:
        print(f"   Deteniendo {len(ingest_processes)} proceso(s) de ingest...")
        for proc in ingest_processes:
            try:
                proc.terminate()
                proc.wait(timeout=3)
                print(f"      ✓ Proceso {proc.pid} detenido")
            except (psutil.NoSuchProcess, psutil.TimeoutExpired):
                try:
                    proc.kill()
                    print(f"      ✓ Proceso {proc.pid} forzado a cerrar")
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
        print("   ✓ Proceso reiniciado (un solo proceso limpio)")
        time.sleep(3)
        return True
    except Exception as e:
        print(f"   ❌ Error reiniciando: {e}")
        return False

def main():
    print("=" * 80)
    print("MONITOR INTELIGENTE DE INGESTION")
    print("=" * 80)
    print(f"Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nEste monitor ajusta automaticamente el batch_size segun el progreso")
    print("Presiona Ctrl+C para detener\n")
    
    # Valores iniciales
    last_indexed_count = get_indexed_count()
    total_files = get_total_files()
    current_batch = get_current_batch_size() or 10
    no_progress_count = 0
    check_interval = 60  # Verificar cada 60 segundos
    last_check_time = time.time()
    
    # Historial de ajustes
    adjustment_history = []
    min_batch = 5  # Minimo muy bajo para poder bajar si es necesario
    max_batch = 2000  # Maximo alto pero subiremos poco a poco
    
    print(f"Configuracion inicial:")
    print(f"   Total de archivos: {total_files}")
    print(f"   Archivos indexados: {last_indexed_count}")
    print(f"   batch_size actual: {current_batch}")
    print(f"   Rango de batch_size: {min_batch} - {max_batch}")
    print("\n" + "="*80 + "\n")
    
    try:
        while True:
            current_time = time.time()
            elapsed = current_time - last_check_time
            
            # Obtener estado actual
            indexed_count = get_indexed_count()
            ingest_processes = get_ingest_processes()
            ingest_proc = ingest_processes[0] if ingest_processes else None
            
            # Verificar procesos duplicados
            if len(ingest_processes) > 1:
                print(f"\n   ⚠️  ADVERTENCIA: Se detectaron {len(ingest_processes)} procesos de ingest corriendo!")
                print(f"   Esto puede causar conflictos. Deteniendo todos y reiniciando...")
                for proc in ingest_processes:
                    try:
                        proc.terminate()
                        proc.wait(timeout=3)
                        print(f"      ✓ Proceso {proc.pid} detenido")
                    except (psutil.NoSuchProcess, psutil.TimeoutExpired):
                        try:
                            proc.kill()
                        except:
                            pass
                
                time.sleep(3)
                restart_ingest()
                ingest_proc = get_ingest_process()
                time.sleep(5)  # Esperar más tiempo después de reiniciar
                continue
            
            if indexed_count is None:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Error obteniendo conteo, reintentando...")
                time.sleep(check_interval)
                continue
            
            # Verificar si hay progreso
            if indexed_count > last_indexed_count:
                # ¡Hay progreso!
                progress = indexed_count - last_indexed_count
                no_progress_count = 0
                print(f"[{datetime.now().strftime('%H:%M:%S')}] PROGRESO DETECTADO!")
                print(f"   Archivos indexados: {last_indexed_count} -> {indexed_count} (+{progress})")
                if total_files:
                    percentage = (indexed_count / total_files) * 100
                    remaining = total_files - indexed_count
                    print(f"   Progreso total: {indexed_count}/{total_files} ({percentage:.1f}%)")
                    print(f"   Pendientes: {remaining}")
                
                # Si hay buen progreso, aumentar POCO A POCO
                if progress >= 5:  # Con solo 5 archivos de progreso, considerar aumentar
                    # Aumentar gradualmente: +10 si está bajo, +50 si está medio, +100 si está alto
                    if current_batch < 50:
                        increment = 10
                    elif current_batch < 200:
                        increment = 25
                    elif current_batch < 500:
                        increment = 50
                    else:
                        increment = 100
                    
                    new_batch = min(current_batch + increment, max_batch)
                    if new_batch != current_batch:
                        print(f"\n   Buen progreso detectado (+{progress} archivos)")
                        print(f"   Aumentando batch_size gradualmente: {current_batch} -> {new_batch} (+{increment})")
                        if update_batch_size(new_batch):
                            current_batch = new_batch
                            adjustment_history.append(('increase', new_batch, datetime.now()))
                            restart_ingest()
                            time.sleep(10)  # Esperar más tiempo después de reiniciar
                
                last_indexed_count = indexed_count
                
            elif indexed_count == last_indexed_count:
                # No hay progreso
                no_progress_count += 1
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Sin progreso ({no_progress_count} checks)")
                
                # Verificar si el proceso está corriendo
                if not ingest_proc:
                    print("   ⚠️  ADVERTENCIA: No se detecta proceso de ingest corriendo")
                    print("   El proceso se detuvo. Reiniciando...")
                    restart_ingest()
                    ingest_proc = get_ingest_process()
                    no_progress_count = 0  # Reset contador después de reiniciar
                    time.sleep(10)
                    continue
                
                # Verificar si el proceso terminó o está zombie
                try:
                    if ingest_proc.status() in ['zombie', 'stopped']:
                        print("   ⚠️  Proceso en estado anormal, reiniciando...")
                        restart_ingest()
                        ingest_proc = get_ingest_process()
                        no_progress_count = 0
                        time.sleep(10)
                        continue
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    print("   ⚠️  Proceso ya no existe, reiniciando...")
                    restart_ingest()
                    ingest_proc = get_ingest_process()
                    no_progress_count = 0
                    time.sleep(10)
                    continue
                
                # Verificar estado del proceso
                try:
                    proc_status = ingest_proc.status()
                    cpu = ingest_proc.cpu_percent(interval=0.5)
                    mem_mb = ingest_proc.memory_info().rss / (1024**2)
                    
                    print(f"   Proceso: {proc_status} | CPU: {cpu:.1f}% | Mem: {mem_mb:.1f} MB")
                    
                    # Si el proceso está corriendo pero sin progreso por mucho tiempo
                    if no_progress_count >= 3:  # 3 checks sin progreso (3 minutos)
                        print(f"\n   ADVERTENCIA: Sin progreso por {no_progress_count} checks")
                        
                        if current_batch > min_batch:
                            # Reducir batch_size POCO A POCO
                            # Reducir gradualmente: -5 si está bajo, -25 si está medio, -50 si está alto
                            if current_batch <= 50:
                                decrement = 5
                            elif current_batch <= 200:
                                decrement = 15
                            elif current_batch <= 500:
                                decrement = 25
                            else:
                                decrement = 50
                            
                            new_batch = max(current_batch - decrement, min_batch)
                            print(f"   Sin progreso por {no_progress_count} checks")
                            print(f"   Reduciendo batch_size gradualmente: {current_batch} -> {new_batch} (-{decrement})")
                            if update_batch_size(new_batch):
                                current_batch = new_batch
                                adjustment_history.append(('decrease', new_batch, datetime.now()))
                                restart_ingest()
                                no_progress_count = 0  # Reset contador
                                time.sleep(10)
                        else:
                            print(f"   batch_size ya en minimo ({min_batch}), verificando proceso...")
                            # Si ya está en mínimo y no hay progreso, puede ser otro problema
                            if cpu < 5 and proc_status == 'running':
                                print("   Proceso parece estar bloqueado, reiniciando...")
                                restart_ingest()
                                time.sleep(10)
                    
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    print("   Proceso terminado, reiniciando...")
                    restart_ingest()
                    time.sleep(10)
            
            # Mostrar historial de ajustes recientes
            if adjustment_history:
                print(f"\n   Historial de ajustes (ultimos 3):")
                for adj_type, batch, adj_time in adjustment_history[-3:]:
                    print(f"      {adj_time.strftime('%H:%M:%S')}: {adj_type} -> batch_size = {batch}")
            
            print(f"\n   Proxima verificacion en {check_interval} segundos...")
            print("="*80 + "\n")
            
            last_check_time = current_time
            time.sleep(check_interval)
            
    except KeyboardInterrupt:
        print("\n\n" + "="*80)
        print("MONITOR DETENIDO POR EL USUARIO")
        print("="*80)
        final_count = get_indexed_count()
        if final_count is not None:
            print(f"\nEstado final:")
            print(f"   Archivos indexados: {final_count}/{total_files}")
            if total_files:
                percentage = (final_count / total_files) * 100
                print(f"   Progreso: {percentage:.1f}%")
            print(f"   batch_size final: {current_batch}")
        
        if adjustment_history:
            print(f"\nHistorial completo de ajustes:")
            for adj_type, batch, adj_time in adjustment_history:
                print(f"   {adj_time.strftime('%Y-%m-%d %H:%M:%S')}: {adj_type} -> {batch}")

if __name__ == "__main__":
    main()

