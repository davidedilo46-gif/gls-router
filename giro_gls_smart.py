import streamlit as st
from fpdf import FPDF
import urllib.parse
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import folium
from streamlit_folium import st_folium
import time
import re

# --- CONFIGURAZIONE ---
COORDS_SEDE = (45.5147, 10.2285) 
geolocator = Nominatim(user_agent="gls_brescia_smart_v21")

st.set_page_config(page_title="GLS Flex Router", layout="wide")

if 'pacchi' not in st.session_state: st.session_state.pacchi = []
if 'comuni_oggi' not in st.session_state: st.session_state.comuni_oggi = []

def clean_text(text):
    return str(text).encode('latin-1', 'replace').decode('latin-1')

# --- STILE ---
st.markdown("""
    <style>
    .stApp {
        background-image: linear-gradient(rgba(0, 46, 110, 0.7), rgba(255, 255, 255, 0.5)), 
                          url("https://www.gls-italy.com/images/belluno_sedegls_m16.jpg");
        background-size: cover; background-attachment: fixed;
    }
    .main-box { background-color: rgba(255, 255, 255, 0.95); padding: 20px; border-radius: 20px; border: 2px solid #002e6e; }
    </style>
    """, unsafe_allow_html=True)

st.title("📦 GLS Flex Mode - Brescia")

# --- 1. SIDEBAR ---
with st.sidebar:
    st.header("⚙️ SETUP")
    input_c = st.text_input("Comuni di oggi (es: Poncarale, Montirone):")
    if st.button("SALVA"):
        lista = [c.strip().upper() for c in input_c.split(",")]
        centri = []
        for c in lista:
            loc = geolocator.geocode(f"{c}, BS, Italy", timeout=10)
            if loc: centri.append({"nome": c, "coords": (loc.latitude, loc.longitude)})
        st.session_state.comuni_oggi = centri
        st.rerun()

# --- 2. MAPPA ---
st.subheader("🗺️ Mappa Itinerario")
m = folium.Map(location=COORDS_SEDE, zoom_start=12)
folium.Marker(COORDS_SEDE, tooltip="SEDE", icon=folium.Icon(color='black')).add_to(m)

for i, p in enumerate(st.session_state.pacchi):
    if p['coords']:
        color = '#28a745' if p['Tipo'] == 'A' else '#dc3545'
        folium.Marker(
            location=p['coords'],
            icon=folium.DivIcon(html=f'''<div style="font-family:Arial; color:white; background:{color}; border-radius:50%; width:30px; height:30px; display:flex; align-items:center; justify-content:center; font-weight:bold; border:2px solid white; box-shadow: 2px 2px 5px rgba(0,0,0,0.3);">{i+1}</div>''')
        ).add_to(m)

st_folium(m, width=1200, height=400, key="map_v21")

# --- 3. INPUT ---
col_in, col_mod = st.columns(2)

with col_in:
    st.markdown('<div class="main-box">', unsafe_allow_html=True)
    via_raw = st.text_input("📍 Indirizzo (Via e Civico):", placeholder="Es: Via Milano 10").upper()
    comune = st.selectbox("🏙️ Comune:", [x['nome'] for x in st.session_state.comuni_oggi] if st.session_state.comuni_oggi else ["Configura comuni..."])
    
    def add_pacco(tipo):
        if via_raw and comune != "Configura comuni...":
            # Pulizia per il GPS: togliamo nomi Srl, Spa o parole lunghe
            via_gps = via_raw.replace("SRL", "").replace("SPA", "").replace("SAS", "").strip()
            query = f"{via_gps}, {comune}, BS, Italy"
            
            try:
                loc = geolocator.geocode(query, timeout=10)
                if loc:
                    st.session_state.pacchi.append({"Via": via_raw, "Comune": comune, "Tipo": tipo, "coords": (loc.latitude, loc.longitude)})
                    st.toast(f"Trovato: {via_gps}")
                else:
                    st.error(f"❌ GPS non trova: '{via_gps}'. Controlla la via!")
                    # Lo mettiamo in lista comunque per il conteggio palmare
                    st.session_state.pacchi.append({"Via": via_raw, "Comune": comune, "Tipo": tipo, "coords": None})
                st.rerun()
            except:
                st.error("Errore di connessione. Riprova.")

    c1, c2 = st.columns(2)
    if c1.button("🟢 + AZIENDA"): add_pacco("A")
    if c2.button("🔴 + PRIVATO"): add_pacco("P")
    st.markdown('</div>', unsafe_allow_html=True)

with col_mod:
    if st.session_state.pacchi:
        st.markdown('<div class="main-box">', unsafe_allow_html=True)
        st.write(f"📦 Pacchi in lista: {len(st.session_state.pacchi)}")
        if st.button("🗑️ CANCELLA ULTIMO"):
            st.session_state.pacchi.pop()
            st.rerun()
        if st.button("🧹 SVUOTA TUTTO"):
            st.session_state.pacchi = []
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# --- 4. PDF ---
if st.session_state.pacchi:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(190, 10, clean_text("GIRO GLS OTTIMIZZATO"), ln=True, align='C')
    for i, p in enumerate(st.session_state.pacchi):
        pdf.set_fill_color(240, 240, 240) if p['Tipo'] == "A" else pdf.set_fill_color(255, 255, 255)
        pdf.cell(15, 10, str(i+1), 1, 0, 'C', True)
        pdf.cell(175, 10, clean_text(f"{p['Via']} - {p['Comune']}"), 1, 1, 'L', True)
    
    pdf_b = pdf.output(dest='S').encode('latin-1', 'replace')
    st.download_button("📥 SCARICA PDF", pdf_b, "Giro.pdf")
