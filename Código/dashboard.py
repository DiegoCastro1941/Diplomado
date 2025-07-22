import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium
import requests
import io
import seaborn as sns
import matplotlib.pyplot as plt

# Cambiar colores y diseño
CUSTOM_BLUE = "#1E3A8A"
CUSTOM_YELLOW = "#FBBF24"
CUSTOM_GRAY = "#E5E7EB"
CUSTOM_WHITE = "#FFFFFF"

# Aplicando el estilo
st.markdown(f"""
    <style>
    .main {{
        background-color: {CUSTOM_GRAY};
    }}
    .stApp {{
        background-color: {CUSTOM_WHITE};
        color: #000000;
        font-family: 'Arial', sans-serif;
    }}
    .stButton>button {{
        background-color: {CUSTOM_YELLOW};
        color: black;
        font-weight: bold;
        border-radius: 8px;
        padding: 0.4em 0.8em;
    }}
    .stDownloadButton>button {{
        background-color: {CUSTOM_BLUE};
        color: white;
        font-weight: bold;
        border-radius: 8px;
        padding: 0.4em 0.8em;
    }}
    .stTabs [data-baseweb="tab"] {{
        font-weight: bold;
        background-color: {CUSTOM_WHITE};
        color: {CUSTOM_BLUE};
        border-radius: 6px 6px 0 0;
        border: 1px solid #CCC;
    }}
    </style>
""", unsafe_allow_html=True)

# Función para cargar datos desde la API
def load_data_from_api(limit: int = 50000) -> pd.DataFrame:
    """
    Carga datos desde la API de Socrata en formato JSON y los convierte en un DataFrame de pandas.
    
    Args:
        limit (int): Número máximo de registros a solicitar. Por defecto es 50,000.

    Returns:
        pd.DataFrame: DataFrame con los datos cargados. Si ocurre un error, devuelve un DataFrame vacío.
        
    Raises:
        requests.exceptions.RequestException: Si hay un problema de conexión o respuesta HTTP.
    """
    api_url = f"https://www.datos.gov.co/resource/nudc-7mev.json?$limit={limit}"
    try:
        response = requests.get(api_url)
        response.raise_for_status()  # Verifica si la respuesta fue exitosa
        data = response.json()
        df = pd.DataFrame(data)
        return df
    except requests.exceptions.RequestException as e:
        st.error(f"Error de conexión: {e}")
    except Exception as e:
        st.error(f"Error inesperado: {e}")
    return pd.DataFrame()

# Función para mostrar información sobre los datos
def show_data_summary(df):
    st.subheader("📊 Resumen Estadístico de los Datos")
    st.write(f"Total de registros: {len(df)}")
    st.write("### Estadísticas Descriptivas:")
    st.dataframe(df.describe())
    
    st.markdown("---")
    
    # Verificar si hay valores nulos
    missing_values = df.isnull().sum()
    st.write("### Valores Faltantes por Columna:")
    st.write(missing_values)

    st.markdown("---")

