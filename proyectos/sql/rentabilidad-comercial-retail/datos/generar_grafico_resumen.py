"""
Genera un gráfico resumen de los hallazgos del análisis de rentabilidad.
Requiere: matplotlib (pip install matplotlib)
Output: ../output/impacto_hallazgos.png

Reglas de diseño (skills visualizacion-paneles / dashboards-python):
título en negrita = conclusión, barras ordenadas por valor, formato de moneda
argentino ($ ARS, miles con punto y decimales con coma), etiquetas de valor.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os

# --- Paleta del portfolio ---
AZUL_OSC, AZUL_MED, VERDE = "#1F4E79", "#2E75B6", "#70AD47"
NARANJA, AZUL_CLARO = "#ED7D31", "#BDD7EE"


def _ar(x, dec=0):
    return f"{x:,.{dec}f}".replace(",", "§").replace(".", ",").replace("§", ".")


# --- Datos de los hallazgos (del informe.md), ordenados por impacto DESC ---
hallazgos = [
    "Productos bajo margen\nrepreciados",
    "Clientes en fuga\nrecuperados (30 %)",
    "Brecha sucursal\nSur cerrada",
    "Capital de baja\nrotación liberado",
]
impacto = [0.91, 0.74, 0.39, 0.079]          # millones de ARS / año
colores = [AZUL_OSC, AZUL_MED, VERDE, AZUL_CLARO]

# Orden ascendente para que la barra mayor quede ARRIBA en barh
orden = sorted(range(len(impacto)), key=lambda i: impacto[i])
hallazgos = [hallazgos[i] for i in orden]
impacto = [impacto[i] for i in orden]
colores = [colores[i] for i in orden]

fig, ax = plt.subplots(figsize=(9.5, 5))
fig.patch.set_facecolor("white")
ax.set_facecolor("white")

bars = ax.barh(range(len(hallazgos)), impacto, color=colores,
               edgecolor="white", linewidth=0.8, height=0.62, zorder=2)
ax.set_yticks(range(len(hallazgos)))
ax.set_yticklabels(hallazgos, fontsize=10)

# Etiquetas de valor en formato ARS
for i, val in enumerate(impacto):
    txt = f"${_ar(val, 2)} M/año" if val >= 0.05 else f"~${_ar(val*1000, 0)} k (puntual)"
    ax.text(val + 0.015, i, txt, va="center", ha="left",
            fontsize=10, fontweight="bold", color=AZUL_OSC)

ax.set_xlabel("Impacto estimado (millones de $ ARS / año)", fontsize=10, color="#555555")
ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"${_ar(x, 1)} M"))
ax.set_title(
    "Rentabilidad Comercial Retail — Impacto por hallazgo (SQL)\n"
    "TiendaNova · 5 sucursales · $176,6 M ARS facturados en 24 meses",
    fontsize=12.5, fontweight="bold", color=AZUL_OSC, pad=14,
)
ax.set_xlim(0, 1.20)
# Total en un recuadro limpio, arriba a la derecha (no interfiere con las barras)
ax.text(0.975, 0.30, "Impacto total\n~$2,0 M/año",
        transform=ax.transAxes, ha="right", va="center",
        fontsize=10, fontweight="bold", color=AZUL_OSC,
        bbox=dict(boxstyle="round,pad=0.5", facecolor="#EAF1F8", edgecolor=AZUL_MED, linewidth=1.2))

ax.xaxis.grid(True, linestyle="--", alpha=0.35, zorder=0)
ax.set_axisbelow(True)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.tick_params(axis="y", labelsize=10)
ax.tick_params(axis="x", labelsize=9, colors="#555555")

plt.tight_layout()

out_dir = os.path.join(os.path.dirname(__file__), "..", "output")
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, "impacto_hallazgos.png")
plt.savefig(out_path, dpi=150, bbox_inches="tight", facecolor="white")
plt.close()
print(f"Gráfico guardado en: {out_path}")
