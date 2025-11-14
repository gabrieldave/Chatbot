import time
import subprocess
import sys

print("=" * 80)
print("📊 MONITOR DE MEMORIA Y PROGRESO")
print("=" * 80)
print("\nMonitoreando proceso de ingestión...")
print("Presiona Ctrl+C para detener\n")

last_count = 0
check_count = 0

try:
    while True:
        check_count += 1
        
        # Verificar memoria del proceso de Python más grande
        try:
            result = subprocess.run(
                ['powershell', '-Command', 
                 'Get-Process python -ErrorAction SilentlyContinue | '
                 'Sort-Object WorkingSet64 -Descending | '
                 'Select-Object -First 1 | '
                 'Format-List Id,@{Name="Memory(MB)";Expression={[math]::Round($_.WorkingSet64/1MB,2)}}'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.stdout:
                print(f"\n[{check_count}] Memoria del proceso:")
                print(result.stdout.strip())
        except:
            pass
        
        # Verificar progreso
        try:
            result = subprocess.run(
                ['python', 'verify_indexing.py'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if 'Archivos indexados' in result.stdout:
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'Archivos indexados en DB:' in line or 'Progreso:' in line:
                        print(line.strip())
                        if 'Archivos indexados en DB:' in line:
                            try:
                                count = int(line.split(':')[1].strip().split()[0])
                                if count > last_count:
                                    print(f"   ✅ ¡Progreso! +{count - last_count} archivos nuevos")
                                    last_count = count
                            except:
                                pass
        except:
            pass
        
        print(f"\n{'='*80}")
        print(f"Esperando 30 segundos para próxima verificación...")
        time.sleep(30)
        
except KeyboardInterrupt:
    print("\n\n⏹️  Monitoreo detenido")

