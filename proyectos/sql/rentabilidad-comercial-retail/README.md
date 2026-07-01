# 🗄️ Análisis de Rentabilidad Comercial — Retail Multi-sucursal

> **Herramienta:** SQL (SQLite)
> **Sector:** Comercial / Retail
> **Contexto:** Cadena minorista de consumo masivo con 5 sucursales ("TiendaNova")
> **Período:** Enero 2024 – Diciembre 2025 · 800 clientes · 37 productos · 15.700 ventas

---

## 🎯 El problema

La cadena facturaba **$176,6 M** en 24 meses, pero la rentabilidad se gestionaba "a ojo".
Nadie podía responder con datos tres preguntas que valen plata:

- ¿Qué productos estamos vendiendo **a pérdida** sin darnos cuenta?
- ¿Qué clientes **dejaron de comprar** y cuánto se fue con ellos?
- ¿Por qué una sucursal **rinde por debajo** del resto?

> *"Vendíamos mucho, pero al final del mes el margen no cerraba y no sabíamos por qué."*

El margen promedio era del **28,2 %**, sano en apariencia, pero escondía fugas que solo
aparecen cuando cruzás ventas, costos, descuentos, clientes y sucursales en un mismo modelo.

---

## 💡 La solución

Modelé los datos en un **esquema estrella** (una tabla de hechos + tres dimensiones) y escribí
una batería de consultas SQL que detectan exactamente dónde se fuga el margen y el capital.
Cada consulta responde una pregunta de negocio y termina con un número accionable.

### Modelo de datos

```
ventas (15.700 líneas de venta)
│   fecha · cantidad · precio_unitario · descuento · costo_unitario · ingreso · margen
│
├── clientes     → segmento · ciudad · region · fecha_alta
├── productos    → categoria · costo_unitario · precio_lista
└── sucursales   → nombre_sucursal · ciudad · region
```

### Las consultas

| # | Consulta | Pregunta de negocio |
|---|----------|---------------------|
| 00 | [`00_perfilado.sql`](./queries/00_perfilado.sql) | ¿Con qué datos estoy trabajando? (control) |
| 01 | [`01_margen_negativo.sql`](./queries/01_margen_negativo.sql) | ¿Qué productos venden a pérdida? |
| 02 | [`02_baja_rotacion.sql`](./queries/02_baja_rotacion.sql) | ¿Qué productos inmovilizan capital? |
| 03 | [`03_fuga_clientes.sql`](./queries/03_fuga_clientes.sql) | ¿Cuántos clientes perdimos y cuánto valían? |
| 04 | [`04_brecha_sucursales.sql`](./queries/04_brecha_sucursales.sql) | ¿Qué sucursal rinde por debajo y cuánto cuesta? |

---

## 📊 Resultados

| Hallazgo | Antes | Después | Impacto |
|---|---|---|---|
| Productos vendidos bajo margen | No medido | **4 productos · $1,82 M acumulado** | **$0,91 M/año** al repreciar |
| Fuga de clientes | Invisible | **156 clientes (21,7 %)** | **$0,74 M/año** al recuperarlos |
| Brecha de sucursal | Invisible | **Sur: −16 % de ticket** | **$0,39 M/año** al cerrar la brecha |
| Capital en baja rotación | No medido | **5 productos · $79 k** | Capital liberable |
| Tiempo de análisis | Manual, horas | **Consultas reproducibles** | Segundos |

### 💰 Impacto total estimado: **~$2,0 M/año** (≈ 8 % del margen anual)

Todo identificado con SQL, sin invertir en marketing ni en nuevos clientes: solo dejando de
perder margen donde ya se estaba perdiendo. El detalle completo, con supuestos, está en
[`informe.md`](./informe.md).

![Impacto por hallazgo SQL](./output/impacto_hallazgos.png)

---

## 🔧 Técnicas SQL utilizadas

```sql
-- CTEs encadenadas para legibilidad (un paso por bloque)
WITH activos_2024 AS (...), activos_2025 AS (...), fugados AS (...)

-- Agregación de negocio sobre la tabla de hechos
SUM(margen), SUM(ingreso), AVG(descuento)

-- Agrupación temporal sin columnas extra
substr(fecha, 1, 7)

-- Comparación contra línea base (un número solo no dice nada)
ticket_promedio vs. mediana de la red
```

- Modelado en **esquema estrella** (hechos + dimensiones) con índices para rendimiento.
- **JOINs** con `USING`, **CTEs** (`WITH`) y subconsultas correlacionadas.
- Métricas de negocio derivadas: margen $, margen %, ticket promedio, rotación.
- Validación contra totales de control (consulta de perfilado).

---

## 📁 Archivos

| Archivo | Descripción |
|---|---|
| [`queries/`](./queries/) | Las 5 consultas, una por pregunta de negocio, comentadas |
| [`datos/generar_datos.py`](./datos/generar_datos.py) | Generador reproducible del dataset (semilla fija) |
| [`datos/`](./datos/) | CSV crudos + descripción del modelo |
| [`informe.md`](./informe.md) | Hallazgos, evidencia y tabla resumen ejecutiva |
| [`PASO_A_PASO.md`](./PASO_A_PASO.md) | Documentación del proceso de construcción |

### ▶️ Cómo reproducirlo

```bash
cd proyectos/sql/rentabilidad-comercial-retail
python datos/generar_datos.py          # genera datos/retail.db (semilla fija)
sqlite3 datos/retail.db ".read queries/01_margen_negativo.sql"
```

---

## 🧠 Qué demuestra este proyecto

Demuestra la capacidad de **convertir SQL en decisiones de negocio rentables**: no se trata de
escribir consultas, sino de saber qué preguntar. El mismo modelo y las mismas consultas escalan a
millones de filas sin cambiar la lógica, y se traducen directamente a recomendaciones con un
número de impacto detrás.

---

*Datos simulados con distribuciones realistas del sector retail · Portfolio de Datos y Analítica*
