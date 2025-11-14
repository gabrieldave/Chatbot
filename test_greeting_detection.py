"""
Script de prueba para verificar la detección de saludos
"""
import re

def is_simple_greeting(message: str) -> bool:
    """
    Detecta si el mensaje es solo un saludo simple sin contenido de trading.
    Retorna True si es solo un saludo, False si contiene contenido de trading.
    """
    # Normalizar el mensaje: minúsculas, sin espacios extra, sin emojis
    normalized = re.sub(r'[^\w\s]', '', message.lower().strip())
    words = normalized.split()
    
    print(f"Mensaje original: '{message}'")
    print(f"Mensaje normalizado: '{normalized}'")
    print(f"Palabras: {words}")
    print(f"Numero de palabras: {len(words)}")
    
    # Si el mensaje es muy largo, probablemente no es solo un saludo
    if len(words) > 5:
        print("Rechazado: mas de 5 palabras")
        return False
    
    # Lista de saludos simples (español e inglés)
    simple_greetings = [
        'hola', 'hi', 'hello', 'hey',
        'buenas', 'buen', 'día', 'day',
        'qué', 'tal', 'what', 'up',
        'saludos', 'greetings',
        'buenos', 'días', 'mornings', 'afternoon', 'evening',
        'good', 'morning', 'afternoon', 'evening',
        'there', 'hola qué tal', 'hi there', 'hello there', 'hey there'
    ]
    
    # Verificar si todas las palabras son saludos simples
    all_greetings = all(word in simple_greetings for word in words if word)
    print(f"Todas las palabras son saludos: {all_greetings}")
    
    # Palabras relacionadas con trading que indican que NO es solo un saludo
    trading_keywords = [
        'trading', 'trader', 'mercado', 'market', 'operar', 'trade',
        'estrategia', 'strategy', 'riesgo', 'risk', 'capital', 'money',
        'análisis', 'analysis', 'gráfico', 'chart', 'indicador', 'indicator',
        'soporte', 'support', 'resistencia', 'resistance', 'tendencia', 'trend',
        'compra', 'venta', 'buy', 'sell', 'precio', 'price', 'acción', 'stock',
        'forex', 'crypto', 'bitcoin', 'cripto', 'divisa', 'currency',
        'psicología', 'psychology', 'emociones', 'emotions', 'disciplina', 'discipline',
        'swing', 'scalping', 'intradía', 'intraday', 'day trading', 'daytrading',
        'explicar', 'explain', 'qué es', 'what is', 'cómo', 'how', 'cuál', 'which'
    ]
    
    # Si contiene palabras de trading, NO es solo un saludo
    has_trading_content = any(keyword in normalized for keyword in trading_keywords)
    print(f"Contiene palabras de trading: {has_trading_content}")
    
    # Es solo un saludo si: todas las palabras son saludos Y no hay contenido de trading
    result = all_greetings and not has_trading_content and len(words) > 0
    print(f"Resultado final: {result}")
    print("-" * 50)
    return result

# Pruebas
test_cases = [
    "hola",
    "Hola",
    "hola!",
    "Hola 👋",
    "buen día",
    "qué tal",
    "hi",
    "hello",
    "hola, qué tal",
    "hola, explícame gestión de riesgo",
    "hola, qué es el trading",
    "buen día, cómo funciona el mercado",
    "explicame trading",
    "qué es el day trading",
]

print("=" * 50)
print("PRUEBAS DE DETECCIÓN DE SALUDOS")
print("=" * 50)

for test in test_cases:
    result = is_simple_greeting(test)
    status = "SALUDO" if result else "NO ES SALUDO"
    print(f"{status}: '{test}'")
    print()

