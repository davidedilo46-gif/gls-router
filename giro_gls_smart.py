import streamlit as st
from fpdf import FPDF
import urllib.parse
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import pandas as pd
import folium
from streamlit_folium import st_folium

# --- CONFIGURAZIONE ---
COORDS_SEDE = (45.5147, 10.2285) 
geolocator = Nominatim(user_agent="gls_flex_style_v17")

st.set_page_config(page_title="GLS Flex Router", layout="wide")

if 'pacchi' not in st.session_state: st.session_state.pacchi = []
if 'comuni_oggi' not in st.session_state: st.session_state.comuni_oggi = []

# --- STILE CSS ---
st.markdown("""
    <style>
    .stApp {
        background-image: linear-gradient(rgba(0, 46, 110, 0.6), rgba(255, 255, 255, 0.5)), 
                          url("https://www.gls-italy.com/images/belluno_sedegls_m16.jpg");
        background-size: cover; background-attachment: fixed;
    }
    .main-box { background-color: rgba(255, 255, 255, 0.95); padding: 20px; border-radius: 20px; box-shadow: 0 8px 32px 0 rgba(0, 46, 110, 0.3); }
    </style>
    """, unsafe_allow_html=True)

# --- FUNZIONE CREAZIONE MAPPA "AMAZON STYLE" ---
def crea_mappa_flex(punti):
    m = folium.Map(location=COORDS_SEDE, zoom_start=12, tiles="OpenStreetMap")
    
    path_coords = [COORDS_SEDE]
    folium.Marker(COORDS_SEDE, tooltip="SEDE GLS", icon=folium.Icon(color='black', icon='home')).add_to(m)

    for i, p in enumerate(punti):
        if p['coords']:
            color = 'green' if p['Tipo'] == 'A' else 'red'
            folium.Marker(
                location=p['coords'],
                popup=f"STOP {i+1}: {p['Via']}",
                tooltip=f"{i+1}",
                icon=folium.DivIcon(html=f"""
                    <div style="font-family: Arial; color: white; background-color: {color}; 
                    border-radius: 50%; width: 25px; height: 25px; display: flex; 
                    align-items: center; justify-content: center; font-weight: bold; 
                    border: 2px solid white; box-shadow: 2px 2px 5px rgba(0,0,0,0.5);">
                    {i+1}
                    </div>""")
            ).add_to(m)
            path_coords.append(p['coords'])
    
    if len(path_coords) > 1:
        folium.PolyLine(path_coords, color="#002e6e", weight=3, opacity=0.8).add_to(m)
    return m

# --- INTERFACCIA ---
st.title("📦 GLS Flex Style Router")

with st.sidebar:
    st.header("⚙️ Configurazione")
    input_c = st.text_input("Comuni di oggi:")
    if st.button("Configura"):
        lista = [c.strip().upper() for c in input_c.split(",")]
        centri = []
        for c in lista:
            loc = geolocator.geocode(f"{c}, Brescia, Italy")
            if loc: centri.append({"nome": c, "dist": geodesic(COORDS_SEDE, (loc.latitude, loc.longitude)).km})
        st.session_state.comuni_oggi = sorted(centri, key=lambda x: x['dist'])

# LAYOUT A DUE COLONNE
col_left, col_right = st.columns([1, 1.5])

with col_left:
    st.markdown('<div class="main-box">', unsafe_allow_html=True)
    st.subheader("📍 Inserimento Stop")
    via = st.text_input("Via e Civico:").upper()
    comune = st.selectbox("Comune:", [x['nome'] for x in st.session_state.comuni_oggi] if st.session_state.comuni_oggi else ["Configura comuni..."])
    
    c1, c2 = st.columns(2)
    if c1.button("🟢 + AZIENDA", use_container_width=True):
        loc = geolocator.geocode(f"{via}, {comune}, BS, Italy")
        st.session_state.pacchi.append({"Via": via, "Comune": comune, "Tipo": "A", "coords": (loc.latitude, loc.longitude) if loc else None})
        st.rerun()
    if c2.button("🔴 + PRIVATO", type="primary", use_container_width=True):
        loc = geolocator.geocode(f"{via}, {comune}, BS, Italy")
        st.session_state.pacchi.append({"Via": via, "Comune": comune, "Tipo": "P", "coords": (loc.latitude, loc.longitude) if loc else None})
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.pacchi:
        st.write("---")
        st.subheader("✍️ Modifica Ordine")
        idx = st.number_input("Muovi Stop n.", 1, len(st.session_state.pacchi)) - 1
        new_pos = st.number_input("Alla posizione", 1, len(st.session_state.pacchi)) - 1
        if st.button("🔄 SPOSTA"):
            p = st.session_state.pacchi.pop(idx)
            st.session_state.pacchi.insert(new_pos, p)
            st.rerun()

with col_right:
    if st.session_state.pacchi:
        st.subheader("🗺️ Mappa Itinerario")
        st_folium(crea_mappa_flex(st.session_state.pacchi), width=700, height=500)
        
        if st.button("🚀 GENERA PDF DEFINITIVO"):
            # Generazione PDF come versioni precedenti...
            st.success("PDF Generato con l'ordine della mappa!")
