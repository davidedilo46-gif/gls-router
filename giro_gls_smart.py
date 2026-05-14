import streamlit as st
from fpdf import FPDF
from datetime import datetime
import urllib.parse
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import time

# --- CONFIGURAZIONE ---
COORDS_SEDE = (45.5147, 10.2285) 
geolocator = Nominatim(user_agent="gls_brescia_tag_v27")

st.set_page_config(page_title="GLS Router - Tags", layout="centered")

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

def get_comune_coords(nome_comune):
    try:
        loc = geolocator.geocode(f"{nome_comune}, BS, Italy", timeout=10)
        return (loc.latitude, loc.longitude) if loc else COORDS_SEDE
    except: return COORDS_SEDE

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
        prox_c = min(comuni_nomi, key=lambda c: geodesic(posizione_attuale, get_comune_coords(c)).km)
        rimanenti_comune = paesi[prox_c]
        while rimanenti_comune:
            p_vicino = min(rimanenti_comune, key=lambda x: geodesic(posizione_attuale, x['coords']).km if x['coords'] else 999)
            giro_completo.append(p_vicino)
            if p_vicino['coords']: posizione_attuale = p_vicino['coords']
            rimanenti_comune.remove(p_vicino)
        comuni_nomi.remove(prox_c)
    return giro_completo

# --- INTERFACCIA ---
st.title("🚚 GLS Delivery Smart List")

with st.sidebar:
    st.header("⚙️ Configura Paesi")
    input_c = st.text_input("Comuni di oggi (es: Poncarale, Montirone):")
    if st.button("SALVA"):
        st.session_state.comuni_oggi = [c.strip().upper() for c in input_c.split(",")]
        st.rerun()

if st.session_state.comuni_oggi:
    st.markdown(f"<div class='metric-container'><h2>STOP IN LISTA: {len(st.session_state.pacchi)}</h2></div>", unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="main-box">', unsafe_allow_html=True)
        
        # Spunta per identificare la Busta
        is_busta = st.checkbox("✉️ SEGNA COME BUSTA")
        
        c1, c2 = st.columns([2, 1])
        dest = c1.text_input("🏢 Nome o Via:").upper()
        comune = c2.selectbox("🏙️ Comune:", st.session_state.comuni_oggi)
        
        ca, cp = st.columns(2)
        
        def aggiungi(tipo):
            if dest:
                with st.spinner('Salvataggio...'):
                    query = f"{dest}, {comune}, BS, Italy"
                    loc = geolocator.geocode(query, timeout=10)
                    st.session_state.pacchi.append({
                        "Dest": dest, 
                        "Comune": comune, 
                        "Tipo": tipo,
                        "IsBusta": is_busta,
                        "coords": (loc.latitude, loc.longitude) if loc else None
                    })
                    st.rerun()

        if ca.button("🟢 + AZIENDA"): aggiungi("A")
        if cp.button("🔴 + PRIVATO"): aggiungi("P")
        st.markdown('</div>', unsafe_allow_html=True)

if st.session_state.pacchi:
    if st.button("🗑️ RESET"):
        st.session_state.pacchi = []
        st.rerun()

    if st.button("🚀 GENERA PDF GIRO", type="primary", use_container_width=True):
        aziende = [p for p in st.session_state.pacchi if p['Tipo'] == "A"]
        privati = [p for p in st.session_state.pacchi if p['Tipo'] == "P"]
        
        giro_a = ordina_giro(aziende, COORDS_SEDE)
        ultimo_a = giro_a[-1]['coords'] if giro_a and giro_a[-1]['coords'] else COORDS_SEDE
        giro_p = ordina_giro(privati, ultimo_a)
        
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
            tag_busta = " (BUSTA)" if p['IsBusta'] else ""
            tag_tipo = "AZIENDA" if p['Tipo'] == 'A' else "PRIVATO"
            
            testo = f" [{tag_tipo}] {p['Dest']} - {p['Comune']}{tag_busta}"
            
            # Se è una busta, mettiamo il testo in grassetto o corsivo per farlo saltare all'occhio
            if p['IsBusta']:
                pdf.set_font("Arial", 'BI', 10)
            
            pdf.cell(140, 12, clean_text(testo), 1, 0, 'L', True)
            
            pdf.set_text_color(0, 0, 255)
            q = urllib.parse.quote(f"{p['Dest']}, {p['Comune']}, BS, Italy")
            pdf.cell(38, 12, "NAVIGA", 1, 1, 'C', link=f"https://www.google.com/maps/search/?api=1&query={q}")
            pdf.set_text_color(0, 0, 0)

        pdf_b = pdf.output(dest='S').encode('latin-1', 'replace')
        st.download_button("📥 SCARICA PDF", pdf_b, "Giro_GLS_Smart.pdf")
