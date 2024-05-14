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

def check_polygons(polygon) -> list:

    """
    path: Shapely Polygon or MultiPolygon objects

    returns list of Polygon objects
    """
    
    if polygon.geom_type == 'Polygon':
        return [polygon]
    elif polygon.geom_type == 'MultiPolygon':
        return list(polygon.geoms)

def convert_shapely_polygon(polygon) -> dict:

    polygon_exterior = polygon.exterior.xy

    return {
        'lon' : [l for l in polygon_exterior[0]],        
        'lat' : [l for l in polygon_exterior[1]]
    }


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
                polygon.get_mapbox_isochrone(path_c, self.config['profile'], c['lat'], c['lon'], self.config['contours_minutes'], mapbox_token)
                polygon.get_shapely_polygons()

                self.polygons.append(polygon)

        else:
            pass
            # Add simple polygon

class Polygon():

    def __init__(self, center):

        self.center = center
        self.mapbox_coords = []
        self.shapely_polygons = []

    def get_mapbox_isochrone(self, path_c, profile, lat, lon, contours_minutes, mapbox_token):

        if path_c.exists():

            with open(path_c, 'rb') as file:
                self.mapbox_coords = pickle.load(file)

        else:
            self.mapbox_coords = mapbox.get_mapbox_isochrone_polygon(
                profile = profile,
                lat = lat,
                lon = lon,
                contours_minutes = contours_minutes,
                mapbox_token = mapbox_token
            )

            with open(path_c, 'wb') as file:
                pickle.dump(self.mapbox_coords, file)        

    def get_shapely_polygons(self):

        for c in self.mapbox_coords:
            self.shapely_polygons += check_polygons(shapely.geometry.Polygon(c))

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

        name = ' | '.join([c['name'], c['profile'], str(c['contours_minutes'])])

        locations[name] = location
    
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
            locations_stacked[category] = {'shapely_polygons':[]}

        locations_stacked[category]['shapely_polygons'] += [pp for p in location.polygons for pp in p.shapely_polygons]

    # Stack per category
    for category in locations_stacked.keys():
        locations_stacked[category]['final_shapely_polygon'] = check_polygons(unary_union(locations_stacked[category]['shapely_polygons']))
        # locations_stacked[category]['final'] = shapely.geometry.Polygon([[locations_stacked[category]['final'][0][n], locations_stacked[category]['final'][1][n]] 
        #                                         for n in range(len(locations_stacked[category]['final'][0]))])

    # Combine all 
    polygon_intersection = None
    for p in locations_stacked.values():
        for pp in p['final_shapely_polygon']:

            if polygon_intersection is None:
                polygon_intersection = pp
            else:
                polygon_intersection = polygon_intersection.intersection(pp)


    locations_stacked['final_shapely_polygon'] = check_polygons(polygon_intersection)
    
    # locations_stacked['final'] = shapely.geometry.Polygon([[locations_stacked['final'][0][n], locations_stacked['final'][1][n]] 
    #                                         for n in range(len(locations_stacked['final'][0]))])

    return locations_stacked