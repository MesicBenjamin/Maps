import json
import pathlib
import pickle
import shapely
from shapely.ops import unary_union
from matplotlib.patches import Ellipse

from src import mapbox

def load_json(path: str) -> dict:
    """
    path: Path to json file
    
    """

    path_json = pathlib.Path(path)
    with open(path_json, 'r') as file:
        config = json.load(file)

    return config

def convert_coords_to_shapely_polygon(coords: dict) -> list:
    """
    ToDo
    """

    coords_temp = [[lon, lat] for lon, lat in zip(coords['lon'], coords['lat'])]
    shapely_polygon = shapely.Polygon(coords_temp)

    return shapely_polygon

def convert_coords_to_shapely_line(coords: dict, buffer_distance: float) -> list:
    """
    ToDo
    """

    coords_temp = [[lon, lat] for lon, lat in zip(coords['lon'], coords['lat'])]
    shapely_line = shapely.LineString(coords_temp)
    shapely_line = shapely_line.buffer(buffer_distance)

    return shapely_line

def convert_coords_to_shapely_circle(coords: dict, radius_distance: float) -> list:
    """
    ToDo
    """

    center_lon = coords['lon'][0]
    center_lat = coords['lat'][0]
    width = radius_distance
    height = radius_distance*0.75

    # first draw the ellipse using matplotlib
    matplotlib_ellipse = Ellipse((center_lon, center_lat), width, height, angle=0) 
    shapely_ellipse = shapely.Polygon(matplotlib_ellipse.get_verts())

    # shapely_circle = shapely.geometry.point.Point(coords['lon'], coords['lat'])
    # shapely_circle = shapely_circle.buffer(radius_distance)

    return shapely_ellipse

def convert_shapely_line_to_shapely_polygon(shapely_line: shapely.LineString) -> shapely.Polygon:

    """
    ToDo
    """
    shapely_line_coords = shapely_line.coords.xy
    coords = [[lon, lat] for lon, lat in zip(shapely_line_coords[0], shapely_line_coords[1])]
    shapely_polygon = shapely.Polygon(coords)

    return shapely_polygon

# -----------------------------------------------

class Location():
    
    def __init__(self, config : dict):
        """
        ToDo
        """

        self.config = config
        self.polygons = []

        name_attributes = ['name', 'profile', 'contours_minutes', 'buffer_distance']
        name_list = [str(config[a]) for a in name_attributes if a in config]
        self.name = '_'.join(name_list)

        self.get_polygons()

    def get_polygons(self,
            path_cache: str='data/cache'
        ):
        """
        ToDo
        """        

        pathlib.Path(path_cache).mkdir(parents=True, exist_ok=True)

        if self.config['type'] == 'isochrone':
            
            for coord in self.config['coordinates']:

                path_coord = '_'.join([self.name, str(coord['lat']), str(coord['lon']) + '.pkl'])
                path_coord = pathlib.PurePath(path_cache, path_coord)
                path_coord = pathlib.Path(path_coord)

                polygon = Polygon([coord])
                polygon.get_mapbox_isochrone_coordinates(
                    path_coord,
                    self.config['profile'],
                    coord['lat'], coord['lon'],
                    self.config['contours_minutes'],
                )
                polygon.get_shapely_polygons_from_mapbox_coords()

                self.polygons.append(polygon)

        elif self.config['type'] == 'line':
            polygon = Polygon(self.config['coordinates'])
            polygon.get_shapely_polygons_from_line(self.config['buffer_distance'])
            self.polygons.append(polygon)

        elif self.config['type'] == 'circle':
            polygon = Polygon(self.config['coordinates'])
            polygon.get_shapely_polygons_from_circle(self.config['radius'])
            self.polygons.append(polygon)

        else:
            polygon = Polygon(self.config['coordinates'])
            polygon.get_shapely_polygons_standard()
            self.polygons.append(polygon)            

