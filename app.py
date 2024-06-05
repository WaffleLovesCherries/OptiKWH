from dash import Dash, Input, Output, html, dcc
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template

from utils import Transportation, Citybag, costs, plant_supply, city_requirements, CITIES
from Pages.input import make_input_page, load_input_callbacks
from Pages.cities import make_cities_page, load_cities_callbacks
from Pages.plants import make_plants_page, load_plants_callbacks
from Pages.map import make_map_page, load_map_callbacks

app = Dash(__name__, suppress_callback_exceptions=True, external_stylesheets=[dbc.themes.LUX, dbc.icons.BOOTSTRAP])
template = 'flatly'
load_figure_template( [template] )
max_size = 36

transportation = Transportation(costs, plant_supply, city_requirements)
citybag = Citybag( transportation )

navbar = dbc.Navbar(
    dbc.Container(
        [
            dbc.NavbarBrand( 'kWh Solver', href="/input" ),
            dbc.Nav(
                [
                    dbc.NavItem( dbc.NavLink( 'Input', href='/input' ) ),
                    dbc.DropdownMenu([
                        dbc.DropdownMenuItem( 'Cities', href='/cities' ),
                        dbc.DropdownMenuItem( 'Energy plants', href='/plants' )
                    ], label = 'Results', nav=True ),
                    dbc.NavItem( dbc.NavLink( 'Map', href='/map' ) )
                ],
                className="ml-auto",
                navbar=True
            )
        ]
    ),
    color = 'primary',
    dark = True
)

app.layout = html.Div([
    navbar,
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

# /!\---------------/!\ CALLBACK HELL! DO NOT TOUCH! /!\---------------/!\

# Navbar Urls
@app.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname')
)
def display_page(pathname):
    if pathname == '/cities': return make_cities_page( transportation, max_size )
    if pathname == '/plants': return make_plants_page( transportation, max_size )
    elif pathname == '/map': return make_map_page( transportation, citybag )
        
    else: return make_input_page( transportation )


load_input_callbacks( app, transportation, max_size )
load_cities_callbacks( app, transportation, template, max_size )
load_plants_callbacks( app, transportation, template, max_size )
load_map_callbacks( app, transportation, citybag, max_size )

if __name__ == '__main__':
    app.run_server(debug=True)
