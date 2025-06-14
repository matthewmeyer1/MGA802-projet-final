


def airport_data(icao, airport_list):
    print(airport_list.at[icao, "lat"])
    return airport_list.at[icao, "lat"], airport_list.at[icao, "lon"], icao