import json
from dataclasses import dataclass
from datetime import datetime
from math import acos, cos, radians, sin
import os
from pathlib import Path
from urllib.request import urlretrieve

from dateutil.parser import parse

URL = "https://bites-data.s3.us-east-2.amazonaws.com/pycons-europe-2019.json"
RESPONSES = "https://bites-data.s3.us-east-2.amazonaws.com/nominatim_responses.json"

tmp = Path(os.getenv("TMP", "/tmp"))
pycons_file = tmp / "pycons-europe-2019.json"
nominatim_responses = tmp / "nominatim_responses.json"

if not pycons_file.exists() or not nominatim_responses.exists():
    urlretrieve(URL, pycons_file)
    urlretrieve(RESPONSES, nominatim_responses)


@dataclass
class PyCon:
    name: str
    city: str
    country: str
    start_date: datetime
    end_date: datetime
    URL: str
    lat: float = None
    lon: float = None


@dataclass
class Trip:
    origin: PyCon
    destination: PyCon
    distance: float


def _get_pycons():
    """Helper function that retrieves required PyCon data
       and returns a list of PyCon objects
    """
    with open(pycons_file, "r", encoding="utf-8") as f:
        return [
            PyCon(
                pycon["name"],
                pycon["city"],
                pycon["country"],
                parse(pycon["start_date"]),
                parse(pycon["end_date"]),
                pycon["url"],
            )
            for pycon in json.load(f)
        ]


def _km_distance(origin, destination):
    """ Helper function that retrieves the air distance in kilometers for two pycons """
    lon1, lat1, lon2, lat2 = map(
        radians, [origin.lon, origin.lat, destination.lon, destination.lat]
    )
    return 6371 * (
        acos(sin(lat1) * sin(lat2) + cos(lat1) * cos(lat2) * cos(lon1 - lon2))
    )


def update_pycons_lat_lon(pycons):
    """
    Update the latitudes and longitudes based on the city and country
    the PyCon takes places. Use requests from the Nominatim API stored in the
    nominatim_responses json file.
    """
    with open(nominatim_responses) as f:
        nominatim = json.loads(f.read())
    for pycon in pycons:
        url = f'https://nominatim.openstreetmap.org/search?q={pycon.city},{pycon.country}&format=json&accept-language=en'
        if url in nominatim:
            pycon.lat = float(nominatim[url][0]['lat'])
            pycon.lon = float(nominatim[url][0]['lon'])
        else:
            raise ValueError(f'{pycon.city},{pycon.country} not found')


def create_travel_plan(pycons):
    """
    Create your travel plan to visit all the PyCons.
    Assume it's now the start of 2019!
    Return a list of Trips with each Trip containing the origin PyCon,
    the destination PyCon and the travel distance between the PyCons.
    """
    return [Trip(p[0], p[1], _km_distance(p[0], p[1]))
            for p in zip(pycons[:-1], pycons[1:])]


def total_travel_distance(journey):
    """
    Return the total travel distance of your PyCon journey in kilometers
    rounded to one decimal.
    """
    return round(sum([t.distance for t in journey]), 1)
