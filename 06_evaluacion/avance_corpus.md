# Avance de recolección del corpus

Registro de avance de `03_scraping/` para seguimiento con el director —
no es un resultado de evaluación del clasificador (eso va en archivos
aparte cuando arranque Fase 2), es solo el estado del corpus.

**Cómo generarlo de nuevo:** `python 06_evaluacion/generar_avance_corpus.py`
(lee los Parquet de `02_corpus/raw/`, no requiere red).

**Archivo único con todo el corpus junto:** `python 02_corpus/consolidar_corpus.py`
genera `02_corpus/raw/corpus_consolidado.{parquet,csv}` -- las 7 fuentes
en un solo archivo, listo para abrir en Excel o cargar de una sola vez.
Es el corpus crudo (1.250 ítems), **no** la muestra final de 800-1.000
(eso todavía no se ha ejecutado, ver Metodología).

## Corte al 2026-09-22

| Fuente | Tipo | Ítems | % del total |
|---|---|---:|---:|
| ColombiaCheck | fact_checker | 725 | 58% |
| Halcones y Palomas | medio_referencia | 232 | 19% |
| Valora Analitik | medio_referencia | 111 | 9% |
| Bloomberg Línea | medio_referencia | 62 | 5% |
| Superintendencia Financiera | comunicado_oficial | 52 | 4% |
| La República | medio_referencia | 50 | 4% |
| Banco de la República | comunicado_oficial | 18 | 1% |
| **Total** | | **1.250** | 100% |

## Por clase (objetivo del anteproyecto: 300-400 / 300-400 / 200-300)

| Clase | Ítems | Objetivo | Estado |
|---|---:|---|---|
| Verdadera | 536 | 300-400 | Superado |
| Falsa | 410 | 300-400 | Superado |
| Dudosa | 304 | 200-300 | Superado |

## Concentración de fuente dentro de "verdadera" (hallazgo, no resuelto)

| Fuente | Ítems | % de "verdadera" |
|---|---:|---:|
| Halcones y Palomas | 232 | 43% |
| Valora Analitik | 111 | 21% |
| Bloomberg Línea | 62 | 12% |
| Superintendencia Financiera | 52 | 10% |
| La República | 50 | 9% |
| ColombiaCheck (verdadera) | 11 | 2% |
| Banco de la República | 18 | 3% |

Halcones y Palomas sigue siendo dominante (43%) aunque bajó de 47%. Esto
es información de diseño, no un resultado final: el corpus se va a
recortar a un tamaño objetivo con muestreo estratificado por clase **y**
por fuente (asignación desproporcionada, no proporcional — ver
`07_tesis/MainMatter/M06-Methodology.tex`), para que ninguna fuente
domine una clase en la muestra final. Esta tabla es el insumo de ese
muestreo, no el resultado.

## Pendiente

- DANE: sin resolver (comunicados en PDF, no HTML).
- Histórico completo de Superfinanciera: solo cubre el año en curso.
- AFP Factual y Forbes Colombia: excluidas por bloqueo técnico (ver
  `03_scraping/README.md`).
- Muestreo estratificado final: no ejecutado todavía.
