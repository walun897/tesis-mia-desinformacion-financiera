# CLAUDE.md — Convenciones del proyecto

## Contexto
Tesis de Maestría en IA (Universidad Sergio Arboleda). Pipeline híbrido
LangGraph para detección de desinformación financiera en español colombiano.
Trabajo individual, ejecución en Google Colab (T4 gratis) + máquina local,
fecha límite enero 2027.

El documento formal del anteproyecto (alcance, objetivos, metodología,
cronograma) vive en `Documentacion/v2/anteproyecto/` (fuente LaTeX) y en
`Documentacion/v2/Sistema_hibrido_LLM_agente_para_deteccion_y_verificacion_de_desinformacion_financiera_en_Colombia.pdf`.
Ese anteproyecto es la fuente de verdad de alcance formal; si hay conflicto
entre lo que se discute en una sesión de trabajo y el anteproyecto, se
resuelve explícitamente con el usuario antes de implementar, no se asume.

## Decisiones confirmadas (2026-09-21)
- **Enfoque de trabajo**: se sigue el orden secuencial de fases del anteproyecto
  (`Documentacion/v2/anteproyecto/MainMatter/M07-Schedule.tex`), no un MVP
  comprimido. Cronograma original: Fase 1 jun-jul, Fase 2 ago-sep, Fase 3
  oct-nov, Fase 4 dic-ene 2027 (8 meses). A fecha de esta decisión no hay
  corpus ni código, así que el cronograma se re-mapea comprimido a partir de
  hoy (~4 meses restantes) — ver sección "Cronograma vigente" abajo.
- **LLMs del clasificador**: Gemini Pro, **Gemini 3.5 Flash-Lite** (reemplaza a
  Gemini 2.5 Flash, que se deprecó el 16-oct-2026), GPT-4o-mini y un modelo
  open-source cuantizado en Colab (Llama 3.1 8B o Mistral 7B) — conjunto del
  anteproyecto (`M06-Methodology.tex`), no Qwen/Gemma mencionados en una
  sesión anterior. Verificado: Gemini 3.5 Flash-Lite se lanzó el 21-jul-2026,
  con free tier (5-15 RPM, hasta 1.000 RPD) y precio pagado $0.30/$2.50 por
  1M tokens (input/output) — igual que la 2.5 Flash que reemplaza.
- **Presupuesto de APIs**: lo cubre el usuario directamente (no depende de
  aprobación del programa/director). Tope acordado: no debe superar **$50
  USD** para la fase de demo/prueba (GPT-4o-mini + Gemini Pro, que son los
  únicos componentes de pago; Gemini 3.5 Flash-Lite puede correr en free
  tier y Llama/Mistral corren gratis en Colab). Estimación previa del
  asistente: $3-10 USD en escenario económico, hasta ~$50 con iteración
  pesada — dentro del tope.
- **Anotación**: diseño humano-LLM (el usuario + LLM), no se reclutan
  anotadores adicionales. El Kappa de Cohen mide acuerdo humano-LLM, no
  acuerdo inter-anotador clásico entre 2+ humanos como describe
  `M06-Methodology.tex` — esto debe declararse explícitamente como
  limitación metodológica en el capítulo de metodología de la tesis.

## Estructura de carpetas
- 01_bibliografia/ → .bib + anotada, solo referencias reales y verificables
- 02_corpus/ → esquema de datos, datos pesados NUNCA se commitean (ver .gitignore)
- 03_scraping/ → agentes de recolección (Scrapy/Trafilatura)
- 04_clasificador/ → prompts versionados + lógica de clasificación LLM
- 05_agente/ → agente validador ReAct (LangGraph)
- 06_evaluacion/ → métricas, resultados por corrida
- 07_tesis/ → documento de tesis, se actualiza al cerrar cada fase
- 08_presentaciones/ → material de sustentación y avances
- Documentacion/ → anteproyecto formal, cronogramas, pósters (fuente de verdad de alcance)
- config/ → requirements.txt, variables de entorno (plantilla .env.example)

## Reglas de código
- Python con type hints, PEP8.
- Nombres de variables/funciones en inglés; comentarios y docstrings en español (idioma de la tesis).
- Lógica pesada en módulos .py; los notebooks de Colab solo importan y ejecutan.
- Prompts en archivos versionados (no hardcodeados inline), con nombre + versión.

## Datos y secretos
- API keys solo en .env (local) o Colab Secrets — nunca hardcodeadas ni commiteadas.
- Datos crudos/pesados fuera de git (Drive); solo muestras pequeñas de ejemplo en el repo.

## Registro de experimentos
- Cada corrida de clasificador registra: modelo, versión de prompt, fecha, métricas, en 06_evaluacion/.

## Reglas para el asistente (Claude Code)
- No inventar ni asumir referencias bibliográficas, papers, APIs o versiones de modelos:
  verificar antes de citar; si no se puede verificar, decirlo explícitamente.
- No hacer `git push` sin confirmación explícita del usuario.
- Mantener requirements.txt actualizado con cada nueva dependencia.
- No escribir código hasta que el usuario lo pida explícitamente en la sesión.
- Si el contenido de `Documentacion/` (anteproyecto, cronograma) cambia o se
  contradice con la conversación en curso, señalarlo antes de continuar con
  cualquier plan o implementación.

## Convención de commits
- Mensajes cortos en español, formato: "fase X: qué se hizo" (ej. "fase 1: grafo LangGraph mínimo con stub de validador").
