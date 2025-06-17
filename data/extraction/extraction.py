import pymupdf # imports the pymupdf library
import re
import pandas as pd


def dms_to_decimal(dms):
    deg = int(dms[1:4])
    min = int(dms[4:7])
    try:
        sec = int(dms[7:9])
    except ValueError:
        sec = 0
    return round(deg + min/60 + sec/3600,4)


def decimal_to_dms(decimal):
    deg = decimal // 1
    min = (decimal - deg) // (1/60)
    sec = (decimal - deg - min/60) // (1/3600)

    return "".join(f"{str(deg)[0:2]} {str(min)[0:2]} {str(sec)[0:2]}")


def pdf_to_text(pdf_path):
    doc = pymupdf.open(f"{pdf_path}.pdf") # open a document
    text = []
    for page in doc: # iterate the document pages
        text.append(str(page.get_text())) # get plain text encoded as UTF-8
    "".join(text)
    print(text)
    return str(text)


def extract_airport_info(text):
    info = re.findall(".nC[A-Z][A-Z0-9]{2}.nREF.nN[0-9 ]{2,8} W[0-9 ]{2,8}", text)
    alt = re.findall(r"UTC-[0-9() \\n]+Elev [0-9]+", text)
    alt.pop(-1) # Suppresion du dernier élément de la liste

    lon = ["A"] * len(info)
    lat = ["A"] * len(info)
    airport_name = ["A"] * len(info)

    for i in range(len(info)):
        airport_name[i] = info[i][2:6]

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

get_airports("../ressources/pdf/cfs_qc")

# print(len(aeroport_name), aeroport_name)
# print(len(longitude), longitude)
# print(len(lattitude), lattitude)
# print(len(aeroport_name))
