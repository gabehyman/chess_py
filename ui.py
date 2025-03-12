from dash import Dash, dcc, html, Input, Output, State, callback_context, ALL
import dash_bootstrap_components as dbc

from game import Game
from game import Result
from game import Color

app = Dash(__name__, external_stylesheets=[dbc.themes.CYBORG])

class UI:
    def __init__(self, stats):
        self.stats = stats

    def show_layout(self):
        app.layout = self.layout()
        self.callback()
        app.run_server(debug=False)

    def get_and_sort_opening_stats(self, depth: int, color: int, result: int, display: int):
        sorted_openings: dict[str, list[list[int]]] = self.stats.get_and_sort_opening_stats(depth, color, result,
                                                                                            display)

        results_list = []

        # Add header for the table (Ranking, Opening, Scoreboard)
        results_list.append(html.Div([
            html.Div("Rank",
                     style={'width': '10%', 'display': 'inline-block', 'textAlign': 'center', 'fontWeight': 'bold'}),
            html.Div("Opening",
                     style={'width': '80%', 'display': 'inline-block', 'textAlign': 'center', 'fontWeight': 'bold'}),
            html.Div("Scoreboard",
                     style={'width': '10%', 'display': 'inline-block', 'textAlign': 'center', 'fontWeight': 'bold'}),
        ], className="result-header"))

        # Loop through sorted openings and display each one
        for i, (opening, scoreboard) in enumerate(sorted_openings.items(), start=1):
            white_score, black_score = scoreboard  # Now white_score and black_score are both lists [wins, draws, losses]
            formatted_scoreboard = f"White: {white_score[0]}-{white_score[1]}-{white_score[2]}, Black: {black_score[0]}-{black_score[1]}-{black_score[2]}"

            # Add results to the list in a structured format
            opening_id = {"type": "opening", "index": i}  # Give each opening a unique ID for pattern-matching callback
            results_list.append(html.Div([
                html.Div(f"{i}", style={'width': '10%', 'display': 'inline-block', 'textAlign': 'center'}),

                # Make the opening clickable
                html.Div([
                    html.A(
                        opening,
                        href="#",  # You can replace this with a real link or just keep it as "#" for now
                        id=opening_id,  # Set a unique ID to trigger the callback
                        style={'textDecoration': 'none', 'color': 'blue', 'cursor': 'pointer'}
                    )
                ], style={'width': '80%', 'display': 'inline-block', 'textAlign': 'center'}),

                html.Div(formatted_scoreboard,
                         style={'width': '10%', 'display': 'inline-block', 'textAlign': 'center'}),
            ], style={'display': 'flex', 'flexDirection': 'row', 'justifyContent': 'space-between',
                      'marginBottom': '20px'},
                className="result-item"))

            if i >= display:
                break

        # Return the layout with the results and stores - MOVED OUTSIDE THE LOOP
        return html.Div([
            html.H6(className="results-header"),
            html.Div(results_list, className="results-container"),
            dcc.Store(id='sorted-openings-store', data=sorted_openings),
            dcc.Store(id='display-count-store', data=display),  # Store the display count
            dcc.Store(id='opened-opening-store', data=None)
        ], style={"padding": "20px", "border": "1px solid #ccc", "border-radius": "5px",
                  "background-color": "#f9f9f9",
                  "margin-top": "20px", "font-size": "18px"})

    # Add callback to handle the click event using pattern matching
    @app.callback(
        Output('opened-opening-store', 'data'),
        [Input({"type": "opening", "index": ALL}, "n_clicks")],
        [State('sorted-openings-store', 'data'),
         State('display-count-store', 'data')]  # Get the display count from the store
    )
    def handle_opening_click(n_clicks_list, sorted_openings_data, display_count):
        ctx = callback_context
        if not ctx.triggered:
            return None

        trigger_id = ctx.triggered[0]['prop_id']
        import json
        # Parse the trigger_id to get the index
        try:
            # Extract the index from the trigger_id (e.g., {"type":"opening","index":3}.n_clicks)
            dict_str = trigger_id.split('.')[0]
            component_dict = json.loads(dict_str)
            clicked_index = component_dict.get('index', 0) - 1  # Convert to 0-based index

            # Get the list of openings and make sure we don't go out of bounds
            openings = list(sorted_openings_data.keys())
            if 0 <= clicked_index < len(openings) and clicked_index < display_count:
                Game.show_svg_board_of_pgn(openings[clicked_index])
                print(openings[clicked_index])  # You can do something else instead of printing, like displaying an image
                return openings[clicked_index]
        except:
            pass

        return None

    def layout(self):
        return dbc.Container([
            html.H2(f'{self.stats.sorter.username}', className='text-center mb-3 text-primary'),

            # **Sorted Openings Block**
            dbc.Card([
                dbc.CardHeader(html.H4("Sorted Openings", className="text-center text-warning")),

                # **Sort Openings - Collapsible Section**
                dbc.CardBody([
                    dbc.Button(
                        "sorting options ▼",
                        id="collapse-button",
                        color="primary",
                        outline=True,
                        className="w-100 text-start mb-2"
                    ),
                    dbc.Collapse(
                        dbc.CardBody([
                            html.Div([
                                html.H6("color", className="mb-2"),
                                dcc.RadioItems(
                                    id='color-filter',
                                    options=[
                                        {'label': ' white', 'value': Color.WHITE.value},
                                        {'label': ' black', 'value': Color.BLACK.value},
                                        {'label': ' both', 'value': -1},
                                    ],
                                    value=-1,
                                    inline=True,
                                    inputStyle={'margin-right': '10px', 'margin-left': '10px'},
                                )
                            ], className="mb-3"),

                            html.Div([
                                html.H6("result", className="mb-2"),
                                dcc.RadioItems(
                                    id='result-filter',
                                    options=[
                                        {'label': ' Win', 'value': Result.WIN.value},
                                        {'label': ' Draw', 'value': Result.DRAW.value},
                                        {'label': ' Loss', 'value': Result.LOSS.value},
                                        {'label': ' All', 'value': -1},
                                    ],
                                    value=-1,
                                    inline=True,
                                    inputStyle={'margin-right': '10px', 'margin-left': '10px'},
                                )
                            ], className="mb-3"),

                            html.Div([
                                html.H6("depth", className="mb-2"),
                                dbc.Row([
                                    dbc.Col(dcc.Slider(id='depth-filter', min=2, max=20, step=1, value=3), width=8),
                                ], className='align-items-center mb-2'),
                            ], className="mb-3"),

                            html.Div([
                                html.H6("display", className="mb-2"),
                                dbc.Row([
                                    dbc.Col(dcc.Slider(id='display-filter', min=5, max=20, step=1, value=10), width=8),
                                ], className='align-items-center mb-2'),
                            ], className="mb-3"),
                        ]),
                        id="sort-collapse",
                        is_open=True
                    ),
                ]),

                # **Filtered Results Section (Always Visible)**
                dbc.CardBody([
                    html.Div(id="filtered-results", className="p-2 border rounded bg-dark"),
                ])
            ], className='mb-3'),

            # **Ensure `opened-opening-store` is always part of the layout**
            dcc.Store(id='opened-opening-store', data=None),
            dcc.Store(id='sorted-openings-store', data={}),
            dcc.Store(id='display-count-store', data=10)
        ], fluid=True)


    def callback(self):
        # Toggle the collapse when clicking the button
        @app.callback(
            Output("sort-collapse", "is_open"),
            Output("collapse-button", "children"),
            Input("collapse-button", "n_clicks"),
            State("sort-collapse", "is_open"),
            prevent_initial_call=True
        )
        def toggle_collapse(n_clicks, is_open):
            new_open_state = not is_open
            button_text = "sorting options ▼" if new_open_state else "sorting options ▶"
            return new_open_state, button_text

        # Update results based on filters
        @app.callback(
            Output('filtered-results', 'children'),
            [
                Input('depth-filter', 'value'),
                Input('color-filter', 'value'),
                Input('result-filter', 'value'),
                Input('display-filter', 'value'),
            ]
        )
        def update_results(depth: int, color: int, result: int, display: int):
            return self.get_and_sort_opening_stats(depth, color, result, display)
