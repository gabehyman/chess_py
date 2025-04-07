from dash import html, dcc
import dash_bootstrap_components as dbc


def layout(app):
    return dbc.Container([
        html.H1(
            app.server.config['username'],
            className='text-center mb-3 text-primary'
        )
    ])
