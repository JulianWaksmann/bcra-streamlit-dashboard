# BCRA Morosidad Dashboard

Dashboard Streamlit para explorar deudores y niveles de situacion por entidad informante de la Central de Deudores BCRA.

Periodo incluido: `202604`.

El objetivo del tablero es mirar la distribucion de deuda por entidad, segmento y nivel de situacion, sin cargar en la app el archivo bruto completo. El TXT original tiene mas de 40 millones de registros, por eso se procesa previamente y en este repo queda solamente una version agregada y liviana.

## Grano de analisis

El conteo se hace por relacion **entidad + identificador de deudor**.

Eso significa que una misma persona puede contar mas de una vez en el sistema si aparece en mas de una entidad, pero solo una vez dentro de cada entidad.

Ejemplo:

| Deudor | Entidad | Situacion | Como cuenta |
| --- | --- | ---: | --- |
| A | Galicia | 4 | +1 en Galicia nivel 4 |
| A | Macro | 1 | +1 en Macro nivel 1 |

Esta distincion es importante: el dashboard evalua la cartera de cada entidad, no la situacion global consolidada de una persona en todo el sistema financiero.

## Montos

Los montos tambien se toman dentro de cada entidad.

Si una persona debe `100` en Galicia y `50` en Macro:

- Galicia suma `100`
- Macro suma `50`
- no se asigna el total `150` a ninguna de las dos entidades

El promedio por deudor se calcula como:

```text
monto total seleccionado de la entidad / cantidad de deudores seleccionados de la entidad
```

## Segmentos

La clasificacion usada por el tablero es:

- `Empresas`: CUIT con prefijo `30`, `33` o `34`
- `Familias`: cualquier otro identificador
- `Total`: empresas + familias

No se muestra una categoria `Desconocido`. Los casos que no entran en los prefijos de empresa se incorporan a `Familias`.

## Sector financiero / no financiero

El archivo fuente usado para el dashboard no trae un campo textual de sector. Para el tablero se infiere desde el codigo de entidad:

- codigos menores a `50000`: `Financiero`
- codigos mayores o iguales a `50000`: `No Financiero`

Esta regla esta implementada en `scripts/build_streamlit_level_metrics.py`.

## Niveles de situacion

El dashboard contempla los niveles detectados en el periodo `202604`:

- `1`: normal
- `2`: seguimiento especial / riesgo bajo
- `3`: problemas / riesgo medio
- `4`: alto riesgo
- `5`: irrecuperable
- `11`: asistencias cubiertas totalmente con garantias preferidas A

En la sidebar hay un checklist de niveles. Los KPIs, rankings y graficos se recalculan con los niveles marcados.

Si se quieren ver todos los niveles, se deben marcar todos individualmente. Si se quiere la vista clasica de morosidad, se dejan marcados solo los niveles `2`, `3`, `4` y `5`.

## Promedio por deudor

El promedio por deudor no tiene que subir necesariamente cuando sube el nivel de situacion. La situacion BCRA refleja riesgo o comportamiento de pago, no tamano de deuda.

Por ejemplo, en `Familias` puede ocurrir que el nivel `2` tenga mayor monto promedio que el nivel `4` porque los deudores de nivel `2` concentran montos mas grandes, aunque esten en una situacion menos grave.

## Que significa "minimo deudores"

El filtro **Minimo deudores por entidad** elimina del ranking las entidades que tienen menos de esa cantidad de deudores dentro de los niveles seleccionados. Aplica cuando el selector de entidad esta en `Todas`.

Ejemplo: si el segmento es `Familias`, los niveles seleccionados son `2-5` y el minimo es `1.000`, el tablero solo muestra entidades con al menos 1.000 deudores familiares en esos niveles.

La razon del filtro es evitar que casos chicos distorsionen rankings, porcentajes y promedios. Si se elige una entidad puntual, el minimo no se aplica para que esa entidad no desaparezca por tener poco volumen.

## Datos incluidos

La app usa datos agregados livianos:

- `data/morosidad_niveles_202604.csv`
- `data/manifest_morosidad_niveles_202604.json`

El CSV principal contiene:

- periodo
- codigo y nombre de entidad
- sector: financiero / no financiero
- segmento: familias / empresas / total
- nivel de situacion
- cantidad de deudores
- monto total en miles de pesos
- monto promedio por deudor en miles de pesos
- porcentaje de deudores y monto dentro del segmento
- cantidad de registros fuente usados para el agregado

No se incluye el TXT bruto de 40M+ filas.

## Procesamiento reproducible

El codigo de procesamiento esta en:

- `scripts/build_streamlit_level_metrics.py`
- `scripts/build_bcra_deudores.py`

Uso esperado desde una carpeta que contenga los archivos fuente BCRA:

```bash
python scripts/build_streamlit_level_metrics.py \
  --input-dir /ruta/a/202604 \
  --output-dir /ruta/de/salida \
  --period 202604
```

El script espera encontrar:

- `deudores.txt`
- `Maeent.txt`

## Correr localmente

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Publicar gratis

1. Subir esta carpeta como repo a GitHub.
2. Entrar a https://share.streamlit.io/
3. Conectar el repo.
4. Elegir:
   - Branch: `main`
   - Main file path: `app.py`
5. Deploy.
