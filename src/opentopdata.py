import requests
import time
import numpy as np

def get_altitudes(
        config: dict,
        api_batch_size : int = 100,
        api_time_sleep : int = 1,
        link_opentodata : str = "https://api.opentopodata.org/v1/aster30m?locations={}"
    ) -> dict:
    """
    Fetches altitude data for a set of coordinates from the OpenTopoData API.

    Parameters:
    config (dict): Configuration dictionary containing the following keys:
        'top_left' (tuple): The latitude and longitude of the top left point of the area of interest.
        'bottom_right' (tuple): The latitude and longitude of the bottom right point of the area of interest.
        'n_points_lon' (int): The number of points to sample along the longitude.
        'n_points_lat' (int): The number of points to sample along the latitude.

    api_batch_size (int, optional): The number of API requests to send at once. Maximum is 100.
    api_time_sleep (int, optional): The time in seconds to wait between API requests. Minimum is 1 second.
    link_opentodata (str, optional): The URL of the OpenTopoData API endpoint. 

    Returns:
    dict: A dictionary containing the following keys:
        'lon' (list): The longitudes of the sampled points.
        'lat' (list): The latitudes of the sampled points.
        'altitude' (list): The altitudes of the sampled points.
    """

    lon_linspace = np.linspace(config['top_left']['lon'], config['bottom_right']['lon'], config['n_points_lon'])
    lat_linspace = np.linspace(config['top_left']['lat'], config['bottom_right']['lat'], config['n_points_lat'])
    lon_mesh, lat_mesh = np.meshgrid(lon_linspace, lat_linspace)

    # Add longitude shift to get hex
    lon_mesh[::2] +=  (lon_linspace[1] - lon_linspace[0])*0.5

    lon_coords = lon_mesh.flatten()
    lat_coords = lat_mesh.flatten()

    lon_batches = lon_coords.reshape(-1, api_batch_size)
    lat_batches = lat_coords.reshape(-1, api_batch_size)

    coords = {
        'lon' : [],
        'lat' : [],
        'altitude' : []
    }

    for lon_batch, lat_batch in zip(lon_batches, lat_batches):

        lon_lat = ' | '.join([ '{},{}'.format(llat, llon) for llon, llat in zip(lon_batch, lat_batch)])
        link = link_opentodata.format(lon_lat)
        
        try:
            link_content = requests.get(link).json()
        except requests.exceptions.RequestException as e:
            print(f"An error occurred: {e}")
            continue

        for p in link_content['results']:

            coords['lat'].append(p['location']['lat'])
            coords['lon'].append(p['location']['lng'])
            coords['altitude'].append(p['elevation'])       

        time.sleep(api_time_sleep)

    return coords