import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import os
from datetime import datetime
from pathlib import Path
from parsers import get_all_test_results, calculate_metrics, load_environment_results

# Configure Streamlit page
st.set_page_config(
    page_title="QA Dashboard - Dropea",
    page_icon=":rocket:",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .success-metric { border-left-color: #2ca02c; }
    .warning-metric { border-left-color: #ff7f0e; }
    .error-metric { border-left-color: #d62728; }
</style>
""", unsafe_allow_html=True)

# Main title
st.title(":rocket: QA Automation Dashboard - Dropea")
st.markdown("---")

# Sidebar
st.sidebar.header(":wrench: Configuracion")

if st.sidebar.button(":arrows_counterclockwise: Actualizar Datos"):
    st.cache_data.clear()
    st.rerun()

# Load test results
DATA_DIR = Path(__file__).parent / "data"

@st.cache_data(ttl=60)
def load_data():
    return get_all_test_results(str(DATA_DIR))

@st.cache_data(ttl=60)
def load_test_results_json():
    path = DATA_DIR / "test-results.json"
    if path.exists():
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

@st.cache_data(ttl=60)
def load_env_results():
    return load_environment_results(str(DATA_DIR))

df = load_data()
test_results = load_test_results_json()
env_results = load_env_results()

if df.empty and test_results is None and not env_results:
    st.warning("No se encontraron resultados de tests.")
    st.info("""
    Archivos esperados en `data/`:
    - `test-results.json` (Playwright JSON)
    - `test-results-qa.json` / `test-results-dev.json` (por ambiente)
    """)
    st.stop()

# Environment comparison section
if env_results and len(env_results) > 1:
    st.subheader(":earth_americas: Comparacion por Ambiente")

    env_cols = st.columns(len(env_results))
    for i, (env_name, data) in enumerate(sorted(env_results.items())):
        summary = data.get('summary', {})
        total = summary.get('total', 0)
        passed = summary.get('passed', 0)
        failed = summary.get('failed', 0)
        skipped = summary.get('skipped', 0)
        duration_s = summary.get('duration', 0) / 1000
        pass_rate = (passed / max(total, 1)) * 100

        with env_cols[i]:
            st.markdown(f"#### {env_name}")
            st.metric("Total", total)
            st.metric("Passed", passed, delta=f"{pass_rate:.0f}%")
            st.metric("Failed", failed, delta_color="inverse" if failed > 0 else "off")
            st.metric("Skipped", skipped)
            st.metric("Duracion", f"{duration_s:.0f}s")
            if 'startTime' in summary:
                st.caption(f"Run: {summary['startTime'][:16]}")

    st.markdown("---")

# Sidebar filters
st.sidebar.subheader(":bar_chart: Filtros")

# Environment selector
if env_results:
    env_options = ['Ultima ejecucion'] + sorted(env_results.keys())
    selected_env = st.sidebar.selectbox("Ambiente", env_options)
    if selected_env != 'Ultima ejecucion' and selected_env in env_results:
        test_results = env_results[selected_env]
else:
    selected_env = 'Ultima ejecucion'

available_suites = ['Todos'] + list(df['suite'].unique())
selected_suite = st.sidebar.selectbox("Suite de Tests", available_suites)

available_statuses = ['Todos'] + list(df['status'].unique())
selected_status = st.sidebar.selectbox("Estado", available_statuses)

if 'browser' in df.columns:
    available_browsers = ['Todos'] + list(df['browser'].unique())
    selected_browser = st.sidebar.selectbox("Navegador/Tipo", available_browsers)
else:
    selected_browser = 'Todos'

# Apply filters
filtered_df = df.copy()
if selected_suite != 'Todos':
    filtered_df = filtered_df[filtered_df['suite'] == selected_suite]
if selected_status != 'Todos':
    filtered_df = filtered_df[filtered_df['status'] == selected_status]
if selected_browser != 'Todos' and 'browser' in filtered_df.columns:
    filtered_df = filtered_df[filtered_df['browser'] == selected_browser]

# Calculate metrics
metrics = calculate_metrics(filtered_df)

# Display summary from test-results.json if available
if test_results:
    summary = test_results['summary']
    st.subheader(":chart_with_upwards_trend: Ultima Ejecucion")

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("Total Tests", summary['total'])
    with col2:
        st.metric("Passed", summary['passed'],
                  delta=f"{(summary['passed']/max(summary['total'],1)*100):.0f}%")
    with col3:
        st.metric("Failed", summary['failed'],
                  delta_color="inverse" if summary['failed'] > 0 else "off")
    with col4:
        st.metric("Skipped", summary['skipped'])
    with col5:
        duration_sec = summary['duration'] / 1000
        st.metric("Duracion", f"{duration_sec:.0f}s")

    st.markdown("---")

# Key metrics
st.subheader(":bar_chart: Metricas por Filtro")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total de Tests", metrics['total_tests'])
with col2:
    st.metric("Tests Exitosos", metrics['passed'],
              delta=f"{metrics['pass_rate']}% tasa de exito")
with col3:
    st.metric("Tests Fallidos", metrics['failed'])
with col4:
    st.metric("Tiempo Promedio", f"{metrics['avg_execution_time']}s")

# Charts
st.markdown("---")
st.subheader(":bar_chart: Analisis Visual")

col1, col2 = st.columns(2)

with col1:
    if not filtered_df.empty:
        status_counts = filtered_df['status'].value_counts()
        fig_pie = px.pie(
            values=status_counts.values,
            names=status_counts.index,
            title="Distribucion por Estado",
            color_discrete_map={
                'Passed': '#2ca02c',
                'Failed': '#d62728',
                'Skipped': '#ff7f0e',
                'Error': '#8B0000'
            }
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)

with col2:
    if not filtered_df.empty:
        module_status = filtered_df.groupby(['module', 'status']).size().reset_index(name='count')
        fig_bar = px.bar(
            module_status,
            x='module',
            y='count',
            color='status',
            title="Tests por Modulo",
            color_discrete_map={
                'Passed': '#2ca02c',
                'Failed': '#d62728',
                'Skipped': '#ff7f0e',
                'Error': '#8B0000'
            }
        )
        fig_bar.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_bar, use_container_width=True)

# Execution time analysis
if not filtered_df.empty and 'time' in filtered_df.columns:
    st.subheader(":stopwatch: Analisis de Tiempos de Ejecucion")

    col1, col2 = st.columns(2)

    with col1:
        fig_time = px.histogram(
            filtered_df,
            x='time',
            nbins=20,
            title="Distribucion de Tiempos de Ejecucion",
            labels={'time': 'Tiempo (segundos)', 'count': 'Numero de Tests'}
        )
        st.plotly_chart(fig_time, use_container_width=True)

    with col2:
        if len(filtered_df['module'].unique()) > 1:
            avg_time = filtered_df.groupby('module')['time'].mean().reset_index()
            avg_time = avg_time.sort_values('time', ascending=False).head(10)
            fig_avg = px.bar(
                avg_time,
                x='module',
                y='time',
                title="Tiempo Promedio por Modulo (Top 10)",
                labels={'time': 'Tiempo Promedio (s)'}
            )
            fig_avg.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_avg, use_container_width=True)

# Detailed results table
st.markdown("---")
st.subheader(":clipboard: Resultados Detallados")

if not filtered_df.empty:
    failed_tests = filtered_df[filtered_df['status'] == 'Failed']
    if not failed_tests.empty:
        with st.expander(f"Tests Fallidos ({len(failed_tests)})"):
            st.dataframe(
                failed_tests[['name', 'module', 'suite', 'time']],
                use_container_width=True
            )

    skipped_tests = filtered_df[filtered_df['status'] == 'Skipped']
    if not skipped_tests.empty:
        with st.expander(f"Tests Skipped ({len(skipped_tests)})"):
            st.dataframe(
                skipped_tests[['name', 'module', 'suite', 'time']],
                use_container_width=True
            )

    st.dataframe(
        filtered_df[['name', 'module', 'suite', 'status', 'time']],
        use_container_width=True,
        hide_index=True
    )

# Export
st.markdown("---")
if not filtered_df.empty:
    csv = filtered_df.to_csv(index=False)
    st.download_button(
        label=":floppy_disk: Descargar CSV",
        data=csv,
        file_name=f"qa_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )

# Footer
st.markdown("---")
st.markdown(
    f"""
    <div style='text-align: center; color: #666; font-size: 0.8em;'>
        QA Automation Dashboard - Dropea | Ultima actualizacion: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    </div>
    """,
    unsafe_allow_html=True
)
