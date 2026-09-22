# Guía de anotación — Taxonomía trinaria y protocolo humano-LLM

Complementa `criterios_seleccion_fuentes.md`. Basado en
`M06-Methodology.tex` (etiquetado y validación) y en las decisiones de la
sesión de planeación: anotación humano-LLM sin anotadores adicionales
(ver `CLAUDE.md`, sección "Decisiones confirmadas").

## Taxonomía y criterios operacionales

### Verdadera
La afirmación central de la noticia es corroborable con una fuente oficial
o un medio de referencia, sin contradicciones con datos verificables.

Se etiqueta automáticamente como **verdadera** cuando el ítem proviene
directamente de:
- Un comunicado oficial (BanRep, SFC, DANE), o
- Un medio de referencia (Portafolio, La República, El Tiempo-Economía) y
  reporta datos/cifras verificables (tasas, fechas, cifras oficiales).

### Falsa
La afirmación central es contradicha explícitamente por evidencia
verificable, o un fact-checker IFCN la calificó como falsa.

Se etiqueta automáticamente como **falsa** cuando el ítem proviene de un
fact-checker IFCN con calificación "Falso" (ColombiaCheck) o equivalente
verificado (AFP Factual Colombia — pendiente de verificar su taxonomía,
ver `criterios_seleccion_fuentes.md`).

### Dudosa
No cumple los criterios claros de verdadera ni falsa. Incluye:
- Calificada por el fact-checker con una categoría intermedia — en
  ColombiaCheck, específicamente **"Cuestionable"** o **"Verdadero, pero"**
  (taxonomía real verificada en colombiacheck.com/metodologia el
  2026-09-22; reemplaza la redacción genérica "parcialmente cierta /
  descontextualizada / sin evidencia suficiente" que tenía esta sección
  antes de verificar contra el sitio real — ver `03_scraping/scraper/rating_maps.py`).
- "Chequeo Múltiple" de ColombiaCheck (varias afirmaciones verificadas en
  un solo artículo) no es una calificación de verdad — se trata como
  candidata a dudosa por defecto y requiere revisión manual para separar
  las afirmaciones individuales.
- Contenido viral (cadenas, redes sociales) sobre temas financieros **sin**
  verificación institucional, pero con apariencia plausible.
- Mezcla elementos verdaderos y falsos en la misma pieza.
- La fuente citada dentro de la noticia no se puede confirmar que existe.

**Estas son las únicas que requieren anotación manual** — verdadera/falsa
se derivan de la fuente primaria (ver arriba), con un control de calidad
por muestreo (ver "Control de calidad" abajo).

## Checklist de decisión (humano y LLM usan el mismo checklist)

Para cada ítem candidato a "dudosa", responder:
1. ¿La fuente citada en la noticia existe y es verificable?
2. ¿El dato/cifra mencionado es verificable contra una fuente oficial?
3. ¿El lenguaje es neutral o marcadamente sensacionalista?
4. ¿Menciona entidades regulatorias reales (SFC, BanRep, DANE) de forma
   correcta, o las nombra mal / les atribuye algo que no corresponde?
5. ¿Hay elementos verdaderos y falsos mezclados en la misma pieza?

Este checklist es el mismo que alimenta el prompting chain-of-thought del
clasificador LLM en la Fase 2 (`M06-Methodology.tex`, Nivel 4), para que la
guía humana y el prompt del modelo sean consistentes.

## Protocolo de anotación humano-LLM

Dado que no hay anotadores humanos adicionales (decisión confirmada en
`CLAUDE.md`), el protocolo es:

1. **Filtrado automático**: verdadera/falsa por regla de fuente primaria
   (arriba). Solo los candidatos a "dudosa" pasan a anotación manual.
2. **Primera pasada humana**: el usuario etiqueta cada candidato a dudosa
   usando el checklist, sin ver la respuesta de ningún LLM todavía.
3. **Segunda opinión LLM**: se pasa el mismo ítem y checklist a un LLM
   (Gemini 3.5 Flash-Lite o GPT-4o-mini para el grueso del volumen, por
   costo). Para los ítems donde el LLM y el humano **no coinciden**, se
   pasa una tercera consulta a Fable 5.1 (crédito de $100, ver
   `CLAUDE.md`) como árbitro de razonamiento extendido — no como
   anotador de rutina, solo para los desacuerdos.
4. **Resolución final**: el usuario revisa el desacuerdo con la opinión de
   Fable 5.1 en mano y decide la etiqueta final. Se registra: etiqueta
   humana inicial, etiqueta LLM, etiqueta de arbitraje (si aplica),
   etiqueta final, y una nota corta de por qué se resolvió así.
5. **Cálculo de Cohen's Kappa**: sobre una muestra de calibración de ~200
   ítems dudosos, se calcula kappa entre la etiqueta humana inicial y la
   etiqueta LLM (paso 3, antes del arbitraje). Meta: κ ≥ 0.70. Si no se
   alcanza, se refina esta guía (criterios ambiguos, checklist insuficiente)
   y se recalibra antes de etiquetar el resto del corpus.

### Limitación metodológica (declarar en el capítulo de metodología)
Este diseño mide **acuerdo humano-LLM**, no el acuerdo inter-anotador
clásico entre 2+ evaluadores humanos independientes que asume la fórmula
original de Cohen's Kappa y que describe `M06-Methodology.tex`. Es un
diseño válido y cada vez más usado en la literatura de anotación asistida
por LLM, pero debe declararse explícitamente como tal, no presentarse como
IAA (inter-annotator agreement) estándar.

## Control de calidad para verdadera/falsa (etiquetado automático)

Aunque no requieren anotación manual completa, se revisa manualmente una
muestra aleatoria del 10% de los ítems etiquetados automáticamente como
verdadera/falsa, para detectar errores de scraping (p. ej. una noticia mal
atribuida a una fuente, o un fact-check mal parseado). Si el error rate en
la muestra supera 5%, se revisa el proceso de scraping antes de continuar.

## Ejemplos ilustrativos (ficticios, solo para calibrar el checklist)

> Estos ejemplos son inventados para entrenar el criterio de anotación,
> no son noticias reales — no deben citarse como casos del corpus.

- **Verdadera (ejemplo ilustrativo)**: "El Banco de la República mantuvo la
  tasa de interés de referencia en su reunión de política monetaria",
  corroborado por el comunicado oficial de BanRep.
- **Falsa (ejemplo ilustrativo)**: "Circula un mensaje de WhatsApp que dice
  que el Gobierno congelará las cuentas de ahorro por la reforma
  tributaria" — calificado como falso por ColombiaCheck, sin fuente oficial
  que lo respalde.
- **Dudosa (ejemplo ilustrativo)**: una publicación viral que cita "una
  fuente interna de la Superfinanciera" sin nombrarla, sobre una supuesta
  intervención a una entidad financiera, sin comunicado oficial que lo
  confirme ni lo desmienta al momento de la revisión.
