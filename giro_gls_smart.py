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

st.set_page_config(page_title="GLS Router Brescia", page_icon=LOGO_URL, layout="centered")

st.markdown(f"""
    <head><link rel="apple-touch-icon" href="{LOGO_URL}"><meta name="theme-color" content="#002e6e"></head>
    <style>
    .stApp {{ background-color: #ffffff; }}
    div.stButton > button {{ font-weight: bold; border-radius: 15px; height: 3.5em; }}
    div.stButton > button[kind="secondary"] {{ background-color: #28a745; color: white; }}
    div.stButton > button[kind="primary"] {{ background-color: #dc3545; color: white; }}
    .stDownloadButton > button {{ background-color: #002e6e !important; color: white !important; width: 100%; border-radius: 15px; }}
    .stTextInput > div > div > input {{ border: 2px solid #002e6e !important; border-radius: 12px; }}
    </style>
    """, unsafe_allow_html=True)

if 'pacchi' not in st.session_state:
    st.session_state.pacchi = []

geolocator = Nominatim(user_agent="gls_brescia_router_v6")

def calcola_giro_ottimale(punti, punto_inizio):
    percorso = []
    attuale_coords = punto_inizio
    da_visitare = [p for p in punti if p['coords'] is not None]
    senza_coords = [p for p in punti if p['coords'] is None]
    while da_visitare:
        prossimo = min(da_visitare, key=lambda x: geodesic(attuale_coords, x['coords']).km)
        percorso.append(prossimo)
        attuale_coords = prossimo['coords']
        da_visitare.remove(prossimo)
    return percorso + senza_coords

st.title("🚚 GLS Brescia Optimizer")
st.caption("Sede: Via della Volta 120, BS")

indirizzo_raw = st.text_input("📍 Via e n° civico:", placeholder="Es: Via Milano 10")

col1, col2 = st.columns(2)

def aggiungi_pacco(tipo):
    if indirizzo_raw:
        with st.spinner('Localizzazione...'):
            indirizzo_completo = f"{indirizzo_raw}, Brescia, Italy"
            try:
                loc = geolocator.geocode(indirizzo_completo, timeout=10)
                coords = (loc.latitude, loc.longitude) if loc else None
                # Pulizia testo per evitare errori Unicode
                testo_pulito = indirizzo_raw.upper().replace("€", "EUR").encode('ascii', 'ignore').decode('ascii')
                st.session_state.pacchi.append({"Dati": testo_pulito, "Tipo": tipo, "coords": coords})
                time.sleep(1)
            except:
                st.error("Riprova tra un secondo...")

with col1:
    if st.button("🟢 AZIENDA", use_container_width=True):
        aggiungi_pacco("A")
        st.rerun()

with col2:
    if st.button("🔴 PRIVATO", type="primary", use_container_width=True):
        aggiungi_pacco("P")
        st.rerun()

if st.session_state.pacchi:
    st.write("---")
    if st.button("🗑️ SVUOTA TUTTO"):
        st.session_state.pacchi = []
        st.rerun()

    if st.button("🚀 GENERA PDF ORDINATO"):
        aziende = [p for p in st.session_state.pacchi if p['Tipo'] == "A"]
        privati = [p for p in st.session_state.pacchi if p['Tipo'] == "P"]

        giro_a = calcola_giro_ottimale(aziende, COORDS_SEDE)
        punto_rip = giro_a[-1]['coords'] if giro_a and giro_a[-1]['coords'] else COORDS_SEDE
        giro_p = calcola_giro_ottimale(privati, punto_rip)
        
        giro_completo = giro_a + giro_p

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.set_text_color(0, 46, 110) 
        pdf.cell(190, 15, "GIRO OTTIMIZZATO - GLS BRESCIA", ln=True, align='C')
        pdf.ln(10)
        
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
            tipo = "AZ " if p['Tipo'] == "A" else "PR "
            # FIX: Usiamo 'replace' per i caratteri che non piacciono al PDF
            testo_riga = f"{tipo}{p['Dati']}".encode('latin-1', 'replace').decode('latin-1')
            pdf.cell(135, 12, f" {testo_riga}", 1, 0, 'L', True)
            pdf.set_text_color(0, 0, 255)
            pdf.cell(40, 12, "NAVIGA", 1, 1, 'C', link=link)
            pdf.set_text_color(0, 0, 0)

        # FIX FINALE: Conversione sicura per il download
        pdf_bytes = pdf.output(dest='S').encode('latin-1', 'replace')
        st.download_button(label="📥 SCARICA PDF", data=pdf_bytes, file_name="Giro_GLS.pdf", mime="application/pdf")
