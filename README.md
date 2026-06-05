# BCRA Morosidad Dashboard

Dashboard Streamlit para explorar morosidad de entidades informantes de la Central de Deudores BCRA.

Periodo incluido: `202604`.

El objetivo del tablero es mirar morosidad a nivel agregado, sin cargar en la app el archivo bruto completo de deudores. El TXT original tiene mas de 40 millones de registros, por eso se proceso previamente y se dejo en este repo solamente una version resumida por entidad, sector y tipo de persona.

## Criterio de procesamiento

La fuente primaria es el archivo de deudores BCRA del periodo `202604`, interpretado segun el PDF de especificacion incluido en la descarga original. Cada linea del TXT representa una deuda informada por una entidad para un identificador de deudor.

Para el dashboard no se usa el detalle completo. Se construyen agregados por:

- codigo de entidad
- nombre de entidad
- sector de entidad: financiero / no financiero
- tipo de segmento: familias / empresas / total

El tipo de segmento se infiere desde el identificador fiscal:

- familias: CUIT/CUIL con prefijos `20`, `23`, `24` o `27`
- empresas: CUIT con prefijos `30`, `33` o `34`
- desconocido: identificadores que no entran en esas reglas
- total: suma general de la entidad

## Que valores se filtran

La morosidad se calcula tomando como irregulares las situaciones BCRA `2`, `3`, `4` y `5`.

- Situacion `1`: normal. No se considera morosa.
- Situaciones `2` a `5`: deuda irregular. Son el foco del tablero.
- Situacion `11`: asistencias cubiertas totalmente con garantias preferidas A. Se conserva separada para no mezclarla con mora tradicional.

Esto permite responder preguntas como:

- que entidades tienen mayor porcentaje irregular por monto
- que entidades tienen mayor porcentaje irregular por cantidad de deudores
- cuanto credito total e irregular concentra cada entidad
- como se comporta una entidad puntual, por ejemplo `55333 El Nexo S.A.`

## Que significa "minimo deudores"

El filtro **Minimo deudores por entidad** elimina del ranking las entidades que tienen menos de esa cantidad de deudores en el segmento seleccionado.

Ejemplo: si el segmento es `Familias` y el minimo es `1.000`, el tablero solo muestra entidades con al menos 1.000 deudores familiares.

La razon del filtro es evitar que casos muy chicos distorsionen el ranking. Una entidad con pocos deudores puede mostrar un porcentaje de mora muy alto, pero no ser relevante en volumen.

## Datos

La app usa datos agregados livianos:

- `data/morosidad_entidad_202604.csv`
- `data/top_morosidad_familias_202604.csv`

No usa el TXT bruto de 40M+ filas. Ese archivo queda como fuente primaria/procesamiento, no como insumo directo del dashboard.

El CSV principal contiene, entre otros campos:

- deudores totales
- deudores irregulares
- porcentaje irregular por cantidad
- credito total en miles de pesos
- credito irregular en miles de pesos
- porcentaje irregular por monto
- cantidad de registros por situacion BCRA

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

## Definicion resumida de morosidad

Se considera irregular:

- Situacion 2
- Situacion 3
- Situacion 4
- Situacion 5

La situacion 1 se considera normal.

La situacion 11 se muestra separada como cubierta, segun el PDF de especificacion BCRA.
