import pymupdf # imports the pymupdf library
import pandas as pd
import re
import os


def dms_to_decimal(dms):
    dms_cleaned = (re.findall("[0-9]+", dms))
    deg = int(dms_cleaned[0])
    min = int(dms_cleaned[1])
    try:
        sec = int(dms_cleaned[2])
    except IndexError:
        sec = 0
    return round(deg + min/60 + sec/3600,4)


def decimal_to_dms(decimal):
    deg = decimal // 1
    min = (decimal - deg) // (1/60)
    sec = (decimal - deg - min/60) // (1/3600)

    return "".join(f"{str(deg)[0:2]} {str(min)[0:2]} {str(sec)[0:2]}")


def pdf_to_text(pdf_path):
    doc = pymupdf.open(f"{pdf_path}") # open a document
    text = []
    for page in doc: # iterate the document pages
        text.append(str(page.get_text())) # get plain text encoded as UTF-8
    "".join(text)
    print(text)
    return str(text)


def extract_airport_info(text):
    info = re.findall(r"\\nC[A-Z][A-Z0-9]{2}\\nREF\\nN[0-9\\n ]{2,8} W[0-9 ]{2,9}", text)
    alt = re.findall(r"UTC-[0-9()/ \\n\u00BD]+Elev [0-9]+", text)
    alt.pop(-1) # Suppresion du dernier élément de la liste

    print(len(info), info)
    print(len(alt), alt)

    lon = ["A"] * len(info)
    lat = ["A"] * len(info)
    airport_name = ["A"] * len(info)

    for i in range(len(info)):
        airport_name[i] = info[i][2:6]

        print(info[i])

        try:
            lat[i] = dms_to_decimal(re.search("N[0-9 ]{5,8}", info[i]).group())
            lon[i] = -dms_to_decimal(re.search("W[0-9 ]{5,8}", info[i]).group())
            alt[i] = re.search("[0-9]{2,}", alt[i]).group()

        except AttributeError:
            continue

    airports = {'lat': lat,
                'lon': lon,
                'alt': alt}

    apdf = pd.DataFrame(airports)
    apdf.index = airport_name

    print(apdf)

    return apdf


def get_airports(file_path):
    text = pdf_to_text(file_path)
    apdf = extract_airport_info(text)

    return apdf


def convert_cfs():
    pdf_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ressources', 'pdf'))
    pdf_files = [f for f in os.listdir(pdf_dir) if f.startswith('cfs_') and f.endswith('.pdf')]

    for pdf in pdf_files:
        print(pdf)
        df = get_airports(os.path.join(pdf_dir, pdf))

        # Build the output CSV path
        csv_filename = pdf.replace('.pdf', '.csv')
        csv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ressources', 'csv', csv_filename))

        # Save the DataFrame
        df.to_csv(csv_path, index=True)

    return


convert_cfs()


# print(len(aeroport_name), aeroport_name)
# print(len(longitude), longitude)
# print(len(lattitude), lattitude)
# print(len(aeroport_name))
