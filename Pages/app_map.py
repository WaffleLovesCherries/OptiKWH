from dash import Dash, dcc, html, Input, Output, State, ALL
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
from dash.exceptions import PreventUpdate
import math

# Load city data
cities_df = pd.read_csv('worldcities.csv')

app = Dash(__name__, external_stylesheets=[dbc.themes.LUX, dbc.icons.BOOTSTRAP])

app.layout = dbc.Container([
    html.H3('Globe of Cities and Plants'),
    dbc.Row([
        dbc.Col(
            html.Div([
                dcc.Graph(
                    id='globe',
                    style={'width': '100%', 'height': '600px'}
                ), 
                html.Div(id='cities-input-2'),
                html.Div(id='plants-input-2'),
                html.Button('Update Globe', id='update-globe-button', n_clicks=0),
            ]),
            width=8  # Ancho de la columna del mapa
        ),
        dbc.Col(
            html.Div([
                html.Div([
                    dbc.Label("Number of Cities"),
                    dbc.Input(id='num-cities', type='number', min=1, max=50, step=1, value=2),
                ]),
                html.Div(id='cities-input'),
                html.Div([
                    dbc.Label("Number of Plants"),
                    dbc.Input(id='num-plants', type='number', min=1, max=50, step=1, value=2),
                ]),
                html.Div(id='plants-input'),
                html.Button('Update Globe', id='update-globe-button', n_clicks=0),
            ]),
            width=4  # Ancho de la columna de los inputs
        ),
    ]),
], fluid=True)  # fluid=True para que el container ocupe todo el ancho disponible

# Callback to dynamically generate city inputs
@app.callback(
    Output('cities-input', 'children'),
    Input('num-cities', 'value')
)
def update_city_inputs(num_cities):
    options = [{'label': row['city'], 'value': row['city']} for _, row in cities_df.iterrows()]
    return [
        dbc.Row([
            dbc.Col(dbc.Label(f'City {i+1}')),
            dbc.Col(dcc.Dropdown(id={'type': 'city-name', 'index': i}, options=options)),
        ]) for i in range(num_cities)
    ]

# Callback to dynamically generate plant inputs
@app.callback(
    Output('plants-input', 'children'),
    Input('num-plants', 'value')
)
def update_plant_inputs(num_plants):
    options = [{'label': row['city'], 'value': row['city']} for _, row in cities_df.iterrows()]
    return [
        dbc.Row([
            dbc.Col(dbc.Label(f'Plant {i+1}')),
            dbc.Col(dcc.Dropdown(id={'type': 'plant-name', 'index': i}, options=options)),
        ]) for i in range(num_plants)
    ]

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    return distance

# Callback to update the globe with markers
@app.callback(
    Output('globe', 'figure'),
    Input('update-globe-button', 'n_clicks'),
    [State({'type': 'city-name', 'index': ALL}, 'value'),
     State({'type': 'plant-name', 'index': ALL}, 'value')]
)
def update_globe(n_clicks, city_names, plant_names):
    if n_clicks == 0:
        raise PreventUpdate

    globe_data = []

    # Add markers for each city
    city_coords = {}
    for name in city_names:
        if name: 
            row = cities_df[cities_df['city'] == name].iloc[0]
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
    for name in plant_names:
        if name:
            row = cities_df[cities_df['city'] == name].iloc[0]
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

    # Add lines between plants and cities with distances
    for city, (city_lat, city_lon) in city_coords.items():
        for plant, (plant_lat, plant_lon) in plant_coords.items():
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

if __name__ == '__main__':
    app.run_server(debug=True)
