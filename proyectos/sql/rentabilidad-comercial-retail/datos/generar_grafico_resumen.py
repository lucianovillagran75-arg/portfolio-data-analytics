"""
Genera un gráfico resumen de los hallazgos del análisis de rentabilidad.
Requiere: matplotlib (pip install matplotlib)
Output: ../output/impacto_hallazgos.png
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import os

# --- Datos de los hallazgos (del informe.md) ---
hallazgos = [
    "Productos bajo\nmargen repreciados",
    "Clientes en fuga\nrecuperados (30 %)",
    "Brecha sucursal\nSur cerrada",
    "Capital baja\nrotación liberado",
]
impacto = [0.91, 0.74, 0.39, 0.079]
colores = ["#d62728", "#ff7f0e", "#1f77b4", "#2ca02c"]

fig, ax = plt.subplots(figsize=(9, 5))
bars = ax.barh(hallazgos, impacto, color=colores, edgecolor="white", height=0.55)

# Etiquetas con valor
for bar, val in zip(bars, impacto):
    ax.text(
        val + 0.01, bar.get_y() + bar.get_height() / 2,
        f"${val:.2f} M/año",
        va="center", ha="left", fontsize=11, fontweight="bold", color="#333333"
    )

ax.set_xlabel("Impacto estimado (millones ARS / año)", fontsize=10, color="#555555")
ax.set_title(
    "Rentabilidad Comercial Retail — Impacto por hallazgo SQL\n"
    "TiendaNova · 5 sucursales · $176,6 M facturados en 24 meses",
    fontsize=12, fontweight="bold", color="#222222", pad=14
)
ax.set_xlim(0, 1.25)
ax.axvline(sum(impacto), color="#888888", linestyle="--", linewidth=1)
ax.text(sum(impacto) + 0.01, -0.55, f"Total ~$2,0 M/año", fontsize=9,
        color="#888888", style="italic")

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.tick_params(axis="y", labelsize=10)
ax.tick_params(axis="x", labelsize=9, colors="#555555")
fig.patch.set_facecolor("#fafafa")
ax.set_facecolor("#fafafa")

plt.tight_layout()

out_dir = os.path.join(os.path.dirname(__file__), "..", "output")
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, "impacto_hallazgos.png")
plt.savefig(out_path, dpi=150, bbox_inches="tight", facecolor="#fafafa")
plt.close()
print(f"Gráfico guardado en: {out_path}")
