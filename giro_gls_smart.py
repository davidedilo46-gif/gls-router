import streamlit as st
from fpdf import FPDF
from datetime import datetime
import urllib.parse
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import time

# --- CONFIGURAZIONE ---
LOGO_URL = "https://www.gls-italy.com/images/favicon.ico"
COORDS_SEDE = (45.5147, 10.2285) # Via della Volta 120, Brescia

st.set_page_config(page_title="GLS Check & Router", page_icon=LOGO_URL, layout="centered")

# --- STILE CSS ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #ffffff; }}
    .metric-container {{
        background-color: #002e6e;
        padding: 15px;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 20px;
    }}
    div.stButton > button {{ font-weight: bold; border-radius: 15px; height: 3.5em; }}
    div.stButton > button[kind="secondary"] {{ background-color: #28a745; color: white; }}
    div.stButton > button[kind="primary"] {{ background-color: #dc3545; color: white; }}
    .stDownloadButton > button {{ background-color: #002e6e !important; color: white !important; width: 100%; }}
    </style>
    """, unsafe_allow_html=True)

if 'pacchi' not in st.session_state:
    st.session_state.pacchi = []

geolocator = Nominatim(user_agent="gls_smart_check_v8")

# --- FUNZIONI DI LOGICA (CORRETTE PER EVITARE VALUERROR) ---
def calcola_giro(punti, punto_inizio):
    if not punti: 
        return []
    
    # Filtriamo solo i punti che hanno coordinate valide
    punti_validi = [p for p in punti if p.get('coords') is not None]
    punti_invalidi = [p for p in punti if p.get('coords') is None]
    
    if not punti_validi:
        return punti_invalidi

    paesi = {}
    for p in punti_validi:
        c = p['Comune']
        if c not in paesi: paesi[c] = []
        paesi[c].append(p)
    
    giro_tot = []
    attuale = punto_inizio
    lista_comuni = list(paesi.keys())
    
    while lista_comuni:
        # Trova il comune più vicino (Corretto per evitare liste vuote nel min)
        prox_c = min(lista_comuni, key=lambda c: min([geodesic(attuale, p['coords']).km for p in paesi[c]]))
        
        pacchi_c = paesi[prox_c]
        rimanenti = pacchi_c.copy()
        
        while rimanenti:
            p_v = min(rimanenti, key=lambda x: geodesic(attuale, x['coords']).km)
            giro_tot.append(p_v)
            attuale = p_v['coords']
            rimanenti.remove(p_v)
            
        lista_comuni.remove(prox_c)
        
    return giro_tot + punti_invalidi

# --- INTERFACCIA ---
st.title("🚚 GLS Smart Checker")

# 📊 CONTATORE
n_aziende = len([p for p in st.session_state.pacchi if p['Tipo'] == 'A'])
n_privati = len([p for p in st.session_state.pacchi if p['Tipo'] == 'P'])

st.markdown(f"""
    <div class="metric-container">
        <h2 style='color:white; margin:0;'>TOTALE PALMARE: {len(st.session_state.pacchi)}</h2>
        <p style='margin:0;'>🏢 Aziende: {n_aziende} | 🏠 Privati: {n_privati}</p>
    </div>
    """, unsafe_allow_html=True)

c1, c2 = st.columns([2, 1])
with c1:
    ind_raw = st.text_input("📍 Indirizzo:", placeholder="Via Roma 10")
with c2:
    paese_raw = st.text_input("🏙️ Comune:", placeholder="Brescia")

def is_duplicato(via, comune):
    return any(p['Via'].strip().upper() == via.strip().upper() and p['Comune'].strip().upper() == comune.strip().upper() for p in st.session_state.pacchi)

col_a, col_p = st.columns(2)

def aggiungi(tipo):
    if ind_raw and paese_raw:
        if is_duplicato(ind_raw, paese_raw):
            st.warning(f"⚠️ {ind_raw.upper()} è già in lista!")
        else:
            with st.spinner('Localizzazione...'):
                full = f"{ind_raw}, {paese_raw}, BS, Italy"
                try:
                    loc = geolocator.geocode(full, timeout=10)
                    coords = (loc.latitude, loc.longitude) if loc else None
                    st.session_state.pacchi.append({
                        "Via": ind_raw.upper(),
                        "Comune": paese_raw.upper(),
                        "Dati": f"{ind_raw.upper()} ({paese_raw.upper()})",
                        "Tipo": tipo,
                        "coords": coords
                    })
                    time.sleep(0.5)
                    st.rerun()
                except: st.error("Errore GPS.")

with col_a:
    if st.button("🟢 +1 AZIENDA", use_container_width=True): aggiungi("A")
with col_p:
    if st.button("🔴 +1 PRIVATO", type="primary", use_container_width=True): aggiungi("P")

if st.session_state.pacchi:
    st.write("---")
    if st.button("🗑️ SVUOTA TUTTO"):
        st.session_state.pacchi = []
        st.rerun()

    # --- GENERAZIONE PDF ---
    if st.button("🚀 SCARICA PDF OTTIMIZZATO"):
        if len(st.session_state.pacchi) > 0:
            aziende = [p for p in st.session_state.pacchi if p['Tipo'] == "A"]
            privati = [p for p in st.session_state.pacchi if p['Tipo'] == "P"]
            
            # Calcolo Aziende
            giro_a = calcola_giro(aziende, COORDS_SEDE)
            
            # Calcolo Privati partendo dall'ultimo punto delle aziende
            punto_rip = COORDS_SEDE
            if giro_a:
                valido = [p for p in giro_a if p['coords']]
                if valido: punto_rip = valido[-1]['coords']
            
            giro_p = calcola_giro(privati, punto_rip)
            giro_tot = giro_a + giro_p
            
            # PDF Creation
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(190, 10, f"GIRO GLS - {len(giro_tot)} COLLI", ln=True, align='C')
            pdf.ln(5)

            for i, p in enumerate(giro_tot):
                query = urllib.parse.quote(f"{p['Dati']} Brescia")
                link = f"https://www.google.com/maps/search/?api=1&query={query}"
                pdf.set_fill_color(240, 240, 240) if p['Tipo'] == "A" else pdf.set_fill_color(255, 255, 255)
                pdf.set_font("Arial", 'B', 10)
                pdf.cell(15, 12, str(i+1), 1, 0, 'C', True)
                pdf.set_font("Arial", size=9)
                pdf.cell(135, 12, f" {'[AZ]' if p['Tipo']=='A' else '[PR]'} {p['Dati'][:50]}", 1, 0, 'L', True)
                pdf.set_text_color(0, 0, 255)
                pdf.cell(40, 12, "NAVIGA", 1, 1, 'C', link=link)
                pdf.set_text_color(0, 0, 0)

            pdf_bytes = pdf.output(dest='S').encode('latin-1', 'replace')
            st.download_button(label="📥 CLICCA QUI PER IL FILE", data=pdf_bytes, file_name="Giro_GLS.pdf")
        else:
            st.error("Inserisci almeno un pacco!")
