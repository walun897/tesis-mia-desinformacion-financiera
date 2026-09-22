"""Consolida los Parquet individuales de 02_corpus/raw/ en un único archivo.

Genera 02_corpus/raw/corpus_consolidado.parquet y .csv con TODAS las
fuentes juntas. Es el corpus crudo recolectado (~1.250 ítems al
2026-09-22), previo al muestreo estratificado final descrito en
07_tesis/MainMatter/M06-Methodology.tex -- este archivo NO es todavía la
muestra objetivo de 800-1.000, es el insumo de ese muestreo.
"""

from pathlib import Path

import pandas as pd

RAW_DIR = Path(__file__).resolve().parent / "raw"
FUENTES = [
    "colombiacheck",
    "larepublica",
    "banrep",
    "halconesypalomas",
    "valoraanalitik",
    "superfinanciera",
    "bloomberglinea",
]


def main() -> None:
    frames = []
    for nombre in FUENTES:
        path = RAW_DIR / f"{nombre}.parquet"
        if not path.exists():
            print(f"(omitido, no existe todavía: {nombre})")
            continue
        df = pd.read_parquet(path)
        frames.append(df)

    if not frames:
        print("No hay ninguna fuente recolectada todavía.")
        return

    consolidado = pd.concat(frames, ignore_index=True)

    # Sanity check: el id (hash de la URL) debe ser único en todo el
    # corpus consolidado -- si no lo es, hay un duplicado real entre
    # fuentes que la deduplicación no atrapó.
    duplicados = consolidado["id"].duplicated().sum()
    if duplicados:
        print(f"ADVERTENCIA: {duplicados} ids duplicados en el consolidado -- revisar antes de usar")

    parquet_path = RAW_DIR / "corpus_consolidado.parquet"
    csv_path = RAW_DIR / "corpus_consolidado.csv"
    consolidado.to_parquet(parquet_path, index=False)
    consolidado.to_csv(csv_path, index=False, encoding="utf-8-sig")

    print(f"Consolidado: {len(consolidado)} ítems de {len(frames)} fuentes")
    print(f"  -> {parquet_path}")
    print(f"  -> {csv_path}")
    print()
    print("Por clase:")
    print(f"  verdadera: {(consolidado['label_fuente'] == 'verdadera').sum()}")
    print(f"  falsa:     {(consolidado['label_fuente'] == 'falsa').sum()}")
    print(f"  dudosa:    {consolidado['label_fuente'].isna().sum()}")


if __name__ == "__main__":
    main()
