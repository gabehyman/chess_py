"""
### initial page of program where user enters username
"""

from dash import html, dcc, Input, Output, State, ALL

from dash_style import DashStyle
from sort import Sort


def register_callbacks(app):
    @app.callback(
        [Output("hidden-output", "children"),
         Output("url", "pathname")],
        [Input("submit-button", "n_clicks"),
         Input("username-input", "n_submit"),
         Input({'type': 'username-btn', 'index': ALL}, 'n_clicks')],
        [State("username-input", "value"),
         State("selected-username", "data")],
        prevent_initial_call=True
    )
    def handle_username_entry(n_clicks, n_submit, button_clicks, value, selected_username):
        """handle username entry and populate app.server.config fields"""

        # check if any quick load user was clicked
        clicked_username = None
        if any(button_clicks):
            clicked_index = button_clicks.index(1)  # find the index of the button clicked
            clicked_username = Sort.preloaded_usernames()[clicked_index]

        # prioritize button click, fallback to input
        username = clicked_username if clicked_username else value

        if username:
            sorter: Sort = Sort(username)

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
    # get users already loaded and stored in db for quick access
    usernames: list[str] = Sort.preloaded_usernames()

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



        # store to handle username from button click
        dcc.Store(id="selected-username"),
        html.H1("quick load:",
                style=DashStyle.get_landing_sub_title_style()),
        #grid for previous usernames
        html.Div([
            html.Div([
                html.Button(name, id={'type': 'username-btn', 'index': name}, n_clicks=0,
                            style=DashStyle.get_user_button_style())
                for name in usernames
            ], style=DashStyle.get_user_button_div_style())
        ], id="username-buttons", style={'display': 'none' if not usernames else 'block'}),  # only show if we have

        # show loading icon when waiting for sorter to sort
        dcc.Loading(
            id="loading-icon",
            type="cube",
            children=html.Div(id="hidden-output")
        ),
        html.Div(id="output-username"),
        dcc.Location(id="url", refresh=True),
    ], style=DashStyle.get_landing_style())