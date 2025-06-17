import pandas as pd
from .waypoints import Waypoint
from .legs import Leg
from .data_retrieval import airport_data
import datetime
import pytz
import folium
import numpy as np



class Itinerary:
    def __init__(self):
        self.wp = []
        self.legs = []
        self.start_time = self.get_start_time()



    def save_waypoints(self, filename):
        with open(filename, 'w') as f:
            for w in self.wp:
                for v in vars(w).items():

                    f.write(str(v[1]) + ",")

                f.write("\n")

    def load_waypoints(self, filename):
        self.wp = []
        with open(filename, 'r') as f:
            for line in f:
                data = line.split(',')[:-1]
                print(data)
                self.wp.append(Waypoint(float(data[1]), float(data[2]), name=data[0]))

    def add_airport(self, icao, ap_list, start = True):
        lat, lon, name = airport_data(icao, ap_list)
        if start:
            self.add_waypoint(lat, lon, name, wp_index = 0)
        else:
            self.add_waypoint(lat, lon, name)


    def add_waypoint(self, lat, long, name="", wp_index=None):
        if wp_index is None:
            self.wp.append(Waypoint(lat, long, name))
        else:
            self.wp.insert(wp_index, Waypoint(lat, long, name))


    def remove_waypoint(self, index):
        self.wp.pop(index)

    def swap_waypoints(self, first_index):
        temp = self.wp[first_index]
        self.wp[first_index] = self.wp[first_index + 1]
        self.wp[first_index + 1] = temp

    def write_waypoints(self):
        wp_pd = pd.DataFrame([t.__dict__ for t in self.wp])
        print(wp_pd)

    def write_legs(self):
        self.create_legs()
        leg_pd = pd.DataFrame([s.to_dict() for s in self.legs])
        pd.set_option("display.max_columns", None)
        print(leg_pd)

    def create_legs(self):
        leg_list = []
        for i in range(len(self.wp) - 1):
            leg_list.append(Leg(self.wp[i], self.wp[i + 1], tas=100))
            leg_list[i].calc_wind(self.start_time)
            leg_list[i].calc_speeds()

            if i == 0:
                leg_list[i].calc_time(prev_time = 0)
            else:
                leg_list[i].calc_time(prev_time = leg_list[i - 1].time_tot)

            leg_list[i].calc_fuel_burn(6.7)

        self.legs = leg_list

    def get_start_time(self):
        date = input("Input date in format: MM-DD: ")
        date = date.split("-")
        print(date)
        time = input("Input time in format: HH: ")

        dt = datetime.datetime(2025, int(date[0]), int(date[1]), int(time))
        tz = pytz.timezone('America/Montreal')
        dt = tz.localize(dt)
        dt = dt.astimezone(pytz.utc)
        return dt

    def show_map(self):
        borne = np.zeros((2,2))
        lat = []
        lon = []
        for i in range(len(self.wp)):
            lat.append(self.wp[i].lat)
            lon.append(self.wp[i].lon)

        borne[0,0] = min(lat)
        borne[0,1] = min(lon)
        borne[1,0] = max(lat)
        borne[1,1] = max(lon)
        map_center = [np.mean(borne[:,0]),np.mean(borne[:,1])]
        my_map = folium.Map(
            location = map_center,
            zoom_start = 4,
            tiles='OpenStreetMap',
        )
        for y in self.wp:
            folium.Marker(location = [y.lat,y.lon],
                          popup=f"<b>{y.name}</b><br>"
            ).add_to(my_map)

        my_map.fit_bounds([[borne[0,0],borne[0,1]],[borne[1,0],borne[1,1]]])


        my_map.save('my_map.html')

        return