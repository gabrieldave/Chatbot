"""
📊 CÁLCULO REAL: IMPACTO DE 10,000 RPM EN OPENAI
================================================

Calcula con números reales:
- Velocidad actual
- Requests por minuto actuales
- Impacto de aumentar a 10,000 RPM
"""

import os
import sys
import time
import re
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

def get_total_chunks():
    """Obtiene el número total de chunks indexados"""
    try:
        conn = psycopg2.connect(postgres_connection_string, connect_timeout=10)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SET statement_timeout = '15s'")
        
        cur.execute(f"""
            SELECT COUNT(*) as count
            FROM vecs.{config.VECTOR_COLLECTION_NAME}
        """)
        result = cur.fetchone()
        cur.close()
        conn.close()
        return result['count'] if result else 0
    except Exception as e:
        return None

def get_current_batch_size():
    """Lee el batch_size actual"""
    try:
        with open('ingest_improved.py', 'r', encoding='utf-8') as f:
            content = f.read()
            match = re.search(r'batch_size\s*=\s*(\d+)', content)
            if match:
                return int(match.group(1))
    except:
        pass
    return None

def get_total_files():
    """Cuenta archivos en ./data"""
    total = 0
    data_dir = './data'
    if os.path.exists(data_dir):
        for root, dirs, files in os.walk(data_dir):
            for file in files:
                if file.lower().endswith(('.pdf', '.epub', '.txt', '.docx', '.md')):
                    total += 1
    return total

