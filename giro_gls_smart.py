import streamlit as st
from fpdf import FPDF
from datetime import datetime
import urllib.parse
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import time

# --- CONFIGURAZIONE ---
COORDS_SEDE = (45.5147, 10.2285) # Via della Volta 120, BS
geolocator = Nominatim(user_agent="gls_final_route_v11")

st.set_page_config(page_title="GLS Router Precision", layout="centered")

if 'pacchi' not in st.session_state: st.session_state.pacchi = []
if 'comuni_oggi' not in st.session_state: st.session_state.comuni_oggi = []

# --- FUNZIONE LOGICA "CATENA" (EVITA AVANTI E INDIETRO) ---
def ordina_catena_precisa(lista_punti, punto_partenza):
    if not lista_punti: return [], punto_partenza
    
    ordinati = []
    attuale = punto_partenza
    # Prendiamo solo quelli con coordinate per il calcolo
    da_elaborare = [p for p in lista_punti if p['coords']]
    senza_coords = [p for p in lista_punti if not p['coords']]
    
    while da_elaborare:
        # Trova il punto più vicino in assoluto alla posizione corrente
        prossimo = min(da_elaborare, key=lambda x: geodesic(attuale, x['coords']).km)
        ordinati.append(prossimo)
        attuale = prossimo['coords']
        da_elaborare.remove(prossimo)
    
    # Aggiunge in coda quelli che il GPS non ha trovato
    return ordinati + senza_coords, attuale

# --- INTERFACCIA ---
st.title("🚚 GLS Precision Router")

# 1. SETUP COMUNI
with st.expander("⚙️ CONFIGURA COMUNI DI OGGI", expanded=not st.session_state.comuni_oggi):
    input_comuni = st.text_input("Comuni separati da virgola (es: Poncarale, Montirone):")
    if st.button("IMPOSTA GIRO"):
        lista = [c.strip().upper() for c in input_comuni.split(",")]
        centri = []
        for c in lista:
            loc = geolocator.geocode(f"{c}, Brescia, Italy")
            if loc:
                dist = geodesic(COORDS_SEDE, (loc.latitude, loc.longitude)).km
                centri.append({"nome": c, "dist": dist})
        st.session_state.comuni_oggi = sorted(centri, key=lambda x: x['dist'])
        st.rerun()

# 2. CARICO
if st.session_state.comuni_oggi:
    st.info(f"Ordine Paesi: {' → '.join([x['nome'] for x in st.session_state.comuni_oggi])}")
    
    c1, c2 = st.columns([2, 1])
    with c1: via = st.text_input("📍 Via e Civico:").upper()
    with c2: comune = st.selectbox("🏙️ Comune:", [x['nome'] for x in st.session_state.comuni_oggi])

    def add(tipo):
        if via:
            # Controllo duplicati
            if any(p['Via'] == via and p['Comune'] == comune for p in st.session_state.pacchi):
                st.warning("⚠️ Indirizzo già inserito!")
                return
            with st.spinner('Localizzazione...'):
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

# 3. LISTA E PDF
if st.session_state.pacchi:
    st.write(f"📦 Colli totali: {len(st.session_state.pacchi)}")
    if st.button("🗑️ SVUOTA TUTTO"):
        st.session_state.pacchi = []
        st.session_state.comuni_oggi = []
        st.rerun()

    if st.button("🚀 GENERA PDF PERFETTO"):
        ordine_paesi = [x['nome'] for x in st.session_state.comuni_oggi]
        aziende = [p for p in st.session_state.pacchi if p['Tipo'] == "A"]
        privati = [p for p in st.session_state.pacchi if p['Tipo'] == "P"]
        
        giro_finale = []
        punto_attuale = COORDS_SEDE
        
        # --- ORDINA AZIENDE ---
        for p_nome in ordine_paesi:
            punti_comune = [p for p in aziende if p['Comune'] == p_nome]
            ordinati, punto_attuale = ordina_catena_precisa(punti_comune, punto_attuale)
            giro_finale.extend(ordinati)
            
        # --- ORDINA PRIVATI ---
        for p_nome in ordine_paesi:
            punti_comune = [p for p in privati if p['Comune'] == p_nome]
            ordinati, punto_attuale = ordina_catena_precisa(punti_comune, punto_attuale)
            giro_finale.extend(ordinati)

        # PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(190, 10, "GIRO OTTIMIZZATO SENZA RITORNI", ln=True, align='C')
        
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
        st.download_button("📥 SCARICA PDF", pdf_bytes, "Giro_Ottimale.pdf")
