"""
📚 EXTRACTOR DE METADATOS RICOS PARA DOCUMENTOS
===============================================

Extrae metadatos útiles de documentos (PDFs, libros):
- Título y autor
- Idioma
- Categoría/tema
- Año de publicación
"""

import os
import re
from typing import Optional, Dict, Any
from datetime import datetime

# Intentar importar librerías para extracción de metadatos
try:
    import PyPDF2
    PDF2_AVAILABLE = True
except ImportError:
    PDF2_AVAILABLE = False

try:
    from langdetect import detect, DetectorFactory
    DetectorFactory.seed = 0  # Para resultados consistentes
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False

try:
    from pdfminer.high_level import extract_text as pdfminer_extract
    PDFMINER_AVAILABLE = True
except ImportError:
    PDFMINER_AVAILABLE = False

# ============================================================================
# EXTRACCIÓN DE TÍTULO Y AUTOR
# ============================================================================

def extract_title_author_from_pdf(file_path: str) -> Dict[str, Optional[str]]:
    """
    Intenta extraer título y autor del PDF usando metadatos del PDF
    
    Args:
        file_path: Ruta del archivo PDF
        
    Returns:
        Dict con 'title' y 'author' (pueden ser None)
    """
    title = None
    author = None
    
    if not file_path.lower().endswith('.pdf'):
        return {'title': None, 'author': None}
    
    try:
        if PDF2_AVAILABLE:
            with open(file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                metadata = pdf_reader.metadata
            
            if metadata:
                title = metadata.get('/Title')
                author = metadata.get('/Author')
                
                # Limpiar valores si existen
                if title:
                    title = title.strip()
                if author:
                    author = author.strip()
    except Exception:
        # Si falla, intentar con pdfminer
        pass
    
    # Si no se encontró en metadatos, intentar heurísticas simples
    if not title or not author:
        try:
            # Heurística: usar nombre del archivo como título base
            filename = os.path.basename(file_path)
            filename_no_ext = os.path.splitext(filename)[0]
            
            # Intentar extraer título y autor del nombre de archivo
            # Formato común: "Autor - Título.pdf" o "Título - Autor.pdf"
            if ' - ' in filename_no_ext:
                parts = filename_no_ext.split(' - ', 1)
                if len(parts) == 2:
                    # Asumir que el primer elemento es autor y el segundo título
                    potential_author = parts[0].strip()
                    potential_title = parts[1].strip()
                    
                    # Si el título no se encontró, usar esta heurística
                    if not title:
                        title = potential_title
                    if not author:
                        author = potential_author
            else:
                # Si no hay separador, usar el nombre del archivo como título
                if not title:
                    title = filename_no_ext
        except Exception:
            pass
    
    return {
        'title': title if title else None,
        'author': author if author else None
    }

def extract_title_author_from_text(text: str, filename: str) -> Dict[str, Optional[str]]:
    """
    Intenta extraer título y autor del texto usando heurísticas
    
    Args:
        text: Texto extraído del documento
        filename: Nombre del archivo
        
    Returns:
        Dict con 'title' y 'author'
    """
    title = None
    author = None
    
    if not text:
        return {'title': None, 'author': None}
    
    # Heurística 1: Buscar en las primeras líneas
    lines = text.split('\n')[:20]  # Primeras 20 líneas
    
    # Buscar patrones comunes de título
    for i, line in enumerate(lines):
        line_clean = line.strip()
        
        # Si la línea es muy corta o muy larga, probablemente no es título
        if len(line_clean) < 5 or len(line_clean) > 200:
            continue
        
        # Si está en mayúsculas o tiene formato especial, podría ser título
        if line_clean.isupper() or (len(line_clean) > 10 and line_clean[0].isupper()):
            # Verificar que no sea una fecha o número
            if not re.match(r'^\d+', line_clean):
                title = line_clean
                break
    
    # Heurística 2: Buscar "Autor:" o "Author:" en el texto
    author_patterns = [
        r'(?:Autor|Author|Escrito por|Written by)[:\s]+([^\n]+)',
        r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\s*$',  # Nombre propio al inicio
    ]
    
    for pattern in author_patterns:
        match = re.search(pattern, text[:1000], re.IGNORECASE | re.MULTILINE)
        if match:
            author = match.group(1).strip()
            break
    
    # Si no se encontró título, usar nombre de archivo
    if not title:
        filename_no_ext = os.path.splitext(filename)[0]
        title = filename_no_ext
    
    return {
        'title': title if title else None,
        'author': author if author else None
    }

# ============================================================================
# DETECCIÓN DE IDIOMA
# ============================================================================

def detect_language(text: str) -> str:
    """
    Detecta el idioma principal del texto
    
    Args:
        text: Texto del documento
        
    Returns:
        Código de idioma (ej: 'es', 'en', 'fr', etc.) o 'unknown' si no se puede detectar
    """
    if not text or len(text.strip()) < 50:
        return 'unknown'
    
    # Usar langdetect si está disponible
    if LANGDETECT_AVAILABLE:
        try:
            # Usar una muestra del texto (primeros 1000 caracteres) para velocidad
            sample = text[:1000] if len(text) > 1000 else text
            lang = detect(sample)
            return lang
        except Exception:
            pass
    
    # Heurística simple basada en palabras comunes
    text_lower = text.lower()
    
    # Palabras comunes en español
    spanish_words = ['el', 'la', 'de', 'que', 'y', 'en', 'un', 'es', 'se', 'no', 'te', 'lo', 'le', 'da', 'su', 'por', 'son', 'con', 'para', 'al', 'del', 'una', 'está', 'pero', 'más', 'muy', 'ser', 'como', 'todo', 'también', 'después', 'hasta', 'año', 'años', 'vez', 'puede', 'cada', 'donde', 'mientras', 'cuando', 'estos', 'estas', 'están', 'hacer', 'hacia', 'hasta', 'había', 'haber', 'hacer', 'hasta', 'hecho', 'hizo', 'hora', 'horas']
    
    # Palabras comunes en inglés
    english_words = ['the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'i', 'it', 'for', 'not', 'on', 'with', 'he', 'as', 'you', 'do', 'at', 'this', 'but', 'his', 'by', 'from', 'they', 'we', 'say', 'her', 'she', 'or', 'an', 'will', 'my', 'one', 'all', 'would', 'there', 'their', 'what', 'so', 'up', 'out', 'if', 'about', 'who', 'get', 'which', 'go', 'me', 'when', 'make', 'can', 'like', 'time', 'no', 'just', 'him', 'know', 'take', 'people', 'into', 'year', 'your', 'good', 'some', 'could', 'them', 'see', 'other', 'than', 'then', 'now', 'look', 'only', 'come', 'its', 'over', 'think', 'also', 'back', 'after', 'use', 'two', 'how', 'our', 'work', 'first', 'well', 'way', 'even', 'new', 'want', 'because', 'any', 'these', 'give', 'day', 'most', 'us']
    
    # Contar ocurrencias
    spanish_count = sum(1 for word in spanish_words if word in text_lower)
    english_count = sum(1 for word in english_words if word in text_lower)
    
    # Determinar idioma
    if spanish_count > english_count and spanish_count > 5:
        return 'es'
    elif english_count > spanish_count and english_count > 5:
        return 'en'
    else:
        return 'unknown'

# ============================================================================
# CLASIFICACIÓN DE CATEGORÍA/TEMA
# ============================================================================

def classify_category(text: str, title: Optional[str] = None, filename: Optional[str] = None) -> str:
    """
    Clasifica el documento en una categoría/tema basado en palabras clave
    
    Args:
        text: Texto del documento
        title: Título del documento (opcional)
        filename: Nombre del archivo (opcional)
        
    Returns:
        Categoría detectada (ej: 'trading', 'psicología', 'finanzas', etc.)
    """
    if not text:
        return 'general'
    
    # Combinar texto, título y nombre de archivo para análisis
    search_text = text.lower()
    if title:
        search_text += ' ' + title.lower()
    if filename:
        search_text += ' ' + filename.lower()
    
    # Definir categorías y palabras clave
    categories = {
        'trading': [
            'trading', 'forex', 'bolsa', 'acciones', 'mercado', 'inversión', 'inversiones',
            'opciones', 'futuros', 'crypto', 'criptomoneda', 'bitcoin', 'ethereum',
            'análisis técnico', 'technical analysis', 'indicadores', 'estrategia',
            'trader', 'trading strategy', 'day trading', 'swing trading'
        ],
        'finanzas': [
            'finanzas', 'financiero', 'financiera', 'economía', 'económico',
            'presupuesto', 'ahorro', 'inversión', 'retiro', 'jubilación',
            'planificación financiera', 'financial planning', 'wealth', 'riqueza'
        ],
        'psicología': [
            'psicología', 'psicológico', 'mental', 'mente', 'emocional', 'emociones',
            'terapia', 'cognitivo', 'comportamiento', 'conducta', 'personalidad',
            'ansiedad', 'depresión', 'estrés', 'autoestima', 'motivación',
            'psicología positiva', 'mindfulness', 'meditación'
        ],
        'autoayuda': [
            'autoayuda', 'desarrollo personal', 'crecimiento personal', 'superación',
            'motivación', 'éxito', 'logro', 'objetivos', 'metas', 'hábitos',
            'productividad', 'liderazgo', 'emprendimiento', 'negocio propio',
            'self-help', 'personal development', 'success', 'habits'
        ],
        'tecnología': [
            'tecnología', 'tecnológico', 'programación', 'software', 'hardware',
            'computadora', 'ordenador', 'aplicación', 'app', 'desarrollo',
            'código', 'algoritmo', 'inteligencia artificial', 'machine learning',
            'data science', 'big data', 'cloud computing'
        ],
        'salud': [
            'salud', 'saludable', 'nutrición', 'dieta', 'ejercicio', 'fitness',
            'bienestar', 'medicina', 'médico', 'enfermedad', 'tratamiento',
            'prevención', 'cuidado', 'cuerpo', 'mente', 'mental health'
        ],
        'educación': [
            'educación', 'educativo', 'aprendizaje', 'enseñanza', 'estudio',
            'curso', 'tutorial', 'guía', 'manual', 'instrucción', 'método',
            'pedagogía', 'didáctica', 'conocimiento', 'saber'
        ]
    }
    
    # Contar coincidencias por categoría
    category_scores = {}
    for category, keywords in categories.items():
        score = 0
        for keyword in keywords:
            if keyword in search_text:
                score += search_text.count(keyword)
        if score > 0:
            category_scores[category] = score
    
    # Si hay categorías con puntuación, devolver la de mayor puntuación
    if category_scores:
        best_category = max(category_scores, key=category_scores.get)
        # Solo devolver si la puntuación es significativa (al menos 2 coincidencias)
        if category_scores[best_category] >= 2:
            return best_category
    
    # Si no se encontró categoría clara, devolver 'general'
    return 'general'

# ============================================================================
# EXTRACCIÓN DE AÑO DE PUBLICACIÓN
# ============================================================================

def extract_published_year(text: str, title: Optional[str] = None, filename: Optional[str] = None) -> Optional[int]:
    """
    Intenta extraer el año de publicación del documento
    
    Args:
        text: Texto del documento
        title: Título del documento (opcional)
        filename: Nombre del archivo (opcional)
        
    Returns:
        Año (int) o None si no se puede determinar
    """
    # Buscar patrones de año en el texto
    # Patrones comunes: "2023", "(2023)", "© 2023", "Publicado en 2023", etc.
    year_patterns = [
        r'\b(19|20)\d{2}\b',  # Años entre 1900-2099
        r'\((\d{4})\)',  # Año entre paréntesis
        r'©\s*(\d{4})',  # Copyright
        r'publicado\s+en\s+(\d{4})',  # "Publicado en 2023"
        r'edición\s+(\d{4})',  # "Edición 2023"
    ]
    
    search_text = text[:5000]  # Buscar en los primeros 5000 caracteres
    if title:
        search_text = title + ' ' + search_text
    
    years_found = []
    for pattern in year_patterns:
        matches = re.findall(pattern, search_text, re.IGNORECASE)
        for match in matches:
            if isinstance(match, tuple):
                year_str = match[0] + match[1] if len(match) > 1 else match[0]
            else:
                year_str = match
            
            try:
                year = int(year_str)
                # Validar que sea un año razonable (entre 1900 y año actual + 1)
                current_year = datetime.now().year
                if 1900 <= year <= current_year + 1:
                    years_found.append(year)
            except ValueError:
                continue
    
    # Si se encontraron años, devolver el más reciente (probablemente el año de publicación)
    if years_found:
        return max(years_found)
    
    return None

# ============================================================================
# FUNCIÓN PRINCIPAL DE EXTRACCIÓN
# ============================================================================

def extract_rich_metadata(file_path: str, text: Optional[str] = None) -> Dict[str, Any]:
    """
    Extrae todos los metadatos ricos de un documento
    
    Args:
        file_path: Ruta del archivo
        text: Texto extraído del documento (opcional, se usará si está disponible)
        
    Returns:
        Dict con todos los metadatos extraídos
    """
    filename = os.path.basename(file_path)
    
    # 1. Extraer título y autor
    if file_path.lower().endswith('.pdf'):
        title_author = extract_title_author_from_pdf(file_path)
    else:
        title_author = {'title': None, 'author': None}
    
    # Si no se encontró en PDF y tenemos texto, intentar del texto
    if (not title_author['title'] or not title_author['author']) and text:
        text_title_author = extract_title_author_from_text(text, filename)
        if not title_author['title']:
            title_author['title'] = text_title_author['title']
        if not title_author['author']:
            title_author['author'] = text_title_author['author']
    
    # Si aún no hay título, usar nombre de archivo
    if not title_author['title']:
        title_author['title'] = os.path.splitext(filename)[0]
    
    # 2. Detectar idioma
    language = 'unknown'
    if text:
        language = detect_language(text)
    
    # 3. Clasificar categoría
    category = 'general'
    if text:
        category = classify_category(text, title=title_author['title'], filename=filename)
    
    # 4. Extraer año de publicación
    published_year = None
    if text:
        published_year = extract_published_year(text, title=title_author['title'], filename=filename)
    
    return {
        'title': title_author['title'],
        'author': title_author['author'],
        'language': language,
        'category': category,
        'published_year': published_year,
        'filename': filename,
        'file_path': file_path
    }



