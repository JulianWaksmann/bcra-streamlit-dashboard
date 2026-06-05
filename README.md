# BCRA Morosidad Dashboard

Dashboard Streamlit para explorar morosidad de entidades informantes de la Central de Deudores BCRA.

Periodo incluido: `202604`.

## Datos

La app usa datos agregados livianos:

- `data/morosidad_entidad_202604.csv`
- `data/top_morosidad_familias_202604.csv`

No usa el TXT bruto de 40M+ filas. Ese archivo queda como fuente primaria/procesamiento, no como insumo directo del dashboard.

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

## Definicion de morosidad

Se considera irregular:

- Situacion 2
- Situacion 3
- Situacion 4
- Situacion 5

La situacion 1 se considera normal.

La situacion 11 se muestra separada como cubierta, segun el PDF de especificacion BCRA.
