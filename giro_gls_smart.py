import streamlit as st
from fpdf import FPDF
from datetime import datetime
import urllib.parse

# --- CONFIGURAZIONE GRAFICA ---
st.set_page_config(page_title="GLS Smart Router", page_icon="🚚")

# Qui c'era l'errore: ho corretto unsafe_allow_html
st.markdown("""
    <style>
    .stApp { background-color: white; }
    .stButton>button { background-color: #002e6e; color: white; font-weight: bold; border-radius: 10px; width: 100%; height: 3em; }
    .stTextInput>div>div>input { border: 2px solid #002e6e; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚚 GLS Mobile Router")

if 'pacchi' not in st.session_state:
    st.session_state.pacchi = []

# --- INPUT ---
indirizzo = st.text_input("📍 Inserisci Via o Azienda", placeholder="Usa il microfono per fare prima!")

c1, c2 = st.columns(2)
with c1:
    if st.button("🟢 AZIENDA"):
        if indirizzo:
            st.session_state.pacchi.append({"Dati": indirizzo.upper(), "Tipo": "A"})
            st.rerun()
with c2:
    if st.button("🔴 PRIVATO"):
        if indirizzo:
            st.session_state.pacchi.append({"Dati": indirizzo.upper(), "Tipo": "P"})
            st.rerun()

# --- LISTA E PDF ---
if st.session_state.pacchi:
    st.write("---")
    st.write("### Pacchi in lista:")
    for i, p in enumerate(st.session_state.pacchi):
        emoji = "🏢" if p['Tipo'] == "A" else "🏠"
        st.write(f"**{i+1}.** {emoji} {p['Dati']}")

    st.write("---")
    
    col_del, col_pdf = st.columns(2)
    with col_del:
        if st.button("🗑️ SVUOTA TUTTO"):
            st.session_state.pacchi = []
            st.rerun()
            
    with col_pdf:
        # Generazione PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.set_text_color(0, 46, 110)
        pdf.cell(190, 15, "PROGRAMMA CONSEGNE GLS", ln=True, align='C')
        pdf.ln(5)
        
        pdf.set_font("Arial", size=10)
        pdf.set_text_color(0, 0, 0)
        
        for i, p in enumerate(st.session_state.pacchi):
            query = urllib.parse.quote(p['Dati'])
            link = f"https://www.google.com/maps/search/?api=1&query={query}"
            
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(15, 10, f"#{i+1}", 1, 0, 'C')
            pdf.set_font("Arial", size=10)
            pdf.cell(135, 10, f" {p['Dati'][:50]}", 1, 0)
            pdf.set_text_color(0, 0, 255)
            pdf.cell(40, 10, "MAPS", 1, 1, 'C', link=link)
            pdf.set_text_color(0, 0, 0)
        
        pdf_output = pdf.output(dest='S').encode('latin-1')
        st.download_button(label="🚀 SCARICA PDF", data=pdf_output, file_name="Giro_GLS.pdf", mime="application/pdf")