def main():
    print("=" * 80)
    print("📊 CÁLCULO REAL: IMPACTO DE 10,000 RPM EN OPENAI")
    print("=" * 80)
    print()
    
    # Obtener datos actuales
    print("📊 Obteniendo datos actuales...")
    indexed_count = get_indexed_count()
    total_chunks = get_total_chunks()
    total_files = get_total_files()
    current_batch = get_current_batch_size() or 60
    
    if indexed_count is None:
        print("❌ Error: No se pudo obtener el conteo de archivos indexados")
        return
    
    print(f"   ✅ Archivos indexados: {indexed_count}")
    print(f"   ✅ Chunks totales: {total_chunks:,}")
    print(f"   ✅ Total de archivos: {total_files}")
    print(f"   ✅ batch_size actual: {current_batch}")
    print()
    
    # Calcular chunks por archivo promedio
    if indexed_count > 0:
        chunks_per_file_avg = total_chunks / indexed_count
    else:
        chunks_per_file_avg = 100  # Estimación conservadora
    
    print("=" * 80)
    print("📈 ANÁLISIS DE REQUESTS A OPENAI")
    print("=" * 80)
    print()
    
    print(f"📊 DATOS REALES OBSERVADOS:")
    print(f"   Chunks por archivo (promedio): {chunks_per_file_avg:.1f}")
    print(f"   batch_size actual: {current_batch}")
    print()
    
    # Calcular requests por batch
    requests_per_batch = current_batch * chunks_per_file_avg
    print(f"📦 REQUESTS POR BATCH:")
    print(f"   {current_batch} archivos × {chunks_per_file_avg:.1f} chunks/archivo = {requests_per_batch:.0f} requests")
    print()
    
    # Calcular tiempo por batch con diferentes límites de RPM
    print("⏱️  TIEMPO POR BATCH (según límite de RPM):")
    print()
    
    rpm_scenarios = [
        (3500, "Límite actual (tier básico)"),
        (10000, "Límite propuesto (tier superior)"),
    ]
    
    results = []
    for rpm_limit, description in rpm_scenarios:
        # Tiempo mínimo para procesar un batch (sin esperas)
        time_per_batch_minutes = requests_per_batch / rpm_limit
        time_per_batch_seconds = time_per_batch_minutes * 60
        
        # Archivos por hora teóricos
        files_per_hour = (current_batch * 60) / time_per_batch_minutes if time_per_batch_minutes > 0 else 0
        
        results.append({
            'rpm': rpm_limit,
            'description': description,
            'time_per_batch_min': time_per_batch_minutes,
            'time_per_batch_sec': time_per_batch_seconds,
            'files_per_hour': files_per_hour
        })
        
        print(f"   {description}:")
        print(f"      • Requests por batch: {requests_per_batch:.0f}")
        print(f"      • Límite RPM: {rpm_limit:,}")
        print(f"      • Tiempo mínimo por batch: {time_per_batch_minutes:.2f} min ({time_per_batch_seconds:.1f} seg)")
        print(f"      • Velocidad teórica máxima: {files_per_hour:.0f} archivos/hora")
        print()
    
    # Comparar velocidades
    current_rpm = results[0]
    proposed_rpm = results[1]
    
    speed_improvement = proposed_rpm['files_per_hour'] / current_rpm['files_per_hour'] if current_rpm['files_per_hour'] > 0 else 0
    time_reduction = (1 - (proposed_rpm['time_per_batch_min'] / current_rpm['time_per_batch_min'])) * 100 if current_rpm['time_per_batch_min'] > 0 else 0
    
    print("=" * 80)
    print("🔍 COMPARACIÓN: 3,500 RPM vs 10,000 RPM")
    print("=" * 80)
    print()
    
    print(f"📊 MEJORA TEÓRICA:")
    print(f"   Velocidad actual (3,500 RPM): {current_rpm['files_per_hour']:.0f} archivos/hora")
    print(f"   Velocidad con 10,000 RPM: {proposed_rpm['files_per_hour']:.0f} archivos/hora")
    print(f"   Mejora: {speed_improvement:.2f}x más rápido ({speed_improvement*100:.0f}% más rápido)")
    print()
    print(f"⏱️  REDUCCIÓN DE TIEMPO POR BATCH:")
    print(f"   Tiempo actual: {current_rpm['time_per_batch_min']:.2f} minutos")
    print(f"   Tiempo con 10,000 RPM: {proposed_rpm['time_per_batch_min']:.2f} minutos")
    print(f"   Reducción: {time_reduction:.1f}% más rápido")
    print()
    
    # Calcular tiempo total restante
    remaining_files = total_files - indexed_count
    if remaining_files > 0:
        print("=" * 80)
        print("⏱️  TIEMPO TOTAL RESTANTE ESTIMADO")
        print("=" * 80)
        print()
        
        # Con velocidad actual (3,500 RPM)
        hours_current = remaining_files / current_rpm['files_per_hour'] if current_rpm['files_per_hour'] > 0 else 0
        minutes_current = (hours_current - int(hours_current)) * 60
        
        # Con velocidad propuesta (10,000 RPM)
        hours_proposed = remaining_files / proposed_rpm['files_per_hour'] if proposed_rpm['files_per_hour'] > 0 else 0
        minutes_proposed = (hours_proposed - int(hours_proposed)) * 60
        
        # Ahorro de tiempo
        time_saved_hours = hours_current - hours_proposed
        time_saved_minutes = (time_saved_hours - int(time_saved_hours)) * 60
        
        print(f"📊 Archivos restantes: {remaining_files:,}")
        print()
        print(f"⏱️  Con 3,500 RPM (actual):")
        print(f"   Tiempo restante: {int(hours_current)}h {int(minutes_current)}m")
        print()
        print(f"⏱️  Con 10,000 RPM (propuesto):")
        print(f"   Tiempo restante: {int(hours_proposed)}h {int(minutes_proposed)}m")
        print()
        print(f"💾 Ahorro de tiempo:")
        print(f"   {int(time_saved_hours)}h {int(time_saved_minutes)}m menos")
        print(f"   ({time_saved_hours/hours_current*100:.1f}% más rápido)" if hours_current > 0 else "")
        print()
    
    # Verificar si estamos limitados por RPM actualmente
    print("=" * 80)
    print("🔍 ANÁLISIS: ¿ESTAMOS LIMITADOS POR RPM?")
    print("=" * 80)
    print()
    
    # Obtener velocidad real observada (necesitamos medir en tiempo real)
    print("📊 Para determinar si estamos limitados por RPM, necesitamos medir la velocidad real...")
    print("   Esperando 30 segundos para medir velocidad actual...")
    print()
    
    start_count = indexed_count
    start_time = time.time()
    time.sleep(30)
    end_count = get_indexed_count()
    end_time = time.time()
    
    if end_count and end_count > start_count:
        elapsed_minutes = (end_time - start_time) / 60
        files_processed = end_count - start_count
        real_files_per_minute = files_processed / elapsed_minutes
        real_files_per_hour = real_files_per_minute * 60
        
        print(f"✅ VELOCIDAD REAL OBSERVADA (últimos 30 segundos):")
        print(f"   Archivos procesados: {files_processed}")
        print(f"   Tiempo: {elapsed_minutes:.2f} minutos")
        print(f"   Velocidad: {real_files_per_minute:.2f} archivos/minuto")
        print(f"   Velocidad: {real_files_per_hour:.0f} archivos/hora")
        print()
        
        # Comparar con teórico
        theoretical_max = current_rpm['files_per_hour']
        efficiency = (real_files_per_hour / theoretical_max * 100) if theoretical_max > 0 else 0
        
        print(f"📊 COMPARACIÓN CON TEÓRICO:")
        print(f"   Velocidad real: {real_files_per_hour:.0f} archivos/hora")
        print(f"   Velocidad teórica máxima (3,500 RPM): {theoretical_max:.0f} archivos/hora")
        print(f"   Eficiencia: {efficiency:.1f}%")
        print()
        
        if efficiency > 90:
            print("   ⚠️  Estamos cerca del límite teórico de 3,500 RPM")
            print("   ✅ Aumentar a 10,000 RPM SÍ haría diferencia significativa")
        elif efficiency > 70:
            print("   ⚠️  Estamos usando bastante del límite de 3,500 RPM")
            print("   ✅ Aumentar a 10,000 RPM haría diferencia moderada")
        elif efficiency > 50:
            print("   ⚠️  Estamos usando parte del límite de 3,500 RPM")
            print("   ⚠️  Aumentar a 10,000 RPM haría diferencia, pero no es crítica")
        else:
            print("   ✅ No estamos limitados por RPM actualmente")
            print("   ⚠️  Aumentar a 10,000 RPM no haría mucha diferencia")
        
        print()
        
        # Calcular velocidad esperada con 10,000 RPM
        if efficiency > 50:  # Si estamos usando más del 50% del límite
            expected_with_10k = real_files_per_hour * (10000 / 3500)
            print(f"📈 VELOCIDAD ESPERADA CON 10,000 RPM:")
            print(f"   Basado en velocidad real actual: {expected_with_10k:.0f} archivos/hora")
            print(f"   Mejora esperada: {expected_with_10k / real_files_per_hour:.2f}x más rápido")
            print()
            
            # Tiempo restante con velocidad esperada
            if remaining_files > 0:
                hours_with_10k = remaining_files / expected_with_10k
                minutes_with_10k = (hours_with_10k - int(hours_with_10k)) * 60
                print(f"⏱️  Tiempo restante con 10,000 RPM (estimado real):")
                print(f"   {int(hours_with_10k)}h {int(minutes_with_10k)}m")
                print()
    else:
        print("   ⚠️  No se detectó progreso en los últimos 30 segundos")
        print("   Esto puede indicar que el proceso está pausado o hay otro cuello de botella")
        print()
    
    print("=" * 80)
    print("💡 CONCLUSIÓN")
    print("=" * 80)
    print()
    
    if end_count and end_count > start_count:
        if efficiency > 70:
            print("✅ RECOMENDACIÓN: Aumentar a 10,000 RPM SÍ vale la pena")
            print(f"   • Estamos usando {efficiency:.1f}% del límite actual")
            print(f"   • Mejora esperada: {speed_improvement:.2f}x más rápido")
            print(f"   • Ahorro de tiempo: {int(time_saved_hours)}h {int(time_saved_minutes)}m")
        elif efficiency > 50:
            print("⚠️  RECOMENDACIÓN: Aumentar a 10,000 RPM puede ayudar")
            print(f"   • Estamos usando {efficiency:.1f}% del límite actual")
            print(f"   • Mejora esperada: {speed_improvement:.2f}x más rápido")
            print(f"   • Ahorro de tiempo: {int(time_saved_hours)}h {int(time_saved_minutes)}m")
        else:
            print("⚠️  RECOMENDACIÓN: Aumentar a 10,000 RPM no es crítico")
            print(f"   • Estamos usando {efficiency:.1f}% del límite actual")
            print(f"   • El cuello de botella no es el límite de RPM")
    else:
        print("⚠️  No se pudo determinar la eficiencia actual")
        print("   Revisa si el proceso está corriendo correctamente")
    
    print()

if __name__ == "__main__":
    main()




