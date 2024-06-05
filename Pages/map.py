from dash import Dash, Input, Output, State, dcc, html, callback_context, no_update, ALL
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
import plotly.graph_objects as go

from utils import Transportation, Citybag, CITIES

def _make_input_tab( cities: list, title: str ):
    return dbc.Tab(
        dbc.Card([ 
            dbc.CardBody( 
                dbc.Row([
                    dbc.Col( html.P(city) ),
                    dbc.Col( dbc.DropdownMenu([
                        dbc.DropdownMenuItem( target ) for target in list(CITIES['city'])
                    ], label='Choose city' ))
                ])
            ) for i, city in enumerate(cities) 
        ], className="mt-3" ), label=title
    )
def make_map_page( transportation: Transportation, citybag: Citybag ):
    return html.Div([
        html.H2('Interactive map', style={ 'text-align':'center' }),
        html.Hr(),
        dbc.Row([
            dbc.Col([
                dcc.Graph( id = 'globe', style={'height': '600px'} )
            ], width=8),
            dbc.Col([
                dbc.Tabs([
                    _make_input_tab([f'City {i}' for i in range(1,5)],'Cities'),
                    _make_input_tab([f'Plant {i}' for i in range(1,4)],'Plants')
                ])
            ], width=4)
        ])
    ], style={ 'margin':'24px' })

def load_map_callbacks( app: Dash, transportation: Transportation, citybag: Citybag, max_size: int ):
    @app.callback(
        Output('globe', 'figure'),
        [ Input('url', 'pathname') ]
    )
    def update_globe(pathname):
        if pathname == '/map':
            globe_data = []

            # Add markers for each city
            city_coords = {}
            for name in ["Tokyo, JPN", "Seoul, KOR", "Shanghai, CHN", "Guangzhou, CHN"]:
                if name: 
                    row = CITIES[CITIES['city'] == name].iloc[0]
                    lat, lon = row['lat'], row['lng']
                    city_coords[name] = (lat, lon)
                    globe_data.append(go.Scattergeo(
                        lon=[lon],
                        lat=[lat],
                        mode='markers',
                        marker=dict(size=10, color='red'),
                        text=name,
                        name=name
                    ))

            # Add markers for each plant
            plant_coords = {}
            for name in ["Delhi, IND", "Shenzhen, CHN", "Moscow, RUS" ]:
                if name:
                    row = CITIES[CITIES['city'] == name].iloc[0]
                    lat, lon = row['lat'], row['lng']
                    plant_coords[name] = (lat, lon)
                    globe_data.append(go.Scattergeo(
                        lon=[lon],
                        lat=[lat],
                        mode='markers',
                        marker=dict(size=10, color='blue'),
                        text=name,
                        name=name
                    ))

            layout = go.Layout(
                title='Globe of Cities and Plants',
                showlegend=True,
                geo=dict(
                    scope='world',
                    resolution=50,
                    projection=dict(
                        type='orthographic',
                        rotation=dict(
                            lon=0,
                            lat=0,
                            roll=0
                        )
                    ),
                    showland=True,
                    showcoastlines=True,
                    showocean=True,
                    showcountries=True,
                    countrycolor='#133c55',
                    oceancolor='#132630',
                    lakecolor='#132630',
                    coastlinecolor='#829199',
                    landcolor='#f9f9f9',
                    lonaxis=dict(
                        showgrid=True,
                        gridcolor='rgb(102, 102, 102)',
                        gridwidth=0.5
                    ),
                    lataxis=dict(
                        showgrid=True,
                        gridcolor='rgb(102, 102, 102)',
                        gridwidth=0.5
                    ),
                )
            )

            return {'data': globe_data, 'layout': layout}
        return no_update