"""Consolida los Parquet individuales de 02_corpus/raw/ en un único archivo.

Genera 02_corpus/raw/corpus_consolidado.parquet y .csv con TODAS las
fuentes juntas. Es el corpus crudo recolectado (~1.250 ítems al
2026-09-22), previo al muestreo estratificado final descrito en
07_tesis/MainMatter/M06-Methodology.tex -- este archivo NO es todavía la
muestra objetivo de 800-1.000, es el insumo de ese muestreo.
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "03_scraping"))
from scraper.utils import derivar_clase  # noqa: E402

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

    # Columna `clase` explícita (verdadera|falsa|dudosa), agregada junto a
    # label_fuente -- ver derivar_clase() en 03_scraping/scraper/utils.py
    # y REGISTRO_CORRECCIONES.md #7 (label_fuente=None sin esto se veía
    # como una celda vacía sin explicación en el CSV).
    consolidado["clase"] = consolidado["label_fuente"].apply(derivar_clase)

    # Sanity check: el id (hash de la URL) debe ser único en todo el
    # corpus consolidado -- si no lo es, hay un duplicado real entre
    # fuentes que la deduplicación no atrapó.
    duplicados = consolidado["id"].duplicated().sum()
    if duplicados:
        print(f"ADVERTENCIA: {duplicados} ids duplicados en el consolidado -- revisar antes de usar")

    parquet_path = RAW_DIR / "corpus_consolidado.parquet"
    csv_path = RAW_DIR / "corpus_consolidado.csv"
    consolidado.to_parquet(parquet_path, index=False)

    # Para el CSV (y solo para el CSV): se aplanan los saltos de línea
    # internos del texto del artículo. Un salto de línea dentro de un
    # campo con comillas es CSV válido (RFC 4180), pero muchos visores
    # simples -- incluido Excel al abrir el archivo con doble clic -- no
    # lo manejan bien y fragmentan visualmente la fila. El Parquet no se
    # toca: conserva el texto con sus párrafos originales.
    consolidado_csv = consolidado.copy()
    consolidado_csv["texto"] = consolidado_csv["texto"].str.replace(r"[\r\n]+", " ", regex=True)

    # sep=';' porque Excel en configuración regional en español espera
    # punto y coma como separador de columnas (usa la coma como separador
    # decimal) -- con coma como separador, Excel no divide bien las
    # columnas al abrir el archivo directamente.
    consolidado_csv.to_csv(csv_path, index=False, encoding="utf-8-sig", sep=";")

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
