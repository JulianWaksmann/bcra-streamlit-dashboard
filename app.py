from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


APP_DIR = Path(__file__).parent
DATA_PATH = APP_DIR / "data" / "morosidad_entidad_202604.csv"
PERIOD_LABEL = "Abril 2026"


st.set_page_config(
    page_title="BCRA Morosidad 202604",
    page_icon="📉",
    layout="wide",
    initial_sidebar_state="expanded",
)


CSS = """
<style>
    :root {
        --bg: #111318;
        --panel: #191d26;
        --panel-soft: #222838;
        --text: #f5f7fb;
        --muted: #9aa3b2;
        --blue: #4c8dff;
        --red: #ff5c68;
        --amber: #f2b84b;
        --green: #58d68d;
    }

    .stApp {
        background:
            radial-gradient(circle at 20% 0%, rgba(76, 141, 255, 0.18), transparent 28rem),
            radial-gradient(circle at 90% 18%, rgba(255, 92, 104, 0.10), transparent 24rem),
            var(--bg);
        color: var(--text);
    }

    [data-testid="stSidebar"] {
        background: #0e1015;
        border-right: 1px solid rgba(255,255,255,0.08);
    }

    .hero {
        padding: 1.1rem 0 0.8rem;
        border-bottom: 1px solid rgba(255,255,255,0.08);
        margin-bottom: 1rem;
    }

    .hero h1 {
        font-size: 2.15rem;
        line-height: 1.05;
        margin: 0;
        letter-spacing: 0;
    }

    .hero p {
        color: var(--muted);
        margin: 0.55rem 0 0;
        font-size: 0.98rem;
    }

    .kpi-card {
        background: linear-gradient(180deg, rgba(255,255,255,0.055), rgba(255,255,255,0.025));
        border: 1px solid rgba(255,255,255,0.10);
        border-radius: 8px;
        padding: 1rem 1rem 0.9rem;
        min-height: 7.2rem;
        box-shadow: 0 10px 26px rgba(0,0,0,0.20);
    }

    .kpi-card .label {
        color: var(--muted);
        font-size: 0.74rem;
        text-transform: uppercase;
        letter-spacing: 0.04rem;
        margin-bottom: 0.45rem;
    }

    .kpi-card .value {
        color: var(--text);
        font-size: 1.65rem;
        font-weight: 760;
        line-height: 1.12;
    }

    .kpi-card .sub {
        color: var(--muted);
        margin-top: 0.45rem;
        font-size: 0.82rem;
    }

    .callout {
        background: rgba(76, 141, 255, 0.10);
        border: 1px solid rgba(76, 141, 255, 0.32);
        border-radius: 8px;
        padding: 1rem 1.05rem;
        color: var(--text);
    }

    .callout strong {
        color: white;
    }

    .section-title {
        font-size: 1.1rem;
        margin: 1.2rem 0 0.5rem;
        font-weight: 700;
    }

    div[data-testid="stMetric"] {
        background: var(--panel);
        border: 1px solid rgba(255,255,255,0.10);
        border-radius: 8px;
        padding: 0.85rem 1rem;
    }

    .stDataFrame {
        border: 1px solid rgba(255,255,255,0.10);
        border-radius: 8px;
        overflow: hidden;
    }
</style>
"""

