import streamlit as st
from fpdf import FPDF
from datetime import datetime
import urllib.parse
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import pandas as pd
import time

# --- CONFIGURAZIONE ---
COORDS_SEDE = (45.5147, 10.2285) 
geolocator = Nominatim(user_agent="gls_ocr_router_v30")

st.set_page_config(page_title="GLS Fast Scan", layout="centered")

# --- STILE ---
st.markdown("""
    <style>
    .stApp {
        background-image: linear-gradient(rgba(0, 46, 110, 0.7), rgba(255, 255, 255, 0.5)), 
                          url("https://www.gls-italy.com/images/belluno_sedegls_m16.jpg");
        background-size: cover; background-attachment: fixed;
    }
    .main-box { background-color: rgba(255, 255, 255, 0.95); padding: 25px; border-radius: 20px; border-left: 10px solid #f9ba00; }
    .scan-btn { background-color: #f9ba00 !important; color: #002e6e !important; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

if 'pacchi' not in st.session_state: st.session_state.pacchi = []
if 'comuni_oggi' not in st.session_state: st.session_state.comuni_oggi = []

# --- FUNZIONE OCR (Simulata per Streamlit Cloud) ---
# Nota: Streamlit non ha accesso diretto alla cam "live" per estrarre testo 
# in modo nativo senza librerie pesanti, ma usiamo l'input cam integrato.

st.title("🚀 GLS Fast Scan & Route")
st.write("Spara all'indirizzo con la fotocamera per fare prima!")

# --- 1. CONFIGURAZIONE PAESI ---
with st.sidebar:
    input_c = st.text_input("Comuni di oggi (es: Poncarale, Montirone):")
    if st.button("SALVA"):
        st.session_state.comuni_oggi = [c.strip().upper() for c in input_c.split(",")]

# --- 2. INPUT VELOCE (OCR / FOTOCAMERA) ---
if st.session_state.comuni_oggi:
    with st.container():
        st.markdown('<div class="main-box">', unsafe_allow_html=True)
        
        # Tasto "Amazon Flex Style" per cattura rapida
        foto_etichetta = st.camera_input("📷 INQUADRA INDIRIZZO ETICHETTA")
        
        if foto_etichetta:
            st.warning("✨ Sistema OCR pronto: In una versione futura caricheremo l'estrazione automatica del testo. Per ora scrivi l'indirizzo catturato qui sotto.")

        c1, c2 = st.columns([2, 1])
        via = c1.text_input("📍 Indirizzo o Nome Azienda:").upper()
        comune = c2.selectbox("🏙️ Comune:", st.session_state.comuni_oggi)
        
        is_busta = st.checkbox("✉️ BUSTA")
        
        ca, cp = st.columns(2)
        
        def aggiungi(tipo):
            if via:
                # Ricerca posizione
                loc = geolocator.geocode(f"{via}, {comune}, BS, Italy", timeout=10)
                st.session_state.pacchi.append({
                    "Via": via, "Comune": comune, "Tipo": tipo, 
                    "IsBusta": is_busta, "coords": (loc.latitude, loc.longitude) if loc else None
                })
                st.rerun()

        if ca.button("🏢 + AZIENDA", use_container_width=True): aggiungi("A")
        if cp.button("🏠 + PRIVATO", use_container_width=True, type="primary"): aggiungi("P")
        st.markdown('</div>', unsafe_allow_html=True)

# --- 3. LISTA E PDF ---
if st.session_state.pacchi:
    st.write(f"📦 Stop in lista: {len(st.session_state.pacchi)}")
    
    if st.button("🚀 GENERA PDF OTTIMIZZATO"):
        # (Qui inseriamo la logica di ordinamento precedentemente approvata)
        # ...
        st.success("Giro pronto!")
