import streamlit as st
import pandas as pd
import requests

# ===================================================================
# Función: load_data_from_api
# ===================================================================
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
        # Muestra un mensaje de error en la interfaz de Streamlit si hay un problema de conexión
        st.error(f"Error de conexión: {e}")
    except Exception as e:
        # Muestra un mensaje en caso de errores inesperados
        st.error(f"Error inesperado: {e}")
    # Retorna un DataFrame vacío en caso de error
    return pd.DataFrame()

# ===================================================================
# Función: show_data_tab
# ===================================================================
def show_data_tab():
    """
    Muestra la interfaz de la pestaña para cargar datos desde la API.
    Incluye instrucciones y un botón para iniciar la carga.
    """
    st.header("📥 Carga de Datos del MEN vía API")  # Encabezado de la sección

    # Descripción del origen de los datos y instrucciones
    st.markdown("""
    Este conjunto de datos proviene del portal [datos.gov.co](https://www.datos.gov.co/Educaci-n/MEN_ESTADISTICAS_EN_EDUCACION_EN_PREESCOLAR-B-SICA/nudc-7mev).
    
    Presiona el botón para cargar los datos directamente desde la API.
    """)

    # Botón para cargar los datos
    if st.button("🔄 Cargar datos"):
        with st.spinner("Cargando datos desde la API..."):
            df_raw = load_data_from_api()

        # Verifica si se cargaron datos correctamente
        if not df_raw.empty:
            # Guardar el dataframe en sesión para usarlo en otras pestañas
            st.session_state['df_raw'] = df_raw
            
            st.success(f"¡Datos cargados exitosamente! ({len(df_raw)} filas)")
            st.dataframe(df_raw.head(10))
        else:
            st.warning("No se encontraron datos o hubo un error en la carga.")
    else:
        # Mensaje informativo si aún no se ha presionado el botón
        st.info("Presiona el botón para iniciar la carga.")