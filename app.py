from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


APP_DIR = Path(__file__).parent
DATA_PATH = APP_DIR / "data" / "morosidad_niveles_202604.csv"
PERIOD_LABEL = "Abril 2026"

LEVEL_LABELS = {
    "1": "1 - Normal",
    "2": "2 - Seguimiento especial",
    "3": "3 - Problemas",
    "4": "4 - Alto riesgo",
    "5": "5 - Irrecuperable",
    "11": "11 - Cubierta garantia A",
}
LEVEL_ORDER = ["1", "2", "3", "4", "5", "11"]


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

    .stDataFrame {
        border: 1px solid rgba(255,255,255,0.10);
        border-radius: 8px;
        overflow: hidden;
    }

    div[data-baseweb="select"],
    div[data-baseweb="select"] *,
    div[role="radiogroup"] label,
    div[role="radiogroup"] label *,
    label[data-baseweb="checkbox"],
    label[data-baseweb="checkbox"] * {
        cursor: pointer !important;
    }

    div[data-baseweb="select"] input {
        caret-color: transparent !important;
    }
</style>
"""

st.markdown(CSS, unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH, dtype={"codigo_entidad": str, "fecha_info": str, "situacion_codigo": str})
    numeric_cols = [
        "deudores",
        "monto_total_miles_pesos",
        "monto_promedio_miles_pesos",
        "pct_deudores_segmento",
        "pct_monto_segmento",
        "registros_origen",
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    df["situacion_codigo"] = df["situacion_codigo"].replace({"nan": "0", "": "0"}).fillna("0")
    df["entidad"] = df["codigo_entidad"] + " · " + df["nombre_entidad"]
    df["nivel"] = df["situacion_codigo"].map(LEVEL_LABELS).fillna(df["situacion_codigo"])
    df["monto_promedio_pesos"] = df["monto_promedio_miles_pesos"] * 1_000
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


def fmt_money_from_miles(value: float) -> str:
    return f"{compact_number(float(value) * 1_000)} $"


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


def aggregate_entities(df: pd.DataFrame) -> pd.DataFrame:
    grouped = (
        df.groupby(["codigo_entidad", "nombre_entidad", "sector", "tipo_segmento"], as_index=False)
        .agg(
            deudores=("deudores", "sum"),
            monto_total_miles_pesos=("monto_total_miles_pesos", "sum"),
            registros_origen=("registros_origen", "sum"),
        )
    )
    grouped["monto_promedio_miles_pesos"] = (
        grouped["monto_total_miles_pesos"] / grouped["deudores"].replace(0, pd.NA)
    ).fillna(0)
    grouped["monto_promedio_pesos"] = grouped["monto_promedio_miles_pesos"] * 1_000
    grouped["entidad"] = grouped["codigo_entidad"] + " · " + grouped["nombre_entidad"]
    return grouped


df = load_data()

st.markdown(
    f"""
    <div class="hero">
        <h1>Mapa de morosidad BCRA</h1>
        <p>{PERIOD_LABEL}. Deudores por entidad, segmento y nivel de situacion.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Explorar")
    selected_segment = st.radio(
        "Segmento",
        ["Familias", "Empresas", "Total"],
        index=0,
        help=(
            "Empresas: CUIT con prefijo 30, 33 o 34. "
            "Familias: todo el resto de identificadores. Total: empresas + familias."
        ),
    )

    st.markdown(
        """
        <div style="font-size:0.875rem; margin-bottom:0.35rem;">
            Niveles de situacion
            <span title="Los KPIs, rankings y montos se recalculan con los niveles marcados." style="cursor:help; color:#9aa3b2;">?</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    selected_levels = {
        level
        for level in LEVEL_ORDER
        if st.checkbox(LEVEL_LABELS[level], value=True, key=f"level_{level}")
    }

    sectors = ["Todos"] + sorted(df["sector"].dropna().unique().tolist())
    selected_sector = st.selectbox("Sector", sectors)

    entity_scope = df[df["tipo_segmento"].eq(selected_segment)].copy()
    if selected_sector != "Todos":
        entity_scope = entity_scope[entity_scope["sector"].eq(selected_sector)]
    entity_options = ["Todas"] + sorted(entity_scope["entidad"].dropna().unique().tolist())
    pending_entity = st.session_state.pop("pending_entity", None)
    if pending_entity in entity_options:
        st.session_state["selected_entity"] = pending_entity
    elif st.session_state.get("selected_entity", "Todas") not in entity_options:
        st.session_state["selected_entity"] = "Todas"
    selected_entity = st.selectbox(
        "Entidad",
        entity_options,
        key="selected_entity",
        help="Filtra una entidad puntual. Las opciones se ajustan al segmento y sector seleccionados.",
    )

    min_debtors = st.slider(
        "Minimo deudores por entidad",
        0,
        250_000,
        1_000,
        step=1_000,
        help=(
            "Cuando Entidad esta en Todas, filtra entidades con al menos esta cantidad de deudores "
            "dentro de los niveles seleccionados. Sirve para sacar casos chicos que distorsionan rankings."
        ),
    )

    metric_mode = st.segmented_control(
        "Ranking",
        options=["monto total", "cantidad deudores", "monto promedio"],
        default="monto total",
    )

if not selected_levels:
    st.warning("Selecciona al menos un nivel de situacion.")
    st.stop()

base = df[df["tipo_segmento"].eq(selected_segment)].copy()
if selected_sector != "Todos":
    base = base[base["sector"].eq(selected_sector)]
if selected_entity != "Todas":
    base = base[base["entidad"].eq(selected_entity)]

selected_rows = base[base["situacion_codigo"].isin(selected_levels)].copy()
entity_totals_all_levels = aggregate_entities(base)
entity_selected = aggregate_entities(selected_rows)

if min_debtors and selected_entity == "Todas":
    entity_selected = entity_selected[entity_selected["deudores"].ge(min_debtors)]
    selected_entity_codes = set(entity_selected["codigo_entidad"])
    selected_rows = selected_rows[selected_rows["codigo_entidad"].isin(selected_entity_codes)]
    base = base[base["codigo_entidad"].isin(selected_entity_codes)]
    entity_totals_all_levels = entity_totals_all_levels[
        entity_totals_all_levels["codigo_entidad"].isin(selected_entity_codes)
    ]

total_debtors = entity_selected["deudores"].sum()
total_amount = entity_selected["monto_total_miles_pesos"].sum()
all_level_debtors = entity_totals_all_levels["deudores"].sum()
all_level_amount = entity_totals_all_levels["monto_total_miles_pesos"].sum()
avg_amount = 0.0 if total_debtors == 0 else total_amount / total_debtors

k1, k2, k3 = st.columns(3)
with k1:
    kpi_card("Monto niveles seleccionados", fmt_money_miles(total_amount), f"{fmt_pct(weighted_pct(total_amount, all_level_amount))} del monto total")
with k2:
    kpi_card("Deudores seleccionados", fmt_int(total_debtors), f"{fmt_pct(weighted_pct(total_debtors, all_level_debtors))} del segmento")
with k3:
    kpi_card("Promedio por deudor", fmt_money_from_miles(avg_amount), "monto promedio dentro de entidad")

if entity_selected.empty:
    st.warning("No hay datos para los filtros seleccionados.")
    st.stop()

left, right = st.columns([2.05, 1])

rank_metric = {
    "monto total": "monto_total_miles_pesos",
    "cantidad deudores": "deudores",
    "monto promedio": "monto_promedio_pesos",
}[metric_mode]

top = entity_selected.sort_values(rank_metric, ascending=False).head(15).copy()
top["nombre_corto"] = top["nombre_entidad"].str.slice(0, 34)

with left:
    st.markdown('<div class="section-title">Ranking por niveles seleccionados</div>', unsafe_allow_html=True)
    st.caption("Toca una barra para filtrar automaticamente esa entidad.")
    fig_rank = px.bar(
        top.sort_values(rank_metric),
        x=rank_metric,
        y="nombre_corto",
        orientation="h",
        color=rank_metric,
        color_continuous_scale=["#4c8dff", "#f2b84b", "#ff5c68"],
        labels={
            "nombre_corto": "",
            "monto_total_miles_pesos": "monto total (miles $)",
            "deudores": "deudores",
            "monto_promedio_pesos": "monto promedio ($)",
        },
        hover_data={
            "codigo_entidad": True,
            "nombre_entidad": True,
            "deudores": ":,.0f",
            "monto_total_miles_pesos": ":,.0f",
            "monto_promedio_pesos": ":,.0f",
            "nombre_corto": False,
        },
        custom_data=["entidad"],
    )
    fig_rank.update_traces(marker_line_width=0, hovertemplate=None)
    fig_rank.update_layout(coloraxis_showscale=False)
    rank_event = st.plotly_chart(
        base_layout(fig_rank, height=520),
        width="stretch",
        key="ranking_entidades",
        on_select="rerun",
        selection_mode="points",
    )
    selection = getattr(rank_event, "selection", None)
    selected_points = selection.get("points", []) if selection else []
    if selected_points:
        clicked_entity = selected_points[0].get("customdata", [None])[0]
        if clicked_entity and clicked_entity != st.session_state.get("selected_entity"):
            st.session_state["pending_entity"] = clicked_entity
            st.rerun()

with right:
    st.markdown('<div class="section-title">Distribucion por nivel</div>', unsafe_allow_html=True)
    level_totals = (
        selected_rows.groupby(["situacion_codigo", "nivel"], as_index=False)
        .agg(deudores=("deudores", "sum"), monto_total_miles_pesos=("monto_total_miles_pesos", "sum"))
        .sort_values("situacion_codigo", key=lambda col: col.map({level: idx for idx, level in enumerate(LEVEL_ORDER)}))
    )
    fig_donut = px.pie(
        level_totals,
        names="nivel",
        values="monto_total_miles_pesos",
        hole=0.58,
        color="situacion_codigo",
        color_discrete_map={
            "0": "#9aa3b2",
            "1": "#58d68d",
            "2": "#4c8dff",
            "3": "#f2b84b",
            "4": "#ff8d4c",
            "5": "#ff5c68",
            "11": "#7f8cff",
        },
    )
    fig_donut.update_traces(textposition="inside", textinfo="percent")
    st.plotly_chart(base_layout(fig_donut, height=325), width="stretch")

st.markdown('<div class="section-title">Mapa cantidad vs monto promedio</div>', unsafe_allow_html=True)
scatter_source = entity_selected[entity_selected["deudores"].gt(0)].copy()
scatter_source["bubble_size"] = scatter_source["monto_total_miles_pesos"].clip(lower=1)
fig_scatter = px.scatter(
    scatter_source,
    x="deudores",
    y="monto_promedio_pesos",
    size="bubble_size",
    color="sector",
    hover_name="nombre_entidad",
    hover_data={
        "codigo_entidad": True,
        "deudores": ":,.0f",
        "monto_total_miles_pesos": ":,.0f",
        "monto_promedio_pesos": ":,.0f",
        "bubble_size": False,
    },
    labels={
        "deudores": "deudores en niveles seleccionados",
        "monto_promedio_pesos": "monto promedio por deudor ($)",
    },
    color_discrete_map={"Financiero": "#4c8dff", "No Financiero": "#ff5c68"},
)
fig_scatter.update_xaxes(type="log")
fig_scatter.update_traces(marker=dict(opacity=0.72, line=dict(width=0.5, color="rgba(255,255,255,0.35)")))
st.plotly_chart(base_layout(fig_scatter, height=460), width="stretch")

st.markdown('<div class="section-title">Detalle por entidad y nivel</div>', unsafe_allow_html=True)
detail = selected_rows.sort_values(["codigo_entidad", "situacion_codigo"])[
    [
        "codigo_entidad",
        "nivel",
        "deudores",
        "monto_promedio_pesos",
        "monto_total_miles_pesos",
        "pct_deudores_segmento",
        "pct_monto_segmento",
        "nombre_entidad",
    ]
]

st.dataframe(
    detail,
    width="stretch",
    hide_index=True,
    column_config={
        "codigo_entidad": "codigo",
        "nivel": "nivel situacion",
        "monto_promedio_pesos": st.column_config.NumberColumn("promedio $", format="%.0f"),
        "monto_total_miles_pesos": st.column_config.NumberColumn("monto total miles $", format="%.0f"),
        "pct_deudores_segmento": st.column_config.NumberColumn("% deudores segmento", format="%.2f%%"),
        "pct_monto_segmento": st.column_config.NumberColumn("% monto segmento", format="%.2f%%"),
    },
)

st.caption(
    "Fuente: BCRA Central de Deudores del Sistema Financiero. "
    "Conteo por entidad-deudor: una misma persona cuenta una vez por cada entidad donde aparece. "
    "Empresas: prefijos CUIT 30, 33 y 34; todo el resto se clasifica como Familias. "
    "Los montos corresponden al deudor dentro de esa entidad, no a su deuda total en el sistema."
)
