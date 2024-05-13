import json
import pathlib
import pickle
import shapely
from shapely.ops import unary_union

from src import mapbox

def load_json(path: str) -> dict:
    """
    path: Path to json file
    
    """

    path_json = pathlib.Path(path)
    with open(path_json, 'r') as file:
        config = json.load(file)

    return config

class Location():
    
    def __init__(self, config):

        self.config = config
        self.polygons = []

    def get_polygons(self, path_cache, mapbox_token):

        if self.config['type'] == 'isochrone':
            
            for c in self.config['coordinates']:

                path_c = '_'.join([
                    self.config['name'].replace(' ', ''),
                    str(c['lat']), str(c['lon']),
                    self.config['profile'], str(self.config['contours_minutes']) + '.pickle'
                    ])
                path_c = pathlib.PurePath(path_cache, path_c)
                path_c = pathlib.Path(path_c)

                polygon = Polygon(c)
                polygon.get_isochrone(path_c, self.config['profile'], c['lat'], c['lon'], self.config['contours_minutes'], mapbox_token)

                self.polygons.append(polygon)

        else:
            pass
            # Add simple polygon

class Polygon():

    def __init__(self, center):

        self.center = center
        self.coords = None

    def get_isochrone(self, path_c, profile, lat, lon, contours_minutes, mapbox_token):

        if path_c.exists():

            with open(path_c, 'rb') as file:
                self.coords = pickle.load(file)

        else:
            self.coords = mapbox.get_mapbox_isochrone_polygon(
                profile = profile,
                lat = lat,
                lon = lon,
                contours_minutes = contours_minutes,
                mapbox_token = mapbox_token
            )

            with open(path_c, 'wb') as file:
                pickle.dump(self.coords, file)        

def prepare_locations(
        path_config: str,
        path_database: str = 'data/database',
        path_cache: str = 'data/cache',
        path_token: str = 'data/tokens/mapbox.txt'        
    ) -> dict:

    """
    ToDo
    """
    
    configuration = load_json(path_config)
    mapbox_token = mapbox.get_token(path_token)

    locations = {}

    for c in configuration['locations']:        

        path_l = pathlib.PurePath(path_database, c['category'] + '.json')
        c.update(load_json(path_l)[c['name']])

        location = Location(c)
        location.get_polygons(path_cache, mapbox_token)
  
        locations[c['name']] = location
    
    return locations

def stack_locations(
        locations: dict,    
    ) -> dict:

    """
    ToDo
    """

    locations_stacked = {}

    # Get all polygons
    for location_name, location in locations.items():

        category = location.config['category']

        if not category in locations_stacked:
            locations_stacked[category] = {'polygons':[]}

        locations_stacked[category]['polygons'] += [shapely.geometry.Polygon(pp)
                                                    for p in location.polygons for pp in p.coords]

    # Stack per category
    for category in locations_stacked.keys():
        locations_stacked[category]['final'] = unary_union(locations_stacked[category]['polygons']).exterior.coords.xy
        locations_stacked[category]['final'] = shapely.geometry.Polygon([[locations_stacked[category]['final'][0][n], locations_stacked[category]['final'][1][n]] 
                                                for n in range(len(locations_stacked[category]['final'][0]))])

    # Combine all 
    list_final = [p['final'] for p in locations_stacked.values()]
    number_of_stacked = len(list_final)
    if number_of_stacked > 0:
        polygon_intersection = list_final[0]
        if number_of_stacked > 1:
            for p in list_final[1:]:
                polygon_intersection = polygon_intersection.intersection(p)
    else:
        polygon_intersection = Polygon([])

    locations_stacked['final'] = polygon_intersection.exterior.coords.xy
    locations_stacked['final'] = shapely.geometry.Polygon([[locations_stacked['final'][0][n], locations_stacked['final'][1][n]] 
                                            for n in range(len(locations_stacked['final'][0]))])

    return locations_stacked