st.markdown(CSS, unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH, dtype={"codigo_entidad": str, "fecha_info": str})
    numeric_cols = [
        "deudores_total",
        "deudores_irregulares",
        "pct_irregular_cantidad",
        "credito_total_miles_pesos",
        "credito_irregular_miles_pesos",
        "pct_irregular_monto",
        "registros_situacion_1",
        "registros_situacion_2",
        "registros_situacion_3",
        "registros_situacion_4",
        "registros_situacion_5",
        "registros_situacion_11",
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    df["entidad"] = df["codigo_entidad"] + " · " + df["nombre_entidad"]
    return df


def compact_number(value: float) -> str:
    value = float(value)
    abs_value = abs(value)
    if abs_value >= 1_000_000_000:
        return f"{value / 1_000_000_000:.1f}B"
    if abs_value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if abs_value >= 1_000:
        return f"{value / 1_000:.1f}K"
    return f"{value:,.0f}"


def fmt_int(value: float) -> str:
    return f"{value:,.0f}".replace(",", ".")


def fmt_pct(value: float) -> str:
    return f"{value:.2f}%".replace(".", ",")


def fmt_money_miles(value: float) -> str:
    return f"{compact_number(value)} miles $"


def weighted_pct(numerator: float, denominator: float) -> float:
    return 0.0 if denominator == 0 else numerator / denominator * 100


def base_layout(fig: go.Figure, height: int = 420) -> go.Figure:
    fig.update_layout(
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#f5f7fb",
        margin=dict(l=10, r=10, t=35, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    fig.update_xaxes(gridcolor="rgba(255,255,255,0.08)", zerolinecolor="rgba(255,255,255,0.18)")
    fig.update_yaxes(gridcolor="rgba(255,255,255,0.08)", zerolinecolor="rgba(255,255,255,0.18)")
    return fig


def kpi_card(label: str, value: str, sub: str = "") -> None:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="label">{label}</div>
            <div class="value">{value}</div>
            <div class="sub">{sub}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


df = load_data()

st.markdown(
    f"""
    <div class="hero">
        <h1>Mapa de morosidad BCRA</h1>
        <p>{PERIOD_LABEL}. Entidades financieras y no financieras, segmentadas por familias, empresas y total.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Explorar")
    segment_options = ["Familias", "Empresas", "Total", "Desconocido"]
    selected_segment = st.radio("Segmento", segment_options, index=0)

    sectors = ["Todos"] + sorted(df["sector"].dropna().unique().tolist())
    selected_sector = st.selectbox("Sector", sectors)

    min_debtors = st.slider(
        "Mínimo deudores por entidad",
        0,
        250_000,
        1_000,
        step=1_000,
        help=(
            "Filtra entidades con al menos esta cantidad de deudores en el segmento elegido. "
            "Sirve para sacar casos muy chicos donde un porcentaje alto puede venir de pocos registros."
        ),
    )

    search = st.text_input("Buscar entidad", placeholder="Ej. UALA, Nexo, Galicia...")

    metric_mode = st.segmented_control(
        "Ranking",
        options=["% monto", "% cantidad", "crédito irregular"],
        default="% monto",
    )


filtered = df[df["tipo_segmento"].eq(selected_segment)].copy()
if selected_sector != "Todos":
    filtered = filtered[filtered["sector"].eq(selected_sector)]
if min_debtors:
    filtered = filtered[filtered["deudores_total"].ge(min_debtors)]
if search.strip():
    needle = search.strip().casefold()
    filtered = filtered[
        filtered["entidad"].str.casefold().str.contains(needle, regex=False)
    ]

total_credit = filtered["credito_total_miles_pesos"].sum()
irregular_credit = filtered["credito_irregular_miles_pesos"].sum()
total_debtors = filtered["deudores_total"].sum()
irregular_debtors = filtered["deudores_irregulares"].sum()
irregular_amount_pct = weighted_pct(irregular_credit, total_credit)
irregular_count_pct = weighted_pct(irregular_debtors, total_debtors)

k1, k2, k3, k4 = st.columns(4)
with k1:
    kpi_card("% irreg. monto", fmt_pct(irregular_amount_pct), fmt_money_miles(irregular_credit))
with k2:
    kpi_card("% irreg. cantidad", fmt_pct(irregular_count_pct), f"{fmt_int(irregular_debtors)} irregulares")
with k3:
    kpi_card("Crédito total", fmt_money_miles(total_credit), "montos expresados en miles de pesos")
with k4:
    kpi_card("Deudores total", fmt_int(total_debtors), f"{len(filtered)} filas entidad-segmento")

if filtered.empty:
    st.warning("No hay datos para los filtros seleccionados.")
    st.stop()

left, right = st.columns([2.05, 1])

rank_metric = {
    "% monto": "pct_irregular_monto",
    "% cantidad": "pct_irregular_cantidad",
    "crédito irregular": "credito_irregular_miles_pesos",
}[metric_mode]

top = filtered.sort_values(rank_metric, ascending=False).head(15).copy()
top["nombre_corto"] = top["nombre_entidad"].str.slice(0, 34)

with left:
    st.markdown('<div class="section-title">Ranking de alerta</div>', unsafe_allow_html=True)
    fig_rank = px.bar(
        top.sort_values(rank_metric),
        x=rank_metric,
        y="nombre_corto",
        orientation="h",
        color=rank_metric,
        color_continuous_scale=["#4c8dff", "#f2b84b", "#ff5c68"],
        labels={
            "nombre_corto": "",
            "pct_irregular_monto": "% irregular por monto",
            "pct_irregular_cantidad": "% irregular por cantidad",
            "credito_irregular_miles_pesos": "crédito irregular (miles $)",
        },
        hover_data={
            "codigo_entidad": True,
            "nombre_entidad": True,
            "deudores_total": ":,.0f",
            "deudores_irregulares": ":,.0f",
            "credito_total_miles_pesos": ":,.0f",
            "credito_irregular_miles_pesos": ":,.0f",
            "pct_irregular_monto": ":.2f",
            "pct_irregular_cantidad": ":.2f",
            "nombre_corto": False,
        },
    )
    fig_rank.update_traces(marker_line_width=0, hovertemplate=None)
    fig_rank.update_layout(coloraxis_showscale=False)
    st.plotly_chart(base_layout(fig_rank, height=520), width="stretch")

with right:
    el_nexo = df[(df["codigo_entidad"].eq("55333")) & (df["tipo_segmento"].eq("Familias"))]
    st.markdown('<div class="section-title">Foco 55333</div>', unsafe_allow_html=True)
    if not el_nexo.empty:
        row = el_nexo.iloc[0]
        st.markdown(
            f"""
            <div class="callout">
                <strong>{row["nombre_entidad"]}</strong><br>
                Sector: {row["sector"]} · Tipo: Familias<br><br>
                <strong>{fmt_pct(row["pct_irregular_monto"])}</strong> irregular por monto<br>
                <strong>{fmt_pct(row["pct_irregular_cantidad"])}</strong> irregular por cantidad<br><br>
                Crédito total: <strong>{fmt_money_miles(row["credito_total_miles_pesos"])}</strong><br>
                Deudores: <strong>{fmt_int(row["deudores_total"])}</strong>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown('<div class="section-title">Composición del riesgo</div>', unsafe_allow_html=True)
    situation_totals = filtered[
        [
            "registros_situacion_1",
            "registros_situacion_2",
            "registros_situacion_3",
            "registros_situacion_4",
            "registros_situacion_5",
            "registros_situacion_11",
        ]
    ].sum()
    situation_df = pd.DataFrame(
        {
            "situación": ["1 Normal", "2 Bajo", "3 Medio", "4 Alto", "5 Irrecuperable", "11 Cubierta"],
            "registros": situation_totals.values,
        }
    )
    fig_donut = px.pie(
        situation_df,
        names="situación",
        values="registros",
        hole=0.58,
        color_discrete_sequence=["#58d68d", "#4c8dff", "#f2b84b", "#ff8d4c", "#ff5c68", "#9aa3b2"],
    )
    fig_donut.update_traces(textposition="inside", textinfo="percent")
    st.plotly_chart(base_layout(fig_donut, height=325), width="stretch")

st.markdown('<div class="section-title">Mapa monto vs cantidad</div>', unsafe_allow_html=True)
scatter_source = filtered[filtered["deudores_total"].gt(0)].copy()
scatter_source["credito_total_log"] = scatter_source["credito_total_miles_pesos"].clip(lower=1)
fig_scatter = px.scatter(
    scatter_source,
    x="pct_irregular_cantidad",
    y="pct_irregular_monto",
    size="credito_total_log",
    color="sector",
    hover_name="nombre_entidad",
    hover_data={
        "codigo_entidad": True,
        "deudores_total": ":,.0f",
        "deudores_irregulares": ":,.0f",
        "credito_total_miles_pesos": ":,.0f",
        "credito_irregular_miles_pesos": ":,.0f",
        "pct_irregular_cantidad": ":.2f",
        "pct_irregular_monto": ":.2f",
        "credito_total_log": False,
    },
    labels={
        "pct_irregular_cantidad": "% irregular cantidad",
        "pct_irregular_monto": "% irregular monto",
    },
    color_discrete_map={"Financiero": "#4c8dff", "No Financiero": "#ff5c68"},
)
fig_scatter.update_traces(marker=dict(opacity=0.72, line=dict(width=0.5, color="rgba(255,255,255,0.35)")))
st.plotly_chart(base_layout(fig_scatter, height=460), width="stretch")

table_cols = [
    "codigo_entidad",
    "nombre_entidad",
    "sector",
    "tipo_segmento",
    "deudores_total",
    "deudores_irregulares",
    "pct_irregular_cantidad",
    "credito_total_miles_pesos",
    "credito_irregular_miles_pesos",
    "pct_irregular_monto",
]
st.markdown('<div class="section-title">Detalle descargable</div>', unsafe_allow_html=True)
st.dataframe(
    filtered.sort_values(rank_metric, ascending=False)[table_cols],
    width="stretch",
    hide_index=True,
    column_config={
        "pct_irregular_cantidad": st.column_config.NumberColumn("% irreg. cantidad", format="%.2f%%"),
        "pct_irregular_monto": st.column_config.NumberColumn("% irreg. monto", format="%.2f%%"),
        "credito_total_miles_pesos": st.column_config.NumberColumn("crédito total miles $", format="%.0f"),
        "credito_irregular_miles_pesos": st.column_config.NumberColumn("crédito irregular miles $", format="%.0f"),
    },
)

st.caption(
    "Fuente: BCRA Central de Deudores del Sistema Financiero. "
    "El dashboard usa agregados por entidad y segmento, no el TXT bruto. "
    "Irregularidad definida como situaciones 2 a 5. Situación 1 es normal y situación 11 se muestra separada como cubierta."
)
