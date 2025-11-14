"""
📊 ANÁLISIS DETALLADO: IMPACTO REAL DE 10,000 RPM
==================================================

Análisis completo con datos reales y múltiples mediciones
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
    print("📊 ANÁLISIS DETALLADO: IMPACTO REAL DE 10,000 RPM")
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
        chunks_per_file_avg = 100
    
    print("=" * 80)
    print("📈 CÁLCULOS CON NÚMEROS REALES")
    print("=" * 80)
    print()
    
    print(f"📊 DATOS REALES:")
    print(f"   • Chunks por archivo (promedio): {chunks_per_file_avg:.1f}")
    print(f"   • batch_size actual: {current_batch}")
    print(f"   • Requests por batch: {current_batch * chunks_per_file_avg:.0f}")
    print()
    
    # Calcular con diferentes límites de RPM
    requests_per_batch = current_batch * chunks_per_file_avg
    
    print("=" * 80)
    print("⏱️  TIEMPO POR BATCH Y VELOCIDAD")
    print("=" * 80)
    print()
    
    scenarios = [
        (3500, "Límite actual (3,500 RPM)"),
        (10000, "Límite propuesto (10,000 RPM)"),
    ]
    
    results = {}
    for rpm_limit, description in scenarios:
        time_per_batch_min = requests_per_batch / rpm_limit
        time_per_batch_sec = time_per_batch_min * 60
        files_per_hour = (current_batch * 60) / time_per_batch_min if time_per_batch_min > 0 else 0
        
        results[rpm_limit] = {
            'time_per_batch_min': time_per_batch_min,
            'time_per_batch_sec': time_per_batch_sec,
            'files_per_hour': files_per_hour
        }
        
        print(f"{description}:")
        print(f"   • Tiempo por batch: {time_per_batch_min:.2f} min ({time_per_batch_sec:.1f} seg)")
        print(f"   • Velocidad teórica: {files_per_hour:.0f} archivos/hora")
        print()
    
    # Medir velocidad real con múltiples puntos
    print("=" * 80)
    print("🔍 MEDICIÓN DE VELOCIDAD REAL")
    print("=" * 80)
    print()
    print("📊 Midiendo velocidad en 3 intervalos de 1 minuto...")
    print()
    
    measurements = []
    for i in range(3):
        start_count = get_indexed_count()
        start_time = time.time()
        
        if i < 2:
            print(f"   Intervalo {i+1}/3: midiendo...")
            time.sleep(60)
        else:
            print(f"   Intervalo {i+1}/3: midiendo...")
            time.sleep(60)
        
        end_count = get_indexed_count()
        end_time = time.time()
        
        if end_count and start_count and end_count > start_count:
            elapsed_min = (end_time - start_time) / 60
            files_processed = end_count - start_count
            files_per_min = files_processed / elapsed_min
            files_per_hour = files_per_min * 60
            
            measurements.append({
                'files_processed': files_processed,
                'elapsed_min': elapsed_min,
                'files_per_min': files_per_min,
                'files_per_hour': files_per_hour
            })
            
            print(f"      ✅ {files_processed} archivos en {elapsed_min:.2f} min = {files_per_min:.2f} arch/min ({files_per_hour:.0f} arch/hora)")
        else:
            print(f"      ⚠️  Sin progreso en este intervalo")
    
    print()
    
    if measurements:
        # Calcular promedio
        avg_files_per_hour = sum(m['files_per_hour'] for m in measurements) / len(measurements)
        avg_files_per_min = sum(m['files_per_min'] for m in measurements) / len(measurements)
        
        print(f"📊 VELOCIDAD REAL PROMEDIO:")
        print(f"   {avg_files_per_min:.2f} archivos/minuto")
        print(f"   {avg_files_per_hour:.0f} archivos/hora")
        print()
        
        # Comparar con teórico
        theoretical_3500 = results[3500]['files_per_hour']
        theoretical_10000 = results[10000]['files_per_hour']
        
        efficiency_3500 = (avg_files_per_hour / theoretical_3500 * 100) if theoretical_3500 > 0 else 0
        efficiency_10000 = (avg_files_per_hour / theoretical_10000 * 100) if theoretical_10000 > 0 else 0
        
        print("=" * 80)
        print("📊 COMPARACIÓN: REAL vs TEÓRICO")
        print("=" * 80)
        print()
        
        print(f"Velocidad real observada: {avg_files_per_hour:.0f} archivos/hora")
        print()
        print(f"Con 3,500 RPM (actual):")
        print(f"   • Velocidad teórica máxima: {theoretical_3500:.0f} archivos/hora")
        print(f"   • Eficiencia: {efficiency_3500:.1f}% del límite")
        print()
        print(f"Con 10,000 RPM (propuesto):")
        print(f"   • Velocidad teórica máxima: {theoretical_10000:.0f} archivos/hora")
        print(f"   • Eficiencia: {efficiency_10000:.1f}% del límite")
        print()
        
        # Calcular mejora esperada
        if efficiency_3500 > 50:  # Si estamos usando más del 50% del límite
            # Estamos limitados por RPM, así que la mejora sería proporcional
            expected_improvement = (10000 / 3500)
            expected_speed_with_10k = avg_files_per_hour * expected_improvement
            speed_improvement_factor = expected_improvement
        else:
            # No estamos limitados por RPM, la mejora sería menor
            # Calcular cuánto podríamos mejorar si elimináramos el límite de RPM
            bottleneck_factor = efficiency_3500 / 100  # Factor de cuello de botella
            expected_improvement = 1 + (bottleneck_factor * (10000 / 3500 - 1))
            expected_speed_with_10k = avg_files_per_hour * expected_improvement
            speed_improvement_factor = expected_improvement
        
        print("=" * 80)
        print("💡 IMPACTO DE AUMENTAR A 10,000 RPM")
        print("=" * 80)
        print()
        
        if efficiency_3500 > 70:
            print("✅ CONCLUSIÓN: SÍ estamos limitados por RPM")
            print(f"   • Estamos usando {efficiency_3500:.1f}% del límite de 3,500 RPM")
            print(f"   • Aumentar a 10,000 RPM SÍ haría diferencia significativa")
            print()
            print(f"📈 MEJORA ESPERADA:")
            print(f"   • Velocidad actual: {avg_files_per_hour:.0f} archivos/hora")
            print(f"   • Velocidad esperada con 10,000 RPM: {expected_speed_with_10k:.0f} archivos/hora")
            print(f"   • Mejora: {speed_improvement_factor:.2f}x más rápido ({speed_improvement_factor*100:.0f}% más rápido)")
        elif efficiency_3500 > 50:
            print("⚠️  CONCLUSIÓN: Parcialmente limitados por RPM")
            print(f"   • Estamos usando {efficiency_3500:.1f}% del límite de 3,500 RPM")
            print(f"   • Aumentar a 10,000 RPM haría diferencia moderada")
            print()
            print(f"📈 MEJORA ESPERADA:")
            print(f"   • Velocidad actual: {avg_files_per_hour:.0f} archivos/hora")
            print(f"   • Velocidad esperada con 10,000 RPM: {expected_speed_with_10k:.0f} archivos/hora")
            print(f"   • Mejora: {speed_improvement_factor:.2f}x más rápido ({speed_improvement_factor*100:.0f}% más rápido)")
        else:
            print("⚠️  CONCLUSIÓN: NO estamos limitados por RPM")
            print(f"   • Estamos usando solo {efficiency_3500:.1f}% del límite de 3,500 RPM")
            print(f"   • El cuello de botella es otro factor (procesamiento, I/O, etc.)")
            print()
            print(f"📈 MEJORA ESPERADA (si elimináramos el límite de RPM):")
            print(f"   • Velocidad actual: {avg_files_per_hour:.0f} archivos/hora")
            print(f"   • Velocidad esperada con 10,000 RPM: {expected_speed_with_10k:.0f} archivos/hora")
            print(f"   • Mejora: {speed_improvement_factor:.2f}x más rápido")
            print()
            print("   ⚠️  NOTA: La mejora real podría ser menor porque hay otros cuellos de botella")
        
        print()
        
        # Calcular tiempo restante
        remaining_files = total_files - indexed_count
        if remaining_files > 0:
            print("=" * 80)
            print("⏱️  TIEMPO RESTANTE ESTIMADO")
            print("=" * 80)
            print()
            
            hours_current = remaining_files / avg_files_per_hour if avg_files_per_hour > 0 else 0
            hours_with_10k = remaining_files / expected_speed_with_10k if expected_speed_with_10k > 0 else 0
            
            time_saved = hours_current - hours_with_10k
            
            print(f"📊 Archivos restantes: {remaining_files:,}")
            print()
            print(f"⏱️  Con velocidad actual ({avg_files_per_hour:.0f} arch/hora):")
            print(f"   Tiempo restante: {int(hours_current)}h {int((hours_current - int(hours_current)) * 60)}m")
            print()
            print(f"⏱️  Con 10,000 RPM (estimado {expected_speed_with_10k:.0f} arch/hora):")
            print(f"   Tiempo restante: {int(hours_with_10k)}h {int((hours_with_10k - int(hours_with_10k)) * 60)}m")
            print()
            print(f"💾 Ahorro de tiempo: {int(time_saved)}h {int((time_saved - int(time_saved)) * 60)}m")
            print()
    else:
        print("⚠️  No se detectó progreso en las mediciones")
        print("   El proceso puede estar pausado o hay un problema")
        print()
    
    print("=" * 80)
    print("📋 RESUMEN FINAL")
    print("=" * 80)
    print()
    print(f"📊 DATOS REALES:")
    print(f"   • Chunks por archivo: {chunks_per_file_avg:.1f}")
    print(f"   • Requests por batch: {requests_per_batch:.0f}")
    print(f"   • batch_size: {current_batch}")
    print()
    print(f"⏱️  TIEMPO POR BATCH:")
    print(f"   • Con 3,500 RPM: {results[3500]['time_per_batch_min']:.2f} min")
    print(f"   • Con 10,000 RPM: {results[10000]['time_per_batch_min']:.2f} min")
    print(f"   • Reducción: {(1 - results[10000]['time_per_batch_min']/results[3500]['time_per_batch_min'])*100:.1f}%")
    print()
    if measurements:
        print(f"📈 VELOCIDAD REAL:")
        print(f"   • Observada: {avg_files_per_hour:.0f} archivos/hora")
        print(f"   • Eficiencia vs 3,500 RPM: {efficiency_3500:.1f}%")
        print()
        if efficiency_3500 > 50:
            print("✅ RECOMENDACIÓN: Aumentar a 10,000 RPM SÍ vale la pena")
        else:
            print("⚠️  RECOMENDACIÓN: Aumentar a 10,000 RPM no es crítico")
    print()

if __name__ == "__main__":
    main()




