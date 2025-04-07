from dash import html
from dash_style import DashStyle

import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State

def get_navbar(hide: bool):
    return html.Div([
        # actual button
        dbc.Button(
            '☰',
            id='navbar-toggle',
            className='me-2',
            outline=True,
            color='light',
            n_clicks=0,
            style=DashStyle.get_navbar_style(hide)
        ),
        # collapsable options with all pages
        dbc.Collapse(
            dbc.Nav(
                [
                    dbc.NavLink(
                        'landing',
                        href='/landing',
                        active='exact',
                        id='landing-link',
                        style=DashStyle.get_nav_bar_ind_style()
                    ),
                    dbc.NavLink(
                        'user',
                        href='/user',
                        active='exact',
                        id='user-link',
                        style=DashStyle.get_nav_bar_ind_style()
                    ),
                    dbc.NavLink(
                        'openings',
                        href='/openings',
                        active='exact',
                        id='openings-link',
                        style=DashStyle.get_nav_bar_ind_style()
                    )
                ],
                pills=True,
                navbar=True,
                horizontal='start'
            ),
            id='navbar-collapse',
            is_open=False,
            className='mt-2'
        )
    ], style=DashStyle.get_navbar_full_style())

def register_navbar_callbacks(app):
    @app.callback(
        Output('navbar-collapse', 'is_open'),
        Input('navbar-toggle', 'n_clicks'),
        State('navbar-collapse', 'is_open'),
    )
    def toggle_navbar(navbar_click, is_navbar_open):
        """if clicked on, change open state"""
        if navbar_click:
            return not is_navbar_open
        return is_navbar_open