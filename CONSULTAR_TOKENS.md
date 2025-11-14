# Cómo Consultar el Consumo de Tokens

## Opción 1: Ver Logs en Tiempo Real (Consola del Backend)

Cuando haces una consulta, el backend imprime en la consola:

```
============================================================
[INFO] Consulta procesada:
  Modelo: deepseek/deepseek-chat
  Input tokens: XXX
  Output tokens: YYY
  Total tokens: ZZZ
  Tokens restantes antes: NNNN
============================================================
[INFO] Tokens descontados: ZZZ tokens
[INFO] Tokens restantes después: MMMM tokens
```

**Para ver las últimas 2 consultas:**
1. Abre la ventana del backend
2. Desplázate hacia arriba en la consola
3. Busca las últimas 2 secciones con "Consulta procesada"

## Opción 2: Usar el Script de Consulta (Después de Reiniciar)

Después de reiniciar el backend con el nuevo código de logging:

1. **Haz algunas consultas** (el sistema guardará automáticamente los logs)

2. **Ejecuta el script:**
   ```bash
   python ver_tokens_ultimas_consultas.py
   ```

3. **Verás un resumen completo** de todas las consultas con:
   - Timestamp
   - Modo de respuesta (Rápida/Estudio profundo)
   - Input tokens
   - Output tokens
   - Total tokens
   - Resumen de las últimas 2 consultas

## Opción 3: Ver el Archivo de Logs Directamente

El archivo `tokens_log.json` se crea automáticamente en la carpeta `backend/` después de hacer consultas.

Puedes abrirlo con cualquier editor de texto para ver el historial completo.

## Nota Importante

**Para que el sistema de logging funcione:**
- El backend debe estar reiniciado con el nuevo código
- Las consultas que hagas DESPUÉS del reinicio se guardarán automáticamente
- Las consultas anteriores no estarán en el log (solo en la consola del backend)



