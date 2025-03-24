"""
### page that handles all things related to openings
"""

from dash import Dash, dcc, html, Input, Output, State, callback_context, ALL
import dash_bootstrap_components as dbc
import json

from dash_style import DashStyle

from stats import Stats
from game import Game
from game import Result
from game import Color

def format_scoreboard(score: list[int], color='white'):
    return f'{color}: {score[0]}-{score[1]}-{score[2]}'

def create_results_list(sorted_openings, display, color):
    """populate list of all openings based on sort"""
    results_list = [
        # header of list
        html.Div([
            html.Div(
                'rank',
                style=DashStyle.get_header_div_style(DashStyle.SMALL_WIDTH)
            ),
            html.Div(
                'opening (click to open in chess.com)',
                style=DashStyle.get_header_div_style(DashStyle.BIG_WIDTH)
            ),
            html.Div(
                'record',
                     style=DashStyle.get_header_div_style(DashStyle.SMALL_WIDTH)
            ),
        ],
            className='result-header',
            style=DashStyle.get_class_style('10px')
        )
    ]

    # iterate through sorted dict
    for i, (opening, performance) in enumerate(sorted_openings.items(), start=1):
        white_score, black_score, board_eval = performance
        board_eval_formatted = f'eval = {Game.eval_to_mate_str(board_eval[0], color)}'

        opening_id = {'type': 'opening', 'index': i}

        # conditionally display scores based on selections
        if color == Color.WHITE.value:
            color_score_display = html.Div([
                    html.Span(format_scoreboard(white_score))
                ], style=DashStyle.get_score_div_style())
        elif color == Color.BLACK.value:
            color_score_display = html.Div([
                html.Span(format_scoreboard(black_score, 'black'))
            ], style=DashStyle.get_score_div_style())
        else:
            color_score_display = html.Div([
                html.Span(format_scoreboard(white_score)),
                html.Span(format_scoreboard(black_score, 'black'))
            ], style=DashStyle.get_score_div_style())  # stack outputs

        results_list.append(html.Div([
            # rank
            html.Div(
                f'{i})',
                style=DashStyle.get_div_style(DashStyle.SMALL_WIDTH)
            ),
            # opening
            html.Div([
                html.A(
                    opening,
                    href='#',
                    id=opening_id,
                    style=DashStyle.get_div_a_style()
                )
            ], style=DashStyle.get_div_style(DashStyle.BIG_WIDTH)
            ),
            # record
            html.Div([
                color_score_display,
                html.Span(board_eval_formatted)
            ], style={**DashStyle.get_div_style(DashStyle.SMALL_WIDTH), 'flexDirection': 'column'})  # stack outputs
        ],
            className='result-item',
            style=DashStyle.get_class_style(margin='5px')
        ))

        # only show based on display# selected by user
        if i >= display:
            break

    return html.Div([
        html.H6(
            className='results-header'
        ),
        html.Div(
            results_list,
            className='results-list'
        ),
        dcc.Store(
            id='sorted-openings-store',
            data=sorted_openings
        ),
        dcc.Store(
            id='display-count-store',
            data=display
        ),
        dcc.Store(
            id='opened-opening-store',
            data=None
        )
    ], style=DashStyle.get_page_style()
    )

