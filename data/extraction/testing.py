import numpy as np
from scipy.interpolate import RegularGridInterpolator

def interpolation_function(altitude_before, altitude_after, temp_before, temp_after, rpm_bef, rpm_after, ):
    altitude = np.array([altitude_before, altitude_after])
    temperature = np.array([temp_before, temp_after])
    rpm = np.array([rpm_bef, rpm_after])
    inter_func = RegularGridInterpolator((altitude, rpm, temperature), y)
