import pathlib

import kaleido
import plotly
import plotly.graph_objects as go

from src import mapbox
from src import data_handler

def visualize(
        locations, locations_stacked,
        path_token: str = 'data/tokens/mapbox.txt',
        path_results: str = 'results'          
    ):
    """    
    """

    mapbox_token = mapbox.get_token(path_token)

    # Prepare all figs
    figs = {
        'final' : go.Figure(),
    }
    for location_name, location in locations.items():
        
        category = location.config['category']
        figs[category] = go.Figure()

    # Plot points
    for location_name, location in locations.items():

        category = location.config['category']

        # Plot each category on individual figure
        figs[category].add_trace(
            go.Scattermapbox(
                lat = [l['lat'] for l in location.config['coordinates']],
                lon = [l['lon'] for l in location.config['coordinates']],
                mode='markers',
                marker = {'size': 10, 'color': [location.config['color']]},
                hoverinfo=['name'],
                name=location_name
            )
        )

        # Plot each category on final figure
        figs['final'].add_trace(
            go.Scattermapbox(
                lat = [l['lat'] for l in location.config['coordinates']],
                lon = [l['lon'] for l in location.config['coordinates']],
                mode='markers',
                marker = {'size': 10, 'color': [location.config['color']]},
                hoverinfo=['name'],
                name=location_name
            )
        )

        for p in location.polygons:
            for pp in p.shapely_polygons:

                temp = data_handler.convert_shapely_polygon(pp)
                figs[category].add_trace(
                    go.Scattermapbox(
                        mode = 'lines', fill = 'toself',                        
                        lat = temp['lat'],
                        lon = temp['lon'],
                        hoverinfo=['name'],
                        line = {'color': location.config['color']},
                        name=location_name
                    )
                )

    # Plot final polygons
    for p in locations_stacked['final_shapely_polygon']:

        temp = data_handler.convert_shapely_polygon(p)

        figs['final'].add_trace(
            go.Scattermapbox(
                mode = 'lines', fill = 'toself',
                lat = temp['lat'],
                lon = temp['lon'],
                line = {'color': 'gray'},
                hoverinfo=['name'],
                name='Final'
            ),
        )

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