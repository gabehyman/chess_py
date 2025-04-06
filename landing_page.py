"""
### initial page of program where user enters username
"""

from dash import html, dcc, Input, Output, State, ALL, callback_context, no_update
import dash_bootstrap_components as dbc

from dash_style import DashStyle
from sort import Sort

def register_callbacks(app):
    @app.callback(
        [Output('user-alert-box', 'children'),
         Output('user-alert-box', 'is_open'),
         Output('user-alert-box', 'color'),
         Output('url', 'pathname'),
         Output('hidden-output', 'children')],
        [Input({'type': 'username-btn', 'index': ALL}, 'n_clicks'),
         Input('submit-button', 'n_clicks'),
         Input('username-input', 'n_submit')],
        [State('username-input', 'value'),
         State('selected-username', 'data')],
        prevent_initial_call=True
    )
    def handle_username_entry(user_btn_clicks, submit_button_click, enter_pressed, username_input, preloaded_username):
        """
        ### handle multiple user inputs (pressing enter, clicking the button or clicking preloaded user)
        ### also pop up alerts if invalid user and show sweet dash cube loading icon
        """

        # callback context for selecting preloaded user dash buttons
        triggered_id = callback_context.triggered_id

        # populate clicked_username if we click one
        clicked_username = None
        if isinstance(triggered_id, dict) and triggered_id.get('type') == 'username-btn':
            clicked_username = triggered_id['index']

        # if no username clicked, must have inputted a username
        username = clicked_username if clicked_username else username_input

        if username:
            # only sort valid users
            valid_user: int = Sort.is_user_valid(username)
            if valid_user == 0:  # 0 = valid user with games played
                # loading cube will show
                sorter: Sort = Sort(username.lower())

                # populate app.server.config with program data you need
                app.server.config['username'] = sorter.username
                app.server.config['games_container'] = sorter.games_container
                app.server.config['games_lock'] = sorter.games_lock
                app.server.config['is_eval_done_container'] = sorter.is_eval_done_container
                app.server.config['opening_stats'] = None
                app.server.config['last_depth'] = None
                app.server.config['color'] = None
                app.server.config['selected_time_classes'] = None

                # no update to alert box and go to openings page
                return no_update, False, no_update, '/openings', ''

            else:
                if valid_user == 1: # 1 = user doesn't exist
                    return 'user does not exist, try again.', True, 'danger', no_update, no_update

            # 2 = user has no games
            return 'user has no games to analyze, try again.', True, 'danger', no_update, no_update

        # nothing happened so no update
        return no_update, False, no_update, no_update, no_update

    return app

def layout():
    """main layout of page"""
    # get users already loaded and stored in db for quick access
    usernames: list[str] = Sort.preloaded_usernames()

    return html.Div([
        html.H1(
            'enter a chess.com username',
                style=DashStyle.get_landing_title_style()
        ),
        html.Div([
            dcc.Input(
                id='username-input',
                placeholder='e.g., magnuscarlsen',
                type='text',
                className='form-control',
                style=DashStyle.get_user_input_style()
            ),
            html.Button(
                '➡',
                id='submit-button',
                type='button',
                style=DashStyle.get_enter_button_style()
            ),
        ], style=DashStyle.get_div_style(
            width='40%',
            height='100px',
            border_bottom='')
        ),

        # alert user if user not valid
        dbc.Alert(id='user-alert-box',
            is_open=False,
            dismissable=True,
            duration=4000,  # auto close after 6 seconds
            style=DashStyle.get_alert_style()
        ),

        # store to handle username from button click
        dcc.Store(id='selected-username'),
        #grid for previous usernames
        html.Div([
            html.H1(
                'quick load:',
                    style=DashStyle.get_landing_sub_title_style()
            ),
            html.Div([
                html.Button(
                    name,
                    id={'type': 'username-btn', 'index': name},
                    n_clicks=0,
                    style=DashStyle.get_user_button_style()
                )
                for name in usernames
            ],
                # always show scrollbar if scrollable and make it cyborg blue
                className='scrollable-wrapper',
                style=DashStyle.get_user_button_div_style()
            )
        ],
            # only show if we have usernames in db
            id='username-buttons',
            style={'display': 'none' if not usernames else 'block'}
        ),

        # show loading icon when waiting for sorter to sort
        dcc.Loading(
            id='loading-icon',
            type='cube',
            color=DashStyle.CYBORG_GREEN,
            children=html.Div(id='hidden-output')
        )
    ], style=DashStyle.get_landing_style()
    )