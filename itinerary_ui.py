from itinerary import itinerary

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

        it1.add_waypoint(float(input("lat: ")), float(input("lon: ")), name=input("name: "))
    elif choice == 2:
        it1.swap_waypoints(float(input("First index to swap with: ")))
    elif choice == 3:
        it1.remove_waypoint(float(input("Index to remove: ")))
    elif choice == 4:
        it1.write_legs()
    elif choice == 5:
        it1.save_waypoints("wp.csv")
    elif choice == 6:
        it1.load_waypoints("wp.csv")
    elif choice == 0:
        break

    it1.write_waypoints()
