
def airport_data(icao, airport_list):
    return airport_list.at[icao, "lat"], airport_list.at[icao, "lon"], icao