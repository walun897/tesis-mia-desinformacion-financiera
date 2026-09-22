"""Genera un resumen legible del avance de recolección del corpus.

Lee 02_corpus/raw/*.parquet y calcula totales por fuente y por clase,
para actualizar 06_evaluacion/avance_corpus.md a mano con estos números
(no sobrescribe el .md automáticamente, porque ese archivo también tiene
texto interpretativo que no se debe perder).
"""

from pathlib import Path

import pandas as pd

RAW_DIR = Path(__file__).resolve().parents[1] / "02_corpus" / "raw"
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
        df["fuente_archivo"] = nombre
        frames.append(df)

    full = pd.concat(frames, ignore_index=True)
    total = len(full)
    verdadera = (full["label_fuente"] == "verdadera").sum()
    falsa = (full["label_fuente"] == "falsa").sum()
    dudosa = full["label_fuente"].isna().sum()

    print(f"Total: {total}")
    print(f"  verdadera: {verdadera}  (objetivo 300-400)")
    print(f"  falsa:     {falsa}  (objetivo 300-400)")
    print(f"  dudosa:    {dudosa}  (objetivo 200-300)")
    print()
    print("Por fuente:")
    for nombre, grupo in full.groupby("fuente_archivo"):
        print(f"  {nombre:20s} {len(grupo):5d}  ({100 * len(grupo) / total:.0f}% del total)")
    print()
    print("Concentración de fuente dentro de 'verdadera':")
    solo_verdadera = full[full["label_fuente"] == "verdadera"]
    for nombre, grupo in solo_verdadera.groupby("fuente_archivo"):
        pct = 100 * len(grupo) / len(solo_verdadera) if len(solo_verdadera) else 0
        print(f"  {nombre:20s} {len(grupo):5d}  ({pct:.0f}% de verdadera)")


if __name__ == "__main__":
    main()
