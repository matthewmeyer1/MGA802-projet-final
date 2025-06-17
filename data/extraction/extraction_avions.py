import pymupdf # imports the pymupdf library
import re
import pandas as pd
from sympy.codegen import Print

def pdf_to_text(pdf_path):
    doc = pymupdf.open(f"{pdf_path}.pdf") # open a document
    text = []
    for page in doc: # iterate the document pages
        text.append(str(page.get_text())) # get plain text encoded as UTF-8
    "".join(text)
    #print(text)
    return text

class autoDict(dict):
    def __missing__(self, key):
        x = autoDict()
        self[key] = x
        return x


def get_plane(file_path):
    text = pdf_to_text(file_path)
    perf_dict = autoDict()
    for page in text:
        if "Recommended Lean Mixture At All Altitudes" in page:

            line = page.split(' \n')

            ind = max(i for i, v in enumerate(line) if v == "BHP")
            table_vals = []
            for line in line[ind+1:]:
                line = line.replace(' .', '.')
                line = line.replace(',', '')

                if 'Figure' in line:
                    break
                table_vals += (line.split(' '))


            table_vals = list(map(float, table_vals))
            print(table_vals)


            ind = 0
            itt_var = 0
            press_alt_ind = 0
            temp = [-20, 0 , 20]
            while ind < len(table_vals):
                if table_vals[ind] + table_vals[ind + 1] >= 4000:
                    press_alt_ind  = ind
                    ind += 1

                for temp_var in range(3):
                    for itt_var in range(3):
                        try:
                            perf_dict[table_vals[press_alt_ind]][table_vals[ind]][temp[temp_var]]['bhp'] = table_vals[ind - 2 + (itt_var + 1) * (temp_var + 1)]
                            perf_dict[table_vals[press_alt_ind]][table_vals[ind]][temp[temp_var]]['ktas'] = table_vals[ind - 1 + (itt_var + 1) * (temp_var + 1)]
                            perf_dict[table_vals[press_alt_ind]][table_vals[ind]][temp[temp_var]]['gph'] = table_vals[ind + (itt_var + 1) * (temp_var + 1)]
                        except IndexError:
                            print(ind + 4 + itt_var * temp_var)
                            print(len(table_vals))

                ind += 10

    print(perf_dict)
    print(perf_dict[10000][2500][0]['ktas'])

    pressure = *perf_dict,

    print(pressure[pressure.index(10000)])


    return 0

get_plane("../ressources/pdf/POH-cessna-182")