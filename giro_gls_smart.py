import customtkinter as ctk
from PIL import Image
from fpdf import FPDF
from datetime import datetime
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import os
import sys
import urllib.parse # Nuova: serve per i link di Google Maps

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class AppGLS(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("GLS Smart Router v3.0")
        self.geometry("750x700")
        self.configure(fg_color="#ffffff")
        
        self.pacchi_aziende = []
        self.pacchi_privati = []
        self.geolocator = Nominatim(user_agent="gls_optimizer_v3")

        # Header
        self.header = ctk.CTkFrame(self, height=100, fg_color="#002e6e", corner_radius=0)
        self.header.pack(fill="x")

        # Logo e Titolo
        try:
            path_logo = resource_path("logo_gls.png")
            img = Image.open(path_logo)
            self.logo_img = ctk.CTkImage(light_image=img, dark_image=img, size=(80, 80))
            ctk.CTkLabel(self.header, image=self.logo_img, text="").place(relx=0.1, rely=0.5, anchor="center")
        except: pass

        ctk.CTkLabel(self.header, text="GLS INTERACTIVE ROUTER", font=("Arial", 28, "bold"), text_color="white").place(relx=0.55, rely=0.5, anchor="center")

        # Icona Finestra
        path_icona = resource_path("logo_gls.ico")
        if os.path.exists(path_icona): self.after(200, lambda: self.iconbitmap(path_icona))

        # Input
        self.entry = ctk.CTkEntry(self, width=500, height=45, placeholder_text="Indirizzo o Nome Azienda...")
        self.entry.pack(pady=20)

        # Bottoni
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=10)
        ctk.CTkButton(btn_frame, text="AZIENDA (Verde)", fg_color="#28a745", command=lambda: self.aggiungi("A")).grid(row=0, column=0, padx=10)
        ctk.CTkButton(btn_frame, text="PRIVATO (Rosso)", fg_color="#dc3545", command=lambda: self.aggiungi("P")).grid(row=0, column=1, padx=10)

        # Console
        self.console = ctk.CTkTextbox(self, width=650, height=200)
        self.console.pack(pady=20)
        
        # Genera
        ctk.CTkButton(self, text="GENERA PDF CON LINK MAPS", fg_color="#002e6e", width=400, height=50, command=self.genera).pack(pady=20)

    def aggiungi(self, tipo):
        dati = self.entry.get().strip().upper()
        if not dati: return
        self.console.insert("end", f"Ricerca: {dati}...\n")
        self.update()
        try:
            loc = self.geolocator.geocode(f"{dati}, Italia", timeout=10)
            coords = (loc.latitude, loc.longitude) if loc else None
        except: coords = None
        
        pacco = {"Dati": dati, "Tipo": tipo, "coords": coords}
        if tipo == "A": self.pacchi_aziende.append(pacco)
        else: self.pacchi_privati.append(pacco)
        
        self.console.insert("end", f"✅ Aggiunto! (GPS: {'OK' if coords else 'NO'})\n")
        self.entry.delete(0, 'end')

    def genera(self):
        # Ordinamento (semplificato)
        giro = self.pacchi_aziende + self.pacchi_privati
        
        desktop = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
        cartella = os.path.join(desktop, "GIRI_GLS")
        if not os.path.exists(cartella): os.makedirs(cartella)

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(190, 10, "GIRO GLS CLICCABILE", ln=True, align='C')
        pdf.ln(10)

        # Tabella
        pdf.set_font("Arial", 'B', 10)
        pdf.set_fill_color(0, 46, 110)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(15, 10, "STOP", 1, 0, 'C', True)
        pdf.cell(135, 10, "DESTINAZIONE", 1, 0, 'C', True)
        pdf.cell(40, 10, "NAVIGATORE", 1, 1, 'C', True)

        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Arial", size=9)

        for i, p in enumerate(giro):
            # Crea Link Google Maps
            query = urllib.parse.quote(p['Dati'])
            link = f"https://www.google.com/maps/search/?api=1&query={query}"
            
            pdf.cell(15, 12, str(i+1), 1, 0, 'C')
            pdf.cell(135, 12, f" {p['Dati'][:55]}", 1, 0)
            pdf.set_text_color(0, 0, 255) # Blu per il link
            pdf.cell(40, 12, "APRI MAPS", 1, 1, 'C', link=link)
            pdf.set_text_color(0, 0, 0)

        nome_file = os.path.join(cartella, f"Giro_{datetime.now().strftime('%H%M')}.pdf")
        pdf.output(nome_file)
        os.startfile(nome_file)
        self.destroy()

if __name__ == "__main__":
    AppGLS().mainloop()