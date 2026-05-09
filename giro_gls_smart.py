import streamlit as st
from fpdf import FPDF
import urllib.parse

# --- CONFIGURAZIONE PAGINA E ICONA ---
# L'icona che vedi nella scheda del browser
st.set_page_config(page_title="GLS Router", page_icon="🚚", layout="centered")

# Link all'icona per l'installazione su cellulare (G azzurra GLS)
LOGO_URL = "https://www.gls-italy.com/images/favicon.ico"

st.markdown(f"""
    <head>
        <link rel="apple-touch-icon" href="{LOGO_URL}">
        <link rel="icon" href="{LOGO_URL}">
        <meta name="theme-color" content="#002e6e">
    </head>
    <style>
    /* Sfondo e font */
    .stApp {{ background-color: #f8f9fa; }}
    
    /* Stile dei bottoni */
    div.stButton > button:first-child {{
        font-weight: bold;
        border-radius: 12px;
        height: 3.5em;
        transition: 0.3s;
        border: none;
        box-shadow: 0px 4px 6px rgba(0,0,0,0.1);
    }}
    
    /* Colore Bottone Azienda (Verde) */
    div.stButton > button[kind="secondary"]:first-child {{
        background-color: #28a745;
        color: white;
    }}
    
    /* Colore Bottone Privato (Rosso) */
    div.stButton > button[kind="primary"]:first-child {{
        background-color: #dc3545;
        color: white;
    }}
    
    /* Colore Bottone Genera PDF (Blu GLS) */
    .generate-btn > div > button {{
        background-color: #002e6e !important;
        color: white !important;
        width: 100%;
    }}

    /* Input box */
    .stTextInput > div > div > input {{
        border: 2px solid #002e6e;
        border-radius: 10px;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- INIZIALIZZAZIONE DATI ---
if 'pacchi' not in st.session_state:
    st.session_state.pacchi = []

# --- INTERFACCIA ---
st.title("🚚 GLS Mobile Router")
st.write("Dettate gli indirizzi per creare il giro interattivo.")

# Input Indirizzo
indirizzo = st.text_input("📍 Destinatario o Via (Usa il microfono!)", placeholder="Es: Mario Rossi Via Roma 10 Milano")

col1, col2 = st.columns(2)

with col1:
    if st.button("🟢 AZIENDA", use_container_width=True):
        if indirizzo:
            st.session_state.pacchi.append({"Dati": indirizzo.upper(), "Tipo": "A"})
            st.rerun()

with col2:
    # Uso type="primary" per distinguerlo via CSS più facilmente
    if st.button("🔴 PRIVATO", type="primary", use_container_width=True):
        if indirizzo:
            st.session_state.pacchi.append({"Dati": indirizzo.upper(), "Tipo": "P"})
            st.rerun()

# --- VISUALIZZAZIONE LISTA ---
if st.session_state.pacchi:
    st.write("---")
    st.subheader("Lista Carico Corrente:")
    
    for i, p in enumerate(st.session_state.pacchi):
        emoji = "🏢" if p['Tipo'] == "A" else "🏠"
        st.write(f"**{i+1}.** {emoji} {p['Dati']}")

    st.write("---")
    
    c_del, c_pdf = st.columns(2)
    
    with c_del:
        if st.button("🗑️ SVUOTA TUTTO", use_container_width=True):
            st.session_state.pacchi = []
            st.rerun()

    with c_pdf:
        # --- LOGICA GENERAZIONE PDF ---
        pdf = FPDF()
        pdf.add_page()
        
        # Header PDF
        pdf.set_font("Arial", 'B', 16)
        pdf.set_text_color(0, 46, 110) # Blu GLS
        pdf.cell(190, 15, "PROGRAMMA CONSEGNE GLS", ln=True, align='C')
        pdf.ln(5)
        
        # Tabelle Stop
        pdf.set_font("Arial", 'B', 10)
        pdf.set_fill_color(0, 46, 110)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(15, 10, "STOP", 1, 0, 'C', True)
        pdf.cell(135, 10, "INDIRIZZO", 1, 0, 'C', True)
        pdf.cell(40, 10, "MAPS", 1, 1, 'C', True)
        
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Arial", size=10)
        
        for i, p in enumerate(st.session_state.pacchi):
            # Creazione link Google Maps
            query_mappa = urllib.parse.quote(p['Dati'])
            link_maps = f"https://www.google.com/maps/search/?api=1&query={query_mappa}"
            
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(15, 12, str(i+1), 1, 0, 'C')
            pdf.set_font("Arial", size=9)
            pdf.cell(135, 12, f" {p['Dati'][:55]}", 1, 0)
            
            # Link Blu
            pdf.set_text_color(0, 0, 255)
            pdf.set_font("Arial", 'U', 9)
            pdf.cell(40, 12, "NAVIGA", 1, 1, 'C', link=link_maps)
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Arial", '', 9)
        
        pdf_output = pdf.output(dest='S').encode('latin-1', 'replace')
        
        st.download_button(
            label="🚀 SCARICA PDF",
            data=pdf_output,
            file_name=f"Giro_GLS_{datetime.now().strftime('%H%M')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
