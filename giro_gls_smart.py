import streamlit as st
from fpdf import FPDF
from datetime import datetime
import urllib.parse
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import time

# --- CONFIGURAZIONE ---
LOGO_URL = "https://www.gls-italy.com/images/favicon.ico"
COORDS_SEDE = (45.5147, 10.2285) # Via della Volta 120, BS

st.set_page_config(page_title="GLS Custom Router", page_icon=LOGO_URL, layout="centered")

if 'pacchi' not in st.session_state: st.session_state.pacchi = []
if 'comuni_oggi' not in st.session_state: st.session_state.comuni_oggi = []

geolocator = Nominatim(user_agent="gls_flexible_router_v10")

# --- STILE ---
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    .metric-container { background-color: #002e6e; padding: 15px; border-radius: 15px; color: white; text-align: center; margin-bottom: 20px;}
    div.stButton > button { font-weight: bold; border-radius: 15px; height: 3.5em; }
    div.stButton > button[kind="secondary"] { background-color: #28a745; color: white; }
    div.stButton > button[kind="primary"] { background-color: #dc3545; color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. CONFIGURAZIONE GIORNALIERA ---
st.title("🚚 GLS Daily Optimizer")
with st.expander("⚙️ 1. CONFIGURA I COMUNI DI OGGI", expanded=not st.session_state.comuni_oggi):
    input_comuni = st.text_input("Inserisci i comuni separati da virgola:", placeholder="Es: Poncarale, Montirone, Bagnolo Mella")
    if st.button("SALVA GIRO DEL GIORNO"):
        if input_comuni:
            lista = [c.strip().upper() for c in input_comuni.split(",")]
            # Calcoliamo la distanza di ogni centro comune dalla sede per ordinarli subito
            centri_ordinati = []
            for c in lista:
                loc = geolocator.geocode(f"{c}, Brescia, Italy")
                if loc:
                    dist = geodesic(COORDS_SEDE, (loc.latitude, loc.longitude)).km
                    centri_ordinati.append({"nome": c, "dist": dist, "coords": (loc.latitude, loc.longitude)})
                time.sleep(0.5)
            # Ordiniamo i comuni dal più vicino al più lontano
            st.session_state.comuni_oggi = sorted(centri_ordinati, key=lambda x: x['dist'])
            st.success(f"Giro configurato! Ordine: {' → '.join([x['nome'] for x in st.session_state.comuni_oggi])}")
            st.rerun()

# --- 2. CARICO PACCHI ---
if st.session_state.comuni_oggi:
    n_az = len([p for p in st.session_state.pacchi if p['Tipo'] == 'A'])
    n_pr = len([p for p in st.session_state.pacchi if p['Tipo'] == 'P'])
    st.markdown(f"<div class='metric-container'><h2>TOTALE CARICO: {len(st.session_state.pacchi)}</h2><p>🏢 AZIENDE: {n_az} | 🏠 PRIVATI: {n_pr}</p></div>", unsafe_allow_html=True)

    c1, c2 = st.columns([2, 1])
    with c1:
        ind_raw = st.text_input("📍 Via e Civico:", key="input_via")
    with c2:
        paese_scelto = st.selectbox("🏙️ Comune:", [x['nome'] for x in st.session_state.comuni_oggi])

    def aggiungi(tipo):
        if ind_raw:
            with st.spinner('Puntamento...'):
                full = f"{ind_raw}, {paese_scelto}, BS, Italy"
                loc = geolocator.geocode(full, timeout=10)
                coords = (loc.latitude, loc.longitude) if loc else None
                st.session_state.pacchi.append({
                    "Via": ind_raw.upper(), "Comune": paese_scelto, "Tipo": tipo, "coords": coords,
                    "Dati": f"{ind_raw.upper()} ({paese_scelto})"
                })
                st.rerun()

    col_a, col_p = st.columns(2)
    with col_a:
        if st.button("🟢 +1 AZIENDA", use_container_width=True): aggiungi("A")
    with col_p:
        if st.button("🔴 +1 PRIVATO", type="primary", use_container_width=True): aggiungi("P")

# --- 3. GENERAZIONE PDF ---
if st.session_state.pacchi:
    st.write("---")
    if st.button("🗑️ AZZERA TUTTO (NUOVO GIORNO)"):
        st.session_state.pacchi = []
        st.session_state.comuni_oggi = []
        st.rerun()

    if st.button("🚀 GENERA PDF OTTIMIZZATO"):
        # Ordiniamo i pacchi secondo la sequenza dei comuni salvata
        ordine_comuni = [x['nome'] for x in st.session_state.comuni_oggi]
        
        def ordina_settore(lista):
            risultato = []
            pos_attuale = COORDS_SEDE
            for c in ordine_comuni:
                pacchi_c = [p for p in lista if p['Comune'] == c]
                # Ordina le vie dentro il comune
                rimanenti = [p for p in pacchi_c if p['coords']]
                while rimanenti:
                    prox = min(rimanenti, key=lambda x: geodesic(pos_attuale, x['coords']).km)
                    risultato.append(prox)
                    pos_attuale = prox['coords']
                    rimanenti.remove(prox)
                risultato.extend([p for p in pacchi_c if not p['coords']])
            return risultato

        aziende = [p for p in st.session_state.pacchi if p['Tipo'] == "A"]
        privati = [p for p in st.session_state.pacchi if p['Tipo'] == "P"]
        
        giro_tot = ordina_settore(aziende) + ordina_settore(privati)
        
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 14)
        pdf.set_text_color(0, 46, 110)
        pdf.cell(190, 10, f"GIRO GLS BRESCIA - {datetime.now().strftime('%d/%m/%Y')}", ln=True, align='C')
        pdf.ln(5)

        for i, p in enumerate(giro_tot):
            pdf.set_fill_color(240, 240, 240) if p['Tipo'] == "A" else pdf.set_fill_color(255, 255, 255)
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(12, 12, str(i+1), 1, 0, 'C', True)
            pdf.set_font("Arial", size=8)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(138, 12, f" {'[AZ]' if p['Tipo']=='A' else '[PR]'} {p['Dati']}", 1, 0, 'L', True)
            pdf.set_text_color(0, 0, 255)
            q = urllib.parse.quote(f"{p['Dati']} Brescia")
            pdf.cell(40, 12, "MAPS", 1, 1, 'C', link=f"https://www.google.com/maps/search/?api=1&query={q}")
            pdf.set_text_color(0, 0, 0)

        pdf_bytes = pdf.output(dest='S').encode('latin-1', 'replace')
        st.download_button(label="📥 SCARICA PDF", data=pdf_bytes, file_name="Giro_Daily.pdf")
