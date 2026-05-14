import streamlit as st
from fpdf import FPDF
from datetime import datetime
import urllib.parse
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import time

# --- CONFIGURAZIONE SEDE ---
COORDS_SEDE = (45.5147, 10.2285) # Via della Volta 120, Brescia
# User agent unico per evitare blocchi
geolocator = Nominatim(user_agent="gls_brescia_pro_v25")

st.set_page_config(page_title="GLS Delivery Business", layout="centered")

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
    .main-box { background-color: rgba(255, 255, 255, 0.95); padding: 20px; border-radius: 20px; border: 2px solid #002e6e; }
    .metric-container { background-color: #002e6e; padding: 15px; border-radius: 15px; color: white; text-align: center; margin-bottom: 20px;}
    div.stButton > button { font-weight: bold; border-radius: 12px; height: 3.5em; }
    </style>
    """, unsafe_allow_html=True)

def clean_text(text):
    return str(text).encode('latin-1', 'replace').decode('latin-1')

# --- LOGICA DI ORDINAMENTO (FIX CRASH) ---
def get_comune_coords(nome_comune):
    try:
        loc = geolocator.geocode(f"{nome_comune}, BS, Italy", timeout=10)
        return (loc.latitude, loc.longitude) if loc else COORDS_SEDE
    except:
        return COORDS_SEDE

def ordina_giro(lista_punti, punto_partenza):
    if not lista_punti: return []
    
    paesi = {}
    for p in lista_punti:
        c = p['Comune']
        if c not in paesi: paesi[c] = []
        paesi[c].append(p)
    
    giro_completo = []
    posizione_attuale = punto_partenza
    comuni_nomi = list(paesi.keys())
    
    while comuni_nomi:
        # Troviamo il comune più vicino gestendo potenziali errori di geocode
        prox_c = min(comuni_nomi, key=lambda c: geodesic(posizione_attuale, get_comune_coords(c)).km)
        
        rimanenti_comune = paesi[prox_c]
        while rimanenti_comune:
            # Ordina gli stop interni
            p_vicino = min(rimanenti_comune, key=lambda x: geodesic(posizione_attuale, x['coords']).km if x['coords'] else 999)
            giro_completo.append(p_vicino)
            if p_vicino['coords']: posizione_attuale = p_vicino['coords']
            rimanenti_comune.remove(p_vicino)
            
        comuni_nomi.remove(prox_c)
    return giro_completo

# --- INTERFACCIA ---
st.title("🚚 GLS Business Router")

with st.sidebar:
    st.header("⚙️ Paesi di oggi")
    input_c = st.text_input("Comuni (es: Poncarale, Montirone)")
    if st.button("CONFIGURA"):
        st.session_state.comuni_oggi = [c.strip().upper() for c in input_c.split(",")]
        st.rerun()

if st.session_state.comuni_oggi:
    st.markdown(f"<div class='metric-container'><h2>STOP TOTALI: {len(st.session_state.pacchi)}</h2></div>", unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="main-box">', unsafe_allow_html=True)
        c1, c2 = st.columns([2, 1])
        # Etichetta dinamica
        label_via = "🏢 Nome Azienda o Indirizzo:"
        input_dest = c1.text_input(label_via).upper()
        comune = c2.selectbox("🏙️ Comune:", st.session_state.comuni_oggi)
        
        ca, cp = st.columns(2)
        
        # LOGICA AGGIUNTA
        def aggiungi(tipo):
            if input_dest:
                with st.spinner('Ricerca posizione...'):
                    # Se è azienda, cerchiamo il nome dell'attività nel comune
                    query = f"{input_dest}, {comune}, BS, Italy"
                    loc = geolocator.geocode(query, timeout=10)
                    
                    st.session_state.pacchi.append({
                        "Dest": input_dest, 
                        "Comune": comune, 
                        "Tipo": tipo, 
                        "coords": (loc.latitude, loc.longitude) if loc else None
                    })
                    st.rerun()

        if ca.button("🟢 + AZIENDA", use_container_width=True): aggiungi("A")
        if cp.button("🔴 + PRIVATO", use_container_width=True): aggiungi("P")
        st.markdown('</div>', unsafe_allow_html=True)

if st.session_state.pacchi:
    col_del, col_pdf = st.columns([1, 2])
    with col_del:
        if st.button("🗑️ AZZERA"):
            st.session_state.pacchi = []
            st.rerun()

    with col_pdf:
        if st.button("🚀 GENERA PDF BUSINESS", type="primary", use_container_width=True):
            aziende = [p for p in st.session_state.pacchi if p['Tipo'] == "A"]
            privati = [p for p in st.session_state.pacchi if p['Tipo'] == "P"]
            
            giro_a = ordina_giro(aziende, COORDS_SEDE)
            ultimo_p = giro_a[-1]['coords'] if giro_a and giro_a[-1]['coords'] else COORDS_SEDE
            giro_p = ordina_giro(privati, ultimo_p)
            
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
                tag = "AZIENDA" if p['Tipo'] == 'A' else "PRIVATO"
                testo = f" [{tag}] {p['Dest']} - {p['Comune']}"
                pdf.cell(140, 12, clean_text(testo), 1, 0, 'L', True)
                
                pdf.set_text_color(0, 0, 255)
                # Link intelligente: se non ha trovato le coords, usa il testo per la ricerca Maps
                q = urllib.parse.quote(f"{p['Dest']}, {p['Comune']}, BS, Italy")
                pdf.cell(38, 12, "NAVIGA", 1, 1, 'C', link=f"https://www.google.com/maps/search/?api=1&query={q}")
                pdf.set_text_color(0, 0, 0)

            pdf_b = pdf.output(dest='S').encode('latin-1', 'replace')
            st.download_button("📥 SCARICA PDF", pdf_b, "Giro_GLS_Business.pdf")
