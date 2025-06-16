import fitz  # PyMuPDF
import re
import os
import pandas as pd

# Répertoire contenant les fichiers CFS
pdf_dir = "/mnt/data"

# Expressions régulières pour extraire les données clés
re_code = re.compile(r'^[A-Z]{2}[A-Z0-9]{2,4}')  # Ex: CYUL, CSE4, CAM4
re_location = re.compile(r'REF\s+([N|S]\d{2} \d{2} \d{2})\s+([W|E]\d{3} \d{2} \d{2})')
re_elevation = re.compile(r'Elev\s+(\d{2,4})[´\']')
re_operator = re.compile(r'OPR\s+(.*?)\s+\d{3,4}-\d{3,4}-\d{4}', re.DOTALL)
re_runway = re.compile(r'RWY DATA\s+Rwy\s+([\d/()°]+)\s+([\d]+x\d+)\s+([\w/ ]+)?')
re_fuel = re.compile(r'FUEL\s+([A-Z0-9\-/(), ]+)', re.DOTALL)

def extract_aerodromes_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    data = []
    for page in doc:
        text = page.get_text()
        if 'AERODROME / FACIL' in text or 'AB' in text or 'QC' in text:
            # Tentative d’extraction
            code_match = re_code.search(text)
            location_match = re_location.search(text)
            elev_match = re_elevation.search(text)
            runway_match = re_runway.search(text)
            fuel_match = re_fuel.search(text)
            operator_match = re_operator.search(text)

            info = {
                "Aérodrome": code_match.group(0) if code_match else None,
                "Latitude": location_match.group(1) if location_match else None,
                "Longitude": location_match.group(2) if location_match else None,
                "Élévation (pi)": elev_match.group(1) if elev_match else None,
                "Opérateur": operator_match.group(1).strip() if operator_match else None,
                "Piste": runway_match.group(1) if runway_match else None,
                "Dimensions piste": runway_match.group(2) if runway_match else None,
                "Surface": runway_match.group(3).strip() if runway_match else None,
                "Carburant": fuel_match.group(1).strip() if fuel_match else None,
            }
            if info["Aérodrome"]:
                data.append(info)
    doc.close()
    return data

# Lire tous les fichiers PDF de CFS fournis
cfs_files = [f for f in os.listdir(pdf_dir) if f.endswith(".pdf") and "cfs_" in f]
all_data = []

for file in cfs_files:
    print(f"Traitement : {file}")
    pdf_path = os.path.join(pdf_dir, file)
    ad_data = extract_aerodromes_from_pdf(pdf_path)
    all_data.extend(ad_data)

# Convertir en DataFrame pour manipulation/affichage/exportation
df = pd.DataFrame(all_data)
