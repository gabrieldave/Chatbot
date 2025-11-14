# Cómo Ver los Tokens en la Consola del Backend

## Pasos:

1. **Abre la ventana del backend** (donde está corriendo `python main.py`)

2. **Desplázate hacia arriba** en la consola (usa la barra de desplazamiento o scroll)

3. **Busca las últimas 2 secciones** que se ven así:

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

4. **Anota los valores de "Total tokens"** de cada consulta

5. **Súmalos** para obtener el total de las 2 consultas

## Alternativa: Hacer una consulta nueva

Si prefieres, puedes hacer UNA consulta nueva (en cualquier modo) y el sistema guardará automáticamente el log. Luego ejecuto el script para mostrártelo.



