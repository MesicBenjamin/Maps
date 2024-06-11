import json
import pathlib
import pickle
import shapely
import pandas as pd
from shapely.ops import unary_union
from matplotlib.patches import Ellipse
from scipy.spatial import Voronoi
from collections import defaultdict

from src import mapbox
from src import opentopdata

def load_json(path: str) -> dict:
    """
    Loads a JSON file from the given path.

    Parameters:
    path str: The path to the JSON file.

    Returns:
    dict: The loaded JSON data as a dictionary. If the file does not exist, returns an empty dictionary.
    """
    path_json = pathlib.Path(path)

    if not path_json.exists():
        return {}

    try:
        with open(path_json, 'r') as file:
            config = json.load(file)
    except json.JSONDecodeError:
        raise ValueError(f"File {path} is not a valid JSON file")

    return config

def convert_coords_to_shapely_polygon(coords: dict[str, list]) -> shapely.Polygon:
    """
    Converts coordinates to a Shapely Polygon.

    Parameters:
    coords (dict): A dictionary with 'lon' and 'lat' keys containing lists of longitudes and latitudes respectively.

    Returns:
    Polygon: A Shapely Polygon object.
    """
    if 'lon' not in coords or 'lat' not in coords:
        raise ValueError("Input dictionary must have 'lon' and 'lat' keys")

    coords_temp = [(lon, lat) for lon, lat in zip(coords['lon'], coords['lat'])]
    shapely_polygon = shapely.Polygon(coords_temp)

    return shapely_polygon

def convert_coords_to_shapely_line(coords: dict[str, list], buffer_distance: float) -> shapely.LineString:
    """
    Converts coordinates to a Shapely LineString and applies a buffer.

    Parameters:
    coords (dict): A dictionary with 'lon' and 'lat' keys containing lists of longitudes and latitudes respectively.
    buffer_distance (float): The buffer distance to apply to the LineString.

    Returns:
    LineString: A buffered Shapely LineString object.
    """
    if 'lon' not in coords or 'lat' not in coords:
        raise ValueError("Input dictionary must have 'lon' and 'lat' keys")

    coords_temp = [(lon, lat) for lon, lat in zip(coords['lon'], coords['lat'])]
    shapely_line = shapely.LineString(coords_temp)
    shapely_line = shapely_line.buffer(buffer_distance)

    return shapely_line

def convert_coords_to_shapely_ellipse(coords: dict, radius_distance: float) -> shapely.Polygon:
    """
    Converts coordinates to a Shapely ellipse.

    Parameters:
    coords (dict): A dictionary containing longitude and latitude.
    radius_distance (float): The radius distance for the ellipse.

    Returns:
    Polygon: A Shapely Polygon object representing the ellipse.
    """

    center_lon = coords['lon'][0]
    center_lat = coords['lat'][0]
    ellipse_width = radius_distance
    ellipse_height = radius_distance * 0.75

    # Draw the ellipse using matplotlib
    matplotlib_ellipse = Ellipse((center_lon, center_lat), ellipse_width, ellipse_height, angle=0) 
    shapely_polygon = shapely.Polygon(matplotlib_ellipse.get_verts())

    # shapely_circle = shapely.geometry.point.Point(coords['lon'], coords['lat'])
    # shapely_circle = shapely_circle.buffer(radius_distance)

    return shapely_polygon

def convert_shapely_line_to_shapely_polygon(shapely_line: shapely.LineString) -> shapely.Polygon:
    """
    Converts a Shapely LineString to a Shapely Polygon.

    Parameters:
    shapely_line (LineString): A Shapely LineString object.

    Returns:
    Polygon: A Shapely Polygon object.
    """

    shapely_line_coords = shapely_line.coords.xy
    polygon_coords = [[lon, lat] for lon, lat in zip(shapely_line_coords[0], shapely_line_coords[1])]
    shapely_polygon = shapely.Polygon(polygon_coords)

    return shapely_polygon

