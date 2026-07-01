"""
generar_datos.py
Genera datos sintéticos para el proyecto Optimización de Inventario ABC-XYZ.
Empresa ficticia: NorteLogix S.A. — distribuidora de consumo masivo.

Outputs (en la misma carpeta datos/):
  productos.csv        — 120 SKUs con precio, costo, lead time, costo de pedido
  demanda_mensual.csv  — 24 meses de ventas por SKU
  inventario_actual.csv — stock al cierre con patrones deliberados (sobrestock/substock)

Ejecutar: python datos/generar_datos.py
"""

import numpy as np
import pandas as pd
from pathlib import Path

SEED    = 42
rng     = np.random.default_rng(SEED)
BASE    = Path(__file__).resolve().parent
N_MESES = 24
FECHA_INI = pd.Timestamp("2023-01-01")

# Diseño de tiers:
# Tier A (15 SKUs): alto precio, alta demanda → generarán el 80% del revenue
# Tier B (30 SKUs): precio y demanda medios  → siguiente 15%
# Tier C (75 SKUs): precio y demanda bajos   → 5% restante
N_A, N_B, N_C = 15, 30, 75
N_SKUS = N_A + N_B + N_C

CATEGORIAS = ["Bebidas", "Lácteos", "Snacks", "Limpieza", "Granos"]

# Perfil de demanda por clase (mu_base, cv)
PERFILES = {
    "AX": (65, 0.15), "AY": (55, 0.40),
    "BX": (30, 0.18), "BY": (25, 0.42), "BZ": (18, 0.75),
    "CX": (13, 0.18), "CY": ( 9, 0.48), "CZ": ( 5, 0.95),
}

# Asignación de perfil XYZ dentro de cada tier
PERFIL_POR_SKU = (
    ["AX"] * 10 + ["AY"] * 5 +
    ["BX"] * 10 + ["BY"] * 15 + ["BZ"] * 5 +
    ["CX"] *  5 + ["CY"] * 25 + ["CZ"] * 45
)

SEASONAL = np.array([0.90, 0.88, 0.92, 0.96, 1.00, 1.05,
                     1.10, 1.12, 1.08, 1.05, 1.02, 1.12])


# ── PRODUCTOS ─────────────────────────────────────────────────────────────────
def generar_productos() -> pd.DataFrame:
    filas = []
    cats  = [CATEGORIAS[i % len(CATEGORIAS)] for i in range(N_SKUS)]
    rng.shuffle(cats)

    for i in range(N_SKUS):
        if i < N_A:                              # Tier A
            precio    = int(rng.integers(6_000, 14_001))
            cost_pct  = rng.uniform(0.60, 0.72)
            lt        = int(rng.integers(8, 21))
            c_pedido  = int(rng.integers(5_000, 10_001))
        elif i < N_A + N_B:                      # Tier B
            precio    = int(rng.integers(2_000,  6_001))
            cost_pct  = rng.uniform(0.58, 0.70)
            lt        = int(rng.integers(5, 18))
            c_pedido  = int(rng.integers(3_000,  7_001))
        else:                                    # Tier C
            precio    = int(rng.integers(300,   2_001))
            cost_pct  = rng.uniform(0.55, 0.68)
            lt        = int(rng.integers(3, 15))
            c_pedido  = int(rng.integers(1_500,  4_001))

        filas.append({
            "sku":              f"SKU-{i+1:03d}",
            "nombre":           f"{cats[i][:3].upper()}-{i+1:03d}",
            "categoria":        cats[i],
            "tier_diseno":      "A" if i < N_A else ("B" if i < N_A + N_B else "C"),
            "precio_unitario":  precio,
            "costo_unitario":   int(precio * cost_pct),
            "lead_time_dias":   lt,
            "costo_pedido_fijo": c_pedido,
        })

    return pd.DataFrame(filas)


