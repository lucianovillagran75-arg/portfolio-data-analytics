"""
Pipeline del Reporte Comercial Mensual + Segmentación RFM — TiendaNova.

Ejecuta de punta a punta y de forma reproducible:
    cargar → validar → transformar → kpis → rfm → exportar → medir_impacto

Reemplaza el armado manual del reporte mensual (horas de copy-paste en Excel) por un proceso
automático, y agrega una segmentación RFM para priorizar la retención de clientes.

Uso:  python src/pipeline.py
Salidas en: output/  (reporte_comercial.xlsx, segmentos_rfm.csv, figuras/*.png)
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")  # backend sin ventana (para generar PNG en cualquier entorno)
import matplotlib.pyplot as plt

# --------------------------------------------------------------------------- #
# Configuración y supuestos (declarados para que el impacto sea creíble)
# --------------------------------------------------------------------------- #
PROY = Path(__file__).resolve().parent.parent
DATOS = PROY / "datos" / "raw"
SALIDA = PROY / "output"
FIGURAS = SALIDA / "figuras"

COSTO_HORA = 4500          # ARS por hora del analista (supuesto, ajustable)
HORAS_MANUALES_MES = 5     # horas que tomaba armar el reporte a mano cada mes
TASA_RECUPERACION = 0.30   # % de clientes "En riesgo" recuperables con campaña dirigida
TASA_OPORTUNIDAD = 0.08    # costo de oportunidad anual del capital

ACCIONES = {
    "Campeones": "Fidelizar: programa VIP y acceso anticipado",
    "Leales": "Upsell y recompensas por lealtad",
    "Potenciales": "Incentivar la segunda compra (frecuencia)",
    "Necesitan atención": "Ofertas reactivadoras antes de que se enfríen",
    "En riesgo": "Campaña de recuperación URGENTE (cupón dirigido)",
    "Hibernando / Perdidos": "Recuperación de bajo costo; no sobreinvertir",
}


# --------------------------------------------------------------------------- #
# 1. Recopilación
# --------------------------------------------------------------------------- #
def cargar() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if not (DATOS / "ventas.csv").exists():
        raise FileNotFoundError(
            "No hay datos. Corré primero: python datos/generar_datos.py"
        )
    ventas = pd.read_csv(DATOS / "ventas.csv", parse_dates=["fecha"])
    clientes = pd.read_csv(DATOS / "clientes.csv")
    sucursales = pd.read_csv(DATOS / "sucursales.csv")
    return ventas, clientes, sucursales


# --------------------------------------------------------------------------- #
# 2. Control de calidad de los datos
# --------------------------------------------------------------------------- #
def validar(ventas: pd.DataFrame, clientes: pd.DataFrame) -> list[str]:
    problemas = []
    if ventas["id_venta"].isna().any():
        problemas.append("Hay ventas sin id_venta.")
    dup = int(ventas.duplicated().sum())
    if dup:
        problemas.append(f"{dup} filas duplicadas en ventas.")
    huerfanos = (~ventas["id_cliente"].isin(clientes["id_cliente"])).sum()
    if huerfanos:
        problemas.append(f"{huerfanos} ventas con id_cliente inexistente.")
    recalculo = (ventas["precio_unitario"] * ventas["cantidad"]).round(2)
    if not np.allclose(recalculo, ventas["ingreso"], atol=0.01):
        problemas.append("El ingreso no coincide con precio_unitario × cantidad.")
    return problemas


# --------------------------------------------------------------------------- #
# 3. Transformación
# --------------------------------------------------------------------------- #
def transformar(ventas: pd.DataFrame, clientes: pd.DataFrame,
                sucursales: pd.DataFrame) -> pd.DataFrame:
    df = ventas.merge(clientes, on="id_cliente", how="left")
    df = df.merge(sucursales[["id_sucursal", "nombre_sucursal", "region"]],
                  on="id_sucursal", how="left", suffixes=("", "_suc"))
    # categoría del producto (la traemos de ventas via id_producto + tabla productos)
    productos = pd.read_csv(DATOS / "productos.csv")
    df = df.merge(productos[["id_producto", "categoria"]], on="id_producto", how="left")
    df["periodo"] = df["fecha"].dt.to_period("M").astype(str)
    return df


# --------------------------------------------------------------------------- #
# 4. KPIs
# --------------------------------------------------------------------------- #
def kpis_mensuales(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby("periodo").agg(
        facturacion=("ingreso", "sum"),
        margen=("margen", "sum"),
        tickets=("id_venta", "nunique"),
        clientes=("id_cliente", "nunique"),
    )
    g["margen_pct"] = (g["margen"] / g["facturacion"] * 100).round(1)
    g["ticket_promedio"] = (g["facturacion"] / g["tickets"]).round(0)
    g["var_facturacion_pct"] = (g["facturacion"].pct_change() * 100).round(1)
    return g.round(0)


def kpis_por(df: pd.DataFrame, dim: str) -> pd.DataFrame:
    g = df.groupby(dim).agg(
        facturacion=("ingreso", "sum"),
        margen=("margen", "sum"),
        tickets=("id_venta", "nunique"),
    )
    g["margen_pct"] = (g["margen"] / g["facturacion"] * 100).round(1)
    return g.sort_values("facturacion", ascending=False).round(0)


# --------------------------------------------------------------------------- #
# 5. Segmentación RFM
# --------------------------------------------------------------------------- #
def _segmento(r: int, fm: int) -> str:
    if r >= 4 and fm >= 4:
        return "Campeones"
    if r >= 3 and fm >= 3:
        return "Leales"
    if r >= 4 and fm <= 2:
        return "Potenciales"
    if r == 3 and fm <= 2:
        return "Necesitan atención"
    if r <= 2 and fm >= 3:
        return "En riesgo"
    return "Hibernando / Perdidos"


def rfm(df: pd.DataFrame) -> pd.DataFrame:
    fecha_ref = df["fecha"].max() + pd.Timedelta(days=1)
    agg = df.groupby("id_cliente").agg(
        recencia=("fecha", lambda s: (fecha_ref - s.max()).days),
        frecuencia=("id_venta", "nunique"),
        monto=("ingreso", "sum"),
        margen=("margen", "sum"),
    ).reset_index()

    # Scores 1–5 usando rank(first) para evitar bordes de bin duplicados.
    # Menor recencia = mejor → score 5.
    agg["R"] = pd.qcut(agg["recencia"].rank(method="first"), 5,
                       labels=[5, 4, 3, 2, 1]).astype(int)
    agg["F"] = pd.qcut(agg["frecuencia"].rank(method="first"), 5,
                       labels=[1, 2, 3, 4, 5]).astype(int)
    agg["M"] = pd.qcut(agg["monto"].rank(method="first"), 5,
                       labels=[1, 2, 3, 4, 5]).astype(int)
    agg["FM"] = ((agg["F"] + agg["M"]) / 2).round().astype(int)
    agg["segmento"] = [_segmento(r, fm) for r, fm in zip(agg["R"], agg["FM"])]
    agg["accion"] = agg["segmento"].map(ACCIONES)
    return agg.sort_values(["R", "FM"], ascending=False).reset_index(drop=True)


def resumen_segmentos(rfm_df: pd.DataFrame) -> pd.DataFrame:
    g = rfm_df.groupby("segmento").agg(
        clientes=("id_cliente", "count"),
        margen_total=("margen", "sum"),
        monto_promedio=("monto", "mean"),
    )
    g["pct_clientes"] = (g["clientes"] / g["clientes"].sum() * 100).round(1)
    return g.sort_values("margen_total", ascending=False).round(0)


# --------------------------------------------------------------------------- #
# 6. Exportar (Excel + figuras + CSV)
# --------------------------------------------------------------------------- #
# Paleta del portfolio (skills visualizacion-paneles / dashboards-python)
AZUL_OSC, AZUL_MED, VERDE, ROJO, MORADO = "#1F4E79", "#2E75B6", "#70AD47", "#C00000", "#7030A0"


def _ar(x, dec=0):
    """Número en formato argentino: miles con punto, decimales con coma."""
    return f"{x:,.{dec}f}".replace(",", "§").replace(".", ",").replace("§", ".")


def _grafico_tendencia(kpis: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(10, 4.5))
    fig.patch.set_facecolor("white")
    x = range(len(kpis))
    ax.plot(x, kpis["facturacion"] / 1e6, marker="o", label="Facturación", color=AZUL_MED, linewidth=2)
    ax.plot(x, kpis["margen"] / 1e6, marker="o", label="Margen", color=VERDE, linewidth=2)
    ax.set_xticks(list(x))
    ax.set_xticklabels(kpis.index, rotation=45, ha="right", fontsize=8)
    ax.set_ylabel("Millones de $ ARS")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"${_ar(v, 1)} M"))
    ax.set_title("Evolución mensual de facturación y margen", fontweight="bold", color=AZUL_OSC)
    ax.legend(loc="upper left", framealpha=0.9)
    ax.grid(axis="y", alpha=0.3)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    fig.savefig(FIGURAS / "tendencia_mensual.png", dpi=140, facecolor="white")
    plt.close(fig)


def _grafico_barras(serie: pd.Series, titulo: str, archivo: str, color: str) -> None:
    fig, ax = plt.subplots(figsize=(8.5, 4.5))
    fig.patch.set_facecolor("white")
    serie = serie.sort_values()
    vals = serie.values / 1e6
    ax.barh(serie.index.astype(str), vals, color=color, edgecolor="white", height=0.62, zorder=2)
    ax.set_xlabel("Millones de $ ARS")
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"${_ar(v, 1)} M"))
    ax.set_title(titulo, fontweight="bold", color=AZUL_OSC)
    for i, v in enumerate(vals):
        ax.text(v * 1.01, i, f"${_ar(v, 1)} M", va="center", ha="left",
                fontsize=8.5, fontweight="bold", color="#333333")
    ax.grid(axis="x", alpha=0.3)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.set_xlim(0, vals.max() * 1.16)
    fig.tight_layout()
    fig.savefig(FIGURAS / archivo, dpi=140, facecolor="white")
    plt.close(fig)


def _grafico_segmentos(res_seg: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(8.5, 4.5))
    fig.patch.set_facecolor("white")
    s = res_seg["clientes"].sort_values()
    colores = [ROJO if ("riesgo" in i.lower() or "perdid" in i.lower()) else AZUL_MED
               for i in s.index]
    ax.barh(s.index, s.values, color=colores, edgecolor="white", height=0.62, zorder=2)
    ax.set_xlabel("Cantidad de clientes")
    ax.set_title("Clientes por segmento RFM (rojo = acción prioritaria)",
                 fontweight="bold", color=AZUL_OSC)
    tope = max(s.values)
    for i, v in enumerate(s.values):
        ax.text(v + tope * 0.01, i, f"{int(v)}", va="center", ha="left",
                fontsize=8.5, fontweight="bold", color="#333333")
    ax.grid(axis="x", alpha=0.3)
    ax.set_axisbelow(True)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.set_xlim(0, tope * 1.12)
    fig.tight_layout()
    fig.savefig(FIGURAS / "segmentos_rfm.png", dpi=140, facecolor="white")
    plt.close(fig)


def exportar(kpis, por_suc, por_cat, rfm_df, res_seg) -> Path:
    SALIDA.mkdir(parents=True, exist_ok=True)
    FIGURAS.mkdir(parents=True, exist_ok=True)

    # Figuras
    _grafico_tendencia(kpis)
    _grafico_barras(por_suc["facturacion"], "Facturación por sucursal",
                    "ventas_por_sucursal.png", AZUL_MED)
    _grafico_barras(por_cat["facturacion"], "Facturación por categoría",
                    "ventas_por_categoria.png", MORADO)
    _grafico_segmentos(res_seg)

    # CSV de segmentos (entregable accionable para el equipo comercial)
    rfm_df.to_csv(SALIDA / "segmentos_rfm.csv", index=False)

    # Excel formateado
    ruta = SALIDA / "reporte_comercial.xlsx"
    with pd.ExcelWriter(ruta, engine="xlsxwriter") as xl:
        kpis.to_excel(xl, sheet_name="Tendencia mensual")
        por_suc.to_excel(xl, sheet_name="Por sucursal")
        por_cat.to_excel(xl, sheet_name="Por categoría")
        res_seg.to_excel(xl, sheet_name="Segmentos RFM")
        rfm_df.to_excel(xl, sheet_name="Clientes RFM", index=False)

        libro = xl.book
        fmt_pesos = libro.add_format({"num_format": "$#,##0"})
        for hoja in ["Tendencia mensual", "Por sucursal", "Por categoría", "Segmentos RFM"]:
            xl.sheets[hoja].set_column("A:A", 22)
            xl.sheets[hoja].set_column("B:H", 16, fmt_pesos)
    return ruta


# --------------------------------------------------------------------------- #
# 7. Control: medir el impacto económico
# --------------------------------------------------------------------------- #
def medir_impacto(df: pd.DataFrame, res_seg: pd.DataFrame) -> dict:
    meses = df["periodo"].nunique()
    # Horas ahorradas por automatizar el reporte
    horas_ano = HORAS_MANUALES_MES * 12
    ahorro_horas = horas_ano * COSTO_HORA

    # Valor recuperable de clientes "En riesgo" (margen anual del grupo × tasa)
    margen_riesgo = res_seg.loc["En riesgo", "margen_total"] if "En riesgo" in res_seg.index else 0
    margen_riesgo_anual = margen_riesgo / (meses / 12)
    valor_recuperable = margen_riesgo_anual * TASA_RECUPERACION

    return {
        "horas_ahorradas_ano": horas_ano,
        "ahorro_horas_ano": round(ahorro_horas),
        "clientes_en_riesgo": int(res_seg.loc["En riesgo", "clientes"]) if "En riesgo" in res_seg.index else 0,
        "valor_recuperable_ano": round(valor_recuperable),
        "impacto_total_ano": round(ahorro_horas + valor_recuperable),
    }


def main() -> None:
    print("== Reporte Comercial + RFM — TiendaNova ==")
    ventas, clientes, sucursales = cargar()
    print(f"  [Recopilación] {len(ventas):,} ventas · {len(clientes)} clientes")

    problemas = validar(ventas, clientes)
    if problemas:
        print("  [Control] PROBLEMAS DE DATOS:")
        for p in problemas:
            print(f"    - {p}")
    else:
        print("  [Control] Validación de datos OK (sin nulos críticos, sin duplicados, totales cuadran)")

    df = transformar(ventas, clientes, sucursales)
    kpis = kpis_mensuales(df)
    por_suc = kpis_por(df, "nombre_sucursal")
    por_cat = kpis_por(df, "categoria")
    rfm_df = rfm(df)
    res_seg = resumen_segmentos(rfm_df)
    print(f"  [RFM] {len(rfm_df)} clientes segmentados en {res_seg.shape[0]} grupos")

    ruta = exportar(kpis, por_suc, por_cat, rfm_df, res_seg)
    impacto = medir_impacto(df, res_seg)

    print("  [Salida] " + str(ruta))
    print("  == IMPACTO ESTIMADO ==")
    print(f"    Horas ahorradas/año : {impacto['horas_ahorradas_ano']} h  -> ${impacto['ahorro_horas_ano']:,}")
    print(f"    Clientes en riesgo  : {impacto['clientes_en_riesgo']}  -> recuperable ${impacto['valor_recuperable_ano']:,}/año")
    print(f"    IMPACTO TOTAL       : ${impacto['impacto_total_ano']:,}/año")


if __name__ == "__main__":
    main()
