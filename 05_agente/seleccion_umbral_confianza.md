# Selección del umbral de confianza del agente validador

Complementa `M06-Methodology.tex` (Fase 3) y usa el split de datos definido
en `02_corpus/README.md` (`calibracion_prompts` / `evaluacion_final`). El
objetivo de este documento es dejar por escrito, **antes** de correr el
experimento, el criterio con el que se elige el umbral de confianza que
activa el agente verificador — para poder defenderlo en la sustentación
con algo más sólido que "0.80 porque sí".

## Problema

El anteproyecto especifica el flujo: si la confianza del clasificador LLM
es ≥0.80 se acepta su veredicto; si es <0.80 se activa el agente. También
dice explícitamente que **se experimenta con varios umbrales (0.70, 0.75,
0.80, 0.85) para determinar el valor óptimo** — es decir, 0.80 en el
diagrama de arquitectura es un valor ilustrativo, no la decisión final. Lo
que falta, y es lo que resuelve este documento, es **el criterio con el
que se decide cuál de esos valores (u otro) es el óptimo**, fijado antes de
ver los resultados para que no sea una justificación post-hoc.

## Marco metodológico

### 1. Chow's rule (Chow, 1970)

Resultado clásico de reconocimiento de patrones: dado un umbral t, se
rechaza (o en este caso, se difiere al agente) una predicción si la
probabilidad posterior máxima P(clase\|x) < t. Existe una curva óptima
error-vs-rechazo cuando las probabilidades posteriores son las verdaderas.

**Limitación relevante para este proyecto**: Chow asume probabilidades
posteriores reales. La "confianza" que reporta un LLM (vía prompting, no
vía softmax calibrado) es una estimación, no necesariamente una
probabilidad posterior verdadera — ver punto 3.

### 2. Selective classification / risk-coverage curve

Framework moderno equivalente (Geifman & El-Yaniv, *"Selective
Classification for Deep Neural Networks"*, NeurIPS 2017; extendido en
*SelectiveNet*, ICML 2019). Se barre el umbral t sobre un conjunto con
etiqueta conocida y se mide, para cada t:

- **Cobertura**: % de ítems que el clasificador acepta sin activar el
  agente (confianza ≥ t).
- **Riesgo**: tasa de error del clasificador *entre los ítems aceptados*
  (no del corpus completo).

Graficar riesgo vs. cobertura para t ∈ {0.70, 0.75, 0.80, 0.85, ...} da la
**curva riesgo-cobertura**. El umbral final se elige sobre esa curva según
un criterio explícito, por ejemplo (elegir uno antes de correr el
experimento):

- **Criterio A (orientado a F1)**: el t que maximiza el F1 macro del
  sistema híbrido completo (clasificador + agente) sobre el split de
  calibración.
- **Criterio B (orientado a riesgo, estilo Chow)**: el menor t tal que la
  precisión de los ítems aceptados sin agente sea ≥ un piso definido (ej.
  95%).
- **Criterio C (orientado a costo)**: el t que minimiza un costo esperado
  = costo_error × P(error \| aceptado) + costo_agente × P(activación del
  agente), si se quiere modelar explícitamente el costo de latencia/API
  del agente frente al costo de un error de clasificación.

Este proyecto usa el **Criterio A** por defecto (más simple de justificar y
consistente con F1 macro como métrica primaria ya definida en
`M06-Methodology.tex`), documentando también la curva completa para que el
lector pueda evaluar el trade-off en cualquier otro punto.

### 3. Caveat específico de LLMs — calibración de la confianza

Evidencia reciente muestra que la confianza verbalizada de los LLMs tiende
a estar mal calibrada (overconfidence) y no siempre correlaciona con la
corrección real de la respuesta. Por eso, **antes** de confiar en el valor
numérico de confianza del clasificador para el barrido de umbral, se debe
verificar su calibración:

- Calcular un **reliability diagram** (confianza reportada vs. accuracy
  observada, por bins) sobre `calibracion_prompts`.
