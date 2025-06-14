class Waypoint:
    def __init__(self, lat, lon, name="", alt=0):
        self.name = name
        self.lat = lat
        self.lon = lon
        self.alt = alt


    def to_dict(self):
        return{
            "name": self.name,
            "lat": self.lat,
            "lon": self.lon,
            "alt": self.alt
        }