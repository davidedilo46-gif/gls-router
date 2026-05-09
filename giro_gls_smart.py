import streamlit as st
from fpdf import FPDF
from datetime import datetime
import urllib.parse

# --- CONFIGURAZIONE PAGINA E ICONA ---
# Usiamo l'URL dell'icona ufficiale GLS per garantire la compatibilità
LOGO_URL = "https://www.gls-italy.com/images/favicon.ico"

st.set_page_config(
    page_title="GLS Router", 
    page_icon=LOGO_URL, 
    layout="centered"
)

# Inserimento dei metadati per "ingannare" il cellulare e fargli usare l'icona GLS
st.markdown(f"""
    <head>
        <link rel="apple-touch-icon" href="{LOGO_URL}">
        <link rel="icon" type="image/x-icon" href="{LOGO_URL}">
        <link rel="shortcut icon" href="{LOGO_URL}">
        <meta name="theme-color" content="#002e6e">
    </head>
    <style>
    /* Sfondo e stile generale */
    .stApp {{ background-color: #ffffff; }}
    
    /* Bottoni arrotondati e grandi per uso con i pollici */
    div.stButton > button {{
        font-weight: bold !important;
        border-radius: 15px !important;
        height: 3.8em !important;
        border: none !important;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.1);
        transition: 0.2s;
    }}
    
    /* Colore Verde per Azienda */
    div.stButton > button[kind="secondary"] {{
        background-color: #28a745 !important;
        color: white !important;
    }}
    
    /* Colore Rosso per Privato */
    div.stButton > button[kind="primary"] {{
        background-color: #dc3545 !important;
        color: white !important;
    }}
    
    /* Colore Blu per il tasto Genera */
    .stDownloadButton > button {{
        background-color: #002e6e !important;
        color: white !important;
        width: 100% !important;
        font-size: 1.2em !important;
    }}

    /* Input box con bordo blu GLS */
    .stTextInput > div > div > input {{
        border: 2px solid #002e6e !important;
        border-radius: 12px !important;
        padding: 10px !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- GESTIONE DATI ---
if 'pacchi' not in st.session_state:
    st.session_state.pacchi = []

# --- INTERFACCIA ---
st.title("🚚 GLS Mobile Router")
st.info("💡 Consiglio: usa il microfono della tastiera per dettare gli indirizzi!")

# Campo inserimento
indirizzo = st.text_input("📍 Digita o detta l'indirizzo:", placeholder="Es: Via Milano 15, Roma")

col1, col2 = st.columns(2)

with col1:
    if st.button("🟢 AZIENDA", use_container_width=True):
        if indirizzo:
            st.session_state.pacchi.append({"Dati": indirizzo.upper(), "Tipo": "A"})
            st.rerun()

with col2:
    if st.button("🔴 PRIVATO", type="primary", use_container_width=True):
        if indirizzo:
            st.session_state.pacchi.append({"Dati": indirizzo.upper(), "Tipo": "P"})
            st.rerun()

# --- ELENCO E GENERAZIONE ---
if st.session_state.pacchi:
    st.write("---")
    st.subheader(f"Lista attuale ({len(st.session_state.pacchi)} colli):")
    
    for i, p in enumerate(st.session_state.pacchi):
        emoji = "🏢" if p['Tipo'] == "A" else "🏠"
        st.write(f"**{i+1}.** {emoji} {p['Dati']}")

    st.write("---")
    
    c_del, c_pdf = st.columns(2)
    
    with c_del:
        if st.button("🗑️ CANCELLA TUTTO", use_container_width=True):
            st.session_state.pacchi = []
            st.rerun()

    with c_pdf:
        # Generazione PDF istantanea
        pdf = FPDF()
        pdf.add_page()
        
        # Titolo PDF
        pdf.set_font("Arial", 'B', 16)
        pdf.set_text_color(0, 46, 110) 
        pdf.cell(190, 15, "TABELLA DI MARCIA GLS", ln=True, align='C')
        pdf.ln(5)
        
        # Intestazioni tabella
        pdf.set_font("Arial", 'B', 10)
        pdf.set_fill_color(0, 46, 110)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(15, 10, "STOP", 1, 0, 'C', True)
        pdf.cell(135, 10, "INDIRIZZO", 1, 0, 'C', True)
        pdf.cell(40, 10, "NAVIGA", 1, 1, 'C', True)
        
        pdf.set_text_color(0, 0, 0)
        
        for i, p in enumerate(st.session_state.pacchi):
            # Crea link per Google Maps
            query = urllib.parse.quote(p['Dati'])
            link = f"https://www.google.com/maps/search/?api=1&query={query}"
            
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(15, 12, str(i+1), 1, 0, 'C')
            pdf.set_font("Arial", size=9)
            pdf.cell(135, 12, f" {p['Dati'][:55]}", 1, 0)
            
            # Bottone cliccabile blu nel PDF
            pdf.set_text_color(0, 0, 255)
            pdf.set_font("Arial", 'U', 9)
            pdf.cell(40, 12, "VAI QUI", 1, 1, 'C', link=link)
            pdf.set_text_color(0, 0, 0)
        
        pdf_bytes = pdf.output(dest='S').encode('latin-1', 'replace')
        
        st.download_button(
            label="🚀 SCARICA PDF",
            data=pdf_bytes,
            file_name=f"Giro_GLS_{datetime.now().strftime('%H%M')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )-
