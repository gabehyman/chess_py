from dash import html, dcc
import dash_bootstrap_components as dbc

from sort import Sort
from stats import Stats
from game import Game

from dash_style import DashStyle

def layout(app):
    # don't have to write out app.server.config['sorter'] each time
    sorter: Sort = app.server.config['sorter']

    game_time_per_month: list[float] =  Stats.calc_game_time_per_month(app.server.config['games_container']['games'],
                                                          sorter.num_months_active,
                                                          sorter.first_month_index)
    month_indices_str: list[str] = [Game.month_index_to_str_months(sorter.first_month_index + i)
                                         for i in range(sorter.num_months_active)]

    game_time_per_month_fig = Stats.create_plotly_fig([Stats.seconds_to_hrs(time) for time in game_time_per_month], month_indices_str,
                            ['month', 'time played (hrs)'], DashStyle.CYBORG_GREEN)

    return dbc.Container([
        # title as header so it scales properly
        html.H1(
            f'{sorter.username}\'s game time per month'
            f' (total time = {Stats.seconds_to_days_str(sum(game_time_per_month))})',  # call it here
            className="text-center mb-3",
            style={
                "color": 'white',
                "fontSize": "24px",
                "whiteSpace": "normal",  # allow text to wrap
                "wordWrap": "break-word",
            }
        ),
        dcc.Graph(
            id='game-time-plot',
            figure=game_time_per_month_fig
        )
    ])
