import streamlit as st
from fpdf import FPDF
from datetime import datetime
import urllib.parse
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

# --- CONFIGURAZIONE ---
LOGO_URL = "https://www.gls-italy.com/images/favicon.ico"
# IMPOSTA QUI LE COORDINATE DELLA TUA SEDE (Esempio: Milano)
COORDS_SEDE = (45.4642, 9.1900) 

st.set_page_config(page_title="GLS Router", page_icon=LOGO_URL, layout="centered")

st.markdown(f"""
    <head><link rel="apple-touch-icon" href="{LOGO_URL}"><meta name="theme-color" content="#002e6e"></head>
    <style>
    .stApp {{ background-color: #ffffff; }}
    div.stButton > button {{ font-weight: bold; border-radius: 15px; height: 3.5em; }}
    div.stButton > button[kind="secondary"] {{ background-color: #28a745; color: white; }}
    div.stButton > button[kind="primary"] {{ background-color: #dc3545; color: white; }}
    .stDownloadButton > button {{ background-color: #002e6e !important; color: white !important; width: 100%; }}
    </style>
    """, unsafe_allow_html=True)

if 'pacchi' not in st.session_state:
    st.session_state.pacchi = []

geolocator = Nominatim(user_agent="gls_smart_nav_v4")

# --- FUNZIONE CALCOLO PERCORSO ---
def ottimizza_percorso(lista_punti, punto_partenza):
    percorso_ordinato = []
    punto_attuale = punto_partenza
    rimanenti = [p for p in lista_punti if p['coords'] is not None]
    senza_coords = [p for p in lista_punti if p['coords'] is None]

    while rimanenti:
        prossimo = min(rimanenti, key=lambda x: geodesic(punto_attuale, x['coords']).km)
        percorso_ordinato.append(prossimo)
        punto_attuale = prossimo['coords']
        rimanenti.remove(prossimo)
    
    return percorso_ordinato + senza_coords

# --- INTERFACCIA ---
st.title("🚚 GLS Smart Optimizer")
indirizzo = st.text_input("📍 Inserisci Via e Città:", placeholder="Es: Via Roma 10, Milano")

col1, col2 = st.columns(2)
with col1:
    if st.button("🟢 AZIENDA", use_container_width=True):
        if indirizzo:
            with st.spinner('Ricerca posizione...'):
                loc = geolocator.geocode(indirizzo, timeout=10)
                coords = (loc.latitude, loc.longitude) if loc else None
                st.session_state.pacchi.append({"Dati": indirizzo.upper(), "Tipo": "A", "coords": coords})
            st.rerun()

with col2:
    if st.button("🔴 PRIVATO", type="primary", use_container_width=True):
        if indirizzo:
            with st.spinner('Ricerca posizione...'):
                loc = geolocator.geocode(indirizzo, timeout=10)
                coords = (loc.latitude, loc.longitude) if loc else None
                st.session_state.pacchi.append({"Dati": indirizzo.upper(), "Tipo": "P", "coords": coords})
            st.rerun()

if st.session_state.pacchi:
    st.write("---")
    st.subheader(f"Colli totali: {len(st.session_state.pacchi)}")
    
    if st.button("🗑️ SVUOTA TUTTO"):
        st.session_state.pacchi = []
        st.rerun()

    # --- GENERAZIONE PDF ORDINATO ---
    aziende_raw = [p for p in st.session_state.pacchi if p['Tipo'] == "A"]
    privati_raw = [p for p in st.session_state.pacchi if p['Tipo'] == "P"]

    if st.button("🚀 SCARICA PDF OTTIMIZZATO"):
        # 1. Ordina Aziende dalla sede
        aziende_ordinate = ottimizza_percorso(aziende_raw, COORDS_SEDE)
        
        # 2. Ordina Privati dall'ultima azienda (o dalla sede se non ci sono aziende)
        ultimo_punto_a = aziende_ordinate[-1]['coords'] if aziende_ordinate and aziende_ordinate[-1]['coords'] else COORDS_SEDE
        privati_ordinati = ottimizza_percorso(privati_raw, ultimo_punto_a)
        
        giro_finale = aziende_ordinate + privati_ordinati

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.set_text_color(0, 46, 110) 
        pdf.cell(190, 15, "GIRO OTTIMIZZATO GLS", ln=True, align='C')
        pdf.ln(5)
        
        pdf.set_font("Arial", 'B', 10)
        pdf.set_fill_color(0, 46, 110)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(15, 10, "STOP", 1, 0, 'C', True)
        pdf.cell(135, 10, "INDIRIZZO (ORDINATO)", 1, 0, 'C', True)
        pdf.cell(40, 10, "MAPS", 1, 1, 'C', True)
        
        pdf.set_text_color(0, 0, 0)
        for i, p in enumerate(giro_finale):
            query = urllib.parse.quote(p['Dati'])
            link = f"https://www.google.com/maps/search/?api=1&query={query}"
            
            # Colore sfondo: Grigio per aziende, Bianco per privati
            pdf.set_fill_color(240, 240, 240) if p['Tipo'] == "A" else pdf.set_fill_color(255, 255, 255)
            
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(15, 12, str(i+1), 1, 0, 'C', True)
            pdf.set_font("Arial", size=9)
            
            tag = "[AZIENDA] " if p['Tipo'] == "A" else "[PRIVATO] "
            gps_error = " (!)" if p['coords'] is None else ""
            pdf.cell(135, 12, f" {tag}{p['Dati'][:45]}{gps_error}", 1, 0, 'L', True)
            
            pdf.set_text_color(0, 0, 255)
            pdf.set_font("Arial", 'U', 9)
            pdf.cell(40, 12, "NAVIGA", 1, 1, 'C', link=link)
            pdf.set_text_color(0, 0, 0)

        pdf_bytes = pdf.output(dest='S').encode('latin-1', 'replace')
        st.download_button(label="📥 SCARICA PDF", data=pdf_bytes, file_name="Giro_GLS_Ottimizzato.pdf", mime="application/pdf")
