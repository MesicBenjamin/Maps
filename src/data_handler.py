import json
import pathlib
import pickle

from shapely.ops import unary_union
from shapely.geometry import Polygon

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
    ) -> dict:

    """
    ToDo
    """
    
    config = load_json(path_config)
    mapbox_token = mapbox.get_token(path_token)

    polygons = {}

    # Loop over directories, each city has its own
    for city, city_value in config.items():        

        polygons[city] = {}

        # Loop over categories for each city (nature, sports, ...)
        for category, category_value in city_value.items():

            polygons[city][category] = {}

            # Loop over all subcategories (parks, lakes, ... for nature)
            for subcategory, subcategory_json in category_value['subcategory'].items():                
                
                path_json = pathlib.PurePath(path_database, city, subcategory + '.json')
                subcategory_config = load_json(path_json)
                polygons[city][category][subcategory] = {}

                # Loop over all locations for a given subcategory
                for polygon_name, polygon_config in subcategory_json.items():

                    polygons[city][category][subcategory][polygon_name] = []

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

                            polygons[city][category][subcategory][polygon_name].append(Polygon(polygon[0]))

                    elif subcategory_config[polygon_name]["type"] == "simple":
                        pass

                    else:
                        pass
    
    return polygons

def stack_polygons(
        polygons: dict,    
    ) -> dict:

    """
    ToDo
    """

    polygons_stacked = {}

    for city, city_value in polygons.items():        

        polygons_stacked[city] = {}

        # Loop over categories for each city (nature, sports, ...)
        for category, category_value in city_value.items():

            polygons_temp = []

            # Loop over all subcategories (parks, lakes, ... for nature)
            for subcategory, subcategory_value in category_value.items():                
                
                # Loop over all locations for a given subcategory
                for polygons_name, polygons in subcategory_value.items():
    
                    for p in polygons:
                        polygons_temp.append(p)

            polygon_union = unary_union(polygons_temp).exterior.coords.xy
            polygon_union = [[polygon_union[0][n], polygon_union[1][n]] for n in range(len(polygon_union[0]))]
            polygons_stacked[city][category] = Polygon(polygon_union)
    
        list_polygons_stacked = list(polygons_stacked[city].values())
        number_of_stacked = len(list_polygons_stacked)
        if number_of_stacked > 0:
            polygon_intersection = list_polygons_stacked[0]
            if number_of_stacked > 1:
                for p in list_polygons_stacked[1:]:
                    polygon_intersection = polygon_intersection.intersection(p)
        else:
            polygon_intersection = Polygon([])

        polygon_intersection_coord = polygon_intersection.exterior.coords.xy
        polygons_stacked[city]['final'] = [[polygon_intersection_coord [0][n], polygon_intersection_coord [1][n]] 
                                                for n in range(len(polygon_intersection_coord[0]))]

    return polygons_stacked