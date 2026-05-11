import streamlit as st
from fpdf import FPDF
from datetime import datetime
import urllib.parse
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import time

# --- CONFIGURAZIONE ---
COORDS_SEDE = (45.5147, 10.2285) 
geolocator = Nominatim(user_agent="gls_precision_styled_v13")

st.set_page_config(page_title="GLS Router Pro", layout="centered")

if 'pacchi' not in st.session_state: st.session_state.pacchi = []
if 'comuni_oggi' not in st.session_state: st.session_state.comuni_oggi = []

# --- STILE CSS AVANZATO (Sfondo e Grafica) ---
st.markdown("""
    <style>
    /* Sfondo sfumato professionale */
    .stApp {
        background: linear-gradient(180deg, #002e6e 0%, #f0f2f6 40%, #ffffff 100%);
        background-attachment: fixed;
    }

    /* Riquadri effetto vetro (Glassmorphism) */
    .main-box {
        background-color: rgba(255, 255, 255, 0.9);
        padding: 20px;
        border-radius: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 46, 110, 0.2);
        margin-bottom: 20px;
    }

    .metric-container {
        background-color: #002e6e;
        padding: 15px;
        border-radius: 15px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }

    h1 { color: white !important; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }

    div.stButton > button {
        font-weight: bold !important;
        border-radius: 15px !important;
        height: 3.5em !important;
        border: none !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    div.stButton > button[kind="secondary"] { background-color: #28a745 !important; color: white !important; }
    div.stButton > button[kind="primary"] { background-color: #dc3545 !important; color: white !important; }
    .stDownloadButton > button { background-color: #002e6e !important; color: white !important; width: 100% !important; }
    
    label { color: #002e6e !important; font-weight: bold !important; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNZIONI LOGICHE ---
def ordina_catena_precisa(lista_punti, punto_partenza):
    if not lista_punti: return [], punto_partenza
    ordinati = []
    attuale = punto_partenza
    da_elaborare = [p for p in lista_punti if p['coords']]
    senza_coords = [p for p in lista_punti if not p['coords']]
    while da_elaborare:
        prossimo = min(da_elaborare, key=lambda x: geodesic(attuale, x['coords']).km)
        ordinati.append(prossimo)
        attuale = prossimo['coords']
        da_elaborare.remove(prossimo)
    return ordinati + senza_coords, attuale

# --- 1. SETUP COMUNI ---
st.title("🚚 GLS Precision Pro")

with st.expander("⚙️ CONFIGURA COMUNI DI OGGI", expanded=not st.session_state.comuni_oggi):
    input_comuni = st.text_input("Comuni di oggi (es: Poncarale, Montirone):")
    if st.button("SALVA E INIZIA"):
        if input_comuni:
            lista = [c.strip().upper() for c in input_comuni.split(",")]
            centri = []
            for c in lista:
                loc = geolocator.geocode(f"{c}, Brescia, Italy")
                if loc:
                    dist = geodesic(COORDS_SEDE, (loc.latitude, loc.longitude)).km
                    centri.append({"nome": c, "dist": dist})
                time.sleep(0.5)
            st.session_state.comuni_oggi = sorted(centri, key=lambda x: x['dist'])
            st.rerun()

# --- 2. CONTATORE E CARICO ---
if st.session_state.comuni_oggi:
    n_az = len([p for p in st.session_state.pacchi if p['Tipo'] == 'A'])
    n_pr = len([p for p in st.session_state.pacchi if p['Tipo'] == 'P'])
    
    st.markdown(f"<div class='metric-container'><h2>TOTALE: {len(st.session_state.pacchi)}</h2><p>🏢 AZIENDE: {n_az} | 🏠 PRIVATI: {n_pr}</p></div>", unsafe_allow_html=True)
    st.write("") # Spazio

    with st.container():
        st.markdown('<div class="main-box">', unsafe_allow_html=True)
        c1, c2 = st.columns([2, 1])
        with c1: via = st.text_input("📍 Via e Civico:").upper()
        with c2: comune = st.selectbox("🏙️ Comune:", [x['nome'] for x in st.session_state.comuni_oggi])

        def add(tipo):
            if via:
                if any(p['Via'] == via and p['Comune'] == comune for p in st.session_state.pacchi):
                    st.toast(f"Altro collo per {via}", icon="📦")
                with st.spinner('Puntamento...'):
                    loc = geolocator.geocode(f"{via}, {comune}, BS, Italy")
                    coords = (loc.latitude, loc.longitude) if loc else None
                    st.session_state.pacchi.append({
                        "Via": via, "Comune": comune, "Tipo": tipo, 
                        "coords": coords, "Dati": f"{via} ({comune})"
                    })
                    st.rerun()

        col1, col2 = st.columns(2)
        with col1: 
            if st.button("🟢 +1 AZIENDA", use_container_width=True): add("A")
        with col2: 
            if st.button("🔴 +1 PRIVATO", type="primary", use_container_width=True): add("P")
        st.markdown('</div>', unsafe_allow_html=True)

# --- 3. GENERAZIONE PDF ---
if st.session_state.pacchi:
    st.markdown('<div class="main-box">', unsafe_allow_html=True)
    if st.button("🗑️ AZZERA TUTTO"):
        st.session_state.pacchi = []
        st.session_state.comuni_oggi = []
        st.rerun()

    if st.button("🚀 GENERA PDF OTTIMIZZATO"):
        ordine_paesi = [x['nome'] for x in st.session_state.comuni_oggi]
        aziende = [p for p in st.session_state.pacchi if p['Tipo'] == "A"]
        privati = [p for p in st.session_state.pacchi if p['Tipo'] == "P"]
        
        giro_finale = []
        punto_attuale = COORDS_SEDE
        
        for p_nome in ordine_paesi:
            punti_comune = [p for p in aziende if p['Comune'] == p_nome]
            ordinati, punto_attuale = ordina_catena_precisa(punti_comune, punto_attuale)
            giro_finale.extend(ordinati)
            
        for p_nome in ordine_paesi:
            punti_comune = [p for p in privati if p['Comune'] == p_nome]
            ordinati, punto_attuale = ordina_catena_precisa(punti_comune, punto_attuale)
            giro_finale.extend(ordinati)

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(190, 10, f"GIRO GLS - {len(giro_finale)} COLLI - {datetime.now().strftime('%d/%m/%Y')}", ln=True, align='C')
        pdf.ln(5)

        for i, p in enumerate(giro_finale):
            pdf.set_fill_color(240, 240, 240) if p['Tipo'] == "A" else pdf.set_fill_color(255, 255, 255)
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(12, 12, str(i+1), 1, 0, 'C', True)
            pdf.set_font("Arial", size=9)
            pdf.cell(138, 12, f" {'[AZ]' if p['Tipo']=='A' else '[PR]'} {p['Dati']}", 1, 0, 'L', True)
            pdf.set_text_color(0, 0, 255)
            q = urllib.parse.quote(f"{p['Dati']} Brescia")
            pdf.cell(40, 12, "MAPS", 1, 1, 'C', link=f"https://www.google.com/maps/search/?api=1&query={q}")
            pdf.set_text_color(0, 0, 0)

        pdf_bytes = pdf.output(dest='S').encode('latin-1', 'replace')
        st.download_button("📥 SCARICA PDF", pdf_bytes, "Giro_GLS.pdf")
    st.markdown('</div>', unsafe_allow_html=True)
