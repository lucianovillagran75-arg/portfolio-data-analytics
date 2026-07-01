"""
Generador de datos sintéticos — FabriTec S.A.
Planta manufacturera: 8 equipos CNC, 3 turnos, 12 meses (Ene–Dic 2024)

Patrón deliberado: Equipos 3, 6 y 7 concentran el 68 % de los paros no programados.
Semilla fija SEED=42 → resultados 100 % reproducibles.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

SEED = 42
rng = np.random.default_rng(SEED)

# ── Directorio de salida ──────────────────────────────────────────────────────
BASE = os.path.dirname(__file__)

# ── 1. EQUIPOS ───────────────────────────────────────────────────────────────
equipos_data = [
    # id, nombre, linea, costo_hora_parada, fecha_ultimo_service, intervalo_dias
    (1, "CNC Alpha 01",    "Línea A", 10500, "2024-08-15", 180),
    (2, "CNC Alpha 02",    "Línea A", 10500, "2024-09-20", 180),
    (3, "Torno CNC 03",    "Línea B", 13200, "2024-03-10", 120),  # crítico
    (4, "Fresadora 04",    "Línea B", 11800, "2024-10-05", 180),
    (5, "Centro Mec. 05",  "Línea C",  9800, "2024-07-22", 150),
    (6, "Torno CNC 06",    "Línea C", 14500, "2024-02-18", 120),  # crítico
    (7, "Rectificadora 07","Línea D", 12000, "2024-04-30", 120),  # crítico
    (8, "CNC Delta 08",    "Línea D", 11200, "2024-11-10", 180),
]

fecha_ref = datetime(2025, 1, 1)  # fecha de "hoy" para calcular días restantes

equipos_rows = []
for (eid, nombre, linea, costo_h, ult_svc, intervalo) in equipos_data:
    ult = datetime.strptime(ult_svc, "%Y-%m-%d")
    prox = ult + timedelta(days=intervalo)
    dias_rest = (prox - fecha_ref).days
    equipos_rows.append({
        "id_equipo":           eid,
        "nombre_equipo":       nombre,
        "linea_produccion":    linea,
        "costo_hora_parada":   costo_h,
        "fecha_ultimo_service": ult_svc,
        "proximo_service":     prox.strftime("%Y-%m-%d"),
        "dias_para_service":   dias_rest,
        "intervalo_servicio_dias": intervalo,
    })

df_equipos = pd.DataFrame(equipos_rows)
df_equipos.to_csv(os.path.join(BASE, "equipos.csv"), index=False, encoding="utf-8-sig")
print(f"  equipos.csv: {len(df_equipos)} equipos")


# ── 2. REGISTRO DE PAROS ─────────────────────────────────────────────────────
CATEGORIAS = {
    "Mecánica":   ["Falla de rodamiento", "Rotura de correa", "Desgaste de herramienta",
                   "Fuga hidráulica", "Desalineación de eje"],
    "Eléctrica":  ["Falla de sensor", "Cortocircuito", "Falla de variador",
                   "Problema en tablero", "Motor quemado"],
    "Operativa":  ["Error de operario", "Cambio de herramienta no planificado",
                   "Material fuera de especificación"],
    "Programada": ["Mantenimiento preventivo", "Calibración", "Limpieza programada"],
}

TURNOS = ["Turno 1 (06–14 h)", "Turno 2 (14–22 h)", "Turno 3 (22–06 h)"]

paros = []

# Probabilidades de paro por equipo (equipos 3, 6, 7 = más frecuentes)
prob_paro = {1: 0.06, 2: 0.06, 3: 0.18, 4: 0.06, 5: 0.07, 6: 0.20, 7: 0.16, 8: 0.05}

fecha_inicio = datetime(2024, 1, 1)
fecha_fin    = datetime(2024, 12, 31)

dia_actual = fecha_inicio
while dia_actual <= fecha_fin:
    for eid, nombre, linea, costo_h, *_ in equipos_data:
        # ¿Hay paro este día en este equipo?
        if rng.random() < prob_paro[eid]:
            tipo = "Programado" if rng.random() < 0.18 else "No programado"
            if tipo == "Programado":
                cat = "Programada"
                causa = rng.choice(CATEGORIAS["Programada"])
                horas = round(rng.uniform(1.0, 4.0), 1)
            else:
                # Equipos críticos tienen más fallas mecánicas/eléctricas
                if eid in (3, 6, 7):
                    cat = rng.choice(["Mecánica", "Mecánica", "Eléctrica", "Operativa"])
                else:
                    cat = rng.choice(["Mecánica", "Eléctrica", "Operativa"])
                causa = rng.choice(CATEGORIAS[cat])
                horas = round(rng.uniform(0.5, 8.0), 1)

            costo = round(horas * costo_h, 0)
            paros.append({
                "fecha":           dia_actual.strftime("%Y-%m-%d"),
                "id_equipo":       eid,
                "nombre_equipo":   nombre,
                "linea":           linea,
                "turno":           rng.choice(TURNOS),
                "tipo_paro":       tipo,
                "categoria_causa": cat,
                "causa_detalle":   causa,
                "horas_paro":      horas,
                "costo_paro":      costo,
            })
    dia_actual += timedelta(days=1)

df_paros = pd.DataFrame(paros)
df_paros.to_csv(os.path.join(BASE, "registro_paros.csv"), index=False, encoding="utf-8-sig")
print(f"  registro_paros.csv: {len(df_paros)} registros")

# Resumen para validar
no_prog = df_paros[df_paros["tipo_paro"] == "No programado"]
total_h = no_prog["horas_paro"].sum()
criticos = no_prog[no_prog["id_equipo"].isin([3, 6, 7])]["horas_paro"].sum()
print(f"  Paros no programados: {len(no_prog)} eventos | {total_h:.0f} h totales")
print(f"  Equipos 3-6-7: {criticos:.0f} h = {criticos/total_h*100:.0f}% del total")
