from dash import Dash, Input, Output, html, dcc, no_update
import dash_bootstrap_components as dbc

import plotly.express as px
from utils import Transportation, get_max, calculate_energy_received
from numpy import sum

# /----------------| Utils. content |----------------\
def _city_heading( transportation: Transportation ):
    spent_by_city = sum( transportation.costs.values * transportation.supply, axis = 0 ) 
    taxes_by_city = sum( transportation.costs.values, axis = 0 ) / len( transportation.plant_supply )
    reqs_by_city = transportation.city_requirements.values

    spender = get_max( spent_by_city, transportation.city_requirements.index )
    spent_prop = spender[1] * 100 / transportation.problem.objective.value()
    taxed = get_max( taxes_by_city, transportation.city_requirements.index )
    req = get_max( reqs_by_city, transportation.city_requirements.index )
    req_prop = req[1] * 100 / sum(transportation.city_requirements.values)

    return html.Div([
        html.H2( 'City results', style={ 'text-align':'center' } ),
        html.Hr(),
        dbc.Row([
            dbc.Col( dbc.Card( dbc.CardBody([
                html.H3('Most money spent', className='card-title'),
                html.P( 
                    f'The city that spent the most money on energy transportation is { spender[0] } with a cost of { spender[1] }.'+
                    ' The percentage of the budget spent is:' 
                ),
                dbc.Progress( value = spent_prop, color='danger' if spent_prop >= 50 else 'info' )
            ])), width=4),
            dbc.Col( dbc.Card( dbc.CardBody([
                html.H3('Highest avg. cost', className='card-title'),
                html.P(
                    f'The city with the highest average cost of energy transportation is { taxed[0] } with an average of { taxed[1] } per kWh.'
                )
            ])), width=4),
            dbc.Col( dbc.Card( dbc.CardBody([
                html.H3('Highest energy requirement', className='card-title'),
                html.P( 
                    f'The city with the highest energy demands is { req[0] }, needing { req[1] } kWh.' +
                    ' The percentage of the total requirements is:' 
                ),
                dbc.Progress( value = req_prop, color='danger' if req_prop >= 50 else 'info' )
            ])), width=4)
        ]),
        html.Hr(),
        dcc.Graph( id='city-total-cost-plot' ),
        html.Hr(),
        html.H4( 'Supply plots', style={ 'text-align':'center' })
    ], style={ 'margin':'32px' } )

def _city_content( transportation: Transportation, max_size ):
    cards = []
    disabled_items = [ i - 1 for i in range( max_size, 0, -1 ) ][ : ( max_size - len(transportation.city_requirements) ) ]
    for i in range(max_size):
        if i in disabled_items: card = dbc.Col([dbc.Card([dcc.Graph(id=f'energy-received-plot-{i}')], style={'display':'none'})], width=4)
        else: card = dbc.Col([dbc.Card([dcc.Graph(id=f'energy-received-plot-{i}')])], width=4)
        cards.append(card)
    rows = [dbc.Row(cards[start:start + 3], style={'margin-top': '24px'}) for start in range(0, max_size, 3)]
    return html.Div(rows, style={'margin': '32px'})

def _city_cost_plot( transportation: Transportation, template: str ):
    costs = sum( transportation.costs.values * transportation.supply, axis = 0 )
    fig = px.bar(
        x = costs,
        y = transportation.city_requirements.index,
        title = 'Cost of energy transportation by city',
        template = template,
        color = transportation.city_requirements.index
    )
    fig.update_layout(font={'family': 'Nunito Sans', 'color': 'black'})
    return fig

# /----------------| Cities page generator |----------------\
def make_cities_page( transportation: Transportation, max_size: int = 36 ):
    return html.Div( [ 
        _city_heading( transportation ),
        _city_content( transportation, max_size )
    ], id = 'city-plots' )

def load_cities_callbacks( app: Dash, transportation: Transportation, template: str, max_size: int = 36 ):

    # //----------------| City tab main plot |----------------\\
    @app.callback(
        Output( 'city-total-cost-plot', 'figure' ),
        [ Input('url', 'pathname') ]
    )
    def gen_cities_costs_plot( pathname ):
        if pathname == '/cities': return _city_cost_plot( transportation, template )
        return no_update

    # //----------------| City tab plots |----------------\\
    @app.callback(
        [ Output( f'energy-received-plot-{i}', 'figure' ) for i in range( max_size ) ],
        [ Input('url', 'pathname') ]
    )
    def gen_energy_received_plot( pathname ):
        if pathname == '/cities':
            energy_received_percentage = calculate_energy_received( transportation.supply, transportation.city_requirements.values )
            figures = [
                px.pie(
                    values=energy_received_percentage[ idx ], 
                    names=[ plant for plant in transportation.plant_supply.index ], 
                    title=f'{ city }: Percentage of requirement satisfied',
                    hole=0.4
                ) for idx, city in enumerate(transportation.city_requirements.index)
            ]
            for fig in figures:
                fig.update_layout( font = { 'family': 'Nunito Sans', 'color': 'black' })
            figures += [ no_update for _ in range( max_size, 0, -1 ) ][ : ( max_size - len(transportation.city_requirements) ) ]
            return figures
        return no_update