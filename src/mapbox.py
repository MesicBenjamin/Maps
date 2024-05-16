import requests
import pathlib

def get_mapbox_isochrone_coordinates(
    profile: str, 
    lon: float,
    lat: float,
    contours_minutes: int,
    path_mapbox_token: str = 'data/tokens/mapbox.txt', 
    mapbox_link: str = 'https://api.mapbox.com/isochrone/v1/mapbox/{}/{},{}?contours_minutes={}&polygons=true&access_token={}'
    ) -> list:
    """
    profile: The Mapbox routing profile that the query should use. This can be walking for pedestrian and hiking travel times, cycling for travel times by bicycle, or driving for travel times by car.
    lon: Longitude value around which to center the isochrone lines.
    lat: Latitude value around which to center the isochrone lines.
    contours_minutes: Times that describe the duration in minutes of the trip. This can be a comma-separated list of up to four times. The maximum duration is 60 minutes.
    path_mapbox_token: Personal token needed for retrieval is stored in txt file
    mapbox_link: Link for polygon retrieval, values in <> need to be replaced

    returns list of dict of coordinates, one pair example is 0 : {'lat':[], 'lon':[]}
    """

    mapbox_token = get_token(path_mapbox_token)

    assert profile in ['driving', 'walking', 'cycling']
    assert contours_minutes in [5, 10, 20, 30, 40, 50, 60]    
    assert isinstance(lon, float)
    assert isinstance(lat, float)
    assert isinstance(mapbox_token, str)
    assert not mapbox_token == '<Here comes Mapbox API token>'

    link = mapbox_link.format(profile, lon, lat, contours_minutes, mapbox_token)
    link_content = requests.get(link)
    link_content_json = link_content.json()
    polygons_coordinates = link_content_json['features'][0]['geometry']['coordinates']

    polygons_coordinates = [{'lon': [pp[0] for pp in p], 'lat': [pp[1] for pp in p]}
                     for p in polygons_coordinates]

    return polygons_coordinates

def get_token(path: str) -> str:
    """
    path: Path to text file which contains Mapbox token
    
    returns token string
    """

    path_token = pathlib.Path(path)
    token = path_token.read_text()

    return token
