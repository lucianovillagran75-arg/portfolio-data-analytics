# Informe de Hallazgos — Panel de Paros y OEE | FabriTec S.A. | 2024

## Resumen ejecutivo

El análisis de 307 registros de paro (Ene–Dic 2024) reveló que la planta perdió **1.079 horas
de producción no programadas**, con un costo directo de **$8,76 M** en el año.
El 64 % de ese costo está concentrado en 3 de los 8 equipos — una oportunidad de acción
focalizada con alto retorno.

---

## Hallazgo 1 — Concentración del downtime en 3 equipos (Pareto de equipos)

**Hallazgo:** Torno CNC 03, Torno CNC 06 y Rectificadora 07 generan el 64 % de las horas de paro no programado.

**Evidencia:**

| Equipo | Horas NP | % Total | % Acumulado |
|---|---|---|---|
| Torno CNC 06  | ~250 h | 23 % | 23 % |
| Rectificadora 07 | ~230 h | 21 % | 44 % |
| Torno CNC 03  | ~210 h | 20 % | 64 % |
| Resto (5 equipos) | ~389 h | 36 % | 100 % |

**Acción:** Plan de mantenimiento preventivo focalizado en estos 3 equipos.

**Impacto estimado:** ~700 h recuperadas/año × $12.000/h = **$8,4 M/año**

*Supuesto: costo de línea parada = promedio ponderado de los 3 equipos ($12.000/h);
reducción estimada del 65 % del downtime actual con plan preventivo estructurado.*

---

## Hallazgo 2 — OEE bajo el umbral aceptable en 3 equipos

**Hallazgo:** Torno CNC 03 (OEE ~71 %), Torno CNC 06 (OEE ~68 %) y Rectificadora 07 (OEE ~73 %) están
por debajo del benchmark de industria (85 % = "Excelente"; 65–84 % = "Aceptable").

**Evidencia:**

| Equipo | Disponibilidad | Rendimiento | Calidad | OEE |
|---|---|---|---|---|
| CNC Alpha 01  | 95,6 % | 91,0 % | 98,0 % | 85,2 % ✅ |
| CNC Delta 08  | 96,5 % | 94,0 % | 98,0 % | 88,9 % ✅ |
| Torno CNC 03  | 92,8 % | 82,0 % | 96,0 % | 73,1 % 🟡 |
| Torno CNC 06  | 91,4 % | 79,0 % | 95,0 % | 68,6 % 🟡 |
| Rectificadora 07 | 92,1 % | 83,0 % | 96,0 % | 73,4 % 🟡 |

**Acción:** Revisar el plan de mantenimiento preventivo y analizar causas de bajo Rendimiento en CNC 06.

**Impacto estimado:** Llevar OEE de 68 % a 78 % en Torno CNC 06 libera ~300 h/año adicionales.
Sin cuantificar hasta tener datos de producción real (unidades/h).

---

## Hallazgo 3 — Causa raíz dominante: fallas mecánicas

**Hallazgo:** Las fallas mecánicas (rodamientos, correas, desgaste) concentran la mayor proporción
del downtime no programado, por encima de fallas eléctricas y errores operativos.

**Evidencia (Pareto de causas):**

| Categoría | Horas NP | % Total | % Acumulado |
|---|---|---|---|
| Mecánica  | ~540 h | ~50 % | ~50 % |
| Eléctrica | ~320 h | ~30 % | ~80 % |
| Operativa | ~219 h | ~20 % | 100 % |

**Acción:** Priorizar la revisión de rodamientos y sistemas de transmisión (mayor impacto).
Invertir en capacitación de operarios para reducir errores operativos (bajo costo, 20 % del problema).

**Impacto estimado:** Reducir fallas mecánicas en un 40 % equivale a ~216 h/año → **$2,6 M/año**.

---

## Hallazgo 4 — Vencimientos de service no controlados

**Hallazgo:** Al 01/01/2025, 2 equipos tienen el service vencido y 1 está a menos de 30 días.
Ninguno tenía sistema de alerta antes de este panel.

**Evidencia:** Semáforo de la hoja `Equipos` muestra:
- Torno CNC 03 → service vencido desde Sep. 2024 (**VENCIDO** 🔴)
- Torno CNC 06 → service vencido desde Oct. 2024 (**VENCIDO** 🔴)
- Rectificadora 07 → próximo service: Feb. 2025 (**URGENTE** 🔴)

**Acción:** Programar service inmediato para los 3 equipos. Estos son exactamente los mismos
equipos que concentran el 64 % del downtime — la correlación confirma la hipótesis.

**Impacto estimado:** Evitar 1 falla catastrófica de línea (8 h × $13.000/h) = **$104.000** por evento evitado.

---

## Hallazgo 5 — Reporte mensual: 3 horas manuales eliminadas

**Hallazgo:** El reporte mensual de mantenimiento se construía a mano: copiar, pegar, formatear,
nombrar el archivo, enviar. Promedio: 3 horas/mes.

**Acción:** Macro VBA `InformeMensual` automatiza el proceso en 1 clic.

**Impacto estimado:** 3 h/mes × $4.500/h × 12 meses = **$162.000/año**

*Supuesto: costo hora analista/coordinador de mantenimiento = ARS 4.500.*

---

## Tabla resumen de impacto

| Hallazgo | Acción | Impacto $/año | Esfuerzo | Supuesto clave |
|---|---|---|---|---|
| Top 3 equipos = 64 % downtime NP | Plan preventivo focalizado | **$8,4 M** | Alto | 700 h × $12.000/h, reducción 65 % |
| Fallas mecánicas = 50 % del downtime | Revisión rodamientos y transmisión | **$2,6 M** (incluido en los $8,4 M) | Medio | 40 % de reducción fallas mecánicas |
| Services vencidos (2 equipos) | Service inmediato | $104.000 por falla evitada | Bajo | 1 falla catastrófica/año evitada |
| Reporte mensual manual | Macro VBA | **$162.000** | Bajo | 36 h/año × $4.500/h |

### Impacto total estimado del análisis: **~$8,6 M/año**

*(Los $2,6 M de fallas mecánicas están incluidos dentro del ahorro de $8,4 M por plan preventivo.
No se duplican.)*

---

## Datos

- Fuente: `datos/registro_paros.csv` (307 registros), `datos/equipos.csv` (8 equipos)
- Generados con semilla fija SEED=42 — distribuciones realistas del sector
- Fecha de referencia para semáforo: 01/01/2025
- Costo hora de línea parada: rango $9.800–$14.500 según equipo; promedio ponderado $12.000
- Costo hora analista: ARS 4.500 (estimación conservadora)
- Horas disponibles por equipo/año: 8 h × 365 días = 2.920 h (1 turno base)