# Función principal para toda la lógica de la aplicación
def main():
    st.title("📊 Análisis Interactivo de Datos Educativos")

    # Paso 1: Subir los datos
    st.header("📥 Cargar Datos desde la API del MEN")
    if st.button("🔄 Cargar datos desde la API"):
        with st.spinner("Cargando datos desde la API..."):
            df = load_data_from_api()
            
        if not df.empty:
            st.success(f"Datos cargados exitosamente ({len(df)} filas)")
            st.dataframe(df.head())
            st.session_state['df'] = df  # Guardamos los datos en la sesión para uso posterior

            # Mostrar resumen de los datos
            show_data_summary(df)
        else:
            st.warning("No se encontraron datos o hubo un error en la carga.")

    # Paso 2: Limpieza y Transformación de Datos
    if 'df' in st.session_state:
        st.header("🔧 Limpieza y Transformación de Datos")

        df = st.session_state['df']

        # Transformación de columnas
        if 'a_o' in df.columns:
            df['Año'] = pd.to_datetime(df['a_o'], format='%Y')
        
        # Eliminar valores nulos y transformar columnas a valores numéricos
        df_clean = df.dropna()
        for col in df_clean.columns:
            if col not in ['departamento', 'municipio']:
                df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')

        st.success(f"Datos limpios: {len(df_clean)} registros")
        st.dataframe(df_clean.head())

        st.session_state['df_clean'] = df_clean  # Guardamos los datos transformados

        # Mostrar el resumen de los datos limpios
        show_data_summary(df_clean)

        # Filtros avanzados
        st.subheader("🔎 Filtros avanzados para explorar los datos")
        departamento_filter = st.selectbox("Selecciona un Departamento", df_clean['departamento'].unique())
        df_filtered = df_clean[df_clean['departamento'] == departamento_filter]
        st.dataframe(df_filtered)

    # Paso 3: Visualización de Datos
    if 'df_clean' in st.session_state:
        st.header("📈 Visualización de Datos")

        df_clean = st.session_state['df_clean']
        
        # Selección de métricas
        metrics = df_clean.columns.to_list()
        selected_metric = st.selectbox("Selecciona una métrica para visualizar", metrics)

        # Crear gráfico de la métrica seleccionada
        fig = px.line(df_clean, x='Año', y=selected_metric, title=f'Visualización de {selected_metric}')
        st.plotly_chart(fig)

        st.markdown("---")

        # Gráfico de barras para mostrar la comparación de departamentos
        st.subheader(f"📊 Comparativa de {selected_metric} por Departamento")
        deptos_avg = df_clean.groupby('departamento')[selected_metric].mean().sort_values(ascending=False).head(10)
        fig2 = px.bar(deptos_avg, x=deptos_avg.index, y=selected_metric, title=f"Top 10 Departamentos por {selected_metric}")
        st.plotly_chart(fig2)

        st.markdown("---")

        # Gráfico de dispersión para explorar relaciones entre métricas
        if 'departamento' in df_clean.columns:
            deptos = df_clean['departamento'].unique()
            selected_depto = st.selectbox("Selecciona un departamento para la visualización de dispersión", deptos)

            depto_df = df_clean[df_clean['departamento'] == selected_depto]
            scatter_fig = px.scatter(depto_df, x='Año', y=selected_metric, title=f"Dispersión de {selected_metric} en {selected_depto}")
            st.plotly_chart(scatter_fig)

        st.markdown("---")

        # Histogramas para mostrar la distribución de los datos
        st.subheader(f"📊 Histograma de {selected_metric}")
        fig3 = px.histogram(df_clean, x=selected_metric, nbins=30, title=f"Distribución de {selected_metric}")
        st.plotly_chart(fig3)

        # Boxplot para explorar la variabilidad de los datos
        st.subheader(f"📊 Boxplot de {selected_metric}")
        fig4 = px.box(df_clean, y=selected_metric, title=f"Rango y Distribución de {selected_metric}")
        st.plotly_chart(fig4)

    # Paso 4: Crear Mapa Interactivo
    if 'df_clean' in st.session_state:
        st.header("🗺️ Visualización en Mapa Interactivo")

        df_clean = st.session_state['df_clean']
        
        # Crear mapa
        map = folium.Map(location=[4.6, -74.1], zoom_start=5)
        
        # Agregar puntos de los municipios
        for _, row in df_clean.iterrows():
            folium.CircleMarker(
                location=[row['lat'], row['lon']],  # Asegúrate de que estas columnas existan
                radius=5,
                color='blue',
                fill=True,
                fill_color='blue'
            ).add_to(map)

        st_folium(map, width=750, height=500)

    # Paso 5: Descarga de Datos Procesados
    if 'df_clean' in st.session_state:
        st.header("📥 Descargar Datos Procesados")

        df_clean = st.session_state['df_clean']

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_clean.to_excel(writer, index=False, sheet_name='Datos Procesados')
        output.seek(0)

        st.download_button(
            label="📥 Descargar Datos Procesados",
            data=output,
            file_name='datos_procesados.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

# Ejecutar la función principal
if __name__ == "__main__":
    main()
