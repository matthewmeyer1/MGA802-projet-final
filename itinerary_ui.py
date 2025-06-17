from itinerary import itinerary
import pandas as pd
from data.extraction import extraction

# airports = {'lat': [45.63954, 45.4580, 44.22639],
#             'lon': [-74.37112, -73.7497, -76.59667]}
#
# apd = pd.DataFrame(airports)
# apd.index = ['CSE4', 'CYUL', 'KYGK']

airport_list = extraction.get_airports("data/ressources/pdf/cfs_qc")
print(airport_list)

it1 = itinerary.Itinerary()


while True:
    print("\n1 - add_waypoint\n" +
          "2 - reorder waypoints\n" +
          "3 - delete waypoints\n" +
          "4 - write legs\n" +
          "5 - Save waypoints\n" +
          "6 - Load waypoints\n" +
          "0 - exit")

    choice = int(input())
    if choice == 1:
        wp_choice = int(input("1 - Starting airport\n" +
                              "2 - Ending airport\n" +
                              "3 - waypoint\n"))
        if wp_choice == 1:
            icao = input("ICAO code: ")
            it1.add_airport(icao, airport_list, start = True)
        elif wp_choice == 2:
            icao = input("ICAO code: ")
            it1.add_airport(icao, airport_list, start=False)
        elif wp_choice == 3:
            it1.add_waypoint(float(input("lat: ")), float(input("lon: ")), name=input("name: "), alt=int(input("alt: ")))
    elif choice == 2:
        it1.swap_waypoints(int(input("First index to swap with: ")))
    elif choice == 3:
        it1.remove_waypoint(int(input("Index to remove: ")))
    elif choice == 4:
        it1.write_legs()
    elif choice == 5:
        it1.save_waypoints("wp.csv")
    elif choice == 6:
        it1.load_waypoints("wp.csv")
    elif choice == 0:
        break

    it1.write_waypoints()
