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
import matplotlib.patheffects as pe
from matplotlib.patches import FancyBboxPatch
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


def _ar(x: float, dec: int = 0) -> str:
    """Número en formato argentino: miles con punto, decimales con coma."""
    return f"{x:,.{dec}f}".replace(",", "§").replace(".", ",").replace("§", ".")


def _money(v: float) -> str:
    """Formato de dinero argentino: millones en M, miles en k."""
    return f"${_ar(v/1e6, 1)}M" if v >= 1e6 else f"${_ar(v/1e3, 0)}k"


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
        "Panel de Inventario — Análisis ABC-XYZ | NorteLogix S.A.",
        fontsize=15, fontweight="bold", color=AZUL_OSC, y=0.975
    )
    fig.text(
        0.5, 0.952,
        f"Impacto total identificado: {_money(impacto['total'])} ARS   ·   "
        f"120 productos   ·   demanda 2023-2024   ·   datos sintéticos reproducibles",
        ha="center", fontsize=10.5, color="#666666",
    )

    gs = GridSpec(3, 2, figure=fig, hspace=0.60, wspace=0.30,
                  height_ratios=[1.3, 1.3, 0.7])

    # -- Panel 1: Salud del inventario (dónut semáforo) -----------------------
    ax1 = fig.add_subplot(gs[0, 0])
    _panel_salud(ax1, df)

    # -- Panel 2: Regla 80/20 — dónde está la facturación ---------------------
    ax2 = fig.add_subplot(gs[0, 1])
    _panel_8020(ax2, df)

    # -- Panel 3: Top 10 sobrestock --------------------------------------------
    ax3 = fig.add_subplot(gs[1, 0])
    _panel_sobrestock(ax3, df)

    # -- Panel 4: Top 10 riesgo de quiebre ------------------------------------
    ax4 = fig.add_subplot(gs[1, 1])
    _panel_quiebre(ax4, df)

    # -- Panel 5: KPIs (ancho completo) ---------------------------------------
    ax5 = fig.add_subplot(gs[2, :])
    _panel_kpis(ax5, impacto, df)

    # -- Marcos tipo tarjeta con borde de color semántico ---------------------
    # (claro/azul = neutro-positivo · naranja = capital atrapado · rojo = urgente)
    fig.canvas.draw()
    _marco(fig, ax1, "#2E75B6")   # salud: neutro
    _marco(fig, ax2, "#548235")   # facturación (dónde está el valor): positivo
    _marco(fig, ax3, "#ED7D31")   # sobrestock: negativo (capital atrapado)
    _marco(fig, ax4, "#C00000")   # quiebre: negativo (urgente)

    ruta = OUT / "dashboard_inventario.png"
    fig.savefig(ruta, dpi=140, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Dashboard guardado: {ruta}")


def _marco(fig, ax, color, ml=0.020, mr=0.020, mb=0.034, mt=0.055):
    """Dibuja una tarjeta (fondo blanco, borde de color y sombra) detrás del panel
    para delimitarlo visualmente. Márgenes en fracción de figura (más arriba para
    incluir el título del gráfico)."""
    pos = ax.get_position()
    x0, y0 = pos.x0 - ml, pos.y0 - mb
    w, h   = pos.width + ml + mr, pos.height + mb + mt
    card = FancyBboxPatch(
        (x0, y0), w, h, transform=fig.transFigure,
        boxstyle="round,pad=0,rounding_size=0.012",
        facecolor="white", edgecolor=color, linewidth=2.4,
        zorder=-1, clip_on=False,
        mutation_aspect=fig.get_figheight() / fig.get_figwidth(),
    )
    card.set_path_effects([pe.withSimplePatchShadow(
        offset=(4, -4), shadow_rgbFace="#9AA6B2", alpha=0.28)])
    fig.add_artist(card)


def _panel_salud(ax, df):
    """Dónut semáforo: qué proporción de los SKUs está sana vs con problemas.
    Verde claro = saludable · Naranja = sobrestock · Rojo = riesgo de quiebre."""
    n_bajo   = int(df["bajo_rop"].sum())
    n_exceso = int((df["exceso_unidades"] > 0).sum())
    n_sano   = len(df) - n_bajo - n_exceso

    datos   = [n_sano, n_exceso, n_bajo]
    labels  = ["Saludable", "Sobrestock", "Riesgo de quiebre"]
    colores = ["#A9D18E", "#F4B183", "#FF6B6B"]   # verde claro · naranja · rojo

    wedges, _ = ax.pie(
        datos, colors=colores, startangle=90, counterclock=False,
        wedgeprops=dict(width=0.42, edgecolor="white", linewidth=2.5),
    )
    # Etiqueta de cantidad sobre cada gajo con peso suficiente
    for w, val in zip(wedges, datos):
        if val == 0:
            continue
        ang = np.deg2rad((w.theta1 + w.theta2) / 2)
        ax.text(0.79 * np.cos(ang), 0.79 * np.sin(ang), f"{val}",
                ha="center", va="center", fontsize=11, fontweight="bold", color="#3D3D3D")

    pct_sano = n_sano / len(df) * 100
    ax.text(0, 0.10, f"{pct_sano:.0f}%", ha="center", va="center",
            fontsize=30, fontweight="bold", color="#548235")
    ax.text(0, -0.20, "del stock\nsaludable", ha="center", va="center",
            fontsize=9.5, color="#666666", multialignment="center")

    n_problema = n_exceso + n_bajo
    ax.set_title(f"Salud del inventario — {n_problema} de 120 productos necesitan acción",
                 fontsize=11, fontweight="bold", color=AZUL_OSC, pad=14)

    leyenda = [mpatches.Patch(facecolor=c, label=f"{l}  ·  {n} SKUs")
               for c, l, n in zip(colores, labels, datos)]
    ax.legend(handles=leyenda, fontsize=8.5, loc="center",
              bbox_to_anchor=(0.5, -0.10), ncol=1, frameon=False)
    ax.set_aspect("equal")


def _panel_8020(ax, df):
    """Regla 80/20 en formato gerencial: dos barras 100% comparando la porción de
    PRODUCTOS vs la porción de FACTURACIÓN que aporta cada clase A/B/C."""
    g = (df.groupby("abc")
           .agg(n=("sku", "count"), rev=("revenue_total", "sum"))
           .reindex(["A", "B", "C"]))
    pct_n   = g["n"]   / g["n"].sum()   * 100
    pct_rev = g["rev"] / g["rev"].sum() * 100

    colores   = {"A": AZUL_OSC, "B": AZUL_MED, "C": AZUL_CLAR}
    tc_claro  = {"A": "white",  "B": "white",  "C": "#3D3D3D"}

    filas = [(1, pct_n), (0, pct_rev)]
    for y, serie in filas:
        izq = 0.0
        for cls in ["A", "B", "C"]:
            w = float(serie[cls])
            ax.barh(y, w, left=izq, color=colores[cls], edgecolor="white",
                    height=0.6, zorder=2)
            if w >= 5:
                ax.text(izq + w / 2, y, f"{w:.0f}%", ha="center", va="center",
                        fontsize=10, fontweight="bold", color=tc_claro[cls], zorder=3)
            izq += w

    ax.set_xlim(0, 100)
    ax.set_ylim(-1.5, 2.5)
    ax.set_yticks([0, 1])
    ax.set_yticklabels(["% de\nfacturación", "% de\nproductos"],
                       fontsize=9.5, color="#444444")
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0f}%"))
    ax.tick_params(axis="x", labelsize=8)
    ax.set_xticks([0, 20, 40, 60, 80, 100])
    for sp in ["top", "right", "left"]:
        ax.spines[sp].set_visible(False)
    ax.tick_params(axis="y", length=0)

    n_a   = int(g.loc["A", "n"])
    rev_a = float(pct_rev["A"])
    ax.set_title("Regla 80/20 — Dónde está tu facturación",
                 fontsize=11, fontweight="bold", color=AZUL_OSC, pad=14)

    # Leyenda arriba (dentro del gráfico) y conclusión abajo (dentro del gráfico)
    leyenda = [
        mpatches.Patch(facecolor=AZUL_OSC,  label="A · alto valor"),
        mpatches.Patch(facecolor=AZUL_MED,  label="B · valor medio"),
        mpatches.Patch(facecolor=AZUL_CLAR, label="C · bajo valor"),
    ]
    ax.legend(handles=leyenda, fontsize=8.5, loc="upper center",
              bbox_to_anchor=(0.5, 1.0), ncol=3, frameon=False)
    ax.text(0.5, 0.055,
            f"Los {n_a} productos de clase A ({pct_n['A']:.0f}% del catálogo) "
            f"concentran el {rev_a:.0f}% de la facturación.",
            transform=ax.transAxes, ha="center", va="center",
            fontsize=9, color="#548235", fontweight="bold")


