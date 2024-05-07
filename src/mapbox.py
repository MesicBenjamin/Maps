import requests
import pathlib

def get_mapbox_isochrone_polygon(
    profile: str, 
    lon: float,
    lat: float,
    contours_minutes: int,
    mapbox_token: str, 
    mapbox_link: str = 'https://api.mapbox.com/isochrone/v1/mapbox/{}/{},{}?contours_minutes={}&polygons=true&access_token={}'
    ) -> list:
    """
    profile: The Mapbox routing profile that the query should use. This can be walking for pedestrian and hiking travel times, cycling for travel times by bicycle, or driving for travel times by car.
    lon: Longitude value around which to center the isochrone lines.
    lat: Latitude value around which to center the isochrone lines.
    contours_minutes: Times that describe the duration in minutes of the trip. This can be a comma-separated list of up to four times. The maximum duration is 60 minutes.
    mapbox_token: Personal token needed for retrieval
    mapbox_link: Link for polygon retrieval, values in <> need to be replaced

    returns list of coordinates
    """

    assert profile in ['driving', 'walking', 'cycling']
    assert contours_minutes in [10, 20, 30, 40, 50, 60]    
    assert isinstance(lon, float)
    assert isinstance(lat, float)
    assert isinstance(mapbox_token, str)

    link = mapbox_link.format(profile, lon, lat, contours_minutes, mapbox_token)
    link_content = requests.get(link)
    link_content_json = link_content.json()
    polygon = link_content_json['features'][0]['geometry']['coordinates']

    return polygon

def get_token(path: str) -> str:
    """
    path: Path to text file which contains Mapbox token
    
    returns token string
    """

    path_token = pathlib.Path(path)
    token = path_token.read_text()

    return token
