import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import os
from datetime import datetime
from pathlib import Path

# Configure page
st.set_page_config(
    page_title="Test Analysis - QA Dashboard",
    page_icon=":bar_chart:",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .success-card { background: linear-gradient(135deg, #2ecc71 0%, #27ae60 100%); }
    .warning-card { background: linear-gradient(135deg, #f39c12 0%, #e67e22 100%); }
    .danger-card { background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%); }
    .info-card { background: linear-gradient(135deg, #3498db 0%, #2980b9 100%); }
    .score-badge { font-size: 3rem; font-weight: bold; text-align: center; }
</style>
""", unsafe_allow_html=True)

st.title(":bar_chart: Analisis Completo de la Suite de Tests")
st.markdown("### Estado actual y recomendaciones de mejora")
st.markdown("---")

# Load analysis data
DATA_DIR = Path(__file__).parent.parent / "data"

@st.cache_data(ttl=300)
def load_analysis_data():
    json_path = DATA_DIR / "test-analysis-complete.json"
    if json_path.exists():
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

analysis = load_analysis_data()

if analysis is None:
    st.error("No se encontraron datos de analisis")
    st.info("Se requiere el archivo `data/test-analysis-complete.json`")
    st.stop()

# Metadata
col1, col2 = st.columns([3, 1])
with col1:
    st.caption(f"**Proyecto:** {analysis['metadata']['projectName']}")
with col2:
    if 'generatedAt' in analysis['metadata']:
        st.caption(f"**Generado:** {analysis['metadata']['generatedAt'][:16]}")

st.markdown("---")

# Key metrics
st.subheader(":dart: Metricas Clave")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="metric-card info-card">
        <h3>Tests</h3>
        <div class="score-badge">{analysis['structure']['totalTestCases']}</div>
        <p style="margin: 0; opacity: 0.9;">Test Cases</p>
    </div>
    """, unsafe_allow_html=True)
    st.caption(f"{analysis['structure']['totalTestFiles']} archivos")

with col2:
    st.markdown(f"""
    <div class="metric-card success-card">
        <h3>Page Objects</h3>
        <div class="score-badge">{analysis['structure']['totalPageObjects']}</div>
        <p style="margin: 0; opacity: 0.9;">Objetos de Pagina</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    coverage = analysis['coverage']['coveragePercentage']
    card_class = "success-card" if coverage >= 70 else "warning-card" if coverage >= 50 else "danger-card"
    st.markdown(f"""
    <div class="metric-card {card_class}">
        <h3>Cobertura</h3>
        <div class="score-badge">{coverage}%</div>
        <p style="margin: 0; opacity: 0.9;">Modulos Cubiertos</p>
    </div>
    """, unsafe_allow_html=True)
    if 'coveredModules' in analysis['coverage'] and 'totalModules' in analysis['coverage']:
        st.caption(f"{analysis['coverage']['coveredModules']}/{analysis['coverage']['totalModules']} modulos")

with col4:
    score = analysis['scores']['overall']
    card_class = "success-card" if score >= 8 else "warning-card" if score >= 6 else "danger-card"
    st.markdown(f"""
    <div class="metric-card {card_class}">
        <h3>Score</h3>
        <div class="score-badge">{score}/10</div>
        <p style="margin: 0; opacity: 0.9;">Calidad General</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Distribution charts
st.subheader(":chart_with_upwards_trend: Distribucion de Tests")

col1, col2 = st.columns(2)

with col1:
    if 'byType' in analysis.get('distribution', {}):
        test_types = {k: v for k, v in analysis['distribution']['byType'].items() if v > 0}
        if test_types:
            df_types = pd.DataFrame(list(test_types.items()), columns=['Module', 'Tests'])
            fig_pie = px.pie(
                df_types, values='Tests', names='Module',
                title="Tests por Modulo",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig_pie.update_traces(textposition='inside', textinfo='percent+label+value')
            st.plotly_chart(fig_pie, use_container_width=True)

with col2:
    if 'byType' in analysis.get('distribution', {}):
        all_types = analysis['distribution']['byType']
        df_all = pd.DataFrame(list(all_types.items()), columns=['Type', 'Count'])
        df_all = df_all.sort_values('Count', ascending=True)

        fig_bar = px.bar(
            df_all, x='Count', y='Type', orientation='h',
            title="Inventario Completo de Tests",
            text='Count'
        )
        st.plotly_chart(fig_bar, use_container_width=True)

# Quality scores
if 'scores' in analysis and len(analysis['scores']) > 1:
    st.markdown("---")
    st.subheader(":dart: Scores de Calidad")

    scores_data = {k: v for k, v in analysis['scores'].items() if k != 'overall'}
    if scores_data:
        df_scores = pd.DataFrame(list(scores_data.items()), columns=['Category', 'Score'])
        colors = ['#2ecc71' if s >= 8 else '#f39c12' if s >= 6 else '#e74c3c' for s in df_scores['Score']]

        fig_scores = go.Figure(data=[
            go.Bar(x=df_scores['Category'], y=df_scores['Score'],
                   marker=dict(color=colors), text=df_scores['Score'], textposition='auto')
        ])
        fig_scores.update_layout(
            title="Puntuacion por Categoria",
            yaxis_title="Score (0-10)",
            yaxis=dict(range=[0, 10]),
            showlegend=False
        )
        st.plotly_chart(fig_scores, use_container_width=True)

# Issues
if 'issues' in analysis and analysis['issues']:
    st.markdown("---")
    st.subheader("Problemas Identificados")

    high_issues = [i for i in analysis['issues'] if i['severity'] == 'high']
    medium_issues = [i for i in analysis['issues'] if i['severity'] == 'medium']

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Alta Prioridad", len(high_issues))
    with col2:
        st.metric("Media Prioridad", len(medium_issues))

    for issue in high_issues:
        with st.expander(f"**{issue['category']}**: {issue['description']}"):
            st.warning(f"**Impacto:** {issue['impact']}")

    for issue in medium_issues:
        with st.expander(f"**{issue['category']}**: {issue['description']}"):
            st.info(f"**Impacto:** {issue['impact']}")

# Recommendations
if 'recommendations' in analysis and analysis['recommendations']:
    st.markdown("---")
    st.subheader("Recomendaciones de Mejora")

    for rec in analysis['recommendations']:
        priority_color = {'high': '#e74c3c', 'medium': '#f39c12', 'low': '#3498db'}.get(rec['priority'], '#666')
        st.markdown(f"""
        <div style="border-left: 4px solid {priority_color}; padding: 0.8rem; margin: 0.5rem 0; border-radius: 4px; background: #f8f9fa;">
            <strong>{rec['title']}</strong><br/>
            <span style="color: #555;">{rec['description']}</span><br/>
            <small style="color: #888;">Esfuerzo: {rec['estimatedEffort']}</small>
        </div>
        """, unsafe_allow_html=True)

# Configuration
if 'configuration' in analysis:
    st.markdown("---")
    st.subheader("Configuracion del Proyecto")

    col1, col2 = st.columns(2)
    with col1:
        st.info(f"Framework: {analysis['configuration'].get('framework', 'N/A')}")
        if 'browsers' in analysis['configuration']:
            st.success(f"Navegadores: {', '.join(analysis['configuration']['browsers'])}")
    with col2:
        if 'projectNames' in analysis['configuration']:
            for project in analysis['configuration']['projectNames'][:8]:
                st.text(f"  {project}")

# Last run stats
if 'lastRun' in analysis and analysis['lastRun'].get('total', 0) > 0:
    st.markdown("---")
    st.subheader("Ultima Ejecucion (analisis)")

    last_run = analysis['lastRun']
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total", last_run['total'])
    with col2:
        st.metric("Passed", last_run['passed'])
    with col3:
        st.metric("Failed", last_run['failed'])
    with col4:
        st.metric("Tiempo", f"{last_run['executionTime']:.1f}s")
