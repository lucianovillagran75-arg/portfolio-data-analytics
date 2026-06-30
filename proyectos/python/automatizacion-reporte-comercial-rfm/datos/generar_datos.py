"""
Genera el dataset "TiendaNova" de forma reproducible (semilla fija).
Es el mismo negocio que el proyecto SQL, para mostrar Python y SQL sobre el mismo caso.

Salidas (en esta misma carpeta `datos/`):
  raw/clientes.csv · raw/productos.csv · raw/sucursales.csv · raw/ventas.csv

Uso:  python generar_datos.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

SEMILLA = 42
rng = np.random.default_rng(SEMILLA)

BASE = Path(__file__).resolve().parent
CRUDOS = BASE / "raw"
CRUDOS.mkdir(parents=True, exist_ok=True)

INICIO = pd.Timestamp("2024-01-01")
FIN = pd.Timestamp("2025-12-31")


def construir_sucursales() -> pd.DataFrame:
    sucursales = [
        ("S01", "TiendaNova Centro", "Córdoba", "Centro"),
        ("S02", "TiendaNova Norte", "Salta", "Norte"),
        ("S03", "TiendaNova Litoral", "Rosario", "Centro"),
        ("S04", "TiendaNova Sur", "Bariloche", "Sur"),
        ("S05", "TiendaNova Cuyo", "Mendoza", "Cuyo"),
    ]
    return pd.DataFrame(
        sucursales, columns=["id_sucursal", "nombre_sucursal", "ciudad", "region"]
    )


def construir_productos() -> pd.DataFrame:
    categorias = {
        "Bebidas": (300, 1200),
        "Almacén": (200, 1500),
        "Limpieza": (250, 2000),
        "Perfumería": (400, 3500),
        "Snacks": (150, 900),
        "Bazar": (500, 6000),
    }
    filas = []
    pid = 1
    for cat, (costo_lo, costo_hi) in categorias.items():
        n = rng.integers(6, 9)
        for _ in range(n):
            costo_unitario = float(rng.integers(costo_lo, costo_hi))
            recargo = rng.uniform(1.25, 1.70)
            precio_lista = round(costo_unitario * recargo, -1)
            filas.append(
                {
                    "id_producto": f"P{pid:03d}",
                    "nombre_producto": f"{cat} {pid:03d}",
                    "categoria": cat,
                    "costo_unitario": round(costo_unitario, 2),
                    "precio_lista": float(precio_lista),
                }
            )
            pid += 1
    df = pd.DataFrame(filas)
    fino = rng.choice(df.index, size=4, replace=False)
    df["es_margen_fino"] = False
    df.loc[fino, "precio_lista"] = (df.loc[fino, "costo_unitario"] * 1.08).round(2)
    df.loc[fino, "es_margen_fino"] = True
    baja = rng.choice(df.index.difference(fino), size=5, replace=False)
    df["es_baja_rotacion"] = False
    df.loc[baja, "es_baja_rotacion"] = True
    return df


def construir_clientes(n: int = 800) -> pd.DataFrame:
    segmentos = ["Ocasional", "Minorista", "Mayorista", "VIP"]
    seg_p = [0.45, 0.35, 0.12, 0.08]
    ciudades = {
        "Centro": ["Córdoba", "Rosario"],
        "Norte": ["Salta", "Tucumán"],
        "Sur": ["Bariloche", "Neuquén"],
        "Cuyo": ["Mendoza", "San Juan"],
    }
    regiones = list(ciudades.keys())
    region_p = [0.40, 0.20, 0.18, 0.22]
    filas = []
    for i in range(1, n + 1):
        region = rng.choice(regiones, p=region_p)
        ciudad = rng.choice(ciudades[region])
        segmento = rng.choice(segmentos, p=seg_p)
        alta = INICIO + pd.Timedelta(days=int(rng.integers(-540, 600)))
        filas.append(
            {
                "id_cliente": f"C{i:04d}",
                "nombre_cliente": f"Cliente {i:04d}",
                "segmento": segmento,
                "ciudad": ciudad,
                "region": region,
                "fecha_alta": alta.date().isoformat(),
            }
        )
    df = pd.DataFrame(filas)
    fuga = rng.choice(df.index, size=int(0.18 * len(df)), replace=False)
    df["es_fuga"] = False
    df.loc[fuga, "es_fuga"] = True
    return df


def factor_estacional(ts: pd.Timestamp) -> float:
    mes = ts.month
    base = {
        1: 0.95, 2: 0.80, 3: 1.00, 4: 1.00, 5: 1.05, 6: 1.05,
        7: 1.10, 8: 1.00, 9: 1.00, 10: 1.05, 11: 1.15, 12: 1.45,
    }[mes]
    return base * (1.0 + 0.08 * (ts.year - 2024))


def construir_ventas(clientes, productos, sucursales) -> pd.DataFrame:
    seg_ordenes = {"Ocasional": 4, "Minorista": 14, "Mayorista": 30, "VIP": 40}
    seg_cant = {"Ocasional": (1, 3), "Minorista": (1, 5), "Mayorista": (5, 25), "VIP": (2, 8)}
    peso_prod = np.where(productos["es_baja_rotacion"].values, 0.05, 1.0)
    peso_prod = peso_prod / peso_prod.sum()
    region_a_sucursal = sucursales.set_index("region")["id_sucursal"].to_dict()

    filas = []
    id_venta = 1
    dias_totales = (FIN - INICIO).days
    for _, cli in clientes.iterrows():
        n_ordenes = rng.poisson(seg_ordenes[cli["segmento"]])
        if n_ordenes == 0:
            continue
        for _ in range(n_ordenes):
            offset_dia = int(rng.integers(0, dias_totales + 1))
            fecha = INICIO + pd.Timedelta(days=offset_dia)
            if cli["es_fuga"] and offset_dia > 365 and rng.random() > 0.05:
                continue
            if rng.random() > min(factor_estacional(fecha) / 1.45, 1.0):
                continue
            if rng.random() < 0.75 and cli["region"] in region_a_sucursal:
                id_sucursal = region_a_sucursal[cli["region"]]
            else:
                id_sucursal = rng.choice(sucursales["id_sucursal"].values)
            n_lineas = 1 + rng.poisson(1.2)
            elegidos = rng.choice(productos.index, size=n_lineas, replace=False, p=peso_prod)
            for pidx in elegidos:
                prod = productos.loc[pidx]
                clo, chi = seg_cant[cli["segmento"]]
                cantidad = int(rng.integers(clo, chi + 1))
                if cli["region"] == "Sur":
                    cantidad = max(1, int(cantidad * 0.6))
                if prod["es_margen_fino"]:
                    descuento = rng.choice([0.10, 0.15, 0.20, 0.25])
                else:
                    descuento = rng.choice([0.0, 0.0, 0.0, 0.05, 0.10],
                                           p=[0.55, 0.15, 0.05, 0.15, 0.10])
                precio_unitario = round(prod["precio_lista"] * (1 - descuento), 2)
                filas.append(
                    {
                        "id_venta": id_venta,
                        "fecha": fecha.date().isoformat(),
                        "id_cliente": cli["id_cliente"],
                        "id_producto": prod["id_producto"],
                        "id_sucursal": id_sucursal,
                        "cantidad": cantidad,
                        "precio_unitario": precio_unitario,
                        "descuento": descuento,
                        "costo_unitario": prod["costo_unitario"],
                    }
                )
                id_venta += 1

    df = pd.DataFrame(filas)
    df["ingreso"] = (df["precio_unitario"] * df["cantidad"]).round(2)
    df["costo"] = (df["costo_unitario"] * df["cantidad"]).round(2)
    df["margen"] = (df["ingreso"] - df["costo"]).round(2)
    return df.sort_values("fecha").reset_index(drop=True)


def main() -> None:
    print(f"Semilla fija = {SEMILLA}. Generando TiendaNova...")
    sucursales = construir_sucursales()
    productos = construir_productos()
    clientes = construir_clientes()
    ventas = construir_ventas(clientes, productos, sucursales)
    clientes.to_csv(CRUDOS / "clientes.csv", index=False)
    productos.to_csv(CRUDOS / "productos.csv", index=False)
    sucursales.to_csv(CRUDOS / "sucursales.csv", index=False)
    ventas.to_csv(CRUDOS / "ventas.csv", index=False)
    print(f"Listo: {len(ventas):,} ventas, {len(clientes)} clientes -> {CRUDOS}")


if __name__ == "__main__":
    main()
