import plotly
import plotly.graph_objects as go

from src import mapbox

# class FigureWrapper(object):
#     '''Frees underlying figure when it goes out of scope. 
#     '''

#     def __init__(self, figure):
#         self._figure = figure

#     def __del__(self):
#         # print("Figure removed")
#         pass

def visualize(
        locations, locations_stacked,
        path_token: str = 'data/tokens/mapbox.txt',
    ):
    """    
    """

    mapbox_token = mapbox.get_token(path_token)

    fig = go.Figure()

    for location_name, location in locations.items():

        category = location.config['category']

        fig.add_trace(
            go.Scattermapbox(
                lat = [l['lat'] for l in location.config['coordinates']],
                lon = [l['lon'] for l in location.config['coordinates']],
                mode='markers',
                marker = {'size': 10, 'color': [location.config['color']]},
                hoverinfo=['name'],
                name=location_name
            )
        )

        fig.add_trace(
            go.Scattermapbox(
                mode = 'lines', fill = 'toself',
                lon = [l for l in locations_stacked['final'].exterior.coords.xy[0]],
                lat = [l for l in locations_stacked['final'].exterior.coords.xy[1]],
                line = {'color': 'royalblue'},
            ),
        )



    fig.update_layout(
            # mapbox_style="open-street-map",
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

    # html file
    # plotly.offline.plot(fig, filename='test.html')
    return fig

    # _wrapped_figure = FigureWrapper(fig)