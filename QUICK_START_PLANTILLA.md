# ⚡ Inicio Rápido: Usar como Plantilla

## 🎯 Para crear un nuevo proyecto en 5 minutos:

### 1️⃣ Copia el proyecto
```bash
# Opción A: Copiar carpeta completa
cp -r MI_SAAS_BOT/backend MI_NUEVO_PROYECTO/backend
cd MI_NUEVO_PROYECTO/backend

# Opción B: Usar script de setup
python setup_nuevo_proyecto.py
```

### 2️⃣ Edita `config.py`

Cambia estas líneas según tu dominio:

```python
DOMAIN_NAME = "cocina"  # ← Cambia aquí
ASSISTANT_DESCRIPTION = "Eres un asistente experto en cocina..."  # ← Cambia aquí
API_TITLE = "Chat Bot API - Cocina"  # ← Cambia aquí
```

### 3️⃣ Configura `.env`

```bash
# Copia el ejemplo
cp env.example.txt .env

# Edita .env con tus credenciales de Supabase
```

### 4️⃣ Configura Supabase

Ejecuta estos scripts SQL en Supabase:
- `create_profiles_table.sql`
- `create_conversations_table.sql`

### 5️⃣ Agrega documentos

```bash
# Coloca tus PDFs, EPUBs, etc. en:
./data/
```

### 6️⃣ Indexa documentos

```bash
python ingest_improved.py
```

### 7️⃣ Inicia el servidor

```bash
python main.py
```

## ✅ ¡Listo! Tu chatbot está funcionando

---

## 📝 Ejemplos Rápidos

### Para Cocina:
```python
# config.py
DOMAIN_NAME = "cocina"
ASSISTANT_DESCRIPTION = "Eres un asistente experto en cocina, recetas y técnicas culinarias..."
```

### Para Psicología:
```python
# config.py
DOMAIN_NAME = "psicologia"
ASSISTANT_DESCRIPTION = "Eres un asistente experto en psicología y salud mental..."
```

### Para Medicina:
```python
# config.py
DOMAIN_NAME = "medicina"
ASSISTANT_DESCRIPTION = "Eres un asistente experto en medicina y salud..."
```

---

## 📚 Documentación Completa

Para más detalles, consulta: `README_PLANTILLA.md`

