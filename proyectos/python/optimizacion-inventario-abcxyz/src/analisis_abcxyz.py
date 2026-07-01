"""
analisis_abcxyz.py
Análisis ABC-XYZ + Política de Inventario Óptima — NorteLogix S.A.

Clasifica los 120 SKUs en una matriz ABC-XYZ, calcula el stock de seguridad
estadístico, el punto de reorden y el lote económico de compra (EOQ), identifica
capital inmovilizado en sobrestock y ventas en riesgo por quiebres, y genera un
dashboard ejecutivo de 5 paneles.

Ejecutar: python src/analisis_abcxyz.py
Requiere: pandas, numpy, matplotlib
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
from pathlib import Path

BASE  = Path(__file__).resolve().parent.parent
DATOS = BASE / "datos"
OUT   = BASE / "output"
OUT.mkdir(exist_ok=True)

# -- PARÁMETROS ----------------------------------------------------------------
NIVEL_SERVICIO = 0.95
Z_SCORE        = 1.645      # norm.ppf(0.95)
TASA_HOLDING   = 0.25       # 25% del costo unitario anual
ABC_A          = 0.80
ABC_B          = 0.95
XYZ_X          = 0.30
XYZ_Y          = 0.60
COSTO_HORA     = 3_000      # ARS/h analista
HORAS_MENSUAL  = 7.5        # 8h manual : 30 min automatizado

# -- PALETA --------------------------------------------------------------------
AZUL_OSC  = "#1F4E79"
AZUL_MED  = "#2E75B6"
AZUL_CLAR = "#BDD7EE"
VERDE     = "#70AD47"
AMARILLO  = "#FFD966"
ROJO      = "#FF6B6B"
NARANJA   = "#ED7D31"
GRIS      = "#F2F2F2"

COLORES_CLASE = {
    "AX": AZUL_OSC,  "AY": AZUL_MED,  "AZ": NARANJA,
    "BX": VERDE,     "BY": AZUL_CLAR, "BZ": AMARILLO,
    "CX": "#C6EFCE", "CY": "#FFEB9C", "CZ": "#FFCCCC",
}
COLORES_MATRIX = {
    ("A","X"): AZUL_OSC, ("A","Y"): AZUL_MED,  ("A","Z"): NARANJA,
    ("B","X"): VERDE,    ("B","Y"): AZUL_CLAR,  ("B","Z"): AMARILLO,
    ("C","X"): "#C6EFCE",("C","Y"): "#FFEB9C",  ("C","Z"): "#FFCCCC",
}
TEXTO_OSCURO = {AZUL_OSC, AZUL_MED, NARANJA, VERDE}


# ══════════════════════════════════════════════════════════════════════════════
# CARGA
# ══════════════════════════════════════════════════════════════════════════════
def cargar() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    prod = pd.read_csv(DATOS / "productos.csv")
    dem  = pd.read_csv(DATOS / "demanda_mensual.csv")
    inv  = pd.read_csv(DATOS / "inventario_actual.csv")
    return prod, dem, inv


# ══════════════════════════════════════════════════════════════════════════════
# CLASIFICACIÓN ABC
# ══════════════════════════════════════════════════════════════════════════════
def clasificar_abc(prod: pd.DataFrame, dem: pd.DataFrame) -> pd.DataFrame:
    rev = (
        dem.merge(prod[["sku", "precio_unitario"]], on="sku")
           .assign(revenue=lambda x: x["unidades_vendidas"] * x["precio_unitario"])
           .groupby("sku")["revenue"].sum()
           .reset_index(name="revenue_total")
           .sort_values("revenue_total", ascending=False)
           .reset_index(drop=True)
    )
    rev["pct_rev"]  = rev["revenue_total"] / rev["revenue_total"].sum()
    rev["pct_acum"] = rev["pct_rev"].cumsum()

    def _abc(p):
        return "A" if p <= ABC_A else ("B" if p <= ABC_B else "C")

    rev["abc"] = rev["pct_acum"].apply(_abc)
    return rev


# ══════════════════════════════════════════════════════════════════════════════
# CLASIFICACIÓN XYZ
# ══════════════════════════════════════════════════════════════════════════════
def clasificar_xyz(dem: pd.DataFrame) -> pd.DataFrame:
    stats = (
        dem.groupby("sku")["unidades_vendidas"]
           .agg(demanda_avg="mean", demanda_std="std", demanda_sum="sum")
           .reset_index()
    )
    stats["cv"] = stats["demanda_std"] / stats["demanda_avg"].replace(0, 1)

    def _xyz(cv):
        return "X" if cv < XYZ_X else ("Y" if cv < XYZ_Y else "Z")

    stats["xyz"] = stats["cv"].apply(_xyz)
    return stats


# ══════════════════════════════════════════════════════════════════════════════
# POLÍTICA DE INVENTARIO (SS, ROP, EOQ)
# ══════════════════════════════════════════════════════════════════════════════
def calcular_politica(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["lt_meses"]      = df["lead_time_dias"] / 30.0
    df["safety_stock"]  = (Z_SCORE * df["demanda_std"] *
                           np.sqrt(df["lt_meses"])).clip(lower=0)
    df["rop"]           = df["demanda_avg"] * df["lt_meses"] + df["safety_stock"]
    df["demanda_anual"] = df["demanda_avg"] * 12
    df["costo_holding"] = df["costo_unitario"] * TASA_HOLDING
    df["eoq"]           = np.sqrt(
        2 * df["demanda_anual"] * df["costo_pedido_fijo"] /
        df["costo_holding"].replace(0, 1)
    )
    df["stock_optimo"]  = df["rop"] + df["eoq"] / 2

    for col in ["safety_stock", "rop", "eoq", "stock_optimo"]:
        df[col] = df[col].clip(lower=0).round(0).astype(int)

    # Sobrestock: stock por encima de ROP + 1 ciclo EOQ
    df["exceso_unidades"]     = (df["stock_actual"] - (df["rop"] + df["eoq"])).clip(lower=0)
    df["capital_inmovilizado"]= df["exceso_unidades"] * df["costo_unitario"]

    # Substock: stock por debajo del ROP
    df["deficit_unidades"] = (df["rop"] - df["stock_actual"]).clip(lower=0)
    df["riesgo_ventas"]    = df["deficit_unidades"] * df["precio_unitario"]
    df["bajo_rop"]         = df["stock_actual"] < df["rop"]

    return df


# ══════════════════════════════════════════════════════════════════════════════
# IMPACTO ECONÓMICO
# ══════════════════════════════════════════════════════════════════════════════
def medir_impacto(df: pd.DataFrame) -> dict:
    capital_inmov = df["capital_inmovilizado"].sum()
    riesgo_ventas = df["riesgo_ventas"].sum()

    # Ahorro EOQ: diferencia entre ordenar 12 veces/año vs freq óptima
    freq_opt      = (df["demanda_anual"] / df["eoq"].replace(0, 1)).clip(upper=52)
    ahorro_pedidos = (df["costo_pedido_fijo"] * (12 - freq_opt)).clip(lower=0).sum()

    ahorro_tiempo = HORAS_MENSUAL * 12 * COSTO_HORA

    return {
        "capital_inmovilizado": capital_inmov,
        "riesgo_ventas":        riesgo_ventas,       # riesgo inmediato (puntual)
        "ahorro_pedidos_anual": ahorro_pedidos,
        "ahorro_tiempo_anual":  ahorro_tiempo,
        "total":                capital_inmov + riesgo_ventas + ahorro_pedidos + ahorro_tiempo,
        "skus_bajo_rop":        int(df["bajo_rop"].sum()),
        "skus_sobrestock":      int((df["exceso_unidades"] > 0).sum()),
    }


# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD (5 paneles)
# ══════════════════════════════════════════════════════════════════════════════
def generar_dashboard(df: pd.DataFrame, impacto: dict) -> None:
    fig = plt.figure(figsize=(18, 15), facecolor="white")
    fig.suptitle(
        "Panel de Inventario — Análisis ABC-XYZ | NorteLogix S.A. | 2023-2024",
        fontsize=15, fontweight="bold", color=AZUL_OSC, y=0.98
    )

    gs = GridSpec(3, 2, figure=fig, hspace=0.52, wspace=0.35,
                  height_ratios=[1.3, 1.3, 0.7])

    # -- Panel 1: Matriz ABC-XYZ heatmap --------------------------------------
    ax1 = fig.add_subplot(gs[0, 0])
    _panel_matrix(ax1, df)

    # -- Panel 2: Pareto ABC ---------------------------------------------------
    ax2 = fig.add_subplot(gs[0, 1])
    _panel_pareto(ax2, df)

    # -- Panel 3: Top 10 sobrestock --------------------------------------------
    ax3 = fig.add_subplot(gs[1, 0])
    _panel_sobrestock(ax3, df)

    # -- Panel 4: Top 10 riesgo de quiebre ------------------------------------
    ax4 = fig.add_subplot(gs[1, 1])
    _panel_quiebre(ax4, df)

    # -- Panel 5: KPIs (ancho completo) ---------------------------------------
    ax5 = fig.add_subplot(gs[2, :])
    _panel_kpis(ax5, impacto, df)

    ruta = OUT / "dashboard_inventario.png"
    fig.savefig(ruta, dpi=140, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Dashboard guardado: {ruta}")


def _panel_matrix(ax, df):
    abc_cats = ["A", "B", "C"]
    xyz_cats = ["X", "Y", "Z"]

    ax.set_xlim(-0.5, 2.5)
    ax.set_ylim(-0.5, 2.5)
    ax.set_xticks([0, 1, 2])
    ax.set_xticklabels(["X  (estable)", "Y  (variable)", "Z  (errático)"],
                       fontsize=9, color="#444444")
    ax.set_yticks([0, 1, 2])
    ax.set_yticklabels(["C  (bajo valor)", "B  (medio)", "A  (alto valor)"],
                       fontsize=9, color="#444444")
    ax.set_title("Matriz ABC-XYZ — Clasificación de 120 SKUs",
                 fontsize=11, fontweight="bold", color=AZUL_OSC, pad=10)
    ax.set_xlabel("Variabilidad de demanda", fontsize=9, color="#666666")
    ax.set_ylabel("Valor de facturación", fontsize=9, color="#666666")
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.tick_params(length=0)

    for xi, xy in enumerate(xyz_cats):
        for yi, ab in enumerate(abc_cats):
            y_pos  = 2 - yi
            mask   = (df["abc"] == ab) & (df["xyz"] == xy)
            n_skus = mask.sum()
            rev    = df.loc[mask, "revenue_total"].sum()
            color  = COLORES_MATRIX[(ab, xy)]
            tc     = "white" if color in TEXTO_OSCURO else "#3D3D3D"

            rect = plt.Rectangle((xi - 0.46, y_pos - 0.42), 0.92, 0.84,
                                  facecolor=color, edgecolor="white", linewidth=2,
                                  zorder=2)
            ax.add_patch(rect)
            ax.text(xi, y_pos + 0.14, f"{ab}{xy}", ha="center", va="center",
                    fontsize=12, fontweight="bold", color=tc, zorder=3)
            ax.text(xi, y_pos - 0.05, f"{n_skus} SKUs", ha="center", va="center",
                    fontsize=8.5, color=tc, zorder=3)
            ax.text(xi, y_pos - 0.23, f"${rev/1e6:.1f}M", ha="center", va="center",
                    fontsize=7.5, color=tc, alpha=0.90, zorder=3)


def _panel_pareto(ax, df):
    pareto = (
        df[["sku", "revenue_total", "pct_rev", "pct_acum", "abc"]]
        .sort_values("revenue_total", ascending=False)
        .reset_index(drop=True)
    )
    x    = range(len(pareto))
    cols = [AZUL_OSC if a == "A" else (AZUL_MED if a == "B" else AZUL_CLAR)
            for a in pareto["abc"]]

    ax.bar(x, pareto["revenue_total"] / 1e6, color=cols, width=1.0, edgecolor="none")
    ax2t = ax.twinx()
    ax2t.plot(x, pareto["pct_acum"] * 100, color=NARANJA, linewidth=1.8, zorder=5)
    ax2t.axhline(80, color=AZUL_OSC, linestyle="--", linewidth=0.9, alpha=0.7)
    ax2t.axhline(95, color=AZUL_MED, linestyle="--", linewidth=0.9, alpha=0.7)
    ax2t.set_ylabel("% Acumulado", fontsize=8.5, color=NARANJA)
    ax2t.set_ylim(0, 105)
    ax2t.tick_params(axis="y", colors=NARANJA, labelsize=8)

    ax.set_title("Curva Pareto ABC — Concentración de Revenue",
                 fontsize=11, fontweight="bold", color=AZUL_OSC, pad=10)
    ax.set_xlabel("SKUs (ordenados por revenue)", fontsize=8.5, color="#666666")
    ax.set_ylabel("Revenue total (M$)", fontsize=8.5, color=AZUL_OSC)
    ax.set_xlim(-1, len(pareto))
    ax.tick_params(axis="x", labelbottom=False, length=0)
    ax.tick_params(axis="y", labelsize=8)
    for sp in ["top", "right"]:
        ax.spines[sp].set_visible(False)

    n_a = (pareto["abc"] == "A").sum()
    n_b = (pareto["abc"] == "B").sum()
    leyenda = [
        mpatches.Patch(facecolor=AZUL_OSC, label=f"A ({n_a} SKUs)"),
        mpatches.Patch(facecolor=AZUL_MED, label=f"B ({n_b} SKUs)"),
        mpatches.Patch(facecolor=AZUL_CLAR, label=f"C ({len(pareto)-n_a-n_b} SKUs)"),
    ]
    ax.legend(handles=leyenda, fontsize=8, loc="upper right",
              framealpha=0.8, edgecolor="none")


def _panel_sobrestock(ax, df):
    top = (
        df[df["capital_inmovilizado"] > 0]
        .nlargest(10, "capital_inmovilizado")[["sku", "clase", "capital_inmovilizado"]]
        .sort_values("capital_inmovilizado")
    )
    cols  = [COLORES_CLASE.get(c, "#CCCCCC") for c in top["clase"]]
    barras = ax.barh(top["sku"], top["capital_inmovilizado"] / 1e3,
                     color=cols, edgecolor="none", height=0.6)

    for bar, val in zip(barras, top["capital_inmovilizado"]):
        ax.text(bar.get_width() + bar.get_width() * 0.02,
                bar.get_y() + bar.get_height() / 2,
                f"${val/1e3:,.0f}k", va="center", fontsize=7.5, color="#333333")

    ax.set_title("Top 10 SKUs — Capital Inmovilizado en Sobrestock",
                 fontsize=11, fontweight="bold", color=AZUL_OSC, pad=10)
    ax.set_xlabel("Capital inmovilizado ($k ARS)", fontsize=8.5, color="#666666")
    ax.tick_params(axis="y", labelsize=8)
    ax.tick_params(axis="x", labelsize=8)
    for sp in ["top", "right"]:
        ax.spines[sp].set_visible(False)
    ax.set_xlim(0, top["capital_inmovilizado"].max() / 1e3 * 1.22)


def _panel_quiebre(ax, df):
    top = (
        df[df["riesgo_ventas"] > 0]
        .nlargest(10, "riesgo_ventas")[["sku", "clase", "riesgo_ventas", "bajo_rop"]]
        .sort_values("riesgo_ventas")
    )
    cols  = [ROJO if br else AMARILLO for br in top["bajo_rop"]]
    barras = ax.barh(top["sku"], top["riesgo_ventas"] / 1e3,
                     color=cols, edgecolor="none", height=0.6)

    for bar, val in zip(barras, top["riesgo_ventas"]):
        ax.text(bar.get_width() + bar.get_width() * 0.02,
                bar.get_y() + bar.get_height() / 2,
                f"${val/1e3:,.0f}k", va="center", fontsize=7.5, color="#333333")

    ax.set_title("Top 10 SKUs — Ventas en Riesgo por Quiebre de Stock",
                 fontsize=11, fontweight="bold", color=AZUL_OSC, pad=10)
    ax.set_xlabel("Valor de ventas en riesgo ($k ARS)", fontsize=8.5, color="#666666")
    ax.tick_params(axis="y", labelsize=8)
    ax.tick_params(axis="x", labelsize=8)
    for sp in ["top", "right"]:
        ax.spines[sp].set_visible(False)
    ax.set_xlim(0, top["riesgo_ventas"].max() / 1e3 * 1.22)

    leyenda = [mpatches.Patch(facecolor=ROJO, label="Bajo ROP (urgente)"),
               mpatches.Patch(facecolor=AMARILLO, label="En riesgo")]
    ax.legend(handles=leyenda, fontsize=8, loc="lower right",
              framealpha=0.8, edgecolor="none")


def _panel_kpis(ax, impacto: dict, df: pd.DataFrame):
    ax.axis("off")
    ax.set_title("Impacto Económico Estimado — NorteLogix S.A.",
                 fontsize=11, fontweight="bold", color=AZUL_OSC, pad=8)

    kpis = [
        ("Capital inmovilizado\nen sobrestock",
         f"${impacto['capital_inmovilizado']/1e6:.1f}M",
         "Liberable al ajustar política de compra\nde SKUs C-Z con sobrestock",
         ROJO),
        ("Ventas en riesgo\npor quiebres (inmediato)",
         f"${impacto['riesgo_ventas']/1e6:.1f}M",
         f"{impacto['skus_bajo_rop']} SKUs bajo ROP — reponer urgente\nProductos A-X de alto valor",
         NARANJA),
        ("Ahorro costos de pedido\ncon política EOQ (anual)",
         f"${impacto['ahorro_pedidos_anual']/1e3:,.0f}k/año",
         "EOQ reduce frecuencia de pedido en items\nde baja rotación — menos órdenes, mismo nivel",
         VERDE),
        ("Automatización\ncálculo mensual de stock",
         f"${impacto['ahorro_tiempo_anual']/1e3:,.0f}k/año",
         f"8h manuales/mes : 30s automatizado\n"
         f"{int(HORAS_MENSUAL*12)}h/año × ${COSTO_HORA:,.0f}/h analista",
         AZUL_MED),
    ]

    xs    = [0.04, 0.28, 0.53, 0.77]
    width = 0.22

    for (titulo, valor, desc, color), x in zip(kpis, xs):
        rect = plt.Rectangle((x, 0.05), width, 0.88, transform=ax.transAxes,
                              facecolor=color, alpha=0.12, edgecolor=color,
                              linewidth=1.5, clip_on=False)
        ax.add_patch(rect)
        ax.text(x + width/2, 0.82, titulo, transform=ax.transAxes,
                ha="center", va="top", fontsize=8.5, color="#444444",
                fontweight="bold", multialignment="center")
        ax.text(x + width/2, 0.54, valor, transform=ax.transAxes,
                ha="center", va="center", fontsize=14, color=color,
                fontweight="bold")
        ax.text(x + width/2, 0.18, desc, transform=ax.transAxes,
                ha="center", va="center", fontsize=7.2, color="#666666",
                multialignment="center")

    # Total
    total_m = impacto["total"] / 1e6
    ax.text(0.5, -0.06,
            f"Impacto total estimado del análisis: ${total_m:.1f}M  "
            f"(capital liberado + ventas recuperables + ahorros operativos)",
            transform=ax.transAxes, ha="center", va="center",
            fontsize=10, fontweight="bold", color=AZUL_OSC)


# ══════════════════════════════════════════════════════════════════════════════
# EXPORTAR CSVs
# ══════════════════════════════════════════════════════════════════════════════
def exportar(df: pd.DataFrame) -> None:
    cols_clasif = ["sku", "nombre", "categoria", "abc", "xyz", "clase",
                   "cv", "revenue_total", "pct_rev", "pct_acum"]
    df[cols_clasif].to_csv(OUT / "clasificacion_abcxyz.csv",
                           index=False, encoding="utf-8-sig")

    cols_pol = ["sku", "nombre", "categoria", "clase",
                "demanda_avg", "demanda_std", "cv",
                "lead_time_dias", "safety_stock", "rop", "eoq",
                "stock_actual", "stock_optimo",
                "exceso_unidades", "capital_inmovilizado",
                "deficit_unidades", "riesgo_ventas", "bajo_rop"]
    df[cols_pol].to_csv(OUT / "politica_inventario.csv",
                        index=False, encoding="utf-8-sig")

    print(f"clasificacion_abcxyz.csv : {len(df)} SKUs")
    print(f"politica_inventario.csv  : {len(df)} SKUs")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
def main():
    print("=" * 60)
    print("  NorteLogix S.A. — Análisis ABC-XYZ de Inventario")
    print("=" * 60)

    # 1. Cargar
    prod, dem, inv = cargar()

    # 2. Clasificar ABC + XYZ
    abc_df = clasificar_abc(prod, dem)
    xyz_df = clasificar_xyz(dem)

    # 3. Consolidar
    df = (
        prod
        .merge(abc_df[["sku", "revenue_total", "pct_rev", "pct_acum", "abc"]], on="sku")
        .merge(xyz_df, on="sku")
        .merge(inv[["sku", "stock_actual"]], on="sku")
    )
    df["clase"] = df["abc"] + df["xyz"]

    # 4. Política de inventario
    df = calcular_politica(df)

    # 5. Impacto económico
    impacto = medir_impacto(df)

    # 6. Exportar CSVs
    exportar(df)

    # 7. Dashboard
    generar_dashboard(df, impacto)

    # 8. Reporte de impacto
    print()
    print("-" * 60)
    print("  IMPACTO ECONÓMICO IDENTIFICADO")
    print("-" * 60)

    def fmt(v):
        return f"${v/1e6:.2f}M" if v >= 1e6 else f"${v/1e3:,.0f}k"

    dist_abc = df.groupby("abc")["sku"].count()
    dist_xyz = df.groupby("xyz")["sku"].count()

    print(f"\nDistribución ABC: A={dist_abc.get('A',0)} · "
          f"B={dist_abc.get('B',0)} · C={dist_abc.get('C',0)} SKUs")
    print(f"Distribución XYZ: X={dist_xyz.get('X',0)} · "
          f"Y={dist_xyz.get('Y',0)} · Z={dist_xyz.get('Z',0)} SKUs")
    print(f"\nSKUs bajo ROP (riesgo quiebre):   {impacto['skus_bajo_rop']}")
    print(f"SKUs con sobrestock:               {impacto['skus_sobrestock']}")
    print()
    print(f"Capital inmovilizado (sobrestock): {fmt(impacto['capital_inmovilizado'])}")
    print(f"Ventas en riesgo (inmediato):      {fmt(impacto['riesgo_ventas'])}")
    print(f"Ahorro costos pedido (EOQ/año):    {fmt(impacto['ahorro_pedidos_anual'])}")
    print(f"Ahorro tiempo analista (año):      {fmt(impacto['ahorro_tiempo_anual'])}")
    print("-" * 60)
    print(f"  TOTAL ESTIMADO:  {fmt(impacto['total'])}")
    print("-" * 60)

    return impacto


if __name__ == "__main__":
    main()