class Location:
    """
    A class to represent a location.

    Attributes
    ----------
    config : dict
        a dictionary containing configuration parameters for the location
    polygons : list
        a list to store polygons
    name : str
        a string to store the name of the location
    """

    def __init__(self, config: dict):
        """
        Constructs all the necessary attributes for the location object.

        Parameters
        ----------
            config : dict
                a dictionary containing configuration parameters for the location
        """

        self.config = config
        self.polygons = []

        # Create location name based on config values but ignore the ones in filter list
        name_attributes_filter = ['region', 'color', 'coordinates']
        self.name = '_'.join(str(config[a]) for a in config if a not in name_attributes_filter)
        self.get_polygons()

    def get_polygons(self, path_cache: str = 'data/cache'):
        """
        This function generates polygons based on the type specified in the config.
        It first ensures the cache directory exists, then calls the appropriate method
        to generate the polygons. If the type is not recognized, it defaults to generating
        standard polygons.

        Parameters:
        path_cache (str): The path to the cache directory. Defaults to 'data/cache'.
        """
        pathlib.Path(path_cache).mkdir(parents=True, exist_ok=True)

        polygon_methods = {
            'isochrone': self._get_isochrone_polygons,
            'line': self._get_line_polygons,
            'circle': self._get_circle_polygons,
            'elevation': self._get_elevation_polygons,
        }

        method = polygon_methods.get(self.config['type'], self._get_standard_polygons)
        if self.config['type'] in ['isochrone', 'elevation']:
            method(path_cache)
        else:
            method()

    def _get_isochrone_polygons(self, path_cache: str):
        for coord in self.config['coordinates']:
            file_name = f"{self.name}_{coord['lat']}_{coord['lon']}.pkl"
            path_coord = pathlib.Path(path_cache, file_name)

            polygon = Polygon(center=[coord])
            polygon.get_isochrone_coordinates(
                path_coord,
                self.config['profile'],
                coord['lat'], coord['lon'],
                self.config['contours_minutes'],
            )
            polygon.get_shapely_polygons_from_coords()

            self.polygons.append(polygon)

    def _get_line_polygons(self):
        polygon = Polygon(center=self.config['coordinates'])
        polygon.get_shapely_polygons_from_line(self.config['buffer_distance'])
        self.polygons.append(polygon)

    def _get_circle_polygons(self):
        polygon = Polygon(center=self.config['coordinates'])
        polygon.get_shapely_polygons_from_circle(self.config['radius'])
        self.polygons.append(polygon)

    def _get_elevation_polygons(self, path_cache: str):
        path_elevation = '_'.join([self.name, self.config['category'] + '.pkl'])
        path_elevation = pathlib.Path(path_cache, path_elevation)

        polygon = Polygon()
        polygon.get_shapely_polygons_from_elevations(
            path_elevation,
            self.config['region']
        )
        self.polygons.append(polygon)

    def _get_standard_polygons(self):
        polygon = Polygon(center=self.config['coordinates'])
        polygon.get_shapely_polygons_standard()
        self.polygons.append(polygon)

class Polygon():
    def __init__(
            self,
            center: list = [{'lat': [], 'lon': []}],
            coords: list = [{'lat': [], 'lon': []}],
            shapely_polygons: list = [],
            aux_config : dict = {}
        ):
        """
        Initializes the Polygon class with center coordinates, polygon coordinates,
        shapely polygons, and auxiliary configuration.
        """        
        self.center = center
        self.coords = coords
        self.shapely_polygons = shapely_polygons
        self.aux_config = aux_config

    def _load_or_fetch(self, path, fetch_func, *args):
        """
        Helper function to load data from a file if it exists, or fetch it using
        a provided function and then save it to the file.
        """
        if path.exists():
            with open(path, 'rb') as file:
                return pickle.load(file)
        else:
            data = fetch_func(*args)
            with open(path, 'wb') as file:
                pickle.dump(data, file)
            return data

    def get_isochrone_coordinates(self, 
            path_c: pathlib.Path,
            profile: str,
            lat: float,
            lon: float,
            contours_minutes: int
        ):
        """
        Gets isochrone coordinates either by loading from a file or fetching from Mapbox.
        """
        self.coords = self._load_or_fetch(
            path_c,
            mapbox.get_isochrone_coordinates,
            profile,
            lat,
            lon,
            contours_minutes,
        )

    def _get_shapely_polygons(self, convert_func, buffer_distance_or_radius=None):
        """
        Helper function to get shapely polygons from center coordinates.
        """
        coords = {
            'lat' : [coord['lat'] for coord in self.center],
            'lon' : [coord['lon'] for coord in self.center],
        }
        if buffer_distance_or_radius is None:
            self.shapely_polygons = [convert_func(coords)]
        else:
            self.shapely_polygons = [convert_func(coords, buffer_distance_or_radius)] 

    def get_shapely_polygons_from_line(self, buffer_distance):
        """
        Gets shapely polygons from line.
        """  
        self._get_shapely_polygons(convert_coords_to_shapely_line, buffer_distance)

    def get_shapely_polygons_from_circle(self, buffer_radius):
        """
        Gets shapely polygons from circle.
        """  
        self._get_shapely_polygons(convert_coords_to_shapely_ellipse, buffer_radius)

    def get_shapely_polygons_standard(self):
        """
        Gets standard shapely polygons.
        """  
        self._get_shapely_polygons(convert_coords_to_shapely_polygon)

    def get_shapely_polygons_from_coords(self):
        """
        Gets shapely polygons from coordinates.
        """        
        self.shapely_polygons = [
            convert_coords_to_shapely_polygon(coord) for coord in self.coords
        ]

    def get_shapely_polygons_from_elevations(self,
            path_a: pathlib.Path,
            config: dict
        ):
        """
        Gets elevations either by loading from a file or fetching from OpenTopData.
        """
        self.coords = self._load_or_fetch(
            path_a,
            opentopdata.get_elevations,
            config,
        )

        df = pd.DataFrame(self.coords)
        mask = (df['elevation'] >= config['elevation_range']['min']) & (df['elevation'] <= config['elevation_range']['max'])

        voronoi = Voronoi(df[['lat', 'lon']].to_numpy())
        regions = voronoi.point_region[df[mask].index.values]
        regions = [voronoi.regions[r] for r in regions]
        regions = [list(filter(lambda x: x != -1, r)) for r in regions]
        regions = [r for r in regions if len(r)>2]

        self.shapely_polygons = [unary_union([convert_coords_to_shapely_polygon(
            {
                'lat': voronoi.vertices[r][:,0],
                'lon': voronoi.vertices[r][:,1]})
                for r in regions]
        )]      

