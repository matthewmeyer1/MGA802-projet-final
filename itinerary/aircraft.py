

class Aircraft:
    def __init__(self, tail_num = "", ac_type = "", fuel_cap = 0, burn_rate = 0, equipment = "", cruise_tas = 0, cruise_rpm = 0, climb_tas = 0, climb_rpm = 0):
        self.tail_num = tail_num
        self.ac_type = ac_type
        self.fuel_cap = fuel_cap
        self.burn_rate = burn_rate
        self.equipment = equipment
        self.climb_tas = climb_tas
        self.climb_rpm = climb_rpm
        self.cruise_tas = cruise_tas
        self.cruise_rpm = cruise_rpm

    def load_AC_data(self, folder_name):
        return None
    #def save_AC_data(self, folder_name):

    def to_dict(self):
        return {'Tail Number': self.tail_num,
                'AC type': self.ac_type,
                'Fuel Cap': self.fuel_cap,
                'Burn Rate': self.burn_rate,
                'Equipment': self.equipment,
                'Cruise TAS': self.cruise_tas,
                'Cruise RPM': self.cruise_rpm,
                'Climb Tas': self.climb_tas,
                'Climb RPM': self.climb_rpm,}