def register_callbacks(app):
    @app.callback(
        Output('opened-opening-store', 'data'),
        [Input({'type': 'opening', 'index': ALL}, 'n_clicks')],
        [State('sorted-openings-store', 'data'),
         State('display-count-store', 'data')]  # Get the display count from the store
    )
    def handle_opening_click(n_clicks_list, sorted_openings_data, display_count):
        """callback to handle the click event using pattern matching"""
        ctx = callback_context
        if not ctx.triggered:
            return None

        # parse the trigger_id to get the index
        trigger_id = ctx.triggered[0]['prop_id']

        try:
            # extract the index from the trigger_id (e.g., {'type':'opening','index':3}.n_clicks)
            dict_str = trigger_id.split('.')[0]
            component_dict = json.loads(dict_str)
            clicked_index = component_dict.get('index', 0) - 1  # convert to 0-based index

            # get the list of openings and make sure we don't go out of bounds
            openings = list(sorted_openings_data.keys())
            if 0 <= clicked_index < len(openings) and clicked_index < display_count:
                Game.open_pgn_in_chess_com(openings[clicked_index])
                return openings[clicked_index]
        except:
            pass

        return None

    @app.callback(
        Output('sort-collapse', 'is_open'),
        Output('collapse-button', 'children'),
        Input('collapse-button', 'n_clicks'),
        State('sort-collapse', 'is_open'),
        prevent_initial_call=True
    )
    def toggle_collapse(n_clicks, is_open):
        """handle the collapsing and opening of sorting options"""
        new_open_state = not is_open
        button_text = 'options ▼' if new_open_state else 'options ▶'
        return new_open_state, button_text

    @app.callback(
        Output('filtered-results', 'children'),
        [Input('type-filter', 'value'),
         Input('color-filter', 'value'),
         Input('mates-filter', 'value'),
         Input('result-filter', 'value'),
         Input('order-filter', 'value'),
         Input('time-class-filter', 'value'),
         Input('depth-filter', 'value'),
         Input('display-filter', 'value'),
         Input('eval-status-checker', 'n_intervals')]
    )
    def update_results(filter_type, color, mates, result, order, time_classes, depth, display, checker_n):
        # force update the results if we just finished eval processing
        is_not_eval_done_trigger = not callback_context.triggered[0]['prop_id'].startswith('eval-status-checker')

        with app.server.config['games_lock']:
            games = app.server.config['games_container']['games']

        if (is_not_eval_done_trigger and depth == app.server.config['last_depth'] and
                color == app.server.config['color'] and app.server.config['selected_time_classes'] == time_classes):
            openings_stats = app.server.config['opening_stats']
        else:
            openings_stats = Stats.get_opening_stats(games, depth, color, time_classes)
            app.server.config['opening_stats'] = openings_stats
            app.server.config['last_depth'] = depth
            app.server.config['color'] = color
            app.server.config['selected_time_classes'] = time_classes

        sorted_openings = Stats.sort_opening_stats(openings_stats, filter_type, color, mates, result, order)
        return create_results_list(sorted_openings, display, color)

    @app.callback(
        [Output('result-filter-container', 'style'),
         Output('mates-filter-container', 'style')],
        Input('type-filter', 'value')
    )
    def toggle_sort_by_containers(selected_sort):
        """hide/display result/color info based on what were sorting by"""
        if selected_sort == 1:
            return {'display': 'block'}, {'display': 'none'}  # show result, hide mate
        return {'display': 'none'}, {'display': 'block'}  # show mate, hide result

    @app.callback(
        Output('type-filter', 'options'),
        Output('eval-status-checker', 'disabled'),
        Input('eval-status-checker', 'n_intervals'),
    )
    def show_eval_when_done(n):
        is_eval_done = app.server.config['is_eval_done_container']['is_eval_done']
        options = [
            {'label': ' eval', 'value': 0, 'disabled': not is_eval_done},
            {'label': ' record', 'value': 1}
        ]
        return options, is_eval_done

    return app

