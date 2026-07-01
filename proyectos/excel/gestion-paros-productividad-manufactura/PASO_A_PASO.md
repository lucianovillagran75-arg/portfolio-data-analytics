# PASO A PASO — Panel de Paros, OEE y Mantenimiento Preventivo

## Contexto del proyecto

FabriTec S.A. tiene 8 equipos CNC distribuidos en 4 líneas de producción, operando en 3 turnos.
El área de mantenimiento registraba los paros en papel y un Excel básico sin análisis.
El objetivo: convertir ese registro en un panel que muestre el costo real de cada paro,
identifique las causas raíz y anticipe los próximos vencimientos de service.

---

## Fase 1 — Entender el problema y definir el modelo de datos

**Punto de partida:** el registro histórico de paros (cuaderno y hojas sueltas de Excel).

Definí el esquema de datos necesario para responder las 3 preguntas clave:

| Pregunta de negocio | Dato necesario |
|---|---|
| ¿Cuánto cuesta cada paro? | Horas paro × costo por hora del equipo |
| ¿Cuáles son las causas raíz? | Categoría y detalle de causa por evento |
| ¿Qué máquinas van a fallar? | Fecha último service + intervalo de mantenimiento |

Con eso definí las dos tablas fuente: `equipos` (maestro) y `registro_paros` (hechos).

---

## Fase 2 — Datos sintéticos reproducibles

Generé los datos con Python (`datos/generar_datos.py`) usando semilla fija (SEED=42) para
que cualquier persona que clone el proyecto obtenga exactamente los mismos números.

**Diseño deliberado del dataset:**
- 8 equipos con distintos costos por hora de línea parada ($9.800 a $14.500)
- 307 eventos de paro en 12 meses (programados + no programados)
- Patrón real: Torno CNC 03, Torno CNC 06 y Rectificadora 07 concentran el 64 % del downtime no programado
- Variación de causas por tipo de equipo: los críticos tienen más fallas mecánicas y eléctricas
- Fechas de próximo service con 2 equipos ya vencidos y 1 próximo a vencer → el semáforo "funciona"

---

## Fase 3 — Construcción del Excel (4 hojas)

### Hoja 1: Equipos

Maestro de los 8 equipos con el **semáforo de mantenimiento**:
- Columna "Días Restantes": `=fecha_proximo_service - fecha_ref`
- Formato condicional: rojo si `< 30` días (o vencido), amarillo si `< 60`, verde si `≥ 60`
- Columna "Estado": texto dinámico (VENCIDO / URGENTE / PRÓXIMO / OK)

**Decisión clave:** usar formato condicional basado en el valor de la celda, no en fórmulas IF —
más robusto cuando se actualizan las fechas.

### Hoja 2: Registro_Paros

Los 307 registros de paro convertidos en **tabla Excel nativa** (`Ctrl+T`):
- Columna calculada `costo_paro = horas_paro × costo_hora_parada` (lookup al maestro de equipos)
- Color automático por tipo: rojo claro para "No programado", verde claro para "Programado"
- Filtros habilitados por defecto: cualquier usuario puede filtrar por equipo, turno, categoría o mes

### Hoja 3: Analisis_OEE

**OEE por equipo** (Eficiencia General de Equipos — indicador ISO 22400):
```
OEE = Disponibilidad × Rendimiento × Calidad
Disponibilidad = (2.920 h/año − horas de paro NP) / 2.920 h/año
```
- Rendimiento y Calidad: valores por equipo basados en benchmarks del sector
- Resultado: 3 equipos bajo el 65 % de OEE (nivel "Aceptable")

**Pareto de causas** (tabla ordenada por horas DESC):
- Columna `% acumulado` calculada: identifica con exactitud qué categorías forman el "cuello" del 80 %
- La causa "Mecánica" concentra la mayor proporción del downtime no programado
- Segunda tabla: Pareto por equipo — confirma que los 3 equipos críticos absorben el 64 % del total

### Hoja 4: Dashboard

Vista ejecutiva diseñada para ser presentada en reunión de operaciones:
- **4 KPIs grandes**: horas totales, costo total, eventos NP, OEE promedio planta
- **Gráfico 1 — Pareto de equipos**: barras de horas + línea de % acumulado (doble eje Y)
- **Gráfico 2 — OEE por equipo**: barras horizontales, permite identificar los más débiles de un vistazo
- **Diagnóstico textual**: cuantifica el ahorro proyectado si se implementa el plan preventivo

---

## Fase 4 — Macro VBA (automatización del reporte mensual)

El área de mantenimiento necesitaba generar un informe mensual en formato fijo.
Antes lo hacía copiando celdas a mano, aplicando formato, guardando con nombre del mes — 3 horas.

La macro `InformeMensual` automatiza eso en 1 clic:
1. Detecta el mes anterior automáticamente (`DateSerial`)
2. Copia el Dashboard completo (valores + formatos + gráficos)
3. Congela los valores (sin fórmulas) para que el informe quede "sellado"
4. Agrega fecha y hora de generación
5. Guarda como `Informe_MM_YYYY.xlsx` en la misma carpeta

Segunda macro auxiliar `ActualizarSemaforo`: recalcula los colores de la hoja Equipos al abrir
el archivo meses después (cuando los "días restantes" ya cambiaron).

---

## Resultado final

Un panel que cualquier jefe de mantenimiento puede abrir, filtrar y presentar en reunión:
- Sin conocimientos de SQL ni Python
- Con el diagnóstico ya hecho y el ahorro cuantificado
- Con el reporte mensual automatizado

La misma lógica (Pareto + OEE + semáforo de vencimientos) escala a 50 equipos o a cualquier
planta que registre sus paros en una tabla estructurada.
