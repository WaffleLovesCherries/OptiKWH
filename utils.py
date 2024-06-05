import os
import base64
import tempfile

from pandas import read_csv, read_excel, Series, DataFrame
from pulp import LpProblem, LpMinimize, LpVariable, LpContinuous, value
from numpy import ones, array, sum, argmax, argmin
from dash import html
import dash_bootstrap_components as dbc

CITIES = read_csv( 'Data/cities.csv' )

class Transportation:
    def __init__( self, costs: DataFrame, plant_supply: Series, city_requirements: Series ):
        self.costs = costs
        self.plant_supply = plant_supply
        self.city_requirements = city_requirements
        self.problem, self.kwh, self.supply = None, None, None
        self.solve()

    def set_city( self, name: str, idx: int ):
        self.costs.columns[ idx ] = name
        self.city_requirements.index[ idx ] = name

    def set_plants( self, name: str, idx: int ):
        self.costs.index[ idx ] = name
        self.plant_supply.index[ idx ] = name

    def get_from_file( self, file_path: str ):
        format = file_path.split('.')[-1]
        match format:
            case 'csv': data = read_csv( file_path, index_col=0 )
            case 'xlsx': data = read_excel( file_path, index_col=0 )
            case 'xls': data = read_excel( file_path, index_col=0 )
            case _: raise ValueError("Unsupported file format")

        city_requirements = Series( data.iloc[-1,:-1], name='City requirements' )
        plant_supply = Series(data.iloc[:-1, -1], name='Plant supply')

        self.costs = data.drop(data.index[-1]).drop(data.columns[-1], axis=1)
        self.plant_supply = plant_supply
        self.city_requirements = city_requirements
    
    def delete( self, index: int = 0, axis: int = 0 ):
        if axis: 
            index = self.costs.columns[ index ]
            self.costs.drop( index, axis = axis, inplace=True )
            self.city_requirements.drop( index = index, inplace=True )
        else: 
            index = self.costs.index[ index ]
            self.costs.drop( index, axis = axis, inplace=True )
            self.plant_supply.drop( index = index, inplace=True )
    
    def add( self, axis: int = 0 ):
        if axis:
            self.costs.loc[ : , self.costs.shape[1] + 1 ] = ones( self.costs.shape[0] )
            self.city_requirements.loc[  self.costs.shape[1] + 1 ] = 0
        else: 
            self.costs.loc[ self.costs.shape[0] + 1, : ] = ones( self.costs.shape[1] )
            self.plant_supply.loc[ self.costs.shape[0] + 1 ] = 0
    
    def to_html( self ):
        table_content = [
            html.Tr(
                [ html.Th(idx) ] + [
                    html.Td( dbc.Input( 
                        value = cell, 
                        id = {'type': 'costs-cell', 'index': f'{idx}-{jdx}'}, 
                        type='number', 
                        min = 0 ), 
                        style={'min-width':'176px'}
                    )
                    for jdx, cell in row.items()
                ] + [ html.Td( 
                    dbc.Input( 
                        value = self.plant_supply.iloc[ list( self.costs.index ).index( idx ) ], 
                        id = {'type': 'plant-cell', 'index': idx}, 
                        type='number', 
                        min = 0
                    ), style={'min-width':'176px'} )
                ]
            ) for idx, row in self.costs.iterrows() 
        ] + [ html.Tr(
            [ html.Th( 'City requirement' ) ] + [
                html.Td( 
                    dbc.Input( value = item, id = {'type': 'city-cell', 'index': idx}, type='number', min = 0 ),
                    style={'min-width':'176px'}
                ) for idx, item in self.city_requirements.items()
            ])
        ]
        return [dbc.Table([
            html.Thead([
                html.Tr(
                    [html.Th('')] + 
                    [html.Th(col) for col in self.costs.columns] + 
                    [html.Th('Plant supply')]
                )
            ]),
            html.Tbody(table_content)
        ], className='table primary')]
    
    def solve( self ):
        costs = self.costs.copy().values
        city_requirements = self.city_requirements.copy().values
        plant_supply = self.plant_supply.copy().values

        cities = len( city_requirements )
        plants = len( plant_supply )
        
        problem = LpProblem( 'Min_supply', LpMinimize )

        kwh = array([ 
            [ LpVariable( f'Plant{i+1}ToCity{j+1}', lowBound=0, cat=LpContinuous ) for j in range( cities ) ] 
            for i in range( plants ) 
        ])

        f = sum( kwh*costs )
        problem += f

        supplies = sum( kwh, axis = 1 )
        for i, supply in enumerate( supplies ):
          problem += supply <= plant_supply[ i ]

        supplies = sum( kwh, axis = 0 )
        for i, supply in enumerate( supplies ):
          problem += supply >= city_requirements[ i ]

        problem.solve()
        problem.objective.value()

        self.problem = problem
        self.kwh = kwh
        self.supply = get_supply( kwh )
    
class Citybag:

    def __init__( self, transportation: Transportation ):
        self.cities, self.plants = None, None
        self.set( transportation )

    def set( self, transportation: Transportation ):
        self.cities = DataFrame([
            dict( CITIES[ CITIES['city'] == city].iloc[0]) 
            if city in CITIES['city'].values 
            else {'city': city, 'lat': 0.0, 'lng': 0.0} 
            for city in transportation.city_requirements.index
        ])

        self.plants = DataFrame([
            dict( CITIES[ CITIES['city'] == city].iloc[0]) 
            if city in CITIES['city'].values 
            else {'city': city, 'lat': 0.0, 'lng': 0.0} 
            for city in transportation.plant_supply.index
        ])
    
    def get( self, idx: int ):
        return dict( self.cities.iloc[ idx ] )

def save_uploaded_file( filename: str, content ):
    temp_dir = tempfile.mkdtemp()
    file_extension = filename.split('.')[-1]
    temp_file_path = os.path.join(temp_dir, f"temp.{file_extension}")
    with open(temp_file_path, 'wb') as f:
        f.write(base64.b64decode(content))
    return temp_file_path

def get_supply( kwh: array ):
    return array([ [ value(item) for item in column ] for column in kwh ])

def get_max( items: array, index: list ):
    idx = argmax( items )
    return index[ idx ], items[ idx ]

def get_min( items: array, index: list ):
    idx = argmin( items )
    return index[ idx ], items[ idx ]

def calculate_money_spent( supply: array, costs: array ):
    return sum(supply * costs, axis=0)

def calculate_energy_sent( supply: array, max_supply: array ):
    return ((supply.T / max_supply) * 100 ).T

def calculate_energy_received( supply: array, req_supply: array ):
    return ((supply / req_supply) * 100 ).T

# Init data
costs = DataFrame( 
    array([
      [ 8, 6, 10, 10 ],
      [ 9, 12, 13, 7 ],
      [ 14, 9, 16, 5 ]
    ]), 
    columns = [ f'City {i+1}' for i in range(4) ], 
    index = [ f'Plant {i+1}' for i in range(3) ]
)
city_requirements = Series(
    [ 45, 20, 30, 30 ], 
    index = [ f'City {i+1}' for i in range(4) ] 
)
plant_supply = Series(
    [ 35, 50, 40 ], 
    index = [ f'Plant {i+1}' for i in range(3) ] 
)

