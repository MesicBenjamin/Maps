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
                'color': [color for c in coordinates],
                # 'opacity': 0.5
            },
            hoverinfo=['name'],
            hoverlabel = dict(namelength = -1),
            name=' | '.join(name.split('_'))
        ),
    )

def draw_shapely_polygons(fig, shapely_polygon: shapely.Polygon, color: str, name: str) -> None:
    """
    ToDo
    """

    fig.update_layout(
        mapbox = {
            'layers': [
                {
                    'source': shapely_polygon.__geo_interface__,
                    'type': 'fill',
                    'color': color,
                    'opacity': 0.4
                } 
            ],
        },       
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
    figs = {'final' : go.Figure()}

    # Plot final polygons
    final_shapely_polygon = map.locations_stacked['final_shapely_polygon']
    draw_shapely_polygons(figs['final'], final_shapely_polygon, 'green', name='Final')

    # Plot individual category
    for location_name, location in map.locations.items():

        category = location.config['category']
        if not category in figs:
            figs[category] = go.Figure()

        # Plot each category on individual figure
        if 'coordinates' in location.config:
            draw_initial_coordinates(figs[category], location.config['coordinates'], location.config['color'], location_name)    
    
        draw_shapely_polygons(figs[category], map.locations_stacked[category]['final_shapely_polygon'], location.config['color'], category)

        # Plot each category on final figure but skip line coordinates
        if location.config['type'] == 'line':
            continue

        if 'coordinates' in location.config:
            draw_initial_coordinates(figs['final'], location.config['coordinates'], location.config['color'], location_name)

    # Save output
    for fig_name, fig in figs.items():

        fig.update_layout(
                mapbox = {
                    'accesstoken': mapbox_token,
                    'style': 'open-street-map',
                    'zoom': 12,
                    'center': {'lat' : map.configuration['center']['lat'], 'lon': map.configuration['center']['lon']}            
                },
                margin={'r':0,'t':0,'l':0,'b':0},
                showlegend = False,
                width=1000,
                height=1000            
        )

        path_fig = pathlib.PurePath(path_results, fig_name + '.png')
        path_fig = pathlib.Path(path_fig)
        fig.write_image(path_fig, engine='kaleido', scale=2) 
    
    return figs['final']