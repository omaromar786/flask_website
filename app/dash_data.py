from dash import dcc, html, Dash, dash_table, Input, Output, State
import plotly.graph_objs as go
from app.database import fetch_filtered_data, get_latest_data
import dash_daq as daq
import json
from datetime import datetime

def create_dash_layout(app):
    
    # Initial data fetch (used to set up the initial layout)
    data = fetch_filtered_data()
    sensors, heartbeats = get_latest_data()

    # Prepare initial data for the table
    table_data = []
    for i in range(len(data['field5']['x'])):
        record = {
            "timestamp": data['field5']['x'][i].strftime('%Y-%m-%d %H:%M:%S'),
            "field5": data['field5']['y'][i],
            "field6": data['field6']['y'][i],
            "field7": data['field7']['y'][i],
            "field8": data['field8']['y'][i],
            "field9": data['field9']['y'][i],
            "field10": data['field10']['y'][i],
        }
        table_data.append(record)

    # Define layout
    app.layout = html.Div([
        dcc.Interval(id='interval-component', interval=30*1000, n_intervals=0),  # Update every 30 SEC

        html.Div(children=[
            html.H1(
                'UbiBot Sensor Data', 
                id="ubibot-data",
                style={
                    'padding-top': '20px',
                    'padding-bottom': '5px',
                    'font-family': "'Golos Text', sans-serif"
                }
            ),

            html.Div([
                html.H2(
                    "UbiBot Data Graphs",
                    style={
                        'padding-top': '20px',
                        'padding-bottom': '15px',
                        'font-family': "'Golos Text', sans-serif",
                        'text-align': 'left',
                    }
                ),
            ]),

            # Graphs
            html.Div([
                dcc.Graph(id='graph-5', style={'border': '1px solid black', 'padding': '10px', 'margin': '10px'}),
                dcc.Graph(id='graph-6', style={'border': '1px solid black', 'padding': '10px', 'margin': '10px'}),
            ], style={'display': 'flex', 'justify-content': 'center'}, className='graph-row'),

            html.Div([
                dcc.Graph(id='graph-7', style={'border': '1px solid black', 'padding': '10px', 'margin': '10px'}),
                dcc.Graph(id='graph-8', style={'border': '1px solid black', 'padding': '10px', 'margin': '10px'}),
            ], style={'display': 'flex', 'justify-content': 'center'}, className='graph-row'),

            html.Div([
                dcc.Graph(id='graph-9', style={'border': '1px solid black', 'padding': '10px', 'margin': '10px'}),
                dcc.Graph(id='graph-10', style={'border': '1px solid black', 'padding': '10px', 'margin': '10px'}),
            ], style={'display': 'flex', 'justify-content': 'center'}, className='graph-row'),

            # Table for UbiBot data
            html.Div([
                html.H2(
                    "UbiBot Sensor Data Table",
                    style={
                        'padding-top': '20px',
                        'padding-bottom': '15px',
                        'font-family': "'Golos Text', sans-serif",
                        'text-align': 'left',
                    }
                ),
                dash_table.DataTable(
                    id='ubibot-table',
                    columns=[
                        {"name": "Timestamp", "id": "timestamp"},
                        {"name": data['field5']['name'], "id": "field5"},
                        {"name": data['field6']['name'], "id": "field6"},
                        {"name": data['field7']['name'], "id": "field7"},
                        {"name": data['field8']['name'], "id": "field8"},
                        {"name": data['field9']['name'], "id": "field9"},
                        {"name": data['field10']['name'], "id": "field10"},
                    ],
                    page_current=0,
                    page_size=20,
                    page_action='custom',
                    style_data={
                        'backgroundColor': '#ece8e5',
                        'border': '1px solid #333',
                        'font-family': "'Golos Text', sans-serif"
                    },
                    style_header={
                        'backgroundColor': '#ece8e5',
                        'fontWeight': 'bold',
                        'textAlign': 'center',
                        'border': '1px solid #333',
                        'font-family': "'Golos Text', sans-serif"
                    },
                    style_cell={
                        'border': '1px solid #333',
                        'font-family': "'Golos Text', sans-serif"
                    },
                ),
            ], style={'padding': '10px'}),

            # Store component to hold all table data
            dcc.Store(id='table-data-store', data=json.dumps(table_data)),

        ], style={'text-align': 'center'}),

        html.Div(children=[
            html.H1('Other Sensor Data', id="sensor-data"),

            # Container for tank
            html.Div([
                html.Div([
                    html.H3("Main Tank", id="main-tank-label"),
                    daq.Tank(
                        id="water-level",
                        value=round(sensors.get("water_level_percent", 0), 2) if sensors else 0,
                        min=0,
                        max=100,
                        units="PERCENT",
                        showCurrentValue=True,
                        color="#58afdd",
                        style={"margin-top": "50px"},
                    ),
                ], style={'display': 'inline-block'}),
            ], style={'margin-top': '20px'}),

        ], style={'text-align': 'center', 'background-color': '#ebebe2'}),

        html.Div(id='last-update-time', style={'text-align': 'center', 'margin-top': '20px'}),
    ], style={
    'background-color': '#ebebe2'
    })

    # Clientside callback for pagination
    app.clientside_callback(
        """
        function(page_current, page_size, table_data) {
            const data = JSON.parse(table_data);
            const start = page_current * page_size;
            const end = start + page_size;
            return data.slice(start, end);
        }
        """,
        Output('ubibot-table', 'data'),
        Input('ubibot-table', "page_current"),
        Input('ubibot-table', "page_size"),
        Input('table-data-store', 'data')
    )

    # Callback to update all components
    @app.callback(
        [Output('graph-5', 'figure'),
         Output('graph-6', 'figure'),
         Output('graph-7', 'figure'),
         Output('graph-8', 'figure'),
         Output('graph-9', 'figure'),
         Output('graph-10', 'figure'),
         Output('table-data-store', 'data'),
         Output('water-level', 'value'),
         Output('last-update-time', 'children')],
        [Input('interval-component', 'n_intervals')]
    )
    def update_all_data(n_intervals):
        # Fetch filtered data from MongoDB
        data = fetch_filtered_data()
        sensors, heartbeats = get_latest_data()

        # Prepare data for the table
        table_data = []
        for i in range(len(data['field5']['x'])):
            record = {
                "timestamp": data['field5']['x'][i].strftime('%Y-%m-%d %H:%M:%S'),
                "field5": data['field5']['y'][i],
                "field6": data['field6']['y'][i],
                "field7": data['field7']['y'][i],
                "field8": data['field8']['y'][i],
                "field9": data['field9']['y'][i],
                "field10": data['field10']['y'][i],
            }
            table_data.append(record)

        # Update graph figures
        fig5 = go.Figure(data=[go.Scatter(x=data['field5']['x'], y=data['field5']['y'], mode='lines', name='CO2 Probe Temperature', line=dict(color='#8c564b'))])
        fig5.update_layout(title='CO2 Probe Temperature')

        fig6 = go.Figure(data=[go.Scatter(x=data['field6']['x'], y=data['field6']['y'], mode='lines', name='Light', line=dict(color='#ff7f0e'))])
        fig6.update_layout(title='Light')

        fig7 = go.Figure(data=[go.Scatter(x=data['field7']['x'], y=data['field7']['y'], mode='lines', name='CO2 Probe Humidity', line=dict(color='#2b3e50'))])
        fig7.update_layout(title='CO2 Probe Humidity')

        fig8 = go.Figure(data=[go.Scatter(x=data['field8']['x'], y=data['field8']['y'], mode='lines', name='CO2 Probe', line=dict(color='#7f2b23'))])
        fig8.update_layout(title='CO2 Probe')

        fig9 = go.Figure(data=[go.Scatter(x=data['field9']['x'], y=data['field9']['y'], mode='lines', name='RS485 Soil Temperature -TH1', line=dict(color='#2b572e'))])
        fig9.update_layout(title='Soil Temperature')

        fig10 = go.Figure(data=[go.Scatter(x=data['field10']['x'], y=data['field10']['y'], mode='lines', name='RS485 Soil Moisture', line=dict(color='#4b2b5a'))])
        fig10.update_layout(title='RS485 Soil Moisture')

        # Get current time for last update display
        last_update = f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        return (fig5, fig6, fig7, fig8, fig9, fig10, 
                json.dumps(table_data), 
                sensors.get("water_level_percent", 0) if sensors else 0, 
                last_update)

    return app

# This part can be in your main application file
if __name__ == '__main__':
    app = Dash(__name__)
    app = create_dash_layout(app)
    app.run_server(debug=True)
