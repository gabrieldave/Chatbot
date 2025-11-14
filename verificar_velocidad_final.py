"""
⏱️  VERIFICACIÓN DE VELOCIDAD DESPUÉS DE UNOS MINUTOS
======================================================

Espera unos minutos y luego verifica la velocidad para sacar conclusiones
"""

import os
import sys
import time
import psutil
from urllib.parse import quote_plus
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
import config
from datetime import datetime

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

def get_indexed_count():
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

def get_ingest_process_uptime():
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
        try:
            if proc.info['name'] == 'python.exe' and proc.info['cmdline']:
                cmdline = ' '.join(proc.info['cmdline'])
                if 'ingest_improved.py' in cmdline.lower():
                    return (time.time() - proc.info['create_time'])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return 0

def get_current_batch_size():
    try:
        with open('ingest_improved.py', 'r', encoding='utf-8') as f:
            import re
            content = f.read()
            match = re.search(r'batch_size\s*=\s*(\d+)', content)
            if match:
                return int(match.group(1))
    except:
        pass
    return None

print("=" * 80)
print("⏱️  VERIFICACIÓN DE VELOCIDAD - ESPERANDO 5 MINUTOS")
print("=" * 80)
print(f"Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("\n📊 Obteniendo medición inicial...")

# Medición inicial
initial_count = get_indexed_count()
initial_uptime = get_ingest_process_uptime()
initial_time = time.time()

if initial_count is None:
    print("❌ No se pudo obtener el conteo inicial")
    sys.exit(1)

print(f"   Archivos indexados iniciales: {initial_count}")
print(f"   Tiempo de ejecución inicial: {int(initial_uptime//60)}m {int(initial_uptime%60)}s")

print(f"\n⏳ Esperando 5 minutos para obtener una medición precisa...")
print(f"   (Presiona Ctrl+C para cancelar)")

# Esperar 5 minutos (300 segundos)
wait_time = 300
elapsed = 0
while elapsed < wait_time:
    remaining = wait_time - elapsed
    minutes = int(remaining // 60)
    seconds = int(remaining % 60)
    print(f"\r   Tiempo restante: {minutes}m {seconds}s", end='', flush=True)
    time.sleep(10)
    elapsed += 10

print(f"\n\n✅ Tiempo de espera completado")
print(f"Obteniendo medición final...")

# Medición final
final_count = get_indexed_count()
final_uptime = get_ingest_process_uptime()
final_time = time.time()

if final_count is None:
    print("❌ No se pudo obtener el conteo final")
    sys.exit(1)

# Calcular velocidad
elapsed_time = final_time - initial_time
files_processed = final_count - initial_count

print(f"\n" + "=" * 80)
print("📊 RESULTADOS DE LA MEDICIÓN")
print("=" * 80)

print(f"\n📊 DATOS:")
print(f"   Medición inicial: {initial_count} archivos (a las {datetime.fromtimestamp(initial_time).strftime('%H:%M:%S')})")
print(f"   Medición final: {final_count} archivos (a las {datetime.fromtimestamp(final_time).strftime('%H:%M:%S')})")
print(f"   Archivos procesados: {files_processed}")
print(f"   Tiempo transcurrido: {int(elapsed_time//60)}m {int(elapsed_time%60)}s")

if elapsed_time > 0 and files_processed > 0:
    files_per_second = files_processed / elapsed_time
    files_per_minute = files_per_second * 60
    files_per_hour = files_per_second * 3600
    
    print(f"\n⚡ VELOCIDAD MEDIDA:")
    print(f"   {files_per_hour:.1f} archivos/hora")
    print(f"   {files_per_minute:.2f} archivos/minuto")
    print(f"   {files_per_second:.4f} archivos/segundo")
    
    # Comparación con velocidades anteriores
    print(f"\n" + "=" * 80)
    print("📈 COMPARACIÓN CON VELOCIDADES ANTERIORES")
    print("=" * 80)
    
    speed_batch_15 = 900  # Teórico
    speed_batch_80 = 1384  # Observado anteriormente
    speed_batch_150_initial = 3288.7  # Primera medición
    
    current_batch = get_current_batch_size()
    
    print(f"\n📊 HISTORIAL DE VELOCIDADES:")
    print(f"   batch_size=15 (teórico): ~{speed_batch_15} archivos/hora")
    print(f"   batch_size=80 (observado): ~{speed_batch_80} archivos/hora")
    print(f"   batch_size={current_batch} (primera medición): ~{speed_batch_150_initial:.0f} archivos/hora")
    print(f"   batch_size={current_batch} (medición actual): ~{files_per_hour:.0f} archivos/hora")
    
    print(f"\n📈 MEJORAS:")
    improvement_vs_15 = files_per_hour / speed_batch_15
    improvement_vs_80 = files_per_hour / speed_batch_80
    change_from_initial = (files_per_hour / speed_batch_150_initial) * 100
    
    print(f"   vs batch_size=15: {improvement_vs_15:.2f}x más rápido")
    print(f"   vs batch_size=80: {improvement_vs_80:.2f}x más rápido")
    print(f"   vs primera medición: {change_from_initial:.1f}%")
    
    # Conclusiones
    print(f"\n" + "=" * 80)
    print("🎯 CONCLUSIONES")
    print("=" * 80)
    
    if files_per_hour >= speed_batch_80 * 1.5:
        print(f"\n✅ CONCLUSIÓN PRINCIPAL:")
        print(f"   El batch_size={current_batch} ESTÁ funcionando EXCELENTEMENTE")
        print(f"   Velocidad: {files_per_hour:.0f} archivos/hora")
        print(f"   Mejora vs batch_size=80: {improvement_vs_80:.2f}x más rápido")
        print(f"\n💡 INTERPRETACIÓN:")
        print(f"   • El aumento de batch_size de 80 a {current_batch} mejoró significativamente la velocidad")
        print(f"   • Los recursos de Supabase están siendo aprovechados eficientemente")
        print(f"   • El proceso está optimizado y funcionando bien")
        
        if change_from_initial >= 90 and change_from_initial <= 110:
            print(f"\n✅ ESTABILIDAD:")
            print(f"   La velocidad se mantiene estable ({change_from_initial:.1f}% de la primera medición)")
            print(f"   El batch_size={current_batch} es consistente y confiable")
        elif change_from_initial > 110:
            print(f"\n🚀 MEJORA CONTINUA:")
            print(f"   La velocidad mejoró aún más ({change_from_initial:.1f}% de la primera medición)")
            print(f"   El proceso se está optimizando con el tiempo")
        else:
            print(f"\n⚠️  VELOCIDAD VARIABLE:")
            print(f"   La velocidad cambió ({change_from_initial:.1f}% de la primera medición)")
            print(f"   Puede ser normal debido a variaciones en tamaño de archivos")
            
    elif files_per_hour >= speed_batch_80 * 1.1:
        print(f"\n✅ CONCLUSIÓN PRINCIPAL:")
        print(f"   El batch_size={current_batch} está funcionando BIEN")
        print(f"   Velocidad: {files_per_hour:.0f} archivos/hora")
        print(f"   Mejora vs batch_size=80: {improvement_vs_80:.2f}x más rápido")
        print(f"\n💡 INTERPRETACIÓN:")
        print(f"   • Hay mejora, pero no tan dramática como esperábamos")
        print(f"   • Puede haber un cuello de botella en otro lugar")
        print(f"   • El batch_size={current_batch} es adecuado pero no óptimo")
        
    else:
        print(f"\n⚠️  CONCLUSIÓN PRINCIPAL:")
        print(f"   El batch_size={current_batch} NO está mejorando significativamente")
        print(f"   Velocidad: {files_per_hour:.0f} archivos/hora")
        print(f"   Similar a batch_size=80: ~{speed_batch_80} archivos/hora")
        print(f"\n💡 INTERPRETACIÓN:")
        print(f"   • El cuello de botella no está en el batch_size")
        print(f"   • Puede estar en:")
        print(f"     - API de embeddings (OpenAI)")
        print(f"     - Procesamiento de archivos grandes")
        print(f"     - Límites de Supabase en inserciones")
        print(f"   • Considera reducir batch_size a 100-120 para balance")
    
    # Tiempo restante
    total_files = 1218  # Aproximado
    remaining_files = total_files - final_count
    if files_per_hour > 0:
        remaining_hours = remaining_files / files_per_hour
        remaining_minutes = int(remaining_hours * 60)
        print(f"\n⏱️  TIEMPO RESTANTE ESTIMADO:")
        print(f"   Archivos pendientes: {remaining_files}")
        print(f"   Tiempo estimado: ~{int(remaining_hours)}h {remaining_minutes%60}m")
    
    print(f"\n📋 RECOMENDACIÓN FINAL:")
    if files_per_hour >= speed_batch_80 * 1.5:
        print(f"   ✅ MANTENER batch_size={current_batch}")
        print(f"   ✅ El proceso está optimizado y funcionando excelentemente")
    elif files_per_hour >= speed_batch_80 * 1.1:
        print(f"   ✅ MANTENER batch_size={current_batch} o reducir ligeramente a 120-130")
        print(f"   ⚠️  Monitorear recursos de Supabase")
    else:
        print(f"   ⚠️  REDUCIR batch_size a 100-120")
        print(f"   ⚠️  El batch_size actual no está mejorando la velocidad")
    
else:
    print(f"\n⚠️  No se procesaron archivos en este período")
    print(f"   Esto puede indicar que el proceso está:")
    print(f"   • En fase de carga inicial")
    print(f"   • Procesando archivos muy grandes")
    print(f"   • Esperando recursos")

print("\n" + "=" * 80)
print(f"Fin del análisis: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)