def _panel_ranking(ax, top, valores, cmap, color_txt, titulo, xlabel):
    """Ranking horizontal (barras ordenadas), coloreado por severidad con una escala
    secuencial: a mayor monto, color más intenso. Etiqueta de valor al final de cada barra."""
    vmin, vmax = valores.min(), valores.max()
    rng = (vmax - vmin) or 1
    colores = [cmap(0.42 + 0.50 * (v - vmin) / rng) for v in valores]

    barras = ax.barh(top["sku"], valores / 1e3, color=colores,
                     edgecolor="white", linewidth=0.6, height=0.64, zorder=2)
    for bar, val in zip(barras, valores):
        ax.text(bar.get_width() * 1.02, bar.get_y() + bar.get_height() / 2,
                f"${val/1e3:,.0f}k", va="center", ha="left",
                fontsize=8, color=color_txt, fontweight="bold")

    ax.set_title(titulo, fontsize=11, fontweight="bold", color=AZUL_OSC, pad=10)
    ax.set_xlabel(xlabel, fontsize=8.5, color="#666666")
    ax.xaxis.set_major_formatter(
        plt.FuncFormatter(lambda v, _: "$0" if v == 0 else f"${v:,.0f}k"))
    ax.tick_params(axis="y", labelsize=8.5)
    ax.tick_params(axis="x", labelsize=8)
    ax.xaxis.grid(True, linestyle="--", alpha=0.35, zorder=0)
    ax.set_axisbelow(True)
    for sp in ["top", "right"]:
        ax.spines[sp].set_visible(False)
    ax.set_xlim(0, vmax / 1e3 * 1.20)


