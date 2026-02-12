# QA Automation Dashboard - Dropea

Dashboard de resultados de tests E2E (Playwright) para Dropea.

Muestra metricas de la ultima ejecucion, distribucion por estado, tiempos de ejecucion y analisis de calidad.

### Como ejecutar localmente

1. Instalar dependencias

   ```
   pip install -r requirements.txt
   ```

2. Ejecutar la app

   ```
   streamlit run streamlit_app.py
   ```

### Sincronizar resultados desde dropea-qa

Desde el proyecto `dropea-qa`, ejecutar:

```bash
npm run sync-dashboard
```

Esto copia `test-results.json` y `test-analysis-complete.json` al directorio `data/` de este repo y hace push automaticamente.

### Estructura

```
streamlit_app.py          # Dashboard principal (resultados de tests)
pages/1_Test_Analysis.py  # Analisis de calidad de la suite
parsers.py                # Parsers de JUnit XML y JSON
data/
  test-results.json       # Resultados de la ultima ejecucion
  test-analysis-complete.json  # Analisis completo de la suite
```
