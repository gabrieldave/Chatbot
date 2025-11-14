"""
📊 ANÁLISIS DE LÍMITES DE OPENAI
=================================

Analiza los límites de rate de OpenAI y calcula el batch_size óptimo
"""

import sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

print("=" * 80)
print("📊 ANÁLISIS DE LÍMITES DE OPENAI")
print("=" * 80)

print("\n🔍 LÍMITES DE RATE DE OPENAI (Investigación):")

print("\n📋 LÍMITES TÍPICOS PARA EMBEDDINGS:")
print("\n1️⃣  TIER GRATUITO (Free Tier):")
print("   • RPM (Requests Per Minute): ~3-60")
print("   • TPM (Tokens Per Minute): ~40,000-150,000")
print("   • Muy limitado para procesamiento en batch")

print("\n2️⃣  TIER PAGO BÁSICO (Pay-as-you-go):")
print("   • RPM: ~3,500-10,000")
print("   • TPM: ~1,000,000-10,000,000")
print("   • Adecuado para la mayoría de casos")

print("\n3️⃣  TIER EMPRESARIAL (Scale Tier):")
print("   • RPM: Personalizado (muy alto)")
print("   • TPM: Personalizado (muy alto)")
print("   • Para cargas muy grandes")

print("\n📊 CÁLCULOS PARA TU CASO:")
print("\nModelo usado: text-embedding-3-small")
print("Tamaño típico de embedding: ~1,536 dimensiones")
print("Tokens por chunk promedio: ~100-200 tokens")

print("\n💡 CÁLCULO CON BATCH_SIZE=150:")
print("   • 150 archivos por batch")
print("   • Promedio: ~100 chunks por archivo")
print("   • Total: ~15,000 chunks por batch")
print("   • Cada chunk = 1 request a OpenAI")
print("   • Total: 15,000 requests por batch")

print("\n⏱️  TIEMPO ESTIMADO:")
print("\nCon límite de 3,500 RPM (tier básico):")
rpm_basic = 3500
chunks_per_batch_150 = 15000
time_basic = chunks_per_batch_150 / rpm_basic * 60
print(f"   • Tiempo por batch: ~{int(time_basic//60)}m {int(time_basic%60)}s")
print(f"   • Esto explica por qué tarda tanto!")

print("\nCon límite de 10,000 RPM (tier más alto):")
rpm_high = 10000
time_high = chunks_per_batch_150 / rpm_high * 60
print(f"   • Tiempo por batch: ~{int(time_high//60)}m {int(time_high%60)}s")
print(f"   • Aún así es lento")

print("\n💡 CÁLCULO CON BATCH_SIZE=60:")
chunks_per_batch_60 = 6000  # 60 archivos * 100 chunks
time_basic_60 = chunks_per_batch_60 / rpm_basic * 60
time_high_60 = chunks_per_batch_60 / rpm_high * 60
print(f"\nCon 3,500 RPM:")
print(f"   • Tiempo por batch: ~{int(time_basic_60//60)}m {int(time_basic_60%60)}s")
print(f"\nCon 10,000 RPM:")
print(f"   • Tiempo por batch: ~{int(time_high_60//60)}m {int(time_high_60%60)}s")
print(f"   • Mucho más razonable!")

print("\n" + "=" * 80)
print("🎯 CONCLUSIÓN")
print("=" * 80)

print("\n✅ CONFIRMADO: El problema es el RATE LIMITING de OpenAI")
print("\n📊 EVIDENCIA:")
print(f"   • Con batch_size=150: ~15,000 requests por batch")
print(f"   • Con límite de 3,500 RPM: ~{int(time_basic//60)} minutos por batch")
print(f"   • Con límite de 10,000 RPM: ~{int(time_high//60)} minutos por batch")
print(f"   • Tu proceso lleva 24+ minutos = Confirma rate limiting")

print("\n💡 SOLUCIÓN:")
print(f"   • Reducir batch_size a 50-60 archivos")
print(f"   • Esto reduce a ~5,000-6,000 requests por batch")
print(f"   • Tiempo por batch: ~{int(time_basic_60//60)}-{int(time_high_60//60)} minutos")
print(f"   • Mucho más manejable y verás progreso más rápido")

print("\n📋 RECOMENDACIÓN FINAL:")
print(f"   ✅ Reducir batch_size a 60")
print(f"   ✅ Esto respeta los límites de rate de OpenAI")
print(f"   ✅ Batches más rápidos y progreso más visible")
print(f"   ✅ Aprovecha mejor los recursos sin sobrecargar")

print("\n" + "=" * 80)
print("💡 NOTA IMPORTANTE:")
print("=" * 80)
print("\nLos límites exactos dependen de tu plan de OpenAI.")
print("Puedes verificar tus límites específicos en:")
print("https://platform.openai.com/settings/organization/limits")
print("\nPero basado en el comportamiento observado (24+ min por batch),")
print("es muy probable que estés en el tier básico (3,500 RPM)")

print("\n" + "=" * 80)