def _panel_sobrestock(ax, df):
    top = (
        df[df["capital_inmovilizado"] > 0]
        .nlargest(10, "capital_inmovilizado")[["sku", "capital_inmovilizado"]]
        .sort_values("capital_inmovilizado")
    )
    vals = top["capital_inmovilizado"].to_numpy()
    _panel_ranking(
        ax, top, vals, plt.cm.Oranges, "#8A4B00",
        f"Capital atrapado — el Top 10 inmoviliza {_money(vals.sum())}",
        "Capital inmovilizado (miles de $ ARS)",
    )


def _panel_quiebre(ax, df):
    top = (
        df[df["riesgo_ventas"] > 0]
        .nlargest(10, "riesgo_ventas")[["sku", "riesgo_ventas"]]
        .sort_values("riesgo_ventas")
    )
    vals = top["riesgo_ventas"].to_numpy()
    _panel_ranking(
        ax, top, vals, plt.cm.Reds, "#8B0000",
        f"Riesgo de quiebre — {_money(vals.sum())} en ventas a reponer ya",
        "Ventas en riesgo (miles de $ ARS)",
    )


def _panel_kpis(ax, impacto: dict, df: pd.DataFrame):
    ax.axis("off")
    ax.set_title("Impacto Económico Estimado — NorteLogix S.A.",
                 fontsize=11, fontweight="bold", color=AZUL_OSC, pad=8)

    kpis = [
        ("Capital inmovilizado\nen sobrestock",
         _money(impacto['capital_inmovilizado']),
         "Liberable al ajustar política de compra\nde SKUs C-Z con sobrestock",
         NARANJA),
        ("Ventas en riesgo\npor quiebres (inmediato)",
         _money(impacto['riesgo_ventas']),
         f"{impacto['skus_bajo_rop']} SKUs bajo ROP — reponer urgente\nProductos A-X de alto valor",
         ROJO),
        ("Ahorro costos de pedido\ncon política EOQ (anual)",
         f"{_money(impacto['ahorro_pedidos_anual'])}/año",
         "EOQ reduce frecuencia de pedido en items\nde baja rotación — menos órdenes, mismo nivel",
         VERDE),
        ("Automatización\ncálculo mensual de stock",
         f"{_money(impacto['ahorro_tiempo_anual'])}/año",
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
    ax.text(0.5, -0.06,
            f"Impacto total estimado del análisis: {_money(impacto['total'])} ARS  "
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
