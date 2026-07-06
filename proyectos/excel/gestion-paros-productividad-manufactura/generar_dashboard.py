# -*- coding: utf-8 -*-
"""
generar_dashboard.py
Genera output/dashboard_paros_oee.png: una vista previa del panel ejecutivo del Excel,
pensada para que se entienda SIN abrir la planilla (útil en el README para reclutadores).

Reglas de diseño (skill dashboards-python): título = conclusión, barras ordenadas por valor,
colores semáforo, separadores de miles, una idea por gráfico.

Ejecutar:  python generar_dashboard.py
Requiere:  pandas, numpy, matplotlib   (mismos datos que construir_panel.py)
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
from matplotlib.gridspec import GridSpec

plt.rcParams["mathtext.default"] = "regular"

BASE = os.path.dirname(__file__)
OUT  = os.path.join(BASE, "output", "dashboard_paros_oee.png")

AZUL, AZULM, VERDE = "#1F4E79", "#2E75B6", "#70AD47"
AMAR, ROJO, NARANJA, GRIS = "#FFC000", "#C00000", "#ED7D31", "#7F7F7F"

def miles(x):
    return f"{x:,.0f}".replace(",", ".")

# ── Datos (idénticos a construir_panel.py) ───────────────────────────────────
df_eq    = pd.read_csv(os.path.join(BASE, "datos", "equipos.csv"))
df_paros = pd.read_csv(os.path.join(BASE, "datos", "registro_paros.csv"))

rend_base = {"CNC Alpha 01":0.91,"CNC Alpha 02":0.89,"Torno CNC 03":0.82,"Fresadora 04":0.93,
             "Centro Mec. 05":0.88,"Torno CNC 06":0.79,"Rectificadora 07":0.83,"CNC Delta 08":0.94}
cal_base  = {"CNC Alpha 01":0.98,"CNC Alpha 02":0.97,"Torno CNC 03":0.96,"Fresadora 04":0.99,
             "Centro Mec. 05":0.97,"Torno CNC 06":0.95,"Rectificadora 07":0.96,"CNC Delta 08":0.98}
h_paro = (df_paros[df_paros["tipo_paro"]=="No programado"].groupby("nombre_equipo")["horas_paro"].sum()
          .reindex(df_eq["nombre_equipo"]).fillna(0))
HORAS_ANO = 8*365
disponib = ((HORAS_ANO - h_paro)/HORAS_ANO).clip(0,1)
rendim = pd.Series({n:rend_base[n] for n in df_eq["nombre_equipo"]})
calidad = pd.Series({n:cal_base[n] for n in df_eq["nombre_equipo"]})
oee = disponib*rendim.values*calidad.values

pareto_eq = (df_paros[df_paros["tipo_paro"]=="No programado"].groupby("nombre_equipo")["horas_paro"].sum()
             .sort_values(ascending=False).reset_index())
pareto_eq.columns=["Equipo","Horas"]
pareto_eq["acum"]=pareto_eq["Horas"].cumsum()/pareto_eq["Horas"].sum()*100

total_h = h_paro.sum()
total_costo = df_paros[df_paros["tipo_paro"]=="No programado"]["costo_paro"].sum()
n_eventos = len(df_paros[df_paros["tipo_paro"]=="No programado"])
oee_prom = oee.mean()

# ── Figura ───────────────────────────────────────────────────────────────────
fig = plt.figure(figsize=(13, 8.2)); fig.patch.set_facecolor("white")
gs = GridSpec(3, 4, figure=fig, height_ratios=[0.62, 1.15, 1.15], hspace=0.55, wspace=0.62,
              left=0.06, right=0.965, top=0.9, bottom=0.09)

fig.text(0.06, 0.955, "FabriTec S.A. — Panel de Paros, OEE y Mantenimiento",
         fontsize=17, fontweight="bold", color=AZUL, ha="left")
fig.text(0.06, 0.925, "3 de 8 equipos concentran el 64 % del tiempo de máquina parada  ·  Oportunidad: ~$8,6 M ARS/año",
         fontsize=11, color=GRIS, ha="left")

kpis = [("Horas de máquina\nparada (no previstas)", f"{miles(total_h)} h", "#FDECEA", ROJO),
        ("Costo de esos\nparos", f"\\${miles(total_costo)}", "#FDECEA", ROJO),
        ("Cantidad de\nparos imprevistos", f"{n_eventos}", "#FEF6E7", "#8B5E00"),
        ("Eficiencia media\nde planta (OEE)", f"{oee_prom*100:.0f}%", "#EAF3E5", "#375623")]
for i,(t,v,bg,cv) in enumerate(kpis):
    ax = fig.add_subplot(gs[0, i]); ax.axis("off")
    ax.add_patch(plt.Rectangle((0,0),1,1, facecolor=bg, edgecolor="#D9D9D9", lw=1, transform=ax.transAxes))
    ax.text(0.5,0.72,t, ha="center", va="center", fontsize=9.3, color="#404040", transform=ax.transAxes)
    ax.text(0.5,0.33,v, ha="center", va="center", fontsize=20, fontweight="bold", color=cv, transform=ax.transAxes)

ax1 = fig.add_subplot(gs[1, :2]); x = range(len(pareto_eq))
ax1.bar(x, pareto_eq["Horas"], color=[ROJO if i<3 else AZULM for i in x], edgecolor="white", zorder=2)
ax1.set_xticks(list(x)); ax1.set_xticklabels(pareto_eq["Equipo"], rotation=28, ha="right", fontsize=8.5)
ax1.set_ylabel("Horas paradas/año", fontsize=9.5)
ax1.set_title("¿Dónde atacar primero? — 3 equipos (rojo) causan el 64 % de los paros",
              fontsize=10.5, fontweight="bold", pad=8, loc="left")
ax1.yaxis.grid(True, ls="--", alpha=0.35, zorder=0); ax1.set_axisbelow(True)
for s in ("top","right"): ax1.spines[s].set_visible(False)
ax1b = ax1.twinx()
ax1b.plot(x, pareto_eq["acum"], color=NARANJA, marker="o", lw=2, ms=4, zorder=3)
ax1b.set_ylim(0,115); ax1b.axhline(80, color=GRIS, ls="--", lw=0.9, alpha=0.6); ax1b.set_yticks([])
ax1b.text(-0.35, 80, "80 %", fontsize=8, color=GRIS, va="center", ha="right")
ax1b.annotate(f"{pareto_eq['acum'].iloc[-1]:.0f} %", xy=(len(pareto_eq)-1, pareto_eq['acum'].iloc[-1]),
              xytext=(-4, 8), textcoords="offset points", fontsize=8.5, color=NARANJA, fontweight="bold", ha="right")
for s in ("top",): ax1b.spines[s].set_visible(False)
ax1.legend(handles=[mpatches.Patch(color=ROJO,label="Top 3 críticos"),
                    mpatches.Patch(color=AZULM,label="Resto"),
                    Line2D([0],[0],color=NARANJA,marker="o",label="% acumulado")],
           loc="center right", fontsize=8, framealpha=0.9)

ax2 = fig.add_subplot(gs[1, 2:]); nombres = df_eq["nombre_equipo"].tolist()
vals = [oee[n]*100 for n in nombres]; order = np.argsort(vals)
nombres_o = [nombres[i] for i in order]; vals_o = [vals[i] for i in order]
cols_o = [VERDE if v>=85 else (AMAR if v>=65 else "#FF6B6B") for v in vals_o]
ax2.barh(range(len(nombres_o)), vals_o, color=cols_o, edgecolor="white", height=0.62, zorder=2)
ax2.set_yticks(range(len(nombres_o))); ax2.set_yticklabels(nombres_o, fontsize=8.5)
ax2.set_xlim(60,102); ax2.axvline(85, color=AZUL, ls="--", lw=1, alpha=0.7)
ax2.xaxis.set_major_formatter(plt.FuncFormatter(lambda v,_:f"{v:.0f}%"))
ax2.set_title("Eficiencia por equipo (OEE) — 3 equipos bajo el objetivo del 85 %",
              fontsize=10.5, fontweight="bold", pad=8, loc="left")
ax2.xaxis.grid(True, ls="--", alpha=0.35, zorder=0); ax2.set_axisbelow(True)
for s in ("top","right"): ax2.spines[s].set_visible(False)
for i,v in enumerate(vals_o): ax2.text(v+0.4,i,f"{v:.0f}%",va="center",fontsize=8,fontweight="bold")
ax2.legend(handles=[mpatches.Patch(color=VERDE,label="Excelente ≥85%"),
                    mpatches.Patch(color=AMAR,label="Aceptable 65–84%"),
                    mpatches.Patch(color="#FF6B6B",label="Bajo <65%")],
           loc="lower right", fontsize=7.5, framealpha=0.9)

ax3 = fig.add_subplot(gs[2, :]); ax3.axis("off")
ax3.add_patch(plt.Rectangle((0,0),1,1, facecolor="#FFF7E6", edgecolor="#E8C77A", lw=1.2, transform=ax3.transAxes))
diag = ("DIAGNÓSTICO EJECUTIVO\n"
        "• Los equipos Torno CNC 03, Torno CNC 06 y Rectificadora 07 concentran el 64 % de las horas de máquina parada.\n"
        "• Un plan de mantenimiento preventivo enfocado en esos 3 equipos recupera ~700 horas de producción al año.\n"
        "• Impacto estimado: ~\\$8,4 M ARS/año en producción recuperada + \\$0,16 M ARS/año por automatizar el reporte (macro VBA).\n"
        "  Total: ~\\$8,6 M ARS/año.  ·  Cifras sobre datos sintéticos, con supuestos conservadores declarados en informe.md.")
ax3.text(0.02,0.5, diag, ha="left", va="center", fontsize=9.6, color="#3D3D3D", transform=ax3.transAxes, linespacing=1.5)

os.makedirs(os.path.dirname(OUT), exist_ok=True)
fig.savefig(OUT, dpi=145, facecolor="white", bbox_inches="tight"); plt.close(fig)
print("Dashboard generado:", OUT)
