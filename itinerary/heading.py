import math
tc = 250
tas = 100

wdir = 20
wspeed = 157

y = tas * math.cos(math.radians(tc)) + wspeed * math.cos(math.radians(wdir))
x = tas * math.sin(math.radians(tc)) + wspeed * math.sin(math.radians(wdir))

f = (x ** 2 + y ** 2) ** 0.5
ang = math.degrees(math.acos(y / f))
print(ang)

d = tc + math.degrees(math.asin(wspeed / tas * math.sin(math.radians(tc - (180 + wdir)))))
print(d)