from math import radians, sin, cos, sqrt, atan2

def distance_meters(lat1, lon1, lat2, lon2):
    """Great-circle distance using the Haversine formula."""
    earth_radius = 6_371_000
    p1, p2 = radians(float(lat1)), radians(float(lat2))
    dp = radians(float(lat2) - float(lat1))
    dl = radians(float(lon2) - float(lon1))
    a = sin(dp / 2) ** 2 + cos(p1) * cos(p2) * sin(dl / 2) ** 2
    return earth_radius * 2 * atan2(sqrt(a), sqrt(1 - a))

def inside_geofence(lat, lon, campus_lat, campus_lon, radius):
    distance = distance_meters(lat, lon, campus_lat, campus_lon)
    return distance <= float(radius), round(distance, 1)
