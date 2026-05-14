import streamlit as st
from fpdf import FPDF
from datetime import datetime
import urllib.parse
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import time
import pandas as pd

# --- CONFIGURAZIONE ---
COORDS_SEDE = (45.5147, 10.2285) # Via della Volta 120, BS
geolocator = Nominatim(user_agent="gls_precision_manual_v16")

st.set_page_config(page_title="GLS Router Master", layout="centered")

# Inizializzazione sessioni
if 'pacchi' not in st.session_state: st.session_state.pacchi = []
if 'comuni_oggi' not in st.session_state: st.session_state.comuni_oggi = []
if 'giro_ottimizzato' not in st.session_state: st.session_state.giro_ottimizzato = []

# --- STILE CSS (Sfondo Furgoni GLS) ---
st.markdown("""
    <style>
    .stApp {
        background-image: linear-gradient(rgba(0, 46, 110, 0.5), rgba(255, 255, 255, 0.4)), 
                          url("https://www.gls-italy.com/images/belluno_sedegls_m16.jpg");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }
    .main-box {
        background-color: rgba(255, 255, 255, 0.92);
        padding: 20px;
        border-radius: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 46, 110, 0.3);
        margin-bottom: 15px;
    }
    .metric-container {
        background-color: #002e6e;
        padding: 10px;
        border-radius: 15px;
        color: white;
        text-align: center;
    }
    div.stButton > button { font-weight: bold; border-radius: 12px; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNZIONI LOGICHE ---
def calcola_sequenza():
    ordine_paesi = [x['nome'] for x in st.session_state.comuni_oggi]
    aziende = [p for p in st.session_state.pacchi if p['Tipo'] == "A"]
    privati = [p for p in st.session_state.pacchi if p['Tipo'] == "P"]
    
    def ordina_blocco(lista, inizio):
        res = []
        attuale = inizio
        da_elab = [p for p in lista if p['coords']]
        while da_elab:
            prox = min(da_elab, key=lambda x: geodesic(attuale, x['coords']).km)
            res.append(prox)
            attuale = prox['coords']
            da_elab.remove(prox)
        res.extend([p for p in lista if not p['coords']])
        return res, attuale

    giro = []
    punto = COORDS_SEDE
    for paese in ordine_paesi:
        bloc, punto = ordina_blocco([p for p in aziende if p['Comune'] == paese], punto)
        giro.extend(bloc)
    for paese in ordine_paesi:
        bloc, punto = ordina_blocco([p for p in privati if p['Comune'] == paese], punto)
        giro.extend(bloc)
    return giro

# --- INTERFACCIA ---
st.title("🚚 GLS Router Master")

# 1. SETUP COMUNI
with st.expander("⚙️ 1. SETUP COMUNI DEL GIORNO"):
    input_c = st.text_input("Comuni (es: Poncarale, Montirone):")
    if st.button("CONFIGURA GIRO"):
        lista = [c.strip().upper() for c in input_c.split(",")]
        centri = []
        for c in lista:
            loc = geolocator.geocode(f"{c}, Brescia, Italy")
            if loc: centri.append({"nome": c, "dist": geodesic(COORDS_SEDE, (loc.latitude, loc.longitude)).km})
        st.session_state.comuni_oggi = sorted(centri, key=lambda x: x['dist'])
        st.rerun()

# 2. CARICO
if st.session_state.comuni_oggi:
    st.markdown(f"<div class='metric-container'><h3>PACCHI CARICATI: {len(st.session_state.pacchi)}</h3></div>", unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="main-box">', unsafe_allow_html=True)
        c1, c2 = st.columns([2, 1])
        via = c1.text_input("📍 Via e Civico:").upper()
        comune = c2.selectbox("🏙️ Comune:", [x['nome'] for x in st.session_state.comuni_oggi])
        
        ca, cp = st.columns(2)
        if ca.button("🟢 AZIENDA", use_container_width=True):
            loc = geolocator.geocode(f"{via}, {comune}, BS, Italy")
            st.session_state.pacchi.append({"Via": via, "Comune": comune, "Tipo": "A", "coords": (loc.latitude, loc.longitude) if loc else None, "Dati": f"{via} ({comune})"})
            st.session_state.giro_ottimizzato = calcola_sequenza()
            st.rerun()
        if cp.button("🔴 PRIVATO", type="primary", use_container_width=True):
            loc = geolocator.geocode(f"{via}, {comune}, BS, Italy")
            st.session_state.pacchi.append({"Via": via, "Comune": comune, "Tipo": "P", "coords": (loc.latitude, loc.longitude) if loc else None, "Dati": f"{via} ({comune})"})
            st.session_state.giro_ottimizzato = calcola_sequenza()
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# 3. MODIFICA MANUALE E MAPPA
if st.session_state.giro_ottimizzato:
    st.subheader("🗺️ Mappa e Ottimizzazione")
    
    # Mappa
    df_map = pd.DataFrame([{'lat': p['coords'][0], 'lon': p['coords'][1]} for p in st.session_state.giro_ottimizzato if p['coords']])
    st.map(df_map)

    # MODIFICA MANUALE
    with st.expander("✍️ MODIFICA ORDINE MANUALE (Se vuoi cambiare il giro)"):
        st.write("Sposta un pacco in una posizione diversa:")
        idx_da_muovere = st.selectbox("Seleziona stop da spostare:", range(len(st.session_state.giro_ottimizzato)), format_func=lambda x: f"Stop {x+1}: {st.session_state.giro_ottimizzato[x]['Dati']}")
        nuova_pos = st.number_input("Muovi alla posizione numero:", min_value=1, max_value=len(st.session_state.giro_ottimizzato), value=idx_da_muovere+1)
        
        if st.button("🔄 CONFERMA SPOSTAMENTO E AGGIORNA"):
            pacco = st.session_state.giro_ottimizzato.pop(idx_da_muovere)
            st.session_state.giro_ottimizzato.insert(nuova_pos-1, pacco)
            st.success("Giro modificato! Ora puoi salvare il nuovo PDF.")
            st.rerun()

    # GENERAZIONE PDF
    if st.button("💾 SALVA NUOVO PDF DEFINITIVO", type="primary", use_container_width=True):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(190, 10, "GIRO GLS DEFINITIVO - MODIFICATO", ln=True, align='C')
        
        for i, p in enumerate(st.session_state.giro_ottimizzato):
            pdf.set_fill_color(240, 240, 240) if p['Tipo'] == "A" else pdf.set_fill_color(255, 255, 255)
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(12, 12, str(i+1), 1, 0, 'C', True)
            pdf.set_font("Arial", size=9)
            pdf.cell(138, 12, f" {p['Dati']}", 1, 0, 'L', True)
            
            q = urllib.parse.quote(f"{p['Dati']} Brescia")
            pdf.set_text_color(0, 0, 255)
            pdf.cell(40, 12, "MAPS", 1, 1, 'C', link=f"https://www.google.com/maps/search/?api=1&query={q}")
            pdf.set_text_color(0,0,0)
            
        pdf_bytes = pdf.output(dest='S').encode('latin-1', 'replace')
        st.download_button("📥 SCARICA PDF AGGIORNATO", pdf_bytes, "Giro_Custom.pdf")

    if st.button("🗑️ RESET GIORNALIERO"):
        st.session_state.pacchi = []
        st.session_state.giro_ottimizzato = []
        st.rerun()
