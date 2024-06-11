import pathlib

import kaleido
import plotly
import plotly.graph_objects as go
import shapely

from src import mapbox
from src import data_handler

def save_figs(
        figs: dict[str, go.Figure],
        center_coord: dict,
        path_token: str = 'data/tokens/mapbox.txt',
        path_results: str = 'results',
        figure_width: int = 1000,
        figure_height: int = 1000
    ):
    """
    Save figures with updated layout.

    Parameters:
    figs (dict): Dictionary of figures to be saved.
    path_token (str): Path to the Mapbox token.
    path_results (str): Path to save the figures.
    figure_width (str): Figure width in pixels
    figure_height (str): Figure width in pixels
    """

    # Get the Mapbox token
    mapbox_token = mapbox.get_token(path_token)

    for fig_name, fig in figs.items():
        # Update the layout of the figure
        fig.update_layout(
            mapbox={
                'accesstoken': mapbox_token,
                'style': 'open-street-map',
                'zoom': 12,
                'center': {'lat' : center_coord['lat'], 'lon': center_coord['lon']}            
            },
            margin={'r':0,'t':0,'l':0,'b':0},
            showlegend=False,
            width=figure_width,
            height=figure_height
        )

        # Construct the figure path
        path_fig = pathlib.PurePath(path_results, fig_name + '.png')
        path_fig = pathlib.Path(path_fig)

        # Save the figure
        fig.write_image(path_fig, engine='kaleido', scale=2)

def draw_elevation(
        fig: go.Figure,
        coordinates: dict,
        marker_size : int = 10
    ) -> None:

    fig.add_trace(
        go.Scattermapbox(
            lat = coordinates['lat'],
            lon = coordinates['lon'],
            marker = {
                'size': marker_size,
                'color': coordinates['elevation'],
                'showscale':True
            },
            hoverinfo= 'lat+lon+text',
            text = [str(a) for a in coordinates['elevation']]
        )
    )

def draw_initial_coordinates(
        fig: go.Figure,
        coordinates: dict,
        color: str,
        name: str,
        marker_size : int = 10
    ) -> None:
    """
    This function adds a trace of coordinates to a given figure.

    Parameters:
    fig (go.Figure): The figure to which the trace will be added.
    coordinates (dict): The coordinates to be plotted.
    color (str): The color of the markers.
    name (str): The name of the trace.
    maker_size (int): The size of the markers

    Returns:
    None
    """
    # Plot each category on individual figure
    fig.add_trace(
        go.Scattermapbox(
            lat = [coord['lat'] for coord in coordinates],
            lon = [coord['lon'] for coord in coordinates],
            mode='markers',
            marker = {
                'size': marker_size,
                'color': [color for coord in coordinates],
            },
            hoverinfo=['name'],
            hoverlabel = dict(namelength = -1),
            name=' | '.join(name.split('_'))
        ),
    )

def draw_shapely_polygons(
        fig, 
        shapely_polygon: shapely.Polygon,
        color: str,
        name: str,
        layer_opacity : float = 0.4
    ) -> None:
    """
    This function adds a polygon layer to a given figure.

    Parameters:
    fig: The figure to which the layer will be added.
    shapely_polygon (shapely.Polygon): The polygon to be plotted.
    color (str): The color of the polygon.
    name (str): The name of the layer.
    layer_opacity (float): The opacity of the polygon.
    
    Returns:
    None
    """

    if not fig.data:
        fig.add_trace(go.Scattermapbox(lat=[], lon=[]))

    fig.update_layout(
        mapbox = {
            'layers': [
                {
                    'source': shapely_polygon.__geo_interface__,
                    'type': 'fill',
                    'color': color,
                    'opacity': layer_opacity
                } 
            ],
        },       
    )

def draw_map(
        map: data_handler.Map      
    ):
    """
    This function draws a map with polygons and locations.
    It takes a Map object as input and returns a figure.
    """

    figs = {'final' : go.Figure()}

    # Plot final polygons
    final_shapely_polygon = map.locations_stacked['final_shapely_polygon']
    draw_shapely_polygons(figs['final'], final_shapely_polygon, 'green', name='Final')

    # Plot individual category
    for location_name, location in map.locations.items():

        location_category = location.config['category']
        location_type = location.config['type']

        if not location_category in figs:
            figs[location_category] = go.Figure()

        if location_type == 'elevation':
            for polygon in location.polygons:
                draw_elevation(figs[location_category], polygon.coords)
                # draw_elevation(figs['final'], polygon.coords)
        
        elif location_type == 'line':
            draw_shapely_polygons(
                figs[location_category],
                map.locations_stacked[location_category]['final_shapely_polygon'],
                location.config['color'],
                location_category
            )
        
        else:
            draw_shapely_polygons(
                figs[location_category],
                map.locations_stacked[location_category]['final_shapely_polygon'],
                location.config['color'],
                location_category
            )    

            draw_initial_coordinates(figs[location_category], location.config['coordinates'], location.config['color'], location_name)    
            draw_initial_coordinates(figs['final'], location.config['coordinates'], location.config['color'], location_name)

    save_figs(figs, map.configuration['center'])

    return figs