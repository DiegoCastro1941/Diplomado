import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from streamlit_folium import st_folium

def show_map_tab():
    st.header("🗺️ Mapa Interactivo por Departamento")

    if 'df_fact' not in st.session_state:
        st.warning("Primero debes construir la tabla de hechos en la pestaña 'Transformación y Métricas'.")
        return

    df_fact = st.session_state['df_fact']
    dim_geo = st.session_state['dim_geo']
    dim_tiempo = st.session_state['dim_tiempo']

    # Merge de tabla de hechos con dimensiones
    df = df_fact.merge(dim_geo, on='id_geo').merge(dim_tiempo, on='id_tiempo')

    # Selector de métrica
    metricas = {
        'Cobertura Neta (%)': 'cobertura_neta',
        'Cobertura Bruta (%)': 'cobertura_bruta',
        'Tasa de Matriculación 5-16 (%)': 'tasa_matriculaci_n_5_16'
    }

    metrica_label = st.selectbox("Selecciona la métrica", list(metricas.keys()))
    metrica_col = metricas[metrica_label]

    # Selector de año
    años = sorted(df['a_o'].unique())
    año_sel = st.selectbox("Selecciona el año", años, index=len(años)-1)

    # Agrupación por código de departamento
    df_filtrado = df[df['a_o'] == año_sel]
    resumen = (
        df_filtrado
        .groupby('c_digo_departamento')[metrica_col]
        .mean()
        .reset_index()
        .rename(columns={'c_digo_departamento': 'codigo_departamento'})
    )
    resumen['codigo_departamento'] = resumen['codigo_departamento'].astype(str)

    # ===============================
    # Leer archivo SHP local de departamentos
    # ===============================
    try:
        gdf = gpd.read_file("data/shapes/MGN_ANM_DPTOS.shp")  # Ajusta la ruta si es necesario
    except Exception as e:
        st.error(f"❌ Error al leer el archivo .shp: {e}")
        return

    # Verificar campo de código del departamento
    codigo_col = "DPTO_CCDGO"

    gdf[codigo_col] = gdf[codigo_col].astype(str)
    resumen[codigo_col] = resumen["codigo_departamento"]

    # Merge de shapefile con datos
    gdf_merged = gdf.merge(resumen, on=codigo_col, how="left")

    # ===============================
    # Crear el mapa
    # ===============================
    m = folium.Map(location=[4.6, -74.1], zoom_start=5, tiles="CartoDB positron")

    folium.Choropleth(
        geo_data=gdf_merged,
        name="choropleth",
        data=gdf_merged,
        columns=[codigo_col, metrica_col],
        key_on=f"feature.properties.{codigo_col}",
        fill_color="YlGnBu",
        fill_opacity=0.7,
        line_opacity=0.2,
        nan_fill_color="gray",
        legend_name=f"{metrica_label} - {año_sel}",
        highlight=True
    ).add_to(m)

    folium.LayerControl().add_to(m)

    st.subheader(f"🧭 {metrica_label} por Departamento - {año_sel}")
    st_folium(m, width=750, height=550)
