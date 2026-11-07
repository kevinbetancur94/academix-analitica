# Academix - Analítica de datos

Taller de visualización (pandas + matplotlib) conectado a la API de Academix (Spring Boot).
Genera 15 gráficas, un reporte HTML y lo publica en el front React.

## Uso
1. `pip install -r requirements.txt`
2. (Opcional) encender el backend: `.\mvnw.cmd spring-boot:run` en proyecto-academix, o usar Render.
3. `python generar_reporte.py` (usa la API en localhost:8080; si no responde, usa `datos/*.csv`)
   - Otra API: `python generar_reporte.py --api https://proyecto-academix.onrender.com/api`
   - Publicar en el front: `python generar_reporte.py --front "RUTA\Academix-Front-Final"`

El reporte queda en `reporte/index.html` y las gráficas en `graficas/`.
El notebook `taller_academix.ipynb` se puede ejecutar directo con "Run All".