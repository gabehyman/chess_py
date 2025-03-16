"""
### run chess_py program
"""
from sort import Sort

from dash import Dash, dcc
import dash_bootstrap_components as dbc
import webbrowser
import user_page
import openings_page

def main():
    username = input('enter chess.com username: ').strip()

    sorter: Sort = Sort(username)

    print(f'total time to load = {sorter.time_to_sort:.2f} seconds')
    print(f'total# games = {len(sorter.games)}')

    # initiate app with theme
    app = Dash(__name__, external_stylesheets=[dbc.themes.CYBORG], suppress_callback_exceptions=True)

    # add program data into dict
    app.server.config['username'] = sorter.username
    app.server.config['games'] = sorter.games

    # to avoid having to sort everytime if depth and color don't change
    app.server.config['opening_stats'] = None
    app.server.config['last_depth'] = None
    app.server.config['color'] = None

    # register all pages (this allows accessing them from different files)
    app = openings_page.register_callbacks(app)

    # open and run
    webbrowser.open("http://localhost:8050/user-home")
    app.run_server(debug=True)

if __name__ == '__main__':
    main()