def layout(app):
    """main layout of page"""
    return dbc.Container([
        # store stats object
        dcc.Store(
            id='stats-store',
            storage_type='session'
        ),
        html.H1(
            app.server.config['username'],
            className='text-center mb-3 text-primary'
        ),
        dbc.Card([
            dbc.CardHeader(
                html.H2(
                    'openings',
                    className='text-center text-warning'
                )
            ),
            dbc.CardBody([
                dbc.Button(
                    'options ▼',
                    id='collapse-button',
                    color='primary',
                    outline=True,
                    className='w-100 text-start mb-2',
                    style=DashStyle.get_collapsable_button_style()
                ),
                # all sorting option in collapsable block
                dbc.Collapse(
                    dbc.CardBody([
                        html.Div([
                            # sort by eval or record (= frequency)
                            html.Div([
                                html.H6(
                                    'sort by:',
                                    style=DashStyle.get_header_style({})
                                ),
                                dcc.RadioItems(id='type-filter',
                                               options=[{'label': ' record', 'value': 1}],  # exclude eval until it is ready
                                               value=1,
                                               inline=True,
                                               className="custom-radio",
                                               inputStyle=DashStyle.get_input_style(),
                                )
                            ]),
                            # focus on user color
                            html.Div([
                                html.H6(
                                    'color:',
                                    style=DashStyle.get_header_style({})
                                ),
                                dcc.RadioItems(
                                    id='color-filter',
                                   options=[{'label': ' white', 'value': Color.WHITE.value},
                                            {'label': ' black', 'value': Color.BLACK.value},
                                            {'label': ' both', 'value': -1}],
                                   value=-1,
                                   inline=True,
                                   className="custom-radio",
                                   inputStyle=DashStyle.get_input_style()
                                )
                            ]),
                            # conditionally shown if sorting by result
                            html.Div([
                                html.H6(
                                    'result:',
                                        style=DashStyle.get_header_style({})
                                        ),
                                dcc.RadioItems(
                                    id='result-filter',
                                    options=[{'label': ' win', 'value': Result.WIN.value},
                                            {'label': ' draw', 'value': Result.DRAW.value},
                                            {'label': ' loss', 'value': Result.LOSS.value},
                                            {'label': ' all', 'value': -1}],
                                   value=-1,
                                   inline=True,
                                   className="custom-radio",
                                   inputStyle=DashStyle.get_input_style()
                                )
                            ], id='result-filter-container'
                            ),
                            # conditionally shown if sorting by eval
                            html.Div([
                                html.H6(
                                    'mates:',
                                        style=DashStyle.get_header_style({})
                                        ),
                                dcc.RadioItems(id='mates-filter',
                                               options=[{'label': ' only', 'value': 0},
                                                        {'label': ' exclude', 'value': 1},
                                                        {'label': ' include', 'value': -1}],
                                               value=-1,
                                               inline=True,
                                               className="custom-radio",
                                               inputStyle=DashStyle.get_input_style()
                                )
                            ], id='mates-filter-container'
                            )
                        ], style=DashStyle.get_column_options_style()
                        ),
                        # how to sort
                        html.Div([
                            html.Div([
                                html.H6('order by:',
                                        style=DashStyle.get_header_style({})
                                ),
                                dcc.RadioItems(
                                    id='order-filter',
                                    options=[{'label': ' low->high', 'value': 0},
                                             {'label': ' high->low', 'value': 1}],
                                    value=1,
                                    inline=True,
                                    className='custom-radio',
                                    inputStyle=DashStyle.get_input_style()
                                ),
                            ]),
                            html.Div([
                                html.H6('time class:',
                                        style=DashStyle.get_header_style({})
                                ),
                                dcc.Checklist(
                                    id='time-class-filter',
                                    options=[
                                        {'label': f' {Stats.time_classes[0]}', 'value': f'{Stats.time_classes[0]}'},
                                        {'label': f' {Stats.time_classes[1]}', 'value': f'{Stats.time_classes[1]}'},
                                        {'label': f' {Stats.time_classes[2]}', 'value': f'{Stats.time_classes[2]}'},
                                        {'label': f' {Stats.time_classes[3]}', 'value': f'{Stats.time_classes[3]}'}],
                                    value=Stats.time_classes,
                                    inline=True,
                                    className='custom-checklist',
                                    inputStyle=DashStyle.get_input_style()
                                )
                            ])
                        ], style=DashStyle.get_column_options_style()
                        ),
                        # depth of shown openings
                        html.Div([
                            html.H6('depth of opening:',
                                    style=DashStyle.get_header_style({})
                            ),
                            dbc.Row([
                                dbc.Col(
                                    dcc.Slider(
                                        id='depth-filter',
                                        min=2, max=20, step=1, value=3
                                    ),
                                    width=DashStyle.SLIDER_WIDTH,
                                    className='custom-slider'
                                ),
                            ], className='align-items-center mb-2'
                            ),
                        ], className='mb-3'
                        ),
                        # how many openings to show
                        html.Div([
                            html.H6(
                                '#openings to display:',
                                    style=DashStyle.get_header_style({})
                            ),
                            dbc.Row([
                                dbc.Col(
                                    dcc.Slider(
                                        id='display-filter',
                                        min=10, max=100, step=10, value=20
                                    ),
                                    width=DashStyle.SLIDER_WIDTH,
                                    className='custom-slider'
                                ),
                            ], className='align-items-center mb-2'
                            ),
                        ], className='mb-3'
                        ),
                    ]),
                    id='sort-collapse', is_open=True
                ),
            ]),

            dbc.CardBody([
                html.Div(
                    id='filtered-results',
                    className='p-2 border rounded bg-dark'
                )
            ])
        ], className='mb-3'),

        # ensure opened-opening-store is always part of the layout
        dcc.Store(
            id='sorted-openings-store',
            data={}
        ),
        dcc.Store(
            id='opened-opening-store',
            data=None
        ),
        dcc.Store(
            id='display-count-store',
            data=None),
        # check for evals to come in every 2 seconds until they are ready (then no more)
        dcc.Interval(
            id='eval-status-checker',
            interval=2000, n_intervals=0
        )
    ], fluid=True
    )