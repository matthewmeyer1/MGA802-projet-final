import pymupdf # imports the pymupdf library
import re


def pdf_to_text(pdf_name):
    doc = pymupdf.open(f"{pdf_name}.pdf") # open a document
    text = []
    for page in doc: # iterate the document pages
        text.append(str(page.get_text())) # get plain text encoded as UTF-8
    "".join(text)
    #print(text)
    return str(text)


def extract_airport_info(text):
    aeroport_name = re.findall("[QC]{2}.nC[A-Z0-9]{3}",text)
    coord = re.findall(".nN[0-9 ]{8} W[0-9 ]{8}",text)


    longitude = ["A"] * len(coord)
    lattitude = ["A"] * len(coord)

    for i in range(len(aeroport_name)):
        aeroport_name[i] = aeroport_name[i][4:]

    for i in range(len(coord)):
        longitude[i] = coord[i][2:11]
        lattitude[i] = coord[i][12:]

    return aeroport_name, longitude, lattitude

def get_airports():
    text = pdf_to_text("data/ressources/pdf/cfs_qc")
    aeroport_name, longitude, lattitude = extract_airport_info(text)

    return aeroport_name, longitude, lattitude

    # print(len(aeroport_name), aeroport_name)
    # print(len(longitude), longitude)
    # print(len(lattitude), lattitude)
    #
    # print(len(aeroport_name))
    # print(len(longitude))
    # print(len(lattitude))


