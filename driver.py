"""
### run chess_py program
"""
import user_page
import landing_page
import openings_page
import not_found_page
import navigation_bar
from dash_style import DashStyle

from dash import Dash, html, dcc, Input, Output
import dash_bootstrap_components as dbc
import webbrowser

def main():
    """initiate app with theme"""
    app = Dash(__name__, external_stylesheets=[dbc.themes.CYBORG],
               suppress_callback_exceptions=True)

    # global layout
    app.layout = html.Div([
        dcc.Location(
            id='url', 
            refresh=False
        ),
        html.Div(id='navbar-container'),  # control nav bar here
        html.A(
            html.H1(
                id='username-header',
                className='text-center mb-3'
            ),
            id='username-link',
            href="#",  # placeholder, will be updated dynamically with users profile
            target="_blank",
            style={"textDecoration": "none"}
        ),
        html.Div(id='page-content')
    ])

    # register all pages (this allows for accessing them from different pages)
    landing_page.register_callbacks(app)
    navigation_bar.register_navbar_callbacks(app)
    openings_page.register_callbacks(app)

    # need to initialize for header display
    app.server.config['sorter'] = None

    @app.callback(
        [Output('page-content', 'children'),
         Output('navbar-container', 'children'),
         Output('navbar-container', 'style'),
         Output('username-header', 'children'),
         Output('username-header', 'style'),
         Output('username-link', 'href')],  # <-- new output for link
        Input('url', 'pathname')
    )
    def render_page(pathname):
        """handle page routing and navbar/username header display"""
        layout = not_found_page.layout()
        if pathname == '/landing':
            layout = landing_page.layout()
        elif pathname == '/user':
            layout = user_page.layout(app)
        elif pathname == '/openings':
            layout = openings_page.layout(app)

        hide = pathname not in ['/user', '/openings']

        username = None
        username_link = "#"
        if app.server.config['sorter'] is not None:
            username = app.server.config['sorter'].username
            username_link = f"https://www.chess.com/member/{username}"

        return (layout, navigation_bar.get_navbar(hide), DashStyle.get_navbar_div_style(hide), username,
                DashStyle.get_username_header_style(hide), username_link)

    # open and run on landing page
    webbrowser.open('http://localhost:8050/landing')
    app.run_server(debug=False, use_reloader=True)

if __name__ == '__main__':
    main()
