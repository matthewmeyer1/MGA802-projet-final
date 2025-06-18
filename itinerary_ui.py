from itinerary.itinerary import Itinerary
import pandas as pd
from data.extraction import extraction
from itinerary.aircraft import Aircraft
from itinerary.plane_logic import write_planes, save_plane, load_plane
from pprint import pprint

#airport_list = extraction.get_airports("data/ressources/pdf/cfs_qc")
#print(airport_list)

it1 = Itinerary()

def ac_menu(plane_list):
    choice = 1
    while choice != 0:
        print("\n1 - Create plane\n" +
              "2 - Load plane\n" +
              "3 - Save plane\n" +
              "0 - Back to main menu\n")

        choice = int(input())

        if choice == 1:
            plane_list.append(Aircraft(input("Tail number: "), input("AC type: "), float(input("Fuel Cap: ")), float(input("Burn rate: ")), input("Equipment: "), float(input("Cruise TAS: ")), float(input("Cruise RPM: "))))
        if choice == 2:
            plane_list.append(load_plane(input("Tail number (file name) of aircraft: "), plane_list, "data/ressources/csv"))
        if choice == 3:
            for i in range(len(plane_list)):
                save_plane(i, plane_list, "data/ressources/csv")

        write_planes(plane_list)

def wp_menu(it1, plane_list):
    write_planes(plane_list)
    plane = plane_list[int(input("Aircraft index: "))]
    pprint(plane.to_dict())

    choice = 1
    while choice != 0:
        print("\n1 - add_waypoint\n" +
              "2 - reorder waypoints\n" +
              "3 - delete waypoints\n" +
              "4 - write legs\n" +
              "5 - Save waypoints\n" +
              "6 - Load waypoints\n" +
              "0 - Back to main menu\n")

        choice = int(input())
        if choice == 1:
            wp_choice = int(input("1 - Starting airport\n" +
                                  "2 - Ending airport\n" +
                                  "3 - waypoint\n"))
            if wp_choice == 1:
                icao = input("ICAO code: ")
                it1.add_airport(icao, airport_list, start=True)
            elif wp_choice == 2:
                icao = input("ICAO code: ")
                it1.add_airport(icao, airport_list, start=False)
            elif wp_choice == 3:
                it1.add_waypoint(float(input("lat: ")), float(input("lon: ")), name=input("name: "),
                                 alt=int(input("alt: ")))
        elif choice == 2:
            it1.swap_waypoints(int(input("First index to swap with: ")))
        elif choice == 3:
            it1.remove_waypoint(int(input("Index to remove: ")))
        elif choice == 4:
            it1.write_legs(plane)
        elif choice == 5:
            it1.save_waypoints("wp.csv")
        elif choice == 6:
            it1.load_waypoints("wp.csv")
        elif choice == 0:
            break

        it1.write_waypoints()

plane_list = []
while True:
    print("\n1 - Aircraft menu\n" +
          "2 - Waypoint menu\n" +

    main_menu_choice = int(input())

    if main_menu_choice == 1:
        ac_menu(plane_list)
    elif main_menu_choice == 2:
        wp_menu(it1, plane_list)
          print("\n1 - add_waypoint\n" +
          "2 - reorder waypoints\n" +
          "3 - delete waypoints\n" +
          "4 - write legs\n" +
          "5 - Save waypoints\n" +
          "6 - Load waypoints\n" +
          "7 - Show map\n" +
          "0 - exit")
    else:
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
    elif choice == 7:
        it1.show_map()
    elif choice == 0:
        break


