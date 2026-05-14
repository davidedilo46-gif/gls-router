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
geolocator = Nominatim(user_agent="gls_flex_fix_v18")

st.set_page_config(page_title="GLS Flex Router", layout="wide")

if 'pacchi' not in st.session_state: st.session_state.pacchi = []
if 'comuni_oggi' not in st.session_state: st.session_state.comuni_oggi = []

# --- FUNZIONE PULIZIA TESTO PER PDF (Fix Errore Screenshot) ---
def clean_text(text):
    return str(text).encode('latin-1', 'replace').decode('latin-1')

# --- STILE CSS ---
st.markdown("""
    <style>
    .stApp {
        background-image: linear-gradient(rgba(0, 46, 110, 0.6), rgba(255, 255, 255, 0.5)), 
                          url("https://www.gls-italy.com/images/belluno_sedegls_m16.jpg");
        background-size: cover; background-attachment: fixed;
    }
    .main-box { background-color: rgba(255, 255, 255, 0.95); padding: 20px; border-radius: 20px; border: 2px solid #002e6e; }
    .stButton>button { width: 100%; border-radius: 10px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- INTERFACCIA ---
st.title("📦 GLS Flex Style - Amazon Mode")

# 1. SIDEBAR PER COMUNI
with st.sidebar:
    st.header("⚙️ 1. SETUP PAESI")
    input_c = st.text_input("Inserisci i comuni (es: Poncarale, Montirone):")
    if st.button("Salva Comuni"):
        lista = [c.strip().upper() for c in input_c.split(",")]
        centri = []
        for c in lista:
            loc = geolocator.geocode(f"{c}, Brescia, Italy")
            if loc: centri.append({"nome": c, "dist": geodesic(COORDS_SEDE, (loc.latitude, loc.longitude)).km})
        st.session_state.comuni_oggi = sorted(centri, key=lambda x: x['dist'])
        st.success("Comuni salvati!")

# 2. AREA MAPPA (Sempre visibile in alto)
if st.session_state.pacchi:
    st.subheader("🗺️ Itinerario in Tempo Reale")
    m = folium.Map(location=COORDS_SEDE, zoom_start=12)
    folium.Marker(COORDS_SEDE, tooltip="SEDE", icon=folium.Icon(color='black')).add_to(m)
    
    for i, p in enumerate(st.session_state.pacchi):
        if p['coords']:
            color = 'green' if p['Tipo'] == 'A' else 'red'
            folium.Marker(
                location=p['coords'],
                icon=folium.DivIcon(html=f'<div style="font-family:Arial;color:white;background:{color};border-radius:50%;width:25px;height:25px;display:flex;align-items:center;justify-content:center;font-weight:bold;border:2px solid white;">{i+1}</div>')
            ).add_to(m)
    st_folium(m, width=1000, height=400)

# 3. INSERIMENTO E MODIFICA
col_in, col_mod = st.columns(2)

with col_in:
    st.markdown('<div class="main-box">', unsafe_allow_html=True)
    st.subheader("➕ Aggiungi Stop")
    via = st.text_input("Via e Civico:").upper()
    comune = st.selectbox("Comune:", [x['nome'] for x in st.session_state.comuni_oggi] if st.session_state.comuni_oggi else ["Configura paesi in sidebar"])
    
    if st.button("🟢 AZIENDA"):
        loc = geolocator.geocode(f"{via}, {comune}, BS, Italy")
        st.session_state.pacchi.append({"Via": via, "Comune": comune, "Tipo": "A", "coords": (loc.latitude, loc.longitude) if loc else None})
        st.rerun()
    if st.button("🔴 PRIVATO"):
        loc = geolocator.geocode(f"{via}, {comune}, BS, Italy")
        st.session_state.pacchi.append({"Via": via, "Comune": comune, "Tipo": "P", "coords": (loc.latitude, loc.longitude) if loc else None})
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

with col_mod:
    if st.session_state.pacchi:
        st.markdown('<div class="main-box">', unsafe_allow_html=True)
        st.subheader("🔄 Sposta/Elimina")
        idx = st.number_input("Dal numero:", 1, len(st.session_state.pacchi)) - 1
        new_pos = st.number_input("Al numero:", 1, len(st.session_state.pacchi)) - 1
        if st.button("SPOSTA ORA"):
            p = st.session_state.pacchi.pop(idx)
            st.session_state.pacchi.insert(new_pos, p)
            st.rerun()
        if st.button("🗑️ ELIMINA ULTIMO"):
            st.session_state.pacchi.pop()
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# 4. DOWNLOAD PDF (Il tasto compare qui sotto)
if st.session_state.pacchi:
    st.write("---")
    if st.button("📝 CREA PDF DEFINITIVO"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(190, 10, clean_text(f"GIRO GLS - {len(st.session_state.pacchi)} STOP"), ln=True, align='C')
        
        for i, p in enumerate(st.session_state.pacchi):
            pdf.set_fill_color(240, 240, 240) if p['Tipo'] == "A" else pdf.set_fill_color(255, 255, 255)
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(12, 10, str(i+1), 1, 0, 'C', True)
            pdf.set_font("Arial", size=9)
            testo_pacco = clean_text(f"{p['Via']} - {p['Comune']} ({'AZ' if p['Tipo']=='A' else 'PR'})")
            pdf.cell(178, 10, testo_pacco, 1, 1, 'L', True)
        
        pdf_output = pdf.output(dest='S')
        st.download_button(label="📥 CLICCA QUI PER SCARICARE IL PDF", data=bytes(pdf_output), file_name="Giro_Oggi.pdf", mime="application/pdf")
