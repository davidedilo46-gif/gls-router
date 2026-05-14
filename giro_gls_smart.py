import streamlit as st
from fpdf import FPDF
import urllib.parse
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import folium
from streamlit_folium import st_folium
import time
import random

# --- CONFIGURAZIONE ---
COORDS_SEDE = (45.5147, 10.2285) 
geolocator = Nominatim(user_agent="gls_brescia_precision_v22")

st.set_page_config(page_title="GLS Flex Router Pro", layout="wide")

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

st.title("📦 GLS Flex Mode - Precisione Civici")

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

# --- 2. MAPPA CON SEPARAZIONE PUNTI VICINI ---
st.subheader("🗺️ Itinerario (I punti sovrapposti vengono separati automaticamente)")

# Troviamo un centro mappa
m_lat, m_lon = COORDS_SEDE
if st.session_state.pacchi:
    validi = [p['coords'] for p in st.session_state.pacchi if p['coords']]
    if validi:
        m_lat = sum(c[0] for c in validi) / len(validi)
        m_lon = sum(c[1] for c in validi) / len(validi)

m = folium.Map(location=[m_lat, m_lon], zoom_start=14)
folium.Marker(COORDS_SEDE, tooltip="SEDE", icon=folium.Icon(color='black')).add_to(m)

# Logica per evitare sovrapposizioni (Jittering)
punti_visti = {}

for i, p in enumerate(st.session_state.pacchi):
    if p['coords']:
        pos = list(p['coords'])
        pos_key = f"{pos[0]:.5f}_{pos[1]:.5f}"
        
        # Se la coordinata è già stata usata, sposta leggermente il pallino
        if pos_key in punti_visti:
            punti_visti[pos_key] += 1
            # Spostamento di circa 5-10 metri
            pos[0] += (random.uniform(-0.0001, 0.0001)) 
            pos[1] += (random.uniform(-0.0001, 0.0001))
        else:
            punti_visti[pos_key] = 1

        color = '#28a745' if p['Tipo'] == 'A' else '#dc3545'
        folium.Marker(
            location=pos,
            popup=f"Stop {i+1}: {p['Via']}",
            icon=folium.DivIcon(html=f'''<div style="font-family:Arial; color:white; background:{color}; border-radius:50%; width:30px; height:30px; display:flex; align-items:center; justify-content:center; font-weight:bold; border:2px solid white; box-shadow: 2px 2px 5px rgba(0,0,0,0.3);">{i+1}</div>''')
        ).add_to(m)

st_folium(m, width=1200, height=450, key="map_v22")

# --- 3. INPUT ---
col_in, col_mod = st.columns(2)

with col_in:
    st.markdown('<div class="main-box">', unsafe_allow_html=True)
    via_raw = st.text_input("📍 Via e Civico:", placeholder="Es: Via Milano 1").upper()
    comune = st.selectbox("🏙️ Comune:", [x['nome'] for x in st.session_state.comuni_oggi] if st.session_state.comuni_oggi else ["Configura comuni..."])
    
    def add_pacco(tipo):
        if via_raw and comune != "Configura comuni...":
            # Pulizia specifica per migliorare la ricerca del civico
            via_clean = re.sub(r'[^a-zA-Z0-9 ]', '', via_raw)
            query = f"{via_clean}, {comune}, BS, Italy"
            
            try:
                loc = geolocator.geocode(query, timeout=10, addressdetails=True)
                if loc:
                    st.session_state.pacchi.append({"Via": via_raw, "Comune": comune, "Tipo": tipo, "coords": (loc.latitude, loc.longitude)})
                    st.toast(f"Trovato Stop {len(st.session_state.pacchi)}")
                else:
                    st.error(f"⚠️ GPS approssimativo per: '{via_raw}'.")
                    # Proviamo una ricerca meno specifica per non perdere il punto
                    loc_fallback = geolocator.geocode(f"{comune}, BS, Italy")
                    coords = (loc_fallback.latitude, loc_fallback.longitude) if loc_fallback else None
                    st.session_state.pacchi.append({"Via": via_raw, "Comune": comune, "Tipo": tipo, "coords": coords})
                st.rerun()
            except:
                st.error("Errore di connessione GPS.")

    import re
    c1, c2 = st.columns(2)
    if c1.button("🟢 + AZIENDA"): add_pacco("A")
    if c2.button("🔴 + PRIVATO"): add_pacco("P")
    st.markdown('</div>', unsafe_allow_html=True)

with col_mod:
    if st.session_state.pacchi:
        st.markdown('<div class="main-box">', unsafe_allow_html=True)
        st.write(f"📦 Totale Carico: {len(st.session_state.pacchi)}")
        idx = st.number_input("Sposta stop n.", 1, len(st.session_state.pacchi)) - 1
        new_pos = st.number_input("Al posto n.", 1, len(st.session_state.pacchi)) - 1
        if st.button("SPOSTA"):
            p = st.session_state.pacchi.pop(idx)
            st.session_state.pacchi.insert(new_pos, p)
            st.rerun()
        if st.button("🧹 SVUOTA GIRO"):
            st.session_state.pacchi = []
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# --- 4. PDF ---
if st.session_state.pacchi:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(190, 10, clean_text("ORDINE CONSEGNE GLS"), ln=True, align='C')
    for i, p in enumerate(st.session_state.pacchi):
        pdf.set_fill_color(240, 240, 240) if p['Tipo'] == "A" else pdf.set_fill_color(255, 255, 255)
        pdf.cell(15, 10, str(i+1), 1, 0, 'C', True)
        pdf.cell(175, 10, clean_text(f"{p['Via']} - {p['Comune']}"), 1, 1, 'L', True)
    
    pdf_b = pdf.output(dest='S').encode('latin-1', 'replace')
    st.download_button("📥 SCARICA PDF", pdf_b, "Giro.pdf")
