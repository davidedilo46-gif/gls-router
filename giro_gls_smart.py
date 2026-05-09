import streamlit as st
from fpdf import FPDF
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import urllib.parse

# --- CONFIGURAZIONE GRAFICA ---
st.set_page_config(page_title="GLS Smart Router", page_icon="🚚")

st.markdown("""
    <style>
    .stApp { background-color: white; }
    .stButton>button { background-color: #002e6e; color: white; font-weight: bold; border-radius: 10px; width: 100%; }
    .stTextInput>div>div>input { border: 2px solid #002e6e; }
    </style>
    """, unsafe_allow_index=True)

st.title("🚚 GLS Mobile Router")

if 'pacchi' not in st.session_state:
    st.session_state.pacchi = []

geolocator = Nominatim(user_agent="gls_mobile_app")

# --- INPUT ---
indirizzo = st.text_input("📍 Inserisci Via o Azienda (Usa il microfono!)", placeholder="Es: Via Roma 10, Milano")

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
    st.write("### Pacchi in lista:")
    for i, p in enumerate(st.session_state.pacchi):
        st.write(f"{i+1}. {'🏢' if p['Tipo']=='A' else '🏠'} {p['Dati']}")

    if st.button("🗑️ SVUOTA TUTTO"):
        st.session_state.pacchi = []
        st.rerun()

    if st.button("🚀 GENERA PDF CON MAPS"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.set_text_color(0, 46, 110)
        pdf.cell(190, 15, "GIRO CONSEGNE GLS", ln=True, align='C')
        
        pdf.set_font("Arial", size=10)
        pdf.set_text_color(0, 0, 0)
        
        for i, p in enumerate(st.session_state.pacchi):
            query = urllib.parse.quote(p['Dati'])
            link = f"https://www.google.com/maps/search/?api=1&query={query}"
            pdf.cell(15, 10, str(i+1), 1)
            pdf.cell(135, 10, p['Dati'][:50], 1)
            pdf.set_text_color(0, 0, 255)
            pdf.cell(40, 10, "MAPS", 1, 1, 'C', link=link)
            pdf.set_text_color(0, 0, 0)
        
        pdf_output = pdf.output(dest='S').encode('latin-1')
        st.download_button(label="📥 SCARICA PDF", data=pdf_output, file_name="Giro_GLS.pdf", mime="application/pdf")