- Reportar el **Expected Calibration Error (ECE)**.
- Si la calibración es pobre, documentarlo como limitación y, si el tiempo
  lo permite, aplicar una recalibración simple (ej. temperature scaling)
  antes del barrido de umbral — opcional, no bloquea el resto del
  protocolo si no alcanza el tiempo.

## Protocolo propuesto (Fase 3)

1. Sobre `calibracion_prompts` (split ya definido, no tocar
   `evaluacion_final` en este paso — evita sobreajustar el umbral al
   conjunto de evaluación final): correr el clasificador LLM elegido y
   registrar su confianza reportada por ítem.
2. Reportar calibración de esa confianza (reliability diagram + ECE) como
   hallazgo, no solo como paso intermedio.
3. Barrer t ∈ {0.70, 0.75, 0.80, 0.85} (ampliable a más valores si el
   presupuesto de tiempo/API lo permite) y construir la curva
   riesgo-cobertura.
4. Aplicar el Criterio A (F1 macro del sistema híbrido) para elegir t*.
5. Aplicar t* **una sola vez** sobre `evaluacion_final` y reportar el
   resultado final del sistema híbrido con ese umbral.
6. Registrar la corrida completa (modelo, valores de t probados, criterio,
   t* elegido, fecha) en `06_evaluacion/`, siguiendo la convención de
   registro de experimentos del proyecto.

## Qué reportar en la tesis

- La curva riesgo-cobertura completa (figura), no solo el punto elegido —
  permite al jurado ver el trade-off aunque no esté de acuerdo con el
  criterio elegido.
- El criterio de selección, declarado como fijado *antes* de ver los
  resultados.
- El reliability diagram / ECE de la confianza del clasificador, con la
  limitación de calibración de LLMs declarada explícitamente.
- Respuesta directa a "¿por qué ese valor y no otro?": *"se aplicó
  selective classification (Geifman & El-Yaniv, 2017) con criterio de
  maximizar F1 macro sobre el split de calibración; la curva completa está
  en la Figura X, y el umbral elegido fue t=___"*.

## Referencias — estado de verificación

Los títulos y existencia de estas fuentes se verificaron por búsqueda web
el 2026-09-21 (título + venue confirmados por al menos una fuente
encontrada). **Pendiente antes de citarlas en `01_bibliografia/referencias.bib`**:
confirmar autores completos, DOI/venue exacto y año de publicación
definitivo leyendo el paper original, no solo el snippet de búsqueda —
regla del proyecto de no citar sin verificar.

- Chow, C.K. (1970). Sobre el error óptimo y el trade-off de rechazo en
  reconocimiento de patrones (regla de Chow). Resultado clásico, citado
  ampliamente en la literatura de "reject option classifiers"
  ([ver survey](https://arxiv.org/pdf/2107.11277)).
- Geifman, Y. & El-Yaniv, R. (2017). *Selective Classification for Deep
  Neural Networks*. NeurIPS 2017. [arXiv:1705.08500](https://arxiv.org/pdf/1705.08500)
- Geifman, Y. & El-Yaniv, R. (2019). *SelectiveNet: A Deep Neural Network
  with an Integrated Reject Option*. ICML 2019.
  [PMLR](http://proceedings.mlr.press/v97/geifman19a/geifman19a.pdf)
- Sobre calibración/overconfidence de confianza verbalizada en LLMs (2026,
  hallazgos recientes, útiles para la limitación metodológica):
  [Are LLM Decisions Faithful to Verbal Confidence?](https://arxiv.org/html/2601.07767v1),
  [Reported Confidence in LLMs Tracks Commitment More Than Correctness](https://arxiv.org/pdf/2606.29490)

## Pendiente

- Verificar bibliografía completa antes de incorporarla a
  `01_bibliografia/referencias.bib` (ver nota arriba).
- Decidir si se implementa recalibración (temperature scaling) o se deja
  solo como limitación declarada, según tiempo disponible en Fase 3.
- Este documento es un artefacto de diseño para Fase 3 (Agente validador);
  no bloquea ni forma parte del trabajo pendiente de Fase 1.
