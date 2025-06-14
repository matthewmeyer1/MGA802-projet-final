import math
from geopy.distance import geodesic
import requests
import json
import datetime
import geomag



class Leg:

    def __init__(self, starting_wp, ending_wp, name="", tas=0):
        self.starting_wp = starting_wp
        self.ending_wp = ending_wp
        self.distance = self.calc_dist()
        self.tc = self.calc_tc()
        self.wind_dir = 0
        self.wind_speed = 0
        self.time_start = 0
        self.th = 0
        self.mh = 0
        self.wca = 0
        self.gs = 0
        self.tas = tas
        self.time_leg = 0
        self.time_tot = 0
        self.fuel_burn_leg = 0
        self.fuel_burn_total = 0


        if name=="":
            self.name = self.starting_wp.name
        else:
            self.name = name



    def calc_dist(self):
        return geodesic((self.starting_wp.lat, self.starting_wp.lon), (self.ending_wp.lat, self.ending_wp.lon)).nm

    def calc_tc(self):
        lat1 = math.radians(self.starting_wp.lat)
        lat2 = math.radians(self.ending_wp.lat)


        del_lon = math.radians(self.ending_wp.lon) - math.radians(self.starting_wp.lon)
        y = math.sin(del_lon) * math.cos(lat2)
        x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(del_lon)
        brng = math.atan2(y, x)
        brng = math.degrees(brng)
        return (brng + 360) % 360

    def calc_wind(self, time, windspeed = None, winddirection = None):
        url = ("https://api.tomorrow.io/v4/weather/forecast?location=" + str((self.ending_wp.lat + self.starting_wp.lat) / 2) +
               "%2C%20" + str((self.ending_wp.lon + self.starting_wp.lon) / 2) + "&timesteps=hourly&apikey=CmIKizbzjlLBf8XngqoIAU271bBYNZbk")
        headers = {
            "accept": "application/json",
            "accept-encoding": "deflate, gzip, br"
        }

        if not windspeed is None:
            self.wind_speed = windspeed
            if not winddirection is None:
                self.wind_dir = winddirection
        else:
            response = requests.get(url, headers=headers)
            json_str = json.loads(response.text)
            for x in json_str["timelines"]["hourly"]:
                if x["time"] == "2025-" + str(time.month).zfill(2) + "-" + str(time.day).zfill(2) + "T" + str(time.hour).zfill(2) + ":00:00Z":
                    print("Found weather")
                    self.time_start = x["time"]
                    self.wind_dir = x["values"]["windDirection"]
                    self.wind_speed = x["values"]["windSpeed"] * 1.943844

    def calc_th(self):
        self.wca = math.degrees(math.asin(self.wind_speed / self.tas * math.sin(math.radians(self.tc - (180 + self.wind_dir)))))
        self.th = self.tc + self.wca

    def calc_mh(self):
        self.mh = geomag.mag_heading(self.th, (self.ending_wp.lat + self.starting_wp.lat) / 2, (self.ending_wp.lon + self.starting_wp.lon) / 2)

    def calc_gs(self):
        self.gs = (self.tas ** 2 + self.wind_speed ** 2 - (2 * self.tas * self.wind_speed * math.cos(math.radians(self.tc) - math.radians(self.wind_dir) + math.radians(self.wca)))) ** (1/2)

    def calc_time(self, prev_time):
        self.time_leg = self.distance / self.gs * 60

        self.time_tot = self.time_leg + prev_time

    def calc_speeds(self):
        self.calc_th()
        self.calc_mh()
        self.calc_gs()

    def calc_fuel_burn(self, burn_rate):
        self.fuel_burn_leg = self.time_leg * burn_rate / 60

        self.fuel_burn_total = self.time_tot * burn_rate / 60

    def to_dict(self):
        return {'Starting WP': self.starting_wp.name,
               'Ending WP': self.ending_wp.name,
               'Distance (NM)': self.distance,
               'Time start': self.time_start,
               'Wind Direction (deg)': self.wind_dir,
               'Wind Speed (kn)': self.wind_speed,
               'True course (deg)': self.tc,
               'True heading (deg)': self.th,
               'Magnetic heading (deg)': self.mh,
               'Groundspeed (kn)': self.gs,
                'Leg time (min)': self.time_leg,
                'Total time (min)': self.time_tot,
                'Fuel burn leg (gal)': self.fuel_burn_leg,
                'Fuel burn tot (gal)': self.fuel_burn_total}