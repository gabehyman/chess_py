"""
### run chess_py program
"""
from sort import Sort
import landing_page
import openings_page

from dash import Dash, html, dcc, Input, Output
import dash_bootstrap_components as dbc
import webbrowser

def main():
    # initiate app with theme
    app = Dash(__name__, external_stylesheets=[dbc.themes.CYBORG],
               suppress_callback_exceptions=True)

    # to avoid having to sort everytime if depth and color don't change
    app.server.config['username'] = None
    app.server.config['games'] = None
    app.server.config['opening_stats'] = None
    app.server.config['last_depth'] = None
    app.server.config['color'] = None

    # global layout
    app.layout = html.Div([
        dcc.Location(id="url", refresh=True),
        html.Div(id="page-content")
    ])

    # register all pages (this allows accessing them from different files)
    app = landing_page.register_callbacks(app)
    app = openings_page.register_callbacks(app)

    # handle URL routing here
    @app.callback(
        Output("page-content", "children"),
        Input("url", "pathname")
    )
    def render_page(pathname):
        if pathname == "/landing":
            return landing_page.layout()
        elif pathname == "/openings":
            return openings_page.layout(app)
        else:
            return html.H1("404 - page not found")

    # open and run
    webbrowser.open("http://localhost:8050/landing")
    app.run_server(debug=True, use_reloader=False)

if __name__ == '__main__':
    main()