class Polygon():

    def __init__(
            self,
            center: list = [{'lat': [], 'lon': []}],
            mapbox_coords: list = [{'lat': [], 'lon': []}],
            shapely_polygons: list = []
        ):
        """
        ToDo
        """        

        self.center = center
        self.mapbox_coords = mapbox_coords
        self.shapely_polygons = shapely_polygons

    def get_mapbox_isochrone_coordinates(self, 
            path_c: pathlib.Path,
            profile: str,
            lat: float,
            lon: float,
            contours_minutes: int
        ):
        """
        ToDo
        """

        if path_c.exists():

            with open(path_c, 'rb') as file:
                self.mapbox_coords = pickle.load(file)

        else:
            self.mapbox_coords = mapbox.get_mapbox_isochrone_coordinates(
                profile = profile,
                lat = lat,
                lon = lon,
                contours_minutes = contours_minutes,
            )

            with open(path_c, 'wb') as file:
                pickle.dump(self.mapbox_coords, file)        

    def get_shapely_polygons_from_line(self, buffer_distance):
        """
        ToDo
        """  

        coords = {
            'lat' : [coord['lat'] for coord in self.center],
            'lon' : [coord['lon'] for coord in self.center],
        }

        self.shapely_polygons = [convert_coords_to_shapely_line(coords, buffer_distance)] 

    def get_shapely_polygons_from_circle(self, buffer_radius):
        """
        ToDo
        """  

        coords = {
            'lat' : [coord['lat'] for coord in self.center],
            'lon' : [coord['lon'] for coord in self.center],
        }

        self.shapely_polygons = [convert_coords_to_shapely_circle(coords, buffer_radius)] 

    def get_shapely_polygons_standard(self):
        """
        ToDo
        """  

        coords = {
            'lat' : [coord['lat'] for coord in self.center],
            'lon' : [coord['lon'] for coord in self.center],
        }

        shapely_polygon = convert_coords_to_shapely_polygon(coords)
        self.shapely_polygons = [shapely_polygon]

    def get_shapely_polygons_from_mapbox_coords(self):
        """
        ToDo
        """        
        self.shapely_polygons = []

        for coord in self.mapbox_coords:
            shapely_polygon = convert_coords_to_shapely_polygon(coord)
            self.shapely_polygons.append(shapely_polygon)

class Map():

    def __init__(self, path_config):
        """
        ToDo
        """

        self.configuration = load_json(path_config)

        self.locations = {}
        self.prepare_locations()

        self.locations_stacked = {}
        self.stack_locations()

    def prepare_locations(
            self,
            path_database: str = 'data/database',   
        ) -> None:

        """
        ToDo
        """
        
        for config in self.configuration['locations']:        

            self.update_config_with_database_coordinates(config, path_database)

            location = Location(config)
            self.locations[location.name] = location
    
    def update_config_with_database_coordinates(
            self,
            config: dict,
            path_database: str
        ) -> None:
        """
        ToDo
        """

        path_l = pathlib.PurePath(path_database, config['category'] + '.json')
        c_json = load_json(path_l)
        c_coordinates = c_json[config['name']]
        config.update(c_coordinates)

    def stack_locations(
            self,   
        ) -> None:

        """
        ToDo
        """

        # Get all polygons
        for location_name, location in self.locations.items():

            category = location.config['category']

            if not category in self.locations_stacked:
                self.locations_stacked[category] = {'shapely_polygons':[]}

            self.locations_stacked[category]['shapely_polygons'] += [shapely_polygon for polygon in location.polygons
                                                                        for shapely_polygon in polygon.shapely_polygons]

        # Stack per category
        for category in self.locations_stacked.keys():
            stacked_polygons = unary_union(self.locations_stacked[category]['shapely_polygons'])
            self.locations_stacked[category]['final_shapely_polygon'] = stacked_polygons

        # Combine all 
        final_shapely_polygon = None
        for logic, logic_categories in self.configuration['logic'].items():
            for category, category_shapely_polygons in self.locations_stacked.items():

                if not category in logic_categories:
                    continue

                if category_shapely_polygons['final_shapely_polygon'] is None:
                    continue

                shapely_polygon = category_shapely_polygons['final_shapely_polygon']
                    
                if final_shapely_polygon is None:
                    final_shapely_polygon = shapely_polygon
                    continue

                if logic == 'union':
                    final_shapely_polygon = unary_union([final_shapely_polygon, shapely_polygon])
                elif logic == 'intersection':
                    final_shapely_polygon = final_shapely_polygon.intersection(shapely_polygon)
                elif logic == 'difference':
                    final_shapely_polygon = final_shapely_polygon.difference(shapely_polygon)
                else:
                    pass
                
        self.locations_stacked['final_shapely_polygon'] = final_shapely_polygon