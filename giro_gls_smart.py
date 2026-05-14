import streamlit as st
from fpdf import FPDF
import urllib.parse
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import pandas as pd
import folium
from streamlit_folium import st_folium
import io
import time

# --- CONFIGURAZIONE ---
COORDS_SEDE = (45.5147, 10.2285) # Via della Volta 120, BS
# Usiamo un user_agent unico per evitare blocchi
geolocator = Nominatim(user_agent="gls_router_brescia_final_v20")

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
            loc = geolocator.geocode(f"{c}, Brescia, Italy", timeout=10)
            if loc: centri.append({"nome": c, "dist": geodesic(COORDS_SEDE, (loc.latitude, loc.longitude)).km})
        st.session_state.comuni_oggi = sorted(centri, key=lambda x: x['dist'])
        st.rerun()

# --- 2. MAPPA DINAMICA ---
st.subheader("🗺️ Mappa Itinerario")
# Calcoliamo il centro mappa dinamico
center_lat = COORDS_SEDE[0]
center_lon = COORDS_SEDE[1]
if st.session_state.pacchi:
    valid_coords = [p['coords'] for p in st.session_state.pacchi if p['coords']]
    if valid_coords:
        center_lat = sum(c[0] for c in valid_coords) / len(valid_coords)
        center_lon = sum(c[1] for c in valid_coords) / len(valid_coords)

m = folium.Map(location=[center_lat, center_lon], zoom_start=13)
folium.Marker(COORDS_SEDE, tooltip="SEDE", icon=folium.Icon(color='black')).add_to(m)

for i, p in enumerate(st.session_state.pacchi):
    if p['coords']:
        color = '#28a745' if p['Tipo'] == 'A' else '#dc3545'
        folium.Marker(
            location=p['coords'],
            icon=folium.DivIcon(html=f'''<div style="font-family:Arial; color:white; background:{color}; border-radius:50%; width:30px; height:30px; display:flex; align-items:center; justify-content:center; font-weight:bold; border:2px solid white; box-shadow: 2px 2px 5px rgba(0,0,0,0.3);">{i+1}</div>''')
        ).add_to(m)

st_folium(m, width=1200, height=400, key="map_brescia")

# --- 3. INPUT ---
col_in, col_mod = st.columns(2)

with col_in:
    st.markdown('<div class="main-box">', unsafe_allow_html=True)
    via = st.text_input("📍 Via e Civico (es: Via Milano 10):").upper()
    comune = st.selectbox("🏙️ Comune:", [x['nome'] for x in st.session_state.comuni_oggi] if st.session_state.comuni_oggi else ["Configura paesi in sidebar"])
    
    def add_pacco(tipo):
        if via and comune != "Configura paesi in sidebar":
            # Ricerca potenziata: via + comune + provincia + nazione
            query = f"{via}, {comune}, BS, Lombardia, Italy"
            loc = geolocator.geocode(query, timeout=10)
            if loc:
                st.session_state.pacchi.append({
                    "Via": via, "Comune": comune, "Tipo": tipo, 
                    "coords": (loc.latitude, loc.longitude)
                })
                st.toast(f"Punto trovato: {via}", icon="✅")
            else:
                st.error(f"❌ Impossibile trovare: {via}. Prova a scrivere meglio l'indirizzo.")
                # Lo aggiungiamo comunque ma senza coordinate
                st.session_state.pacchi.append({"Via": via, "Comune": comune, "Tipo": tipo, "coords": None})
            time.sleep(0.5) # Evita blocchi API

    c1, c2 = st.columns(2)
    if c1.button("🟢 + AZIENDA"): add_pacco("A")
    if c2.button("🔴 + PRIVATO"): add_pacco("P")
    st.markdown('</div>', unsafe_allow_html=True)

with col_mod:
    if st.session_state.pacchi:
        st.markdown('<div class="main-box">', unsafe_allow_html=True)
        st.write(f"Lista stop: {len(st.session_state.pacchi)}")
        idx = st.number_input("Muovi stop n.", 1, len(st.session_state.pacchi)) - 1
        new_pos = st.number_input("Al posto n.", 1, len(st.session_state.pacchi)) - 1
        if st.button("SPOSTA"):
            p = st.session_state.pacchi.pop(idx)
            st.session_state.pacchi.insert(new_pos, p)
            st.rerun()
        if st.button("🗑️ CANCELLA TUTTO"):
            st.session_state.pacchi = []
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# --- 4. PDF ---
if st.session_state.pacchi:
    if st.button("🚀 GENERA PDF"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(190, 10, clean_text("GIRO CONSEGNE GLS"), ln=True, align='C')
        pdf.ln(10)
        for i, p in enumerate(st.session_state.pacchi):
            pdf.set_fill_color(240, 240, 240) if p['Tipo'] == "A" else pdf.set_fill_color(255, 255, 255)
            pdf.cell(15, 10, str(i+1), 1, 0, 'C', True)
            testo = f"{p['Via']} - {p['Comune']} ({'AZ' if p['Tipo']=='A' else 'PR'})"
            pdf.cell(175, 10, clean_text(testo), 1, 1, 'L', True)
        
        pdf_bytes = pdf.output(dest='S').encode('latin-1', 'replace')
        st.download_button("📥 SCARICA PDF", pdf_bytes, "Giro_GLS.pdf", "application/pdf")
