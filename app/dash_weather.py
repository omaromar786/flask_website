from dash import dcc, html, Dash, dash_table, Input, Output, State
import plotly.graph_objs as go
from app.database import fetch_weather_data, get_weather_data, get_weather_emoji
import json
import pandas as pd
import dash_bootstrap_components as dbc

def create_weather_layout(app):
    # Fetch weather data from MongoDB
    weather_data = fetch_weather_data()

    # Prepare data for graphs and table
    df = pd.DataFrame(weather_data)
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # Get the weather data
    cloudy, raining, is_night = get_weather_data()
    weather_emoji = get_weather_emoji(cloudy, raining, is_night)

    # Define layout
    app.layout = html.Div([
        # Add external stylesheets for the font
        html.Link(
            rel='stylesheet',
            href='https://fonts.googleapis.com/css2?family=Golos+Text&display=swap'
        ),
        html.Div(children=[
            html.H1(
                'Live Weather Data', 
                id="weather-data",
                style={
                    'padding-top': '8px',
                    'font-family': "'Golos Text', sans-serif",
                    'text-align': 'center',  # Align H1 to the left as well
                }
            ),

            html.Div([
                html.H2(
                    "Current Weather at YuHua AgriLab",
                    style={
                        'padding-top': '20px',
                        'padding-bottom': '5px',
                        'font-family': "'Golos Text', sans-serif",
                        'text-align': 'left',  # Align to the left
                    }
                ),
                dbc.Container([
                    dbc.Row(
                        dbc.Col(
                            html.Div(
                                weather_emoji, 
                                id='weather-display', 
                                style={'fontSize': '100px', 
                                       'textAlign': 'center'}),
                            width=12
                        ),
                        justify='center',
                        align='center'
                    ),
                    dcc.Interval(
                        id='interval-component',
                        interval=60*1000,  # Update every minute
                        n_intervals=0
                    )
                ],
                fluid=True )
            ], style={'margin-top': '20px', 'background-color': '#ebebe2'}),

            # Graphs
            html.Div([
                html.H2(
                    "Weather Data Graphs",
                    style={
                        'padding-top': '20px',
                        'padding-bottom': '15px',
                        'font-family': "'Golos Text', sans-serif",
                        'text-align': 'left',  # Align to the left
                    }
                ),
            ]),

            # First row of graphs
            html.Div([
                dcc.Graph(
                    id='graph-temperature',
                    figure={
                        'data': [
                            go.Scatter(x=df['timestamp'], y=df['temperature'], mode='lines', name='Temperature'),
                            go.Scatter(x=df['timestamp'], y=df['feels_like'], mode='lines', name='Feels Like')
                        ],
                        'layout': {
                            'title': 'Temperature and Feels Like'
                        }
                    },
                    style={'border': '1px solid black', 'padding': '10px', 'margin': '10px'}
                ),
                dcc.Graph(
                    id='graph-humidity',
                    figure={
                        'data': [
                            go.Scatter(x=df['timestamp'], y=df['humidity'], mode='lines', name='Humidity')
                        ],
                        'layout': {
                            'title': 'Humidity'
                        }
                    },
                    style={'border': '1px solid black', 'padding': '10px', 'margin': '10px'}
                )
            ], style={'display': 'flex', 'justify-content': 'center'},
            className='graph-row'),

            # Second row of graphs
            html.Div([
                dcc.Graph(
                    id='graph-wind',
                    figure={
                        'data': [
                            go.Scatter(x=df['timestamp'], y=df['wind_speed'], mode='lines', name='Wind Speed'),
                            go.Scatter(x=df['timestamp'], y=df['wind_gust'], mode='lines', name='Wind Gust')
                        ],
                        'layout': {
                            'title': 'Wind Speed and Gust'
                        }
                    },
                    style={'border': '1px solid black', 'padding': '10px', 'margin': '10px'}
                ),
                dcc.Graph(
                    id='graph-pressure',
                    figure={
                        'data': [
                            go.Scatter(x=df['timestamp'], y=df['pressure'], mode='lines', name='Pressure')
                        ],
                        'layout': {
                            'title': 'Pressure'
                        }
                    },
                    style={'border': '1px solid black', 'padding': '10px', 'margin': '10px'}
                )
            ], style={'display': 'flex', 'justify-content': 'center'},
            className='graph-row'),

            # Third row of graphs
            html.Div([
                dcc.Graph(
                    id='graph-uv',
                    figure={
                        'data': [
                            go.Scatter(x=df['timestamp'], y=df['uv'], mode='lines', name='UV Index')
                        ],
                        'layout': {
                            'title': 'UV Index'
                        }
                    },
                    style={'border': '1px solid black', 'padding': '10px', 'margin': '10px'}
                ),
                dcc.Graph(
                    id='graph-solar',
                    figure={
                        'data': [
                            go.Scatter(x=df['timestamp'], y=df['solar_radiation'], mode='lines', name='Solar Radiation')
                        ],
                        'layout': {
                            'title': 'Solar Radiation'
                        }
                    },
                    style={'border': '1px solid black', 'padding': '10px', 'margin': '10px'}
                )
            ], style={'display': 'flex', 'justify-content': 'center'},
            className='graph-row'),

            # Table for Weather data
            html.Div([
                html.H2(
                    "Weather Data Table",
                    style={
                        'padding-top': '20px',
                        'padding-bottom': '15px',
                        'font-family': "'Golos Text', sans-serif",
                        'text-align': 'left',
                    }
                ),
                dash_table.DataTable(
                    id='weather-table',
                    columns=[{"name": i, "id": i} for i in df.columns if i not in ['_id', 'station_id', 'neighborhood']],
                    data=df.to_dict('records'),
                    page_current=0,
                    page_size=20,
                    page_action='native',
                    style_table={
                        'overflowX': 'auto',
                    },
                    style_data={
                        'backgroundColor': '#ece8e5',
                        'border': '1px solid #333',
                        'font-family': "'Golos Text', sans-serif",
                    },
                    style_header={
                        'backgroundColor': '#ece8e5',
                        'fontWeight': 'bold',
                        'textAlign': 'center',
                        'border': '1px solid #333',
                        'font-family': "'Golos Text', sans-serif",
                    },
                    style_cell={
                        'border': '1px solid #333',
                        'font-family': "'Golos Text', sans-serif",
                    },
                ),
            ], style={'padding': '10px'}),

        ], style={'text-align': 'center'}),
    ], style={
        'background-color': '#ebebe2', 
        'font-family': "'Golos Text', sans-serif",
        'min-height': '100vh',
    })

    return app

# This part can be in your main application file
if __name__ == '__main__':
    app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
    app = create_weather_layout(app)
    app.run_server(debug=True)