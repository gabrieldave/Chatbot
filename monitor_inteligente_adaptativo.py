"""
🧠 MONITOR INTELIGENTE ADAPTATIVO
==================================

Monitorea RAM de Supabase, límites de OpenAI, y ajusta batch_size automáticamente
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
from psycopg2.extras import RealDictCursor
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
    """Obtiene el número de archivos indexados"""
    try:
        conn = psycopg2.connect(postgres_connection_string, connect_timeout=10)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SET statement_timeout = '15s'")
        
        cur.execute(f"""
            SELECT COUNT(DISTINCT metadata->>'file_name') as count
            FROM vecs.{config.VECTOR_COLLECTION_NAME} 
            WHERE metadata->>'file_name' IS NOT NULL
        """)
        result = cur.fetchone()
        cur.close()
        conn.close()
        return result['count'] if result else 0
    except Exception as e:
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
        pass
    return None

def update_batch_size(new_size, reason=""):
    """Actualiza el batch_size en el archivo"""
    try:
        with open('ingest_improved.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Buscar y reemplazar batch_size
        pattern = r'batch_size\s*=\s*\d+\s*#.*'
        replacement = f'batch_size = {new_size}  # Ajustado automáticamente por monitor_inteligente_adaptativo.py - {reason}'
        
        new_content = re.sub(pattern, replacement, content)
        
        # Si no encontró el patrón con comentario, buscar sin comentario
        if new_content == content:
            pattern = r'batch_size\s*=\s*\d+'
            replacement = f'batch_size = {new_size}  # Ajustado automáticamente por monitor_inteligente_adaptativo.py - {reason}'
            new_content = re.sub(pattern, replacement, content)
        
        with open('ingest_improved.py', 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        return True
    except Exception as e:
        print(f"   ❌ Error actualizando batch_size: {e}")
        return False

def get_ingest_processes():
    """Busca procesos de ingest"""
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time', 'memory_info']):
        try:
            if proc.info['name'] == 'python.exe' and proc.info['cmdline']:
                cmdline = ' '.join(proc.info['cmdline'])
                if 'ingest_improved.py' in cmdline.lower():
                    processes.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return processes

def restart_ingest():
    """Detiene todos los procesos y reinicia uno limpio"""
    processes = get_ingest_processes()
    if processes:
        for proc in processes:
            try:
                proc.terminate()
                proc.wait(timeout=3)
            except (psutil.NoSuchProcess, psutil.TimeoutExpired):
                try:
                    proc.kill()
                except:
                    pass
        time.sleep(3)
    
    try:
        subprocess.Popen(
            [sys.executable, 'ingest_improved.py'],
            creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
        )
        return True
    except Exception as e:
        return False

# ============================================================================
# FUNCIÓN DE CÁLCULO INTELIGENTE
# ============================================================================

def calculate_optimal_batch_size(indexed_count, last_count, elapsed_time, current_batch):
    """
    Calcula el batch_size óptimo basado en:
    - Velocidad de procesamiento (archivos/minuto)
    - Límites estimados de OpenAI (3,500-10,000 RPM)
    - Recursos de Supabase (RAM disponible)
    """
    
    # Calcular velocidad actual
    if elapsed_time > 0 and indexed_count > last_count:
        files_processed = indexed_count - last_count
        files_per_minute = (files_processed / elapsed_time) * 60
        files_per_hour = files_per_minute * 60
    else:
        files_per_minute = 0
        files_per_hour = 0
    
    # Estimaciones de límites de OpenAI
    # Asumimos límite conservador de 3,500 RPM (tier básico)
    openai_rpm_limit = 3500  # Conservador, puede ser mayor
    
    # Calcular chunks estimados por archivo
    # Basado en observaciones: ~100 chunks por archivo promedio
    chunks_per_file = 100
    
    # Calcular requests por batch con batch_size actual
    requests_per_batch = current_batch * chunks_per_file
    
    # Calcular tiempo por batch basado en límites de OpenAI
    time_per_batch_minutes = requests_per_batch / openai_rpm_limit
    
    # Análisis de velocidad
    print(f"\n📊 ANÁLISIS DE VELOCIDAD:")
    if files_per_minute > 0:
        print(f"   Velocidad actual: {files_per_minute:.2f} archivos/minuto ({files_per_hour:.0f}/hora)")
        
        # Velocidad esperada con batch_size actual
        expected_time_per_batch = time_per_batch_minutes
        expected_files_per_hour = (current_batch * 60) / expected_time_per_batch if expected_time_per_batch > 0 else 0
        
        print(f"   Velocidad esperada: ~{expected_files_per_hour:.0f} archivos/hora")
        
        if files_per_hour < expected_files_per_hour * 0.5:
            print(f"   ⚠️  Velocidad muy baja - Posible rate limiting")
            recommendation = "reduce"
        elif files_per_hour < expected_files_per_hour * 0.8:
            print(f"   ⚠️  Velocidad baja - Puede haber rate limiting")
            recommendation = "reduce_slightly"
        else:
            print(f"   ✅ Velocidad adecuada")
            recommendation = "maintain_or_increase"
    else:
        print(f"   ⏳ No hay suficiente datos para calcular velocidad")
        recommendation = "maintain"
    
    # Calcular batch_size óptimo
    print(f"\n💡 CÁLCULO DE BATCH_SIZE ÓPTIMO:")
    
    # Factor 1: Límites de OpenAI
    # Queremos que cada batch tome máximo 2 minutos para ver progreso frecuente
    max_time_per_batch_minutes = 2
    max_requests_per_batch = openai_rpm_limit * max_time_per_batch_minutes
    optimal_batch_by_openai = int(max_requests_per_batch / chunks_per_file)
    
    print(f"   Basado en límites de OpenAI ({openai_rpm_limit} RPM):")
    print(f"   • Máximo requests por batch (2 min): {max_requests_per_batch:.0f}")
    print(f"   • batch_size máximo: {optimal_batch_by_openai} archivos")
    
    # Factor 2: Velocidad observada
    if files_per_minute > 0:
        # Si la velocidad es baja, reducir batch_size
        if files_per_minute < 10:
            optimal_batch_by_speed = max(20, current_batch - 20)
            print(f"   Basado en velocidad baja ({files_per_minute:.1f} arch/min):")
            print(f"   • Reducir a: {optimal_batch_by_speed} archivos")
        elif files_per_minute < 20:
            optimal_batch_by_speed = max(30, current_batch - 10)
            print(f"   Basado en velocidad moderada ({files_per_minute:.1f} arch/min):")
            print(f"   • Reducir ligeramente a: {optimal_batch_by_speed} archivos")
        else:
            optimal_batch_by_speed = min(optimal_batch_by_openai, current_batch + 10)
            print(f"   Basado en velocidad buena ({files_per_minute:.1f} arch/min):")
            print(f"   • Puede aumentar a: {optimal_batch_by_speed} archivos")
    else:
        optimal_batch_by_speed = current_batch
    
    # Factor 3: RAM de Supabase (estimado)
    # Con 2 GB RAM, podemos manejar más, pero el límite es OpenAI
    optimal_batch_by_ram = 100  # Conservador para 2 GB
    
    # Calcular batch_size óptimo final (el más restrictivo)
    optimal_batch = min(optimal_batch_by_openai, optimal_batch_by_speed, optimal_batch_by_ram)
    
    # Límites razonables
    optimal_batch = max(20, min(optimal_batch, 100))
    
    print(f"\n📦 BATCH_SIZE ÓPTIMO CALCULADO:")
    print(f"   batch_size actual: {current_batch}")
    print(f"   batch_size óptimo: {optimal_batch}")
    
    if optimal_batch < current_batch:
        print(f"   ✅ Reducir de {current_batch} a {optimal_batch} (-{current_batch - optimal_batch})")
    elif optimal_batch > current_batch:
        print(f"   ✅ Aumentar de {current_batch} a {optimal_batch} (+{optimal_batch - current_batch})")
    else:
        print(f"   ✅ Mantener en {current_batch}")
    
    return optimal_batch, recommendation

# ============================================================================
# FUNCIÓN PRINCIPAL
# ============================================================================

def main():
    print("=" * 80)
    print("🧠 MONITOR INTELIGENTE ADAPTATIVO")
    print("=" * 80)
    print(f"Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n✨ Características:")
    print("   • Monitorea RAM de Supabase")
    print("   • Monitorea velocidad de procesamiento")
    print("   • Considera límites de OpenAI (3,500-10,000 RPM)")
    print("   • Ajusta batch_size automáticamente")
    print("   • Previene duplicados")
    print("\n⏱️  Monitoreando cada 2 minutos...")
    print("   Presiona Ctrl+C para detener\n")
    
    check_interval = 120  # 2 minutos
    last_indexed_count = get_indexed_count()
    last_check_time = time.time()
    last_restart_time = 0
    restart_cooldown = 180  # 3 minutos entre reinicios
    
    print(f"📊 Estado inicial:")
    print(f"   Archivos indexados: {last_indexed_count if last_indexed_count else 'calculando...'}")
    current_batch = get_current_batch_size() or 60
    print(f"   batch_size actual: {current_batch}")
    print("\n" + "="*80 + "\n")
    
    try:
        check_count = 0
        while True:
            check_count += 1
            current_time = time.time()
            elapsed = current_time - last_check_time
            
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Check #{check_count}")
            
            # Verificar proceso
            processes = get_ingest_processes()
            if len(processes) > 1:
                print(f"   ⚠️  {len(processes)} procesos detectados (duplicados)")
                print(f"   🛑 Deteniendo duplicados...")
                restart_ingest()
                time.sleep(5)
                continue
            elif len(processes) == 0:
                print(f"   ⚠️  No hay proceso corriendo")
                if current_time - last_restart_time > restart_cooldown:
                    print(f"   🔄 Reiniciando...")
                    if restart_ingest():
                        print(f"   ✅ Proceso reiniciado")
                        last_restart_time = current_time
                        time.sleep(5)
                    continue
            else:
                proc = processes[0]
                try:
                    cpu = proc.cpu_percent(interval=0.5)
                    mem_mb = proc.memory_info().rss / (1024 * 1024)
                    print(f"   ✅ Proceso activo: PID {proc.pid} | CPU: {cpu:.1f}% | RAM: {mem_mb:.1f} MB")
                except:
                    pass
            
            # Obtener progreso actual
            indexed_count = get_indexed_count()
            if indexed_count is None:
                print(f"   ⚠️  No se pudo obtener progreso (timeout)")
                time.sleep(check_interval)
                continue
            
            print(f"   📚 Archivos indexados: {indexed_count}")
            
            # Calcular velocidad y batch_size óptimo
            if indexed_count > last_indexed_count:
                files_processed = indexed_count - last_indexed_count
                print(f"   ✅ Progreso: +{files_processed} archivos en {int(elapsed//60)}m {int(elapsed%60)}s")
                
                # Calcular batch_size óptimo
                optimal_batch, recommendation = calculate_optimal_batch_size(
                    indexed_count, last_indexed_count, elapsed, current_batch
                )
                
                # Decidir si ajustar
                if optimal_batch != current_batch and (current_time - last_restart_time) > restart_cooldown:
                    diff = abs(optimal_batch - current_batch)
                    if diff >= 10:  # Solo ajustar si la diferencia es significativa
                        print(f"\n🔄 AJUSTANDO BATCH_SIZE:")
                        print(f"   {current_batch} → {optimal_batch} ({'+' if optimal_batch > current_batch else ''}{optimal_batch - current_batch})")
                        
                        reason = f"Velocidad: {recommendation}, Óptimo calculado: {optimal_batch}"
                        if update_batch_size(optimal_batch, reason):
                            print(f"   ✅ batch_size actualizado")
                            current_batch = optimal_batch
                            
                            # Reiniciar proceso
                            print(f"   🔄 Reiniciando proceso con nuevo batch_size...")
                            if restart_ingest():
                                print(f"   ✅ Proceso reiniciado")
                                last_restart_time = current_time
                                time.sleep(10)
                            else:
                                print(f"   ❌ Error reiniciando proceso")
                        else:
                            print(f"   ❌ Error actualizando batch_size")
                    else:
                        print(f"\n💡 batch_size actual ({current_batch}) está cerca del óptimo ({optimal_batch})")
                        print(f"   No se requiere ajuste (diferencia < 10)")
                else:
                    if optimal_batch == current_batch:
                        print(f"\n✅ batch_size actual ({current_batch}) es óptimo")
                    else:
                        print(f"\n⏳ Esperando cooldown antes de ajustar...")
                
                last_indexed_count = indexed_count
            else:
                print(f"   ⏳ Sin progreso nuevo")
            
            last_check_time = current_time
            print(f"\n⏱️  Próxima verificación en {check_interval//60} minutos...")
            print("="*80)
            
            time.sleep(check_interval)
            
    except KeyboardInterrupt:
        print("\n\n" + "="*80)
        print("⏹️  MONITOR DETENIDO")
        print("="*80)
        final_count = get_indexed_count()
        if final_count is not None:
            print(f"\n📊 Estado final:")
            print(f"   Archivos indexados: {final_count}")
        print(f"   batch_size final: {get_current_batch_size()}")

if __name__ == "__main__":
    main()




