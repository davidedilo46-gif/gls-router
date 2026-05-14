import streamlit as st
from fpdf import FPDF
import urllib.parse
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import pandas as pd
import folium
from streamlit_folium import st_folium
import io

# --- CONFIGURAZIONE ---
COORDS_SEDE = (45.5147, 10.2285) 
geolocator = Nominatim(user_agent="gls_flex_final_v19")

st.set_page_config(page_title="GLS Flex Router", layout="wide")

if 'pacchi' not in st.session_state: st.session_state.pacchi = []
if 'comuni_oggi' not in st.session_state: st.session_state.comuni_oggi = []

# --- FUNZIONE PULIZIA TESTO ---
def clean_text(text):
    return str(text).encode('latin-1', 'replace').decode('latin-1')

# --- STILE CSS ---
st.markdown("""
    <style>
    .stApp {
        background-image: linear-gradient(rgba(0, 46, 110, 0.7), rgba(255, 255, 255, 0.5)), 
                          url("https://www.gls-italy.com/images/belluno_sedegls_m16.jpg");
        background-size: cover; background-attachment: fixed;
    }
    .main-box { background-color: rgba(255, 255, 255, 0.95); padding: 20px; border-radius: 20px; border: 2px solid #002e6e; margin-bottom: 20px; }
    .stButton>button { width: 100%; border-radius: 12px; font-weight: bold; height: 3em; }
    </style>
    """, unsafe_allow_html=True)

st.title("📦 GLS Flex Mode - Brescia")

# --- 1. SIDEBAR ---
with st.sidebar:
    st.header("⚙️ CONFIGURA")
    input_c = st.text_input("Comuni di oggi (es: Poncarale, Montirone):")
    if st.button("SALVA GIRO"):
        lista = [c.strip().upper() for c in input_c.split(",")]
        centri = []
        for c in lista:
            loc = geolocator.geocode(f"{c}, Brescia, Italy")
            if loc: centri.append({"nome": c, "dist": geodesic(COORDS_SEDE, (loc.latitude, loc.longitude)).km})
        st.session_state.comuni_oggi = sorted(centri, key=lambda x: x['dist'])
        st.success("Configurato!")

# --- 2. MAPPA (DINAMICA) ---
if st.session_state.pacchi:
    st.subheader("🗺️ Mappa Itinerario Numerato")
    m = folium.Map(location=COORDS_SEDE, zoom_start=12)
    folium.Marker(COORDS_SEDE, tooltip="SEDE GLS", icon=folium.Icon(color='black', icon='info-sign')).add_to(m)
    
    path = [COORDS_SEDE]
    for i, p in enumerate(st.session_state.pacchi):
        if p['coords']:
            color = '#28a745' if p['Tipo'] == 'A' else '#dc3545'
            folium.Marker(
                location=p['coords'],
                icon=folium.DivIcon(html=f'''
                    <div style="font-family:Arial; color:white; background:{color}; 
                    border-radius:50%; width:30px; height:30px; display:flex; 
                    align-items:center; justify-content:center; font-weight:bold; 
                    border:2px solid white; box-shadow: 2px 2px 5px rgba(0,0,0,0.3);">
                    {i+1}
                    </div>''')
            ).add_to(m)
            path.append(p['coords'])
    
    if len(path) > 1:
        folium.PolyLine(path, color="#002e6e", weight=2, opacity=0.7).add_to(m)
    
    st_folium(m, width=1200, height=450, key="map_flex")

# --- 3. INPUT E COMANDI ---
col_in, col_mod = st.columns(2)

with col_in:
    st.markdown('<div class="main-box">', unsafe_allow_html=True)
    st.subheader("➕ Aggiungi Stop")
    via = st.text_input("Via e Civico:", key="via_input").upper()
    comune = st.selectbox("Comune:", [x['nome'] for x in st.session_state.comuni_oggi] if st.session_state.comuni_oggi else ["Configura paesi..."])
    
    c1, c2 = st.columns(2)
    if c1.button("🟢 AZIENDA"):
        if via:
            loc = geolocator.geocode(f"{via}, {comune}, BS, Italy")
            st.session_state.pacchi.append({"Via": via, "Comune": comune, "Tipo": "A", "coords": (loc.latitude, loc.longitude) if loc else None})
            st.rerun()
    if c2.button("🔴 PRIVATO"):
        if via:
            loc = geolocator.geocode(f"{via}, {comune}, BS, Italy")
            st.session_state.pacchi.append({"Via": via, "Comune": comune, "Tipo": "P", "coords": (loc.latitude, loc.longitude) if loc else None})
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

with col_mod:
    if st.session_state.pacchi:
        st.markdown('<div class="main-box">', unsafe_allow_html=True)
        st.subheader("🔄 Modifica Ordine")
        idx = st.number_input("Sposta stop numero:", 1, len(st.session_state.pacchi)) - 1
        new_pos = st.number_input("Alla posizione:", 1, len(st.session_state.pacchi)) - 1
        if st.button("SPOSTA ORA"):
            p = st.session_state.pacchi.pop(idx)
            st.session_state.pacchi.insert(new_pos, p)
            st.rerun()
        if st.button("🗑️ CANCELLA TUTTO"):
            st.session_state.pacchi = []
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# --- 4. GENERAZIONE PDF (FIXED) ---
if st.session_state.pacchi:
    st.write("---")
    if st.button("📝 GENERA PDF DEFINITIVO"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(190, 10, clean_text(f"GIRO GLS BRESCIA - {len(st.session_state.pacchi)} CONSEGNE"), ln=True, align='C')
        pdf.ln(10)
        
        for i, p in enumerate(st.session_state.pacchi):
            pdf.set_fill_color(240, 240, 240) if p['Tipo'] == "A" else pdf.set_fill_color(255, 255, 255)
            pdf.set_font("Arial", 'B', 11)
            pdf.cell(15, 10, str(i+1), 1, 0, 'C', True)
            pdf.set_font("Arial", size=10)
            tipo = "AZIENDA" if p['Tipo'] == 'A' else "PRIVATO"
            testo = f" {tipo}: {p['Via']} - {p['Comune']}"
            pdf.cell(175, 10, clean_text(testo), 1, 1, 'L', True)
        
        # FIX: Generazione corretta del buffer di byte per Streamlit
        pdf_output = pdf.output(dest='S').encode('latin-1', 'replace')
        
        st.download_button(
            label="📥 CLICCA QUI PER SCARICARE IL PDF", 
            data=pdf_output, 
            file_name="Giro_GLS_Brescia.pdf", 
            mime="application/pdf"
        )-