class Map:
    def __init__(self, path_config: str):
        """
        Initializes a Map object.

        Args:
            path_config (str): Path to the configuration file.
        """
        self.configuration = load_json(path_config)
        self.locations = self.prepare_locations()
        self.locations_stacked = self.stack_locations()

    def prepare_locations(self, path_database: str = 'data/database') -> dict:
        """
        Prepares locations by updating their coordinates from the database.
        It iterates over each location in the configuration, updates its coordinates
        from the database, and creates a Location object for it.

        Args:
            path_database (str): Path to the database (default is 'data/database').

        Returns:
            dict: A dictionary of prepared locations.
        """
        locations = {}
        for config in self.configuration['locations']:
            self.update_config_with_database_coordinates(config, path_database)
            location = Location(config)
            locations[location.name] = location
            print(f'Location prepared: {location.name}')
        return locations

    def update_config_with_database_coordinates(
        self,
        config: dict,
        path_database: str
    ) -> None:
        """
        Updates the configuration dictionary with coordinates from a database.
        It loads the database from a JSON file and updates the configuration
        with the coordinates of the location if it exists in the database.

        Args:
            config (dict): Configuration dictionary.
            path_database (str): Path to the database.

        Returns:
            None
        """
        path_l = pathlib.PurePath(path_database, config['category'] + '.json')        
        c_json = load_json(path_l)
        
        if config['name'] in c_json:
            c_coordinates = c_json[config['name']]
            config.update(c_coordinates)

    def stack_locations(self) -> dict:
        """
        Stacks locations based on the logic defined in the configuration.
        It first gets all polygons for each location and stacks them per category.
        Then it combines all polygons according to the logic defined in the configuration.

        Returns:
            dict: A dictionary of stacked locations.
        """
        locations_stacked = defaultdict(lambda: {'shapely_polygons': []})

        # Get all polygons
        for location in self.locations.values():
            category = location.config['category']
            locations_stacked[category]['shapely_polygons'].extend(
                shapely_polygon for polygon in location.polygons
                for shapely_polygon in polygon.shapely_polygons
            )

        # Stack per category
        for category, polygons in locations_stacked.items():
            polygons['final_shapely_polygon'] = unary_union(polygons['shapely_polygons'])

        # Combine all 
        final_shapely_polygon = None
        for logic, logic_categories in self.configuration['logic'].items():
            for category, category_shapely_polygons in locations_stacked.items():
                if category not in logic_categories or category_shapely_polygons['final_shapely_polygon'] is None:
                    continue

                shapely_polygon = category_shapely_polygons['final_shapely_polygon']
                if final_shapely_polygon is None:
                    final_shapely_polygon = shapely_polygon
                elif logic == 'union':
                    final_shapely_polygon = unary_union([final_shapely_polygon, shapely_polygon])
                elif logic == 'intersection':
                    final_shapely_polygon = final_shapely_polygon.intersection(shapely_polygon)
                elif logic == 'difference':
                    final_shapely_polygon = final_shapely_polygon.difference(shapely_polygon)
                
        locations_stacked['final_shapely_polygon'] = final_shapely_polygon

        print('Stacking finished. The map is ready.')

        return locations_stacked
