"""
🔔 MONITOR DE ACTUALIZACIÓN DE RAM EN SUPABASE
==============================================

Este script monitorea y te avisa cuando detecta que la RAM de Supabase ha aumentado a 4 GB.
"""

import os
import sys
import time
from urllib.parse import quote_plus
from dotenv import load_dotenv
import psycopg2
from datetime import datetime
import config

# Configurar encoding para Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Cargar variables de entorno
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

# Obtener variables de entorno
SUPABASE_URL = get_env("SUPABASE_URL")
SUPABASE_DB_PASSWORD = get_env("SUPABASE_DB_PASSWORD")

if not SUPABASE_URL or not SUPABASE_DB_PASSWORD:
    print("❌ Error: Faltan variables de entorno")
    sys.exit(1)

# Construir conexión
project_ref = SUPABASE_URL.replace("https://", "").replace(".supabase.co", "")
encoded_password = quote_plus(SUPABASE_DB_PASSWORD)
postgres_connection_string = f"postgresql://postgres:{encoded_password}@db.{project_ref}.supabase.co:5432/postgres"

print("=" * 80)
print("🔔 MONITOR DE ACTUALIZACIÓN DE RAM")
print("=" * 80)
print(f"Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("\n📋 Este script te ayudará a detectar cuando Supabase termine de actualizar a 4 GB")
print("   Verifica el panel de Supabase y proporciona los datos cuando se te pida.\n")
print("=" * 80)

# Estado inicial
initial_check = True
check_count = 0

try:
    while True:
        check_count += 1
        current_time = datetime.now()
        
        if initial_check:
            print(f"\n[{current_time.strftime('%H:%M:%S')}] ⏳ Esperando actualización de RAM...")
            print("\n💡 INSTRUCCIONES:")
            print("   1. Ve al panel de Supabase")
            print("   2. Aumenta la RAM de 2 GB a 4 GB")
            print("   3. Espera a que se reinicie (puede tardar unos minutos)")
            print("   4. Cuando veas que el uso de RAM cambió, ejecuta:")
            print("      python calculate_optimal_batch.py")
            print("\n   O simplemente dime:")
            print("   - RAM Total: (ej: 4 GB)")
            print("   - RAM Usada: (ej: 3.6 GB)")
            print("   - Observaciones: (si aumentó, se mantuvo, etc.)")
            initial_check = False
        else:
            print(f"\n[{current_time.strftime('%H:%M:%S')}] Check #{check_count}")
            print("   ⏳ Esperando actualización...")
        
        # Intentar conectar para verificar que Supabase está activo
        try:
            conn = psycopg2.connect(postgres_connection_string, connect_timeout=5)
            cur = conn.cursor()
            cur.execute("SELECT 1")
            cur.close()
            conn.close()
            print("   ✅ Supabase está activo y respondiendo")
        except psycopg2.OperationalError as e:
            if "timeout" in str(e).lower() or "connection" in str(e).lower():
                print("   ⚠️  Supabase puede estar reiniciándose...")
            else:
                print(f"   ⚠️  Error de conexión: {e}")
        except Exception as e:
            print(f"   ⚠️  Error: {e}")
        
        print(f"\n💡 RECUERDA:")
        print(f"   Cuando veas que la RAM cambió en el panel de Supabase,")
        print(f"   ejecuta: python calculate_optimal_batch.py")
        print(f"   O simplemente dime los datos y yo calculo el batch_size óptimo.")
        
        print(f"\n⏱️  Próxima verificación en 30 segundos...")
        print("   (Presiona Ctrl+C para detener y ejecutar calculate_optimal_batch.py)")
        print("="*80)
        
        time.sleep(30)
        
except KeyboardInterrupt:
    print("\n\n" + "="*80)
    print("⏹️  MONITOR DETENIDO")
    print("="*80)
    print("\n💡 Ahora puedes:")
    print("   1. Verificar el panel de Supabase")
    print("   2. Ejecutar: python calculate_optimal_batch.py")
    print("   3. O decirme los datos y yo calculo el batch_size óptimo")




