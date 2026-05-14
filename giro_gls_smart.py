import streamlit as st
from fpdf import FPDF
from datetime import datetime
import urllib.parse
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import time

# --- CONFIGURAZIONE SEDE ---
COORDS_SEDE = (45.5147, 10.2285) # Via della Volta 120, Brescia
geolocator = Nominatim(user_agent="gls_brescia_classic_v24")

st.set_page_config(page_title="GLS Router Classic", layout="centered")

# Inizializzazione sessioni
if 'pacchi' not in st.session_state: st.session_state.pacchi = []
if 'comuni_oggi' not in st.session_state: st.session_state.comuni_oggi = []

# --- STILE ---
st.markdown("""
    <style>
    .stApp {
        background-image: linear-gradient(rgba(0, 46, 110, 0.6), rgba(255, 255, 255, 0.5)), 
                          url("https://www.gls-italy.com/images/belluno_sedegls_m16.jpg");
        background-size: cover; background-attachment: fixed;
    }
    .main-box { background-color: rgba(255, 255, 255, 0.95); padding: 20px; border-radius: 20px; border: 1px solid #002e6e; }
    .metric-container { background-color: #002e6e; padding: 15px; border-radius: 15px; color: white; text-align: center; margin-bottom: 20px;}
    div.stButton > button { font-weight: bold; border-radius: 12px; height: 3.5em; }
    </style>
    """, unsafe_allow_html=True)

def clean_text(text):
    return str(text).encode('latin-1', 'replace').decode('latin-1')

# --- LOGICA DI ORDINAMENTO PER PAESE ---
def ordina_giro(lista_punti, punto_partenza):
    if not lista_punti: return []
    
    # 1. Raggruppa per paese
    paesi = {}
    for p in lista_punti:
        c = p['Comune']
        if c not in paesi: paesi[c] = []
        paesi[c].append(p)
    
    # 2. Ordina i paesi in base alla distanza del loro centro dalla posizione attuale
    giro_completo = []
    posizione_attuale = punto_partenza
    
    comuni_nomi = list(paesi.keys())
    while comuni_nomi:
        # Trova il comune più vicino tra quelli rimasti
        prox_c = min(comuni_nomi, key=lambda c: geodesic(posizione_attuale, geolocator.geocode(f"{c}, BS, Italy")).km)
        
        # Ordina internamente gli indirizzi di quel comune (dal più vicino al più lontano)
        rimanenti_comune = paesi[prox_c]
        while rimanenti_comune:
            p_vicino = min(rimanenti_comune, key=lambda x: geodesic(posizione_attuale, x['coords']) if x['coords'] else 999)
            giro_completo.append(p_vicino)
            if p_vicino['coords']: posizione_attuale = p_vicino['coords']
            rimanenti_comune.remove(p_vicino)
            
        comuni_nomi.remove(prox_c)
        
    return giro_completo

# --- INTERFACCIA ---
st.title("🚚 GLS Delivery List")

with st.sidebar:
    st.header("⚙️ Configura Paesi")
    input_c = st.text_input("Quali paesi fai oggi? (es: Poncarale, Montirone)")
    if st.button("SALVA"):
        st.session_state.comuni_oggi = [c.strip().upper() for c in input_c.split(",")]
        st.rerun()

if st.session_state.comuni_oggi:
    st.markdown(f"<div class='metric-container'><h2>PACCHI IN LISTA: {len(st.session_state.pacchi)}</h2></div>", unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="main-box">', unsafe_allow_html=True)
        c1, c2 = st.columns([2, 1])
        via = c1.text_input("📍 Via e Civico:").upper()
        comune = c2.selectbox("🏙️ Comune:", st.session_state.comuni_oggi)
        
        ca, cp = st.columns(2)
        if ca.button("🟢 AZIENDA", use_container_width=True):
            loc = geolocator.geocode(f"{via}, {comune}, BS, Italy")
            st.session_state.pacchi.append({"Via": via, "Comune": comune, "Tipo": "A", "coords": (loc.latitude, loc.longitude) if loc else None})
            st.rerun()
        if cp.button("🔴 PRIVATO", use_container_width=True):
            loc = geolocator.geocode(f"{via}, {comune}, BS, Italy")
            st.session_state.pacchi.append({"Via": via, "Comune": comune, "Tipo": "P", "coords": (loc.latitude, loc.longitude) if loc else None})
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

if st.session_state.pacchi:
    if st.button("🗑️ SVUOTA TUTTO"):
        st.session_state.pacchi = []
        st.rerun()

    if st.button("🚀 GENERA PDF ORDINATO", type="primary", use_container_width=True):
        aziende = [p for p in st.session_state.pacchi if p['Tipo'] == "A"]
        privati = [p for p in st.session_state.pacchi if p['Tipo'] == "P"]
        
        # Ordina per Paese e Distanza
        giro_a = ordina_giro(aziende, COORDS_SEDE)
        ultimo_punto = giro_a[-1]['coords'] if giro_a and giro_a[-1]['coords'] else COORDS_SEDE
        giro_p = ordina_giro(privati, ultimo_punto)
        
        giro_tot = giro_a + giro_p
        
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(190, 10, clean_text(f"GIRO GLS - {datetime.now().strftime('%d/%m/%Y')}"), ln=True, align='C')
        pdf.ln(5)

        for i, p in enumerate(giro_tot):
            pdf.set_fill_color(240, 240, 240) if p['Tipo'] == "A" else pdf.set_fill_color(255, 255, 255)
            pdf.set_font("Arial", 'B', 11)
            pdf.cell(12, 12, str(i+1), 1, 0, 'C', True)
            pdf.set_font("Arial", size=10)
            
            tipo_label = "AZIENDA" if p['Tipo'] == 'A' else "PRIVATO"
            testo = f" [{tipo_label}] {p['Via']} - {p['Comune']}"
            pdf.cell(140, 12, clean_text(testo), 1, 0, 'L', True)
            
            pdf.set_text_color(0, 0, 255)
            q = urllib.parse.quote(f"{p['Via']}, {p['Comune']}, Brescia, Italy")
            pdf.cell(38, 12, "NAVIGA", 1, 1, 'C', link=f"https://www.google.com/maps/search/?api=1&query={q}")
            pdf.set_text_color(0, 0, 0)

        pdf_bytes = pdf.output(dest='S').encode('latin-1', 'replace')
        st.download_button("📥 SCARICA PDF", pdf_bytes, "Giro_GLS.pdf")
