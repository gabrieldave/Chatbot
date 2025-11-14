"""
🔄 MONITOR Y REINICIO AUTOMÁTICO
=================================

Monitorea el proceso de ingest y lo reinicia automáticamente si se detiene
Sin duplicados - asegura que solo haya un proceso corriendo
"""

import os
import sys
import time
import subprocess
import psutil
from datetime import datetime

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def get_ingest_processes():
    """Busca todos los procesos de ingest_improved.py"""
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['name'] == 'python.exe' and proc.info['cmdline']:
                cmdline = ' '.join(proc.info['cmdline'])
                if 'ingest_improved.py' in cmdline.lower():
                    processes.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return processes

def kill_all_ingest_processes():
    """Detiene todos los procesos de ingest"""
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
        time.sleep(2)  # Esperar a que se cierren completamente

def start_ingest_process():
    """Inicia un nuevo proceso de ingest"""
    try:
        subprocess.Popen(
            [sys.executable, 'ingest_improved.py'],
            creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
        )
        return True
    except Exception as e:
        print(f"   ❌ Error iniciando proceso: {e}")
        return False

print("=" * 80)
print("🔄 MONITOR Y REINICIO AUTOMÁTICO")
print("=" * 80)
print(f"Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("\n✨ Funciones:")
print("   • Monitorea el proceso de ingest cada 30 segundos")
print("   • Reinicia automáticamente si se detiene")
print("   • Previene duplicados (solo un proceso a la vez)")
print("   • Duración: 5 minutos")
print("\nPresiona Ctrl+C para detener\n")

monitor_duration = 300  # 5 minutos
start_time = time.time()
check_interval = 30  # Verificar cada 30 segundos
last_restart_time = 0
restart_cooldown = 60  # 1 minuto entre reinicios

print("=" * 80)
print("📊 MONITOREO INICIADO")
print("=" * 80)

try:
    check_count = 0
    while time.time() - start_time < monitor_duration:
        check_count += 1
        current_time = time.time()
        elapsed = current_time - start_time
        remaining = monitor_duration - elapsed
        
        processes = get_ingest_processes()
        
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Check #{check_count} (Quedan {int(remaining//60)}m {int(remaining%60)}s)")
        
        if len(processes) > 1:
            print(f"   ⚠️  Se detectaron {len(processes)} procesos (duplicados)")
            print(f"   🛑 Deteniendo todos y reiniciando uno limpio...")
            kill_all_ingest_processes()
            time.sleep(2)
            if start_ingest_process():
                print(f"   ✅ Proceso reiniciado (un solo proceso limpio)")
                last_restart_time = current_time
            time.sleep(5)
            continue
        
        elif len(processes) == 1:
            proc = processes[0]
            try:
                status = proc.status()
                cpu = proc.cpu_percent(interval=0.5)
                mem_mb = proc.memory_info().rss / (1024 * 1024)
                
                print(f"   ✅ Proceso activo: PID {proc.pid}")
                print(f"      Estado: {status} | CPU: {cpu:.1f}% | RAM: {mem_mb:.1f} MB")
                
                if status in ['zombie', 'stopped']:
                    print(f"   ⚠️  Proceso en estado anormal, reiniciando...")
                    kill_all_ingest_processes()
                    time.sleep(2)
                    if start_ingest_process():
                        print(f"   ✅ Proceso reiniciado")
                        last_restart_time = current_time
                
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                print(f"   ⚠️  Proceso ya no existe, reiniciando...")
                if current_time - last_restart_time > restart_cooldown:
                    if start_ingest_process():
                        print(f"   ✅ Proceso reiniciado")
                        last_restart_time = current_time
                    else:
                        print(f"   ❌ No se pudo reiniciar")
                else:
                    print(f"   ⏳ Esperando cooldown antes de reiniciar...")
        
        else:
            print(f"   ⚠️  No se detecta proceso corriendo")
            if current_time - last_restart_time > restart_cooldown:
                print(f"   🔄 Reiniciando proceso...")
                if start_ingest_process():
                    print(f"   ✅ Proceso iniciado")
                    last_restart_time = current_time
                    time.sleep(5)  # Dar tiempo para que inicie
                else:
                    print(f"   ❌ No se pudo iniciar")
            else:
                print(f"   ⏳ Esperando cooldown antes de reiniciar...")
        
        print(f"   ⏱️  Próxima verificación en {check_interval} segundos...")
        time.sleep(check_interval)
    
    print("\n" + "=" * 80)
    print("✅ MONITOREO COMPLETADO (5 minutos)")
    print("=" * 80)
    
    # Verificar estado final
    processes = get_ingest_processes()
    if processes:
        print(f"\n📊 Estado final:")
        for proc in processes:
            try:
                print(f"   ✅ Proceso activo: PID {proc.pid}")
            except:
                pass
    else:
        print(f"\n⚠️  No hay proceso corriendo al finalizar el monitoreo")
        print(f"   Iniciando uno final...")
        start_ingest_process()
        time.sleep(3)
    
    print(f"\n💡 El proceso debería seguir corriendo")
    print(f"   Verifica con: python check_progress_now.py")

except KeyboardInterrupt:
    print("\n\n" + "=" * 80)
    print("⏹️  MONITOR DETENIDO POR EL USUARIO")
    print("=" * 80)
    
    # Asegurar que hay un proceso corriendo
    processes = get_ingest_processes()
    if not processes:
        print(f"\n🔄 Iniciando proceso final...")
        start_ingest_process()

print("\n" + "=" * 80)




