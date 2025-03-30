"""
### run chess_py program
"""

import landing_page
import openings_page
import not_found_page

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
            refresh=True
        ),
        html.Div(
            id='page-content'
        )
    ])

    # register all pages (this allows for accessing them from different pages)
    app = landing_page.register_callbacks(app)
    app = openings_page.register_callbacks(app)

    @app.callback(
        Output('page-content', 'children'),
        Input('url', 'pathname')
    )
    def render_page(pathname):
        """handle URL routing here"""
        if pathname == '/landing':
            return landing_page.layout()
        elif pathname == '/openings':
            return openings_page.layout(app)
        else:
            return not_found_page.layout()

    # open and run
    webbrowser.open('http://localhost:8050/landing')
    app.run_server(debug=True, use_reloader=True)

if __name__ == '__main__':
    main()
