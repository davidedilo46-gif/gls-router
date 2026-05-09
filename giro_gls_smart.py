import streamlit as st
from fpdf import FPDF
from datetime import datetime
import urllib.parse
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import time

# --- CONFIGURAZIONE ---
LOGO_URL = "https://www.gls-italy.com/images/favicon.ico"
# COORDINATE PRECISE: Via della Volta 120, Brescia
COORDS_SEDE = (45.5147, 10.2285) 

st.set_page_config(page_title="GLS Router Brescia", page_icon=LOGO_URL, layout="centered")

st.markdown(f"""
    <head><link rel="apple-touch-icon" href="{LOGO_URL}"><meta name="theme-color" content="#002e6e"></head>
    <style>
    .stApp {{ background-color: #ffffff; }}
    div.stButton > button {{ font-weight: bold; border-radius: 15px; height: 3.5em; transition: 0.2s; }}
    div.stButton > button[kind="secondary"] {{ background-color: #28a745; color: white; }}
    div.stButton > button[kind="primary"] {{ background-color: #dc3545; color: white; }}
    .stDownloadButton > button {{ background-color: #002e6e !important; color: white !important; width: 100%; border-radius: 15px; }}
    .stTextInput > div > div > input {{ border: 2px solid #002e6e !important; border-radius: 12px; }}
    </style>
    """, unsafe_allow_html=True)

if 'pacchi' not in st.session_state:
    st.session_state.pacchi = []

# User agent specifico per Brescia
geolocator = Nominatim(user_agent="gls_brescia_router_v5")

# --- FUNZIONE LOGICA DI PERCORSO (CATENA) ---
def calcola_giro_ottimale(punti, punto_inizio):
    percorso = []
    attuale_coords = punto_inizio
    da_visitare = [p for p in punti if p['coords'] is not None]
    senza_coords = [p for p in punti if p['coords'] is None]

    while da_visitare:
        # Trova il punto più vicino alla posizione attuale
        prossimo = min(da_visitare, key=lambda x: geodesic(attuale_coords, x['coords']).km)
        percorso.append(prossimo)
        attuale_coords = prossimo['coords']
        da_visitare.remove(prossimo)
    
    return percorso + senza_coords

# --- INTERFACCIA ---
st.title("🚚 GLS Brescia Optimizer")
st.caption("Sede di partenza: Via della Volta 120, BS")

indirizzo_raw = st.text_input("📍 Via e n° civico:", placeholder="Es: Via Milano 10")

col1, col2 = st.columns(2)

def aggiungi_pacco(tipo):
    if indirizzo_raw:
        with st.spinner('Localizzazione in corso...'):
            # Forza la ricerca su Brescia per evitare errori di città
            indirizzo_completo = f"{indirizzo_raw}, Brescia, BS, Italy"
            try:
                loc = geolocator.geocode(indirizzo_completo, timeout=10)
                time.sleep(1) # Rispetta i limiti del servizio mappe
                coords = (loc.latitude, loc.longitude) if loc else None
                st.session_state.pacchi.append({
                    "Dati": indirizzo_raw.upper(), 
                    "Tipo": tipo, 
                    "coords": coords
                })
            except:
                st.error("Errore di connessione mappe. Riprova.")

with col1:
    if st.button("🟢 AZIENDA", use_container_width=True):
        aggiungi_pacco("A")
        st.rerun()

with col2:
    if st.button("🔴 PRIVATO", type="primary", use_container_width=True):
        aggiungi_pacco("P")
        st.rerun()

# --- DISPLAY LISTA ---
if st.session_state.pacchi:
    st.write("---")
    st.subheader(f"Colli inseriti: {len(st.session_state.pacchi)}")
    
    if st.button("🗑️ SVUOTA TUTTO"):
        st.session_state.pacchi = []
        st.rerun()

    # --- GENERAZIONE PDF ---
    if st.button("🚀 GENERA PDF ORDINATO"):
        aziende_input = [p for p in st.session_state.pacchi if p['Tipo'] == "A"]
        privati_input = [p for p in st.session_state.pacchi if p['Tipo'] == "P"]

        # 1. Ordina Aziende partendo dalla sede
        giro_aziende = calcola_giro_ottimale(aziende_input, COORDS_SEDE)
        
        # 2. Ordina Privati partendo dall'ultima azienda
        punto_ripartenza = giro_aziende[-1]['coords'] if giro_aziende and giro_aziende[-1]['coords'] else COORDS_SEDE
        giro_privati = calcola_giro_ottimale(privati_input, punto_ripartenza)
        
        giro_completo = giro_aziende + giro_privati

        pdf = FPDF()
        pdf.add_page()
        
        # Header
        pdf.set_font("Arial", 'B', 16)
        pdf.set_text_color(0, 46, 110) 
        pdf.cell(190, 15, "GIRO OTTIMIZZATO - GLS BRESCIA", ln=True, align='C')
        pdf.set_font("Arial", 'I', 10)
        pdf.cell(190, 5, f"Partenza: Via della Volta 120 | Data: {datetime.now().strftime('%d/%m/%Y')}", ln=True, align='C')
        pdf.ln(10)
        
        # Tabella
        pdf.set_font("Arial", 'B', 10)
        pdf.set_fill_color(0, 46, 110)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(15, 10, "STOP", 1, 0, 'C', True)
        pdf.cell(135, 10, "INDIRIZZO", 1, 0, 'C', True)
        pdf.cell(40, 10, "MAPS", 1, 1, 'C', True)
        
        pdf.set_text_color(0, 0, 0)
        for i, p in enumerate(giro_completo):
            query = urllib.parse.quote(f"{p['Dati']} Brescia")
            link = f"https://www.google.com/maps/search/?api=1&query={query}"
            
            pdf.set_fill_color(245, 245, 245) if p['Tipo'] == "A" else pdf.set_fill_color(255, 255, 255)
            
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(15, 12, str(i+1), 1, 0, 'C', True)
            
            pdf.set_font("Arial", size=9)
            tipo = "🏢 [AZ] " if p['Tipo'] == "A" else "🏠 [PR] "
            status = "" if p['coords'] else " (!)"
            pdf.cell(135, 12, f" {tipo}{p['Dati']}{status}", 1, 0, 'L', True)
            
            pdf.set_text_color(0, 0, 255)
            pdf.set_font("Arial", 'U', 9)
            pdf.cell(40, 12, "NAVIGA", 1, 1, 'C', link=link)
            pdf.set_text_color(0, 0, 0)

        pdf_bytes = pdf.output(dest='S').encode('latin-1', 'replace')
        st.download_button(label="📥 SCARICA PDF", data=pdf_bytes, file_name=f"Giro_Brescia_{datetime.now().strftime('%H%M')}.pdf", mime="application/pdf")
