from dash import Dash, Input, Output, State, dcc, html, callback_context, no_update, ALL
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate

from utils import Transportation, save_uploaded_file
from json import loads

# /----------------| Utils. buttons |----------------\
def _make_buttons( name: str, target: str ):
    return html.Div([
        dbc.ButtonGroup([
            dbc.Button(
                className='bi bi-dash-circle', 
                color='secondary', 
                outline=True, 
                style={ 'font-size': '24px'}, 
                id={'type': 'table-edit', 'target': target, 'action': 'del'}  
            ),
            dbc.Button( name, color='primary', disabled=True ),
            dbc.Button(
                className='bi bi-plus-circle', 
                color='primary', 
                outline=True, 
                style={ 'font-size': '24px'},
                id={'type': 'table-edit', 'target': target, 'action': 'add'} 
            )
        ], className='flex-fill' )
    ], className='d-flex flex-fill' )

# /----------------| Input page generator |----------------\
def make_input_page( transportation: Transportation ):
    data_input = [
        html.Div([
            _make_buttons( 'Cities', 'city' ),
            html.Div([
                dcc.Upload( 
                    id='upload-data', 
                    children=html.Div([ 'Drag and Drop or ', html.A('Select Files') ]),
                    style={ 'textAlign': 'center', 'cursor': 'pointer' },
                    multiple=False
                )
            ], className='flex-fill'),
            _make_buttons( 'Plants', 'plant' ),
        ], className='d-flex align-items-center justify-content-center me-2' ),
        html.Hr()
    ]

    return html.Div([ 
        html.Div( 
            transportation.to_html(), 
            style = {'overflowX':'auto', 'maxWidth': '100%'}, 
            id = 'output-table' 
        )
        ] + data_input + [ 
            html.Div( id='problem-status' ), 
            html.Div( id='problem-results' ) 
        ], style = { 'padding': '48px'}
    )

# /----------------| Results table |----------------\
def make_table_results( transportation: Transportation ):

    table_head = [ 
        html.Th('') 
    ] + [ 
        html.Th(col) for col in transportation.costs.columns 
    ] + [
        html.Th('Plant supply')
    ]
    
    table_content = [
        html.Tr( 
            [ html.Th( transportation.plant_supply.index[ idx ] ) ] +
            [ html.Td( cell ) for cell in row ] +
            [ html.Td( transportation.plant_supply.iloc[ idx ]) ]
        ) for idx, row in enumerate(transportation.supply)
    ] + [
        html.Tr(
            [ html.Th( 'City requirement' ) ] +
            [ html.Td( cell ) for cell in transportation.city_requirements ]
        )
    ]
    return [
        html.H3( 'Results table', style={ 'text-align':'center' } ),
        dbc.Table([
        html.Thead( table_head ),
        html.Tbody( table_content )
        ], 
        bordered=True
    )]

# /----------------| Callback hell generator |----------------\
def load_input_callbacks( app: Dash, transportation: Transportation, max_size: int = 36  ):
    
    # //----------------| Table shape updater |----------------\\
    @app.callback(
        Output('output-table', 'children'),
        [
            Input('upload-data', 'contents'), 
            Input({'type': 'table-edit', 'target': ALL, 'action': ALL}, 'n_clicks')
        ],
        [State('upload-data', 'filename')]
    )
    def update_table( contents, n_clicks, filename ):
        ctx = callback_context
        if not ctx.triggered:
            raise PreventUpdate
        triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

        if 'upload-data' in triggered_id:
            if contents is None:
                raise PreventUpdate
            _, content_string = contents.split(',')
            uploaded_file_path = save_uploaded_file(filename, content_string)
            transportation.get_from_file(uploaded_file_path)

        elif 'table-edit' in triggered_id:
            triggered_id = loads(triggered_id)
            target = triggered_id['target']
            action = triggered_id['action']
            if action == 'add': transportation.add( int( target == 'city' ) )
            elif action == 'del': transportation.delete( -1, int( target == 'city' ) )

        return transportation.to_html()
    
    # //----------------| Table value updater |----------------\\
    @app.callback(
        [
            Input({'type': 'costs-cell', 'index': ALL}, 'value'),
            Input({'type': 'city-cell', 'index': ALL}, 'value'),
            Input({'type': 'plant-cell', 'index': ALL}, 'value')
        ]   
    )
    def update_problem(*cell_values):
        ctx = callback_context
        if not ctx.triggered:
            raise PreventUpdate
        triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

        if 'costs-cell' in triggered_id:
            row, col = loads( triggered_id )['index'].split('-')
            columns = list(transportation.costs.columns)
            rows = list(transportation.costs.index)
            col_idx = columns.index(col)
            row_idx = rows.index(row)
            value = cell_values[0][ col_idx + row_idx * len( transportation.costs.columns ) ]
            if value is None: value = 0
            transportation.costs.loc[ rows[row_idx], columns[col_idx] ] = value

        elif 'city-cell' in triggered_id:
            idx = loads( triggered_id )['index']
            cols = list(transportation.costs.columns)
            transportation.city_requirements.loc[idx] = cell_values[1][ cols.index( idx ) ]

        elif 'plant-cell' in triggered_id:
            idx = loads( triggered_id )['index']
            rows = list(transportation.costs.index)
            transportation.plant_supply.loc[idx] = cell_values[2][ rows.index( idx ) ]

    # //----------------| Max shape restrictions |----------------\\
    @app.callback(
        [ 
            Output({'type': 'table-edit', 'target': 'plant', 'action': 'del'}, 'disabled'),
            Output({'type': 'table-edit', 'target': 'city', 'action': 'del'}, 'disabled'),
            Output({'type': 'table-edit', 'target': 'plant', 'action': 'add'}, 'disabled'),
            Output({'type': 'table-edit', 'target': 'city', 'action': 'add'}, 'disabled'),
        ],
        Input('output-table', 'children')
    )
    def disable_buttons(_):
        return [
            len(transportation.plant_supply) <= 1,
            len(transportation.city_requirements) <= 1,
            len(transportation.plant_supply) >= max_size,
            len(transportation.city_requirements) >= max_size
        ]
    
    # //----------------| Problem status |----------------\\
    @app.callback(
        Output( 'problem-status', 'children' ),
        [
            Input('output-table', 'children'),
            Input('upload-data', 'contents'),
            Input({'type': 'table-edit', 'target': ALL, 'action': ALL}, 'n_clicks'),
            Input({'type': 'costs-cell', 'index': ALL}, 'value'),
            Input({'type': 'city-cell', 'index': ALL}, 'value'),
            Input({'type': 'plant-cell', 'index': ALL}, 'value')
        ]
    )
    def problem_solve( *args ):
        transportation.solve()
        if transportation.problem.status < 1: 
            return dbc.Alert(
                [
                    html.I(className="bi bi-x-octagon-fill me-2"),
                    f'Problem cannot be solved with current inputs.'
                ], color='danger' )
        else:
            return dbc.Alert(
                [
                    html.I(className="bi bi-check-circle-fill me-2"),
                    f'Found minimal value of { transportation.problem.objective.value() }'
                ], color='success', style = { 'cursor':'pointer' } )
        
    # //----------------| Problem result |----------------\\
    @app.callback(
        Output( 'problem-results','children' ),
        Input( 'problem-status','n_clicks' )
    )
    def problem_results( n_clicks ):
        if n_clicks: return make_table_results( transportation )
        return no_update