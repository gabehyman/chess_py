"""
### initial page of program where user enters username
"""

from dash import html, dcc, Input, Output, State

from dash_style import DashStyle
from sort import Sort


def register_callbacks(app):
    @app.callback(
        [Output("hidden-output", "children"),
         Output("url", "pathname")],  # For redirecting after function completes
        [Input("submit-button", "n_clicks"),
         Input("username-input", "n_submit")],
        [State("username-input", "value")],
        prevent_initial_call=True
    )
    def handle_username_entry(n_clicks, n_submit, value):
        """handle username entry and populate app.server.config fields"""
        if (n_clicks > 0 or n_submit) and value:
            sorter: Sort = Sort(value)

            # add program data into dict
            app.server.config['username'] = sorter.username
            app.server.config['games'] = sorter.games

            # to avoid having to sort everytime if depth and color don't change
            app.server.config['opening_stats'] = None
            app.server.config['last_depth'] = None
            app.server.config['color'] = None

            return "", "/openings"

        return "", "/landing"

    return app

def layout():
    """main layout of page"""
    return html.Div([
        html.H1("enter a chess.com username",
                style=DashStyle.get_landing_title_style()),
        html.Div([
            dcc.Input(
                id="username-input",
                type="text",
                placeholder="e.g., magnuscarlsen",
                n_submit=0,
                debounce=True,
                style=DashStyle.get_user_input_style()
            ),
            html.Button("➡", id="submit-button", n_clicks=0,
                        style=DashStyle.get_enter_button_style()),
        ], style=DashStyle.get_div_style(width='40%', height='100px', border_bottom='')),
        # show loading icon when waiting for sorter to sort
        dcc.Loading(
            id="loading-icon",
            type="cube",
            children=html.Div(id="hidden-output"),
            style={
                "position": "absolute",
                "top": "60%",  # Move it further down
                "left": "50%",
                "transform": "translate(-50%, -50%)",  # Center horizontally
                "fontSize": "100px",  # Make it bigger
            }
        ),
        html.Div(id="output-username"),
        dcc.Location(id="url", refresh=True),
    ], style=DashStyle.get_landing_style())