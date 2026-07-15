# ¿Cuánto pedir de cada producto y cuándo? — Optimización de inventario ABC-XYZ

Este proyecto nació de una pregunta que me hago siempre que veo un depósito: **¿por qué a casi todas
las empresas les sobra justo lo que no venden y les falta justo lo que más venden?** Quise ver si
podía reemplazar el "pedir a ojo" por una política que dijera, para cada producto, cuánto comprar y
en qué momento — y ponerle un número a lo que eso vale.

Lo armé sobre una distribuidora mayorista ficticia, **NorteLogix S.A.** (120 productos de consumo
masivo, 24 meses de demanda). Los datos son sintéticos y reproducibles (semilla fija), así que lo
que valida el proyecto es **el método**, no un caso real.

<p align="center">
  <a href="https://lucianovillagran75-arg.github.io/portfolio-data-analytics/proyectos/python/optimizacion-inventario-abcxyz/dashboard_interactivo.html">
    <img src="https://img.shields.io/badge/%E2%96%B6_Ver_dashboard_interactivo-0E6E78?style=for-the-badge&logoColor=white" alt="Ver dashboard interactivo">
  </a>
</p>

Panel ejecutivo con la salud del inventario, la regla 80/20 y los productos con capital atrapado o
en riesgo de quiebre — con tema claro/oscuro y animaciones. También podés abrir
[`dashboard_interactivo.html`](./dashboard_interactivo.html) localmente en el navegador.

---

## Cómo lo encaré

Lo primero fue decidir **cómo clasificar los productos**. La clasificación ABC clásica (ordenar por
facturación y cortar en 80/95%) es la que usa casi todo el mundo, pero tiene un agujero: te dice qué
producto **factura** mucho, no qué producto es **difícil de gestionar**. Un producto puede facturar
alto y ser un dolor de cabeza porque su demanda salta de un mes a otro.

Por eso le sumé la dimensión **XYZ**, que mide la *variabilidad* de la demanda (coeficiente de
variación = desvío / promedio). Cruzando las dos me quedó una matriz donde cada producto cae en una
de 9 celdas:

- **A-X** (facturan mucho, demanda estable) → los que **nunca** pueden faltar.
- **C-Z** (facturan poco, demanda errática) → donde se junta el sobrestock.

Con la clasificación lista, para cada producto calculé:

| Cálculo | Qué responde | Fórmula |
|---|---|---|
| **Stock de seguridad** | ¿Cuánto colchón necesito contra la incertidumbre? | `Z · σ · √LT` (servicio 95%, Z=1,645) |
| **Punto de reorden (ROP)** | ¿En qué nivel disparo la compra? | `μ · LT + stock de seguridad` |
| **Lote óptimo (EOQ)** | ¿De a cuánto conviene comprar? | `√(2·D·S / H)` |

Y con eso comparé el stock real contra la política ideal para detectar **exceso** (capital parado)
y **déficit** (venta en riesgo).

---

## Lo que encontré

Sobre los 120 productos, la matriz quedó así:

| | X (estable) | Y (variable) | Z (errático) |
|---|:--:|:--:|:--:|
| **A (alto valor)** | 13 | 7 | 1 |
| **B (medio)** | 8 | 11 | 2 |
| **C (bajo valor)** | 5 | 33 | 40 |

Lo que más me llamó la atención: **21 productos (los "A") concentran el 80% de la facturación**, y
casi la mitad del catálogo (los "C-Z") son cola larga que casi no mueve la aguja pero sí ocupa plata
y espacio. La foto clásica del 80/20, pero puesta en números.

Traducido a dinero:

| Hallazgo | Detalle | Impacto |
|---|---|---|
| Capital parado en sobrestock | 30 productos con exceso sobre su política óptima | **$1,1 M ARS** liberables |
| Ventas en riesgo por quiebre | 8 productos por debajo del punto de reorden | **$2,2 M ARS** en riesgo |
| Comprar en lote óptimo (EOQ) | menos órdenes en los ítems lentos, mismo nivel de servicio | **$3,5 M ARS/año** |
| Automatizar el cálculo mensual | de 8 h de trabajo manual a 30 segundos | **$0,27 M ARS/año** |

**Impacto total estimado: ~$7,0 M ARS.** El detalle, con cada supuesto declarado, está en
[`informe.md`](./informe.md).

---

## Cómo leo el impacto (y qué asumí)

No me gusta tirar un número sin decir de dónde sale, así que estos son los supuestos que hay detrás.
Son discutibles a propósito — un analista tiene que poder defenderlos o cambiarlos:

- **Nivel de servicio del 95%** (Z = 1,645). Es una decisión de política, no una verdad: subirlo al
  98% agranda el stock de seguridad (y el capital inmovilizado). Lo dejé plano en 95% para todos,
  aunque **no es lo ideal** (ver más abajo).
- **Costo de mantener stock = 25% anual** del costo del producto (almacenamiento + capital + merma).
  Es el rango habitual del sector; con otro número el EOQ cambia.
- **Lead time fijo por producto.** En la vida real el proveedor a veces tarda más; ese riesgo hoy no
  está modelado.
- **Ahorro de tiempo** valuado a $3.000 ARS/hora del analista, 8 h/mes → 30 s.

---

## Limitaciones y qué haría distinto

Si tuviera que llevar esto a una empresa de verdad, hay tres cosas que cambiaría antes:

1. **Nivel de servicio diferenciado por clase.** Usé 95% para todos, pero no tiene sentido cuidar
   igual un A-X (que no puede faltar) que un C-Z (que casi no se vende). Le pondría **98% a los A-X**
   y **90% a los C-Z**: más plata donde importa, menos capital atado donde no.
2. **Demanda con estacionalidad.** El modelo asume una demanda mensual sin patrón. Si el negocio
   tiene picos (fiestas, verano), el punto de reorden se queda corto en temporada alta.
3. **Validar sobre datos reales.** Acá probé que el método funciona sobre datos sintéticos. El paso
   siguiente sería correrlo con el historial real de una distribuidora y ajustar los supuestos.

El EOQ, además, es más confiable en los productos de demanda estable (X/Y) que en los erráticos (Z),
donde la fórmula empieza a hacer agua — a esos conviene manejarlos con revisión periódica, no con
lote fijo.

---

## Qué muestra el dashboard

El script genera este panel de una sola corrida (arriba):

1. **Salud del inventario** — un dónut que muestra, de un vistazo, cuántos productos están sanos y
   cuántos necesitan acción (sobrestock o riesgo de quiebre).
2. **Regla 80/20** — cuánto del catálogo vs cuánto de la facturación aporta cada clase A/B/C.
3. **Top capital atrapado** — los productos con más plata inmovilizada en sobrestock.
4. **Top riesgo de quiebre** — los productos por debajo del punto de reorden, a reponer ya.
5. **Tarjetas de impacto** — los cuatro números económicos en una fila.

📄 También lo dejé como [reporte ejecutivo en PDF](./output/Reporte_OptimizacionInventario.pdf).

---

## Reproducirlo

```bash
cd proyectos/python/optimizacion-inventario-abcxyz
python datos/generar_datos.py     # genera los 3 CSV (semilla fija SEED=42)
python src/analisis_abcxyz.py     # clasifica, calcula la política, arma el dashboard y mide el impacto
```

Requiere `pandas`, `numpy` y `matplotlib` (están en `requirements.txt`).

## Archivos

| Archivo | Qué es |
|---|---|
| [`datos/generar_datos.py`](./datos/generar_datos.py) | Generador reproducible de los 3 CSV |
| [`src/analisis_abcxyz.py`](./src/analisis_abcxyz.py) | El análisis completo: clasificación + política + dashboard + impacto |
| [`output/clasificacion_abcxyz.csv`](./output/clasificacion_abcxyz.csv) | Los 120 productos con su clase, CV y facturación |
| [`output/politica_inventario.csv`](./output/politica_inventario.csv) | Stock de seguridad, ROP, EOQ, exceso y déficit por producto |
| [`output/dashboard_inventario.png`](./output/dashboard_inventario.png) | El panel ejecutivo |
| [`informe.md`](./informe.md) · [`PASO_A_PASO.md`](./PASO_A_PASO.md) | Hallazgos con supuestos · proceso de construcción |

---

*Stack: Python (pandas, numpy, matplotlib). Datos sintéticos del sector distribución, semilla fija
para que el resultado sea siempre el mismo. Importes en pesos argentinos.*