# ── DEMANDA MENSUAL ───────────────────────────────────────────────────────────
def generar_demanda(df_prod: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    fechas  = [(FECHA_INI + pd.DateOffset(months=m)).strftime("%Y-%m")
               for m in range(N_MESES)]
    rows    = []
    mu_sku  = {}

    for i, row in df_prod.iterrows():
        perfil        = PERFIL_POR_SKU[i]
        mu_base, cv   = PERFILES[perfil]
        mu_base       = int(rng.integers(int(mu_base * 0.75), int(mu_base * 1.35)))
        sigma         = mu_base * cv
        mu_sku[row["sku"]] = mu_base

        for m_idx, fecha in enumerate(fechas):
            seasonal = SEASONAL[m_idx % 12]
            mu_mes   = mu_base * seasonal
            if "Z" in perfil:                  # Z items: alta irregularidad
                mu_mes *= rng.uniform(0.3, 2.5)
            demand = max(0, int(rng.normal(mu_mes, sigma)))
            rows.append({"sku": row["sku"], "fecha": fecha,
                         "unidades_vendidas": demand})

    return pd.DataFrame(rows), mu_sku


# ── INVENTARIO ACTUAL ─────────────────────────────────────────────────────────
def generar_inventario(df_prod: pd.DataFrame, mu_sku: dict) -> pd.DataFrame:
    """
    Patrones deliberados para crear insights accionables:
    - SKU-001 a SKU-005 (AX): stock crítico < 40% del ROP  → riesgo de quiebre
    - SKU-006 a SKU-008 (AY): stock bajo ROP (50-80%)
    - SKU-046 a SKU-060 (CZ): sobrestock masivo (3.5-6×)
    - SKU-061 a SKU-075 (CZ/CY): sobrestock moderado (2-3×)
    - Resto: rango normal
    """
    rows = []
    for i, row in df_prod.iterrows():
        lt_m      = row["lead_time_dias"] / 30.0
        mu_m      = mu_sku.get(row["sku"], 10)
        sigma_est = mu_m * 0.20
        ss        = 1.645 * sigma_est * (lt_m ** 0.5)
        rop       = mu_m * lt_m + ss
        eoq       = max(10, (2 * mu_m * 12 * row["costo_pedido_fijo"] /
                             (row["costo_unitario"] * 0.25)) ** 0.5)
        opt       = rop + eoq * 0.5

        if i < 5:                                # Critical understock (AX)
            stock = max(0, int(rop * rng.uniform(0.15, 0.35)))
        elif i < 8:                              # Below ROP (AX/AY)
            stock = int(rop * rng.uniform(0.52, 0.78))
        elif 45 <= i < 60:                       # Massive overstock (CZ)
            stock = int(opt * rng.uniform(3.5, 6.0))
        elif 60 <= i < 75:                       # Moderate overstock (CZ/CY)
            stock = int(opt * rng.uniform(2.0, 3.2))
        else:                                    # Normal range
            stock = int(rop + eoq * rng.uniform(0.3, 0.9))

        rows.append({"sku": row["sku"], "stock_actual": max(0, stock),
                     "fecha_corte": "2025-01"})

    return pd.DataFrame(rows)


# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    df_prod     = generar_productos()
    df_demanda, mu_sku = generar_demanda(df_prod)
    df_inv      = generar_inventario(df_prod, mu_sku)

    df_prod.to_csv(BASE / "productos.csv",         index=False, encoding="utf-8-sig")
    df_demanda.to_csv(BASE / "demanda_mensual.csv", index=False, encoding="utf-8-sig")
    df_inv.to_csv(BASE / "inventario_actual.csv",   index=False, encoding="utf-8-sig")

    print(f"productos.csv         : {len(df_prod)} SKUs")
    print(f"demanda_mensual.csv   : {len(df_demanda)} registros "
          f"({N_MESES} meses x {N_SKUS} SKUs)")
    print(f"inventario_actual.csv : {len(df_inv)} SKUs")


if __name__ == "__main__":
    main()
