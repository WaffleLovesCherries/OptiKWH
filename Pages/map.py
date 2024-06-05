from dash import Dash, Input, Output, State, dcc, html, callback_context, no_update, ALL
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
import plotly.graph_objects as go

from utils import Transportation, Citybag, CITIES

def make_map_page( transportation: Transportation, citybag: Citybag ):
    return html.Div([
        html.H2('Interactive map', style={ 'text-align':'center' }),
        html.Hr(),
        dbc.Row([
            dbc.Col([
                dcc.Graph( id = 'globe', style={'height': '600px'} )
            ], width=8),
            dbc.Col([
                html.Div( [ 
                    dbc.Card([
                        html.H4( 'Cities', style={ 'text-align':'center' } ),
                        dbc.DropdownMenu( label='Choose target variable', style={'width': '100%', 'text-align':'center'}, className='w-100' ),
                        dbc.DropdownMenu( label='Chose outcome city', style={'width': '100%', 'text-align':'center'}, className='w-100' )
                    ], style={ 'padding':'24px' }),
                    html.Hr(),
                    dbc.Card([
                        html.H4( 'Plants', style={ 'text-align':'center' } ),
                        dbc.Row([
                        dbc.DropdownMenu( label='Choose target variable', style={'width': '100%', 'text-align':'center'}, className='w-100' ),
                        dbc.DropdownMenu( label='Chose outcome plant', style={'width': '100%', 'text-align':'center'}, className='w-100' )])
                    ], style={ 'padding':'24px' }),
                 ] )
            ], width=4)
        ])
    ], style={ 'margin':'24px' })

def load_map_callbacks( app: Dash, transportation: Transportation, citybag: Citybag, template: str ):
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
                        name='Cities'
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
                        name='Plants'
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