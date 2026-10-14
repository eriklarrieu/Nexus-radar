# NEXUS-0 — EXPERIMENTO CERRADO (14 DE OCTUBRE DE 2026)

> **Proyecto terminado por decisión estratégica del accionista.** El radar demostró funcionamiento técnico, pero no consiguió pagos ni contribuciones remuneradas. Se desactivaron las tareas horarias de ChatGPT y la programación automática de GitHub Actions. La ejecución en GitHub queda disponible **solo de forma manual**, sin operaciones de cobro.

**Balance final del experimento:** capital de referencia USD 20; transferencias recibidas USD 0; gastos realizados USD 0; ingresos verificados USD 0; beneficios USD 0. Los USD 20 permanecen bajo el control del accionista.

La documentación siguiente se conserva como registro técnico histórico. No constituye una recomendación de continuar la operación.

---


Explorador de incidencias públicas de GitHub que anuncian recompensas por contribuciones. Proyecto experimental sin captación de clientes propios.

> **Importante:** el radar no comprueba financiación, elegibilidad, identidad del pagador, adjudicación ni disponibilidad del premio. Una incidencia etiquetada no equivale a un contrato de pago. La selección final exige verificar condiciones y competencia. No maneja dinero ni reclama trabajos automáticamente.

## Ejecución

Requiere Python 3.11 o posterior. Solo usa biblioteca estándar.

```bash
python -m unittest -v test_nexus.py
python nexus_radar.py --min-usd 30 --limit 12
```

Se generan `reports/resultados_nexus.json` y `reports/resultados_nexus.md`, ignorados por Git para evitar guardar resultados caducos.

## Automatización

La acción `.github/workflows/radar.yml` puede ejecutarse **solo manualmente** desde GitHub Actions. Se desactivó la programación periódica. En GitHub, abre **Actions > NEXUS - radar diario** y revisa el resultado de la ejecución o utiliza *Run workflow*. El informe, si se genera, queda disponible como artefacto de la ejecución durante 7 días.

No se requieren secretos manuales: GitHub proporciona `GITHUB_TOKEN` a cada ejecución con permisos de lectura. El umbral de búsqueda es US$5 (monto anunciado, no ingreso). Los límites de tasa, el número de resultados y la disponibilidad de la API pueden restringir la exploración.

## Criterios antes de perseguir una recompensa

1. Confirmar que el problema original sigue abierto y no tiene solución aceptada.
2. Comprobar la autoridad del pagador, financiación y pagos anteriores verificables.
3. Verificar reglas del programa, elegibilidad desde Chile y el método de cobro.
4. Revisar intentos y solicitudes de incorporación de código (PR) existentes.
5. Estimar trabajo, infraestructura requerida, gastos y **plazo de cobro real**.
6. No gastar el capital ni presentar soluciones sin pruebas y sin cumplir las reglas.

## Contabilidad del experimento

Capital de referencia: USD 20. Meta planteada: USD 40 líquidos antes del 21 de octubre de 2026, devolver USD 20 al accionista y conservar USD 20. **Ingresos realmente cobrados: USD 0** al cierre del experimento. No prometer beneficios ni contabilizar premios anunciados como ganancias.

Desarrollado como prototipo NEXUS para investigación económica. Sin acceso automático a transferencias ni a cuentas de pago.
