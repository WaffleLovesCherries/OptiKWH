from dash import Dash, Input, Output, html, dcc, no_update
import dash_bootstrap_components as dbc

import plotly.express as px
from utils import Transportation, get_max, calculate_energy_sent, get_min
from numpy import sum

# /----------------| Utils. content |----------------\
def _plant_heading( transportation: Transportation ):
    supplied_by_plant = sum( transportation.supply, axis = 1 ) 
    savings_by_plant = sum( transportation.costs.values, axis = 1 ) / len( transportation.city_requirements )
    capacity_by_plant = transportation.plant_supply.values - supplied_by_plant

    supplier = get_max( supplied_by_plant, transportation.plant_supply.index )
    supplier_prop = supplier[1] * 100 / sum( transportation.city_requirements.values )
    saver = get_min( savings_by_plant, transportation.plant_supply.index )
    left = get_max( capacity_by_plant, transportation.plant_supply.index )
    left_prop = left[1] * 100 / transportation.plant_supply.loc[ left[0] ]

    return html.Div([
        html.H2( 'Plant results', style={ 'text-align':'center' } ),
        html.Hr(),
        dbc.Row([
            dbc.Col( dbc.Card( dbc.CardBody([
                html.H3('Most energy supplied', className='card-title'),
                html.P( 
                    f'The power plant that supplied the most energy to the cities is { supplier[0] } with a kWh of { supplier[1] }.'+
                    ' The percentage of the total supply is:' 
                ),
                dbc.Progress( value = supplier_prop, color='success' if supplier_prop >= 50 else 'info' )
            ])), width=4),
            dbc.Col( dbc.Card( dbc.CardBody([
                html.H3('Lowest avg. cost', className='card-title'),
                html.P(
                    f'The city with the lowest average cost of energy transportation is { saver[0] } with an average of { saver[1] } per kWh.'
                )
            ])), width=4),
            dbc.Col( dbc.Card( dbc.CardBody([
                html.H3('Highest capacity left', className='card-title'),
                html.P( 
                    f'The power plan with the most capacity left is { left[0] }, with  { left[1] } kWh.' +
                    ' The percentage of the total requirements is:' 
                ),
                dbc.Progress( value = left_prop, color='danger' if left_prop >= 40 else 'info' )
            ])), width=4)
        ]),
        html.Hr(),
        dcc.Graph( id='plant-total-supply-plot' ),
        html.Hr(),
        html.H4( 'Supply plots', style={ 'text-align':'center' })
    ], style={ 'margin':'32px' } )

def _plant_content( transportation: Transportation, max_size ):
    cards = []
    disabled_items = [ i - 1 for i in range( max_size, 0, -1 ) ][ : ( max_size - len(transportation.plant_supply) ) ]
    for i in range(max_size):
        if i in disabled_items: card = dbc.Col([dbc.Card([dcc.Graph(id=f'energy-sent-plot-{i}')], style={'display':'none'})], width=4)
        else: card = dbc.Col([dbc.Card([dcc.Graph(id=f'energy-sent-plot-{i}')])], width=4)
        cards.append(card)
    rows = [dbc.Row(cards[start:start + 3], style={'margin-top': '24px'}) for start in range(0, max_size, 3)]
    return html.Div(rows, style={'margin': '32px'})
    
def _plant_supply_plot( transportation: Transportation, template: str ):
    costs = sum( transportation.supply, axis = 1 )
    fig = px.bar(
        x = costs,
        y = transportation.plant_supply.index,
        title = 'Total energy supplied per plant',
        template = template,
        color = transportation.plant_supply.index
    )
    fig.update_layout(font={'family': 'Nunito Sans', 'color': 'black'})
    return fig

# /----------------| Plants page generator |----------------\
def make_plants_page( transportation: Transportation, max_size: int = 36 ):
    return html.Div( [ 
        _plant_heading( transportation ),
        _plant_content( transportation, max_size )
    ], id = 'plant-plots' )

def load_plants_callbacks( app: Dash, transportation: Transportation, template: str, max_size: int = 36 ):

    # //----------------| Plant tab main plot |----------------\\
    @app.callback(
        Output( 'plant-total-supply-plot', 'figure' ),
        [ Input('url', 'pathname') ]
    )
    def gen_plants_costs_plot( pathname ):
        if pathname == '/plants': return _plant_supply_plot( transportation, template )
        return no_update

    # //----------------| Plant tab plots |----------------\\
    @app.callback(
        [ Output( f'energy-sent-plot-{i}', 'figure' ) for i in range( max_size ) ],
        [ Input('url', 'pathname') ]
    )
    def gen_energy_sent_plot( pathname ):
        if pathname == '/plants':
            energy_sent_percentage = calculate_energy_sent( transportation.supply, transportation.plant_supply.values )
            figures = [
                px.pie(
                    values=energy_sent_percentage[ idx ],
                    names=[ city for city in transportation.city_requirements.index ], 
                    title=f'{ plant }: Percentage of Capacity Used',
                    hole=0.4
                ) for idx, plant in enumerate(transportation.plant_supply.index)
            ]
            for fig in figures:
                fig.update_layout( font = { 'family': 'Nunito Sans', 'color': 'black' })
            figures += [ no_update for _ in range( max_size, 0, -1 ) ][ : ( max_size - len(transportation.plant_supply) ) ]
            return figures
        else: return no_update