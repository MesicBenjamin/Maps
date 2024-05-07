import json
import pathlib
import pickle

from src import mapbox

def load_json(path: str) -> dict:
    """
    path: Path to json file
    
    """

    path_json = pathlib.Path(path)
    with open(path_json, 'r') as file:
        config = json.load(file)

    return config

def prepare_polygons(
        path_config: str,
        path_database: str = 'data/database',
        path_cache: str = 'data/cache',
        path_token: str = 'data/tokens/mapbox.txt'        
    ) -> None:

    """
    ToDo
    """
    
    config = load_json(path_config)
    mapbox_token = mapbox.get_token(path_token)

    # Loop over directories, each city has its own
    for city, city_value in config.items():
        
        # Loop over categories for each city (nature, sports, ...)
        for category, category_value in city_value.items():

            # Loop over all subcategories (parks, lakes, ... for nature)
            for subcategory, subcategory_json in category_value['subcategory'].items():                
                
                path_json = pathlib.PurePath(path_database, city, subcategory + '.json')
                subcategory_config = load_json(path_json)
               
                # Loop over all locations for a given subcategory
                for polygon_name, polygon_config in subcategory_json.items():

                    if subcategory_config[polygon_name]["type"] == "isochrone":

                        profile = polygon_config['profile']
                        contours_minutes = int(polygon_config['contours_minutes'])

                        # Loop over all coordinates for a given location
                        for coord in subcategory_config[polygon_name]['coordinates']:

                            lat = coord['lat']
                            lon = coord['lon']

                            polygon_filename = '_'.join([city, category, subcategory, polygon_name.replace(' ', ''), str(lat), str(lon), profile, str(contours_minutes) + '.pickle'])
                            path_polygon = pathlib.PurePath(path_cache, polygon_filename)
                            path_polygon = pathlib.Path(path_polygon)

                            if path_polygon.exists():

                                with open(path_polygon, 'rb') as file:
                                    polygon = pickle.load(file)

                            else:
                                polygon = mapbox.get_mapbox_isochrone_polygon(
                                    profile = profile,
                                    lat = lat,
                                    lon = lon,
                                    contours_minutes = contours_minutes,
                                    mapbox_token = mapbox_token
                                )

                                with open(path_polygon, 'wb') as file:
                                    pickle.dump(polygon, file)

                    elif subcategory_config[polygon_name]["type"] == "simple":
                        pass

                    else:
                        pass



