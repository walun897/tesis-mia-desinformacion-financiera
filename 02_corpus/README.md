# 02_corpus — Benchmark de desinformación financiera colombiana

Corpus de **evaluación**, no de entrenamiento (no se hace fine-tuning de
modelos sobre él). Ver también:
- `criterios_seleccion_fuentes.md` — qué entra y qué no al corpus.
- `guia_anotacion.md` — taxonomía trinaria y protocolo de anotación humano-LLM.

## Esquema de datos

Un registro por noticia/ítem. Formato de archivo: CSV o Parquet (Parquet
preferido si el volumen de texto lo justifica).

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | string | Identificador único del ítem |
| `titulo` | string | Titular, si está disponible |
| `texto` | string | Texto limpio (HTML removido, encoding normalizado) |
| `url` | string | URL original de la fuente |
| `fuente` | string | Medio/organización (Portafolio, ColombiaCheck, etc.) |
| `tipo_fuente` | enum | `medio_referencia` \| `comunicado_oficial` \| `fact_checker` \| `viral_no_verificado` \| `dataset_publico` |
| `fecha_publicacion` | date | Fecha original de publicación |
| `fecha_recoleccion` | date | Fecha en que se scrapeó/incorporó |
| `categoria_tematica` | enum | `tasas_interes` \| `creditos` \| `sistema_pensional` \| `tributario` \| `cambiario` \| `banca` \| `otro` |
| `idioma` | string | Esperado `es-CO`; se marca si no aplica |
| `fact_checker_url` | string\|null | Enlace a la verificación, si existe |
| `fact_checker_rating_original` | string\|null | Calificación original del fact-checker, antes de mapear a la taxonomía trinaria |
| `label_fuente` | enum\|null | `verdadera`\|`falsa`, asignada automáticamente por regla de fuente primaria (ver `guia_anotacion.md`); `null` si es candidata a "dudosa" |
| `es_candidata_dudosa` | bool | Si requiere anotación manual |
| `label_humano` | enum\|null | Primera pasada del usuario (solo candidatas dudosas) |
| `label_llm_segunda_opinion` | enum\|null | Etiqueta del LLM de segunda opinión |
| `modelo_segunda_opinion` | string\|null | Qué modelo dio la segunda opinión (`gemini-3.5-flash-lite`, `gpt-4o-mini`) |
| `coincide_humano_llm` | bool\|null | `label_humano == label_llm_segunda_opinion` |
| `label_arbitraje_fable` | enum\|null | Solo si hubo desacuerdo — etiqueta de Fable 5.1 como árbitro |
| `nota_resolucion` | string\|null | Por qué se resolvió así el desacuerdo |
| `label_final` | enum | `verdadera`\|`dudosa`\|`falsa` — etiqueta definitiva usada en evaluación |
| `es_muestra_calibracion_kappa` | bool | Si pertenece a la muestra de ~200 ítems usada para calcular Cohen's Kappa |
| `similitud_ngramas_max` | float | Máxima similitud contra otro ítem ya incluido (umbral de duplicado: 0.85) |
| `conjunto` | enum | `calibracion_prompts` \| `evaluacion_final` — **no** train/val/test, porque es benchmark de evaluación, no de entrenamiento |
| `pii_revisado` | bool | Si se revisó/anonimizó información personal identificable |

## Por qué `conjunto` reemplaza el split train/val/test

`M06-Methodology.tex` describe un split 70/15/15 pensado para el enfoque
de fine-tuning (BETO/XLM-RoBERTa) que ya no es el vigente — el enfoque
actual es prompting sobre LLMs, no entrenamiento. Este corpus es un
benchmark de evaluación (ver contexto original de la tesis), así que el
split relevante es:
- **`calibracion_prompts`**: subconjunto pequeño (~15%) para iterar
  prompts sin contaminar la evaluación final.
- **`evaluacion_final`**: el resto, usado una sola vez por configuración
  para la tabla comparativa de la Fase 2/4.

Si se retoma el enfoque de fine-tuning en algún momento, este esquema
necesita una columna adicional de split train/val/test — no aplica hoy.

## Almacenamiento

- Datos pesados (texto completo, cachés de scraping) → `02_corpus/raw/`,
  excluido de git (ver `.gitignore`, corregido en esta sesión — antes
  apuntaba a `02-corpus/` con guion, que no existe).
- **Pendiente de decidir**: si el CSV/Parquet curado y etiquetado
  (metadatos + labels) se commitea al repo o se queda solo en Drive/local.
  Redistribuir el texto completo de noticias de medios con copyright en un
  repo público puede tener implicaciones de derechos de autor — considerar
  publicar solo metadatos + URL + label + un extracto corto, no el texto
  completo, si el corpus va a vivir en GitHub. No se resuelve en esta
  sesión, queda como pendiente antes de la Fase 1 semana 3-4 (scraping a
  escala).
