import math
import random


def random_location_within_radius(center: tuple[float, float], radius_m: float) -> tuple[float, float]:
    """Return a random (lat, lon) within radius_m of the center."""
    if radius_m < 0:
        raise ValueError("radius_m must be non-negative")

    # Sample uniformly over the area of the circle.
    distance = math.sqrt(random.random()) * radius_m
    bearing = random.random() * 2.0 * math.pi

    earth_radius_m = 6371000.0
    delta = distance / earth_radius_m

    center_lat = center[0]
    center_lon = center[1]

    lat1 = math.radians(center_lat)
    lon1 = math.radians(center_lon)

    sin_lat1 = math.sin(lat1)
    cos_lat1 = math.cos(lat1)

    lat2 = math.asin(
        sin_lat1 * math.cos(delta) + cos_lat1 * math.sin(delta) * math.cos(bearing)
    )
    lon2 = lon1 + math.atan2(
        math.sin(bearing) * math.sin(delta) * cos_lat1,
        math.cos(delta) - sin_lat1 * math.sin(lat2),
    )

    return (math.degrees(lat2), math.degrees(lon2))


if __name__ == '__main__':
	BASE_COORDINATES = (41.386931, 2.112104)  # Barcelona, Spain
	print(random_location_within_radius(BASE_COORDINATES, radius_m=500))
    