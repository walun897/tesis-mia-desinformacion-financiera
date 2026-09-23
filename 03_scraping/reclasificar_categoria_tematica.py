"""Aplica retroactivamente `clasificar_categoria_tematica` a los Parquet
ya recolectados en 02_corpus/raw/.

Por qué existe: `categoria_tematica` quedaba fijo en `"otro"` en los 7
spiders (ver REGISTRO_CORRECCIONES.md #7) -- se corrigió el código de
extracción para que futuras corridas lo asignen bien, pero eso no cambia
los 1.246 ítems ya recolectados. A diferencia de las correcciones de
`texto` (#1-#6), esta no necesita el HTML cacheado: `categoria_tematica`
se deriva solo de `titulo`+`texto`, que ya están correctos en el Parquet
existente. Es una reclasificación pura sobre datos ya extraídos, no una
reextracción.

Uso: python reclasificar_categoria_tematica.py <spider_name> [<spider_name> ...]
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scraper.categoria_tematica import clasificar_categoria_tematica  # noqa: E402

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "02_corpus" / "raw"


def reclasificar(spider_name: str) -> None:
    parquet_path = OUTPUT_DIR / f"{spider_name}.parquet"
    df = pd.read_parquet(parquet_path)

    nueva = (df["titulo"].fillna("") + " " + df["texto"].fillna("")).apply(
        clasificar_categoria_tematica
    )
    cambios = (nueva != df["categoria_tematica"]).sum()
    df["categoria_tematica"] = nueva

    df.to_parquet(parquet_path, index=False)
    csv_path = OUTPUT_DIR / f"{spider_name}.csv"
    df_csv = df.copy()
    df_csv["texto"] = df_csv["texto"].str.replace(r"[\r\n]+", " ", regex=True)
    df_csv.to_csv(csv_path, index=False, encoding="utf-8-sig", sep=";")

    print(f"[{spider_name}] ítems: {len(df)}, categoria_tematica reclasificada en: {cambios}")
    print(df["categoria_tematica"].value_counts().to_string())
    print(f"[{spider_name}] escrito {parquet_path} y {csv_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python reclasificar_categoria_tematica.py <spider_name> [<spider_name> ...]")
        sys.exit(1)
    for name in sys.argv[1:]:
        reclasificar(name)
