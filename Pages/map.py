from dash import Dash, Input, Output, State, dcc, html, callback_context, no_update, ALL
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
import plotly.graph_objects as go

from utils import Transportation, haversine, CITIES
from json import loads
from pandas import DataFrame

# /----------------| Utils. dropdowns |----------------\
def _make_input_tab( cities: list, title: str ):
    locations = [ loc for loc in CITIES['city'] ]
    return dbc.Tab(
        dbc.Card([ 
            dbc.CardBody( 
                dbc.Row([
                    dbc.Col( html.P(city) ),
                    dbc.Col( 
                        dcc.Dropdown(
                            options=locations,
                            value=( cities[ idx ] if cities[ idx ] in locations else None ),
                            placeholder='Choose city',
                            id={ 'type':'dropdown', 'target':title, 'index':idx }
                        )
                    )
                ])
            ) for idx, city in enumerate(cities) 
        ], className="mt-3" ), label=title
    )

# /----------------| Utils. globe |----------------\
def _make_globe( transportation: Transportation ):
    globe_data = []
    locations = [ loc for loc in CITIES['city'] ]
    registered_cities = list( set(transportation.city_requirements.index) & set(locations) )
    # Add markers for each city
    city_coords = {}
    for name in registered_cities:
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

    registered_plants = list( set(transportation.plant_supply.index) & set(locations) )
    # Add markers for each plant
    plant_coords = {}
    for name in registered_plants:
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
    
    conections = DataFrame( transportation.supply, index=transportation.costs.index, columns=transportation.costs.columns )

    for city, (city_lat, city_lon) in city_coords.items():
        for plant, (plant_lat, plant_lon) in plant_coords.items():
            if conections.loc[ plant, city ] > 0:
                distance = haversine(city_lat, city_lon, plant_lat, plant_lon)
                globe_data.append(go.Scattergeo(
                    lon=[city_lon, plant_lon],
                    lat=[city_lat, plant_lat],
                    mode='lines+markers+text',
                    line=dict(width=2, color='#d90429'),
                    text=[f"{distance:.2f} km"],
                    textposition='middle center',
                    name=f"{plant} to {city}"
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

# /----------------| Map page generator |----------------\
def make_map_page( transportation: Transportation ):
    return html.Div([
        html.H2('Interactive map', style={ 'text-align':'center' }),
        html.Hr(),
        dbc.Row([
            dbc.Col([
                dcc.Graph( id = 'globe', style={'height': '600px'} )
            ], width=8),
            dbc.Col([
                dbc.Tabs([
                    _make_input_tab( transportation.city_requirements.index,'Cities'),
                    _make_input_tab( transportation.plant_supply.index,'Plants')
                ])
            ], width=4)
        ])
    ], style={ 'margin':'24px' })

# /----------------| Callback hell generator |----------------\
def load_map_callbacks( app: Dash, transportation: Transportation ):

    # //----------------| Name replacer |----------------\\
    @app.callback(
        Output('globe', 'figure'),
        [ 
            Input( {'type':'dropdown', 'target': 'Cities', 'index':ALL}, 'value' ),
            Input( {'type':'dropdown', 'target': 'Plants', 'index':ALL}, 'value' ),
            Input('url', 'pathname')
        ]

    )
    def set_city_names( changed_cities, changed_plants, pathname ):
        ctx = callback_context
        if not ctx.triggered:
            raise PreventUpdate
        
        triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if 'url' == triggered_id:
            if pathname == '/map': return _make_globe( transportation )
            
        elif 'dropdown' in triggered_id:
            changed_cities = [
                name if name is not None else transportation.city_requirements.index[idx] 
                for idx, name in enumerate(changed_cities)
            ]
            changed_plants = [
                name if name is not None else transportation.plant_supply.index[idx] 
                for idx, name in enumerate(changed_plants)
            ]
            transportation.costs.columns = changed_cities
            transportation.costs.index = changed_plants
            transportation.city_requirements.index = changed_cities
            transportation.plant_supply.index = changed_plants
            return _make_globe( transportation )
        
        return no_update