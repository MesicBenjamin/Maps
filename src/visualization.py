import pathlib

import kaleido
import plotly
import plotly.graph_objects as go
import shapely

from src import mapbox
from src import data_handler

def draw_initial_coordinates(
        fig: go.Figure,
        coordinates: dict,
        color: str,
        name: str
    ) -> None:
    """
    ToDo
    """

    # Plot each category on individual figure
    fig.add_trace(
        go.Scattermapbox(
            lat = [c['lat'] for c in coordinates],
            lon = [c['lon'] for c in coordinates],
            mode='markers',
            marker = {
                'size': 10,
                'color': [color for c in coordinates]
            },
            hoverinfo=['name'],
            name=name,
        ),
    )

def draw_shapely_polygon(fig, shapely_polygon: shapely.Polygon, color: str, name: str) -> None:
    """
    ToDo
    """

    coord = data_handler.convert_shapely_polygon_to_coords(shapely_polygon)

    fig.add_trace(
        go.Scattermapbox(
            mode = 'lines', fill = 'toself',
            lat = coord['lat'],
            lon = coord['lon'],
            line = {'color': color},
            hoverinfo=['name'],
            name=name
        )
    )

def draw_map(
        map: data_handler.Map,
        path_token: str = 'data/tokens/mapbox.txt',
        path_results: str = 'results'          
    ):
    """
    ToDo
    """

    mapbox_token = mapbox.get_token(path_token)
    figs = { 'final' : go.Figure()}

    for location_name, location in map.locations.items():

        category = location.config['category']
        figs[category] = go.Figure()

        # Plot each category on individual figure
        draw_initial_coordinates(figs[category], location.config['coordinates'], location.config['color'], location_name)

        for polygon in location.polygons:
            for shapely_polygon in polygon.shapely_polygons:
                draw_shapely_polygon(figs[category], shapely_polygon, location.config['color'], category)

        # Plot each category on final figure
        draw_initial_coordinates(figs['final'], location.config['coordinates'], location.config['color'], location_name)

    # Plot final polygons
    for shapely_polygon in map.locations_stacked['final_shapely_polygon']:
        draw_shapely_polygon(figs['final'], shapely_polygon, 'gray', name='Final')

    # Save output
    for fig_name, fig in figs.items():

        fig.update_layout(
                mapbox = {
                    'accesstoken': mapbox_token,
                    'style': 'open-street-map',
                    'zoom': 12,
                    'center': {'lat' : 45.55854878748722, 'lon' : 18.684848674241845},
                },
                margin={'r':0,'t':0,'l':0,'b':0},
                showlegend = False,
                width=1000,
                height=1000            
        )

        path_fig = pathlib.PurePath(path_results, fig_name + '.png')
        path_fig = pathlib.Path(path_fig)
        fig.write_image(path_fig, engine='kaleido') 
    
    return figs['final']