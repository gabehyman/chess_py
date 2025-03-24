"""
### page shown if the URL is no good
"""

from dash import html
from dash_style import DashStyle

def layout():
    """main layout of page"""
    return html.Div([
        html.H1(
            'pAge NOt fOUnD',
            className='glitch',
            style=DashStyle.get_landing_title_style(DashStyle.CYBORG_ORANGE)
        ),
        html.A(
            'tAKe mE hOmE',
            href='/landing',
            className='glitch',
            style=DashStyle.get_landing_sub_title_style()
        )
    ], style=DashStyle.get_landing_style()
    )