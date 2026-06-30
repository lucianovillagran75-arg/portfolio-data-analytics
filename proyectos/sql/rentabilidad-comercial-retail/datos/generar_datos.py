"""
Genera el dataset del proyecto "TiendaNova" de forma reproducible (semilla fija).

Salidas (en esta misma carpeta `datos/`):
  raw/dim_customers.csv
  raw/dim_products.csv
  raw/dim_stores.csv
  raw/fact_sales.csv
  retail.db   (SQLite con las 4 tablas + índices)

El dataset incluye PROBLEMAS DELIBERADOS para descubrir con SQL:
  1. Productos vendidos bajo margen (descuentos que dejan margen negativo).
  2. Productos de baja rotación (capital improductivo).
  3. Churn de clientes (un grupo deja de comprar a mitad del período).
  4. Brecha entre sucursales (la región "Sur" rinde por debajo del resto).

Uso:  python generar_datos.py
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
rng = np.random.default_rng(SEED)

BASE = Path(__file__).resolve().parent
RAW = BASE / "raw"
RAW.mkdir(parents=True, exist_ok=True)

START = pd.Timestamp("2024-01-01")
END = pd.Timestamp("2025-12-31")


def build_stores() -> pd.DataFrame:
    stores = [
        ("S01", "TiendaNova Centro", "Córdoba", "Centro"),
        ("S02", "TiendaNova Norte", "Salta", "Norte"),
        ("S03", "TiendaNova Litoral", "Rosario", "Centro"),
        ("S04", "TiendaNova Sur", "Bariloche", "Sur"),    # región rezagada
        ("S05", "TiendaNova Cuyo", "Mendoza", "Cuyo"),
    ]
    return pd.DataFrame(stores, columns=["store_id", "store_name", "city", "region"])


def build_products() -> pd.DataFrame:
    categories = {
        "Bebidas": (300, 1200),
        "Almacén": (200, 1500),
        "Limpieza": (250, 2000),
        "Perfumería": (400, 3500),
        "Snacks": (150, 900),
        "Bazar": (500, 6000),
    }
    rows = []
    pid = 1
    for cat, (cost_lo, cost_hi) in categories.items():
        n = rng.integers(6, 9)
        for _ in range(n):
            unit_cost = float(rng.integers(cost_lo, cost_hi))
            markup = rng.uniform(1.25, 1.70)
            list_price = round(unit_cost * markup, -1)
            rows.append(
                {
                    "product_id": f"P{pid:03d}",
                    "product_name": f"{cat} {pid:03d}",
                    "category": cat,
                    "unit_cost": round(unit_cost, 2),
                    "list_price": float(list_price),
                }
            )
            pid += 1
    df = pd.DataFrame(rows)

    # PROBLEMA 1: 4 productos con margen muy fino (se volverán negativos al descontar)
    thin = rng.choice(df.index, size=4, replace=False)
    df.loc[thin, "list_price"] = (df.loc[thin, "unit_cost"] * 1.08).round(2)
    df["thin_margin_flag"] = False
    df.loc[thin, "thin_margin_flag"] = True

    # PROBLEMA 2: 5 productos de baja rotación (marcados para casi no vender)
    dead = rng.choice(df.index.difference(thin), size=5, replace=False)
    df["dead_stock_flag"] = False
    df.loc[dead, "dead_stock_flag"] = True
    return df


def build_customers(n: int = 800) -> pd.DataFrame:
    segments = ["Ocasional", "Minorista", "Mayorista", "VIP"]
    seg_p = [0.45, 0.35, 0.12, 0.08]
    cities = {
        "Centro": ["Córdoba", "Rosario"],
        "Norte": ["Salta", "Tucumán"],
        "Sur": ["Bariloche", "Neuquén"],
        "Cuyo": ["Mendoza", "San Juan"],
    }
    regions = list(cities.keys())
    region_p = [0.40, 0.20, 0.18, 0.22]
    rows = []
    for i in range(1, n + 1):
        region = rng.choice(regions, p=region_p)
        city = rng.choice(cities[region])
        segment = rng.choice(segments, p=seg_p)
        signup = START + pd.Timedelta(days=int(rng.integers(-540, 600)))
        rows.append(
            {
                "customer_id": f"C{i:04d}",
                "customer_name": f"Cliente {i:04d}",
                "segment": segment,
                "city": city,
                "region": region,
                "signup_date": signup.date().isoformat(),
            }
        )
    df = pd.DataFrame(rows)

    # PROBLEMA 3: 18% de los clientes "churnean" (dejan de comprar pasado el mes ~12)
    churn = rng.choice(df.index, size=int(0.18 * len(df)), replace=False)
    df["churn_flag"] = False
    df.loc[churn, "churn_flag"] = True
    return df


def seasonality_factor(ts: pd.Timestamp) -> float:
    """Pico en diciembre, valle en febrero; leve crecimiento interanual."""
    month = ts.month
    base = {
        1: 0.95, 2: 0.80, 3: 1.00, 4: 1.00, 5: 1.05, 6: 1.05,
        7: 1.10, 8: 1.00, 9: 1.00, 10: 1.05, 11: 1.15, 12: 1.45,
    }[month]
    growth = 1.0 + 0.08 * ((ts.year - 2024))
    return base * growth


def build_sales(customers, products, stores) -> pd.DataFrame:
    seg_orders = {"Ocasional": 4, "Minorista": 14, "Mayorista": 30, "VIP": 40}
    seg_qty = {"Ocasional": (1, 3), "Minorista": (1, 5), "Mayorista": (5, 25), "VIP": (2, 8)}

    prod_weight = np.where(products["dead_stock_flag"].values, 0.05, 1.0)
    prod_weight = prod_weight / prod_weight.sum()
    region_to_store = stores.set_index("region")["store_id"].to_dict()

    rows = []
    sale_id = 1
    total_days = (END - START).days

    for _, cust in customers.iterrows():
        n_orders = rng.poisson(seg_orders[cust["segment"]])
        if n_orders == 0:
            continue
        for _ in range(n_orders):
            day_offset = int(rng.integers(0, total_days + 1))
            date = START + pd.Timedelta(days=day_offset)

            if cust["churn_flag"] and day_offset > 365 and rng.random() > 0.05:
                continue
            if rng.random() > min(seasonality_factor(date) / 1.45, 1.0):
                continue

            if rng.random() < 0.75 and cust["region"] in region_to_store:
                store_id = region_to_store[cust["region"]]
            else:
                store_id = rng.choice(stores["store_id"].values)

            n_lines = 1 + rng.poisson(1.2)
            chosen = rng.choice(products.index, size=n_lines, replace=False, p=prod_weight)
            for pidx in chosen:
                prod = products.loc[pidx]
                qlo, qhi = seg_qty[cust["segment"]]
                qty = int(rng.integers(qlo, qhi + 1))
                if cust["region"] == "Sur":
                    qty = max(1, int(qty * 0.6))

                if prod["thin_margin_flag"]:
                    discount = rng.choice([0.10, 0.15, 0.20, 0.25])
                else:
                    discount = rng.choice([0.0, 0.0, 0.0, 0.05, 0.10],
                                          p=[0.55, 0.15, 0.05, 0.15, 0.10])

                unit_price = round(prod["list_price"] * (1 - discount), 2)
                rows.append(
                    {
                        "sale_id": sale_id,
                        "date": date.date().isoformat(),
                        "customer_id": cust["customer_id"],
                        "product_id": prod["product_id"],
                        "store_id": store_id,
                        "quantity": qty,
                        "unit_price": unit_price,
                        "discount": discount,
                        "unit_cost": prod["unit_cost"],
                    }
                )
                sale_id += 1

    df = pd.DataFrame(rows)
    df["revenue"] = (df["unit_price"] * df["quantity"]).round(2)
    df["cost"] = (df["unit_cost"] * df["quantity"]).round(2)
    df["margin"] = (df["revenue"] - df["cost"]).round(2)
    return df.sort_values("date").reset_index(drop=True)


def save_all(customers, products, stores, sales) -> Path:
    customers.to_csv(RAW / "dim_customers.csv", index=False)
    products.to_csv(RAW / "dim_products.csv", index=False)
    stores.to_csv(RAW / "dim_stores.csv", index=False)
    sales.to_csv(RAW / "fact_sales.csv", index=False)

    db_path = BASE / "retail.db"
    if db_path.exists():
        db_path.unlink()
    con = sqlite3.connect(db_path)
    try:
        customers.to_sql("dim_customers", con, index=False)
        products.to_sql("dim_products", con, index=False)
        stores.to_sql("dim_stores", con, index=False)
        sales.to_sql("fact_sales", con, index=False)
        con.executescript(
            """
            CREATE INDEX idx_sales_date     ON fact_sales(date);
            CREATE INDEX idx_sales_customer ON fact_sales(customer_id);
            CREATE INDEX idx_sales_product  ON fact_sales(product_id);
            CREATE INDEX idx_sales_store    ON fact_sales(store_id);
            """
        )
        con.commit()
    finally:
        con.close()
    return db_path


def main() -> None:
    print(f"Semilla fija = {SEED}. Generando TiendaNova...")
    stores = build_stores()
    products = build_products()
    customers = build_customers()
    sales = build_sales(customers, products, stores)
    db_path = save_all(customers, products, stores, sales)

    print("Listo. Resumen:")
    print(f"  Sucursales : {len(stores):>7,}")
    print(f"  Productos  : {len(products):>7,}  (margen fino: {int(products.thin_margin_flag.sum())}, "
          f"baja rotación: {int(products.dead_stock_flag.sum())})")
    print(f"  Clientes   : {len(customers):>7,}  (churn: {int(customers.churn_flag.sum())})")
    print(f"  Ventas     : {len(sales):>7,}  líneas")
    print(f"  Facturación: ${sales.revenue.sum():>14,.0f}")
    print(f"  Margen     : ${sales.margin.sum():>14,.0f}  ({sales.margin.sum()/sales.revenue.sum():.1%})")
    print(f"  Líneas con margen negativo: {(sales.margin < 0).sum():,}")
    print(f"  Base SQLite: {db_path}")


if __name__ == "__main__":
    main()
