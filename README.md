# Sistema Híbrido LLM-Agente para Detección de Desinformación Financiera en Colombia

**Proyecto de Maestría en Inteligencia Artificial**
Universidad Sergio Arboled
Wilmar Andrey Pachón Adames | 2026–2027

---

## Descripción

Este proyecto propone un sistema híbrido que combina modelos de lenguaje de gran escala (LLMs) con un agente verificador de fuentes institucionales colombianas para la detección automatizada de desinformación financiera.

El sistema opera en dos niveles:
1. **Clasificador LLM**: Clasifica noticias financieras como verdaderas, dudosas o falsas mediante prompting especializado (zero-shot, few-shot, chain-of-thought).
2. **Agente Validador**: Se activa condicionalmente cuando el clasificador presenta baja confianza (< 0.80), consultando fuentes institucionales como la Superintendencia Financiera, el Banco de la República, el DANE y ColombiaCheck.

## Arquitectura

```
Noticia → [LLM Clasificador] → Confianza ≥ ~0.80 → Veredicto final
                               Confianza < ~0.80 → [Agente Validador] → Veredicto + Fuentes
```

Orquestado con LangGraph (grafos de estados con nodos condicionales).

## Estructura del Repositorio

```
├── bibliografia/          # Referencias verificadas (.bib + anotada)
├── corpus/                # Benchmark de desinformación financiera colombiana
├── notebooks/             # Notebooks de experimentación (Colab)
├── agente/                # Implementación del agente validador
└── docs/                  # Anteproyecto, poster, documentación
```

## Contribuciones

1. **Benchmark de evaluación**: Corpus etiquetado de desinformación financiera colombiana (800–1.000 noticias, clasificación trinaria).
2. **Arquitectura con umbral de confianza**: Activación condicional del agente cuando el LLM tiene baja certeza.
3. **Herramientas de dominio**: Tools específicas para el ecosistema regulatorio financiero colombiano (Superfinanciera, BanRep, DANE, ColombiaCheck).


## Referentes Clave

| Referencia | Año | Venue | Relevancia |
|-----------|-----|-------|------------|
| FactAgent — Li, Zhang & Malthouse | 2024 | ECAI 2024 | Enfoque agéntico modular para fact-checking |
| MACAW — Wu et al. | 2024 | arXiv:2504.06269 | 3 agentes especializados para validación cruzada |
| Kolli et al. — Hybrid Fact-Checking | 2025 | arXiv:2511.03217 | Activación condicional KG+LLM+agentes |
| ReAct — Yao et al. | 2023 | ICLR 2023 | Framework fundacional razonamiento+acción |
| Trinh et al. — Multi-Agent FC | 2025 | arXiv:2506.17878 | +12.3% F1 con 4 agentes especializados |
| DelphiAgent — Xiong et al. | 2025 | IPM Vol. 62 | Framework multi-agente confiable |

La bibliografía completa anotada está en [`bibliografia/`](./bibliografia/).

## Stack Tecnológico

- **LLMs**: Qwen 3.5, Gemma 4, Gemini Flash (evaluación comparativa)
- **Orquestador**: LangGraph
- **Entorno**: Google Colab, Python
- **Scraping**: Scrapy + Trafilatura

## Licencia

MIT License — ver [LICENSE](./LICENSE)

## Contacto

- LinkedIn: [linkedin.com/in/wandrey-pachona](https://linkedin.com/in/wandrey-pachona)
