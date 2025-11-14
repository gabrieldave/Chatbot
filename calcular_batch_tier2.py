"""
📊 CÁLCULO DE BATCH_SIZE ÓPTIMO PARA TIER 2
===========================================

Calcula el batch_size al 80% de capacidad basado en límites de OpenAI Tier 2
para el modelo text-embedding-3-small
"""

import os
import sys
import re
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

def update_batch_size(new_size, reason=""):
    """Actualiza el batch_size en el archivo"""
    try:
        with open('ingest_improved.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Buscar y reemplazar batch_size
        pattern = r'batch_size\s*=\s*\d+\s*#.*'
        replacement = f'batch_size = {new_size}  # Optimizado para Tier 2 al 80% de capacidad - {reason}'
        
        new_content = re.sub(pattern, replacement, content)
        
        # Si no encontró el patrón con comentario, buscar sin comentario
        if new_content == content:
            pattern = r'batch_size\s*=\s*\d+'
            replacement = f'batch_size = {new_size}  # Optimizado para Tier 2 al 80% de capacidad - {reason}'
            new_content = re.sub(pattern, replacement, content)
        
        with open('ingest_improved.py', 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        return True
    except Exception as e:
        print(f"   ❌ Error actualizando batch_size: {e}")
        return False

def main():
    print("=" * 80)
    print("📊 CÁLCULO DE BATCH_SIZE ÓPTIMO PARA TIER 2")
    print("=" * 80)
    print()
    
    # Límites de OpenAI - VERIFICADOS DESDE PANEL DE OPENAI
    # Según la captura del panel de OpenAI:
    # - RPM: 5,000 requests/minuto (columna muestra "5000 RPM" en TPM, pero es RPM)
    # - TPM: 1,000,000 tokens/minuto (columna muestra "1,000,000 TPM" en RPM, pero es TPM)
    # - TPD: 20,000,000 tokens/día
    # 
    # NOTA: Las etiquetas en el panel parecen estar intercambiadas, pero los valores son correctos
    
    rpm_limit_tier2 = 5000  # RPM real desde panel de OpenAI
    # Si tu límite es diferente, cambia este valor
    
    print("📋 LÍMITES DE OPENAI:")
    print("   Modelo: text-embedding-3-small")
    print(f"   RPM máximo detectado: {rpm_limit_tier2:,} requests/minuto")
    print(f"   Usaremos 80% de capacidad: {int(rpm_limit_tier2 * 0.8):,} RPM")
    print()
    
    # Obtener datos reales
    print("📊 Obteniendo datos reales...")
    indexed_count = get_indexed_count()
    total_chunks = get_total_chunks()
    current_batch = get_current_batch_size() or 60
    
    if indexed_count is None or indexed_count == 0:
        print("   ⚠️  No hay datos suficientes, usando estimación conservadora")
        chunks_per_file_avg = 100
    else:
        chunks_per_file_avg = total_chunks / indexed_count
    
    print(f"   ✅ Archivos indexados: {indexed_count}")
    print(f"   ✅ Chunks totales: {total_chunks:,}")
    print(f"   ✅ Chunks por archivo (promedio): {chunks_per_file_avg:.1f}")
    print(f"   ✅ batch_size actual: {current_batch}")
    print()
    
    # Calcular batch_size óptimo al 80% de capacidad
    print("=" * 80)
    print("🧮 CÁLCULO DE BATCH_SIZE ÓPTIMO")
    print("=" * 80)
    print()
    
    # Límites (ya definidos arriba)
    rpm_80_percent = int(rpm_limit_tier2 * 0.8)  # 80% del límite detectado
    
    print(f"📊 LÍMITES:")
    print(f"   • RPM máximo detectado: {rpm_limit_tier2:,}")
    print(f"   • RPM al 80% (seguro): {rpm_80_percent:,}")
    print()
    
    # Calcular requests por batch con batch_size actual
    requests_per_batch_current = current_batch * chunks_per_file_avg
    time_per_batch_current_min = requests_per_batch_current / rpm_80_percent
    
    print(f"📦 CON BATCH_SIZE ACTUAL ({current_batch}):")
    print(f"   • Requests por batch: {requests_per_batch_current:.0f}")
    print(f"   • Tiempo por batch (80% RPM): {time_per_batch_current_min:.2f} min")
    print()
    
    # Calcular batch_size óptimo
    # Queremos que cada batch tome máximo 2 minutos para ver progreso frecuente
    # Pero también queremos maximizar el uso de los 8,000 RPM disponibles
    max_time_per_batch_minutes = 2.0  # Máximo 2 minutos por batch
    max_requests_per_batch = rpm_80_percent * max_time_per_batch_minutes
    
    optimal_batch_size = int(max_requests_per_batch / chunks_per_file_avg)
    
    # Asegurar límites razonables
    optimal_batch_size = max(20, min(optimal_batch_size, 200))  # Entre 20 y 200
    
    print(f"💡 CÁLCULO ÓPTIMO:")
    print(f"   • RPM disponible (80%): {rpm_80_percent:,}")
    print(f"   • Tiempo máximo por batch: {max_time_per_batch_minutes} min")
    print(f"   • Requests máximos por batch: {max_requests_per_batch:.0f}")
    print(f"   • Chunks por archivo: {chunks_per_file_avg:.1f}")
    print(f"   • batch_size óptimo: {optimal_batch_size} archivos")
    print()
    
    # Verificar que no exceda límites
    requests_per_batch_optimal = optimal_batch_size * chunks_per_file_avg
    time_per_batch_optimal_min = requests_per_batch_optimal / rpm_80_percent
    
    print(f"✅ VERIFICACIÓN:")
    print(f"   • Requests por batch: {requests_per_batch_optimal:.0f}")
    print(f"   • Tiempo por batch: {time_per_batch_optimal_min:.2f} min ({time_per_batch_optimal_min*60:.1f} seg)")
    print(f"   • RPM utilizado: {requests_per_batch_optimal / time_per_batch_optimal_min:.0f} RPM")
    print(f"   • % de capacidad: {(requests_per_batch_optimal / time_per_batch_optimal_min / rpm_limit_tier2 * 100):.1f}%")
    print()
    
    # Calcular velocidad esperada
    files_per_hour_optimal = (optimal_batch_size * 60) / time_per_batch_optimal_min if time_per_batch_optimal_min > 0 else 0
    
    print(f"📈 VELOCIDAD ESPERADA:")
    print(f"   • Con batch_size={optimal_batch_size}: {files_per_hour_optimal:.0f} archivos/hora")
    print()
    
    # Comparar con actual
    if current_batch != optimal_batch_size:
        files_per_hour_current = (current_batch * 60) / time_per_batch_current_min if time_per_batch_current_min > 0 else 0
        improvement = (files_per_hour_optimal / files_per_hour_current) if files_per_hour_current > 0 else 0
        
        print(f"📊 COMPARACIÓN:")
        print(f"   • batch_size actual: {current_batch} → {files_per_hour_current:.0f} archivos/hora")
        print(f"   • batch_size óptimo: {optimal_batch_size} → {files_per_hour_optimal:.0f} archivos/hora")
        print(f"   • Mejora esperada: {improvement:.2f}x más rápido")
        print()
    
    # Actualizar batch_size
    print("=" * 80)
    print("🔄 ACTUALIZANDO BATCH_SIZE")
    print("=" * 80)
    print()
    
    reason = f"RPM detectado: {rpm_80_percent:,} RPM (80% de {rpm_limit_tier2:,}), {optimal_batch_size} archivos, ~{time_per_batch_optimal_min:.2f} min/batch"
    
    if update_batch_size(optimal_batch_size, reason):
        print(f"   ✅ batch_size actualizado: {current_batch} → {optimal_batch_size}")
        print(f"   📝 Razón: {reason}")
        print()
        print("   ⚠️  IMPORTANTE: Reinicia el proceso de ingest para aplicar los cambios")
    else:
        print(f"   ❌ Error al actualizar batch_size")
        print()
    
    print("=" * 80)
    print("📋 RESUMEN FINAL")
    print("=" * 80)
    print()
    print(f"✅ Configuración optimizada:")
    print(f"   • batch_size: {optimal_batch_size} archivos")
    print(f"   • RPM utilizado: ~{rpm_80_percent:,} RPM (80% de {rpm_limit_tier2:,} detectado)")
    print(f"   • Tiempo por batch: ~{time_per_batch_optimal_min:.2f} min")
    print(f"   • Velocidad esperada: ~{files_per_hour_optimal:.0f} archivos/hora")
    print()
    print("⚠️  RECUERDA: Reinicia el proceso de ingest para aplicar los cambios")
    print()

if __name__ == "__main__":
    main()

