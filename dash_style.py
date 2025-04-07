'''
### class that handles things related to dash style
'''
from dash_bootstrap_components.themes import CYBORG


class DashStyle:
    small_width_int = 14
    SMALL_WIDTH = f'{small_width_int}%'
    BIG_WIDTH = f'{100 - (2 * small_width_int)}%'
    SLIDER_WIDTH = 8

    CYBORG_BLUE = '#00bcd4'
    CYBORG_ORANGE = '#f39c12'
    CYBORG_ORANGE_TRANS = 'rgba(243, 156, 18, 0.9)'
    CYBORG_GREEN = '#00ffae'
    CYBORG_RED = '#944'

    @staticmethod
    def get_landing_title_style(color=CYBORG_BLUE):
        return {
            'textAlign': 'center',
            'fontSize': '70px',
            'color': color
        }

    @staticmethod
    def get_landing_sub_title_style():
        return {
            'textAlign': 'center',
            'fontSize': '40px',
            'fontStyle': 'bold',
            'marginTop': '3rem',
            'marginBottom': '0rem',
            'color': DashStyle.CYBORG_BLUE
        }

    @staticmethod
    def get_score_div_style():
        return {
            'display': 'flex',
            'flexDirection': 'column',
            'alignItems': 'center',
            'justifyContent': 'center'
        }

    @staticmethod
    def get_user_button_style():
        return {
            'color': 'white',
            'textDecoration': 'underline',
            'backgroundColor': DashStyle.CYBORG_ORANGE_TRANS,
            'fontStyle': 'italic',
            'borderRadius': '25px',
            'border': 'none',
            'fontSize': '24px',
            'cursor': 'pointer',
            'padding': '5px 10px',
            'marginBottom': '10px'
        }

    @staticmethod
    def get_user_button_div_style():
        return {
                'maxHeight': '250px',
                'overflowY': 'auto',  # makes it scrollable
                'overflowX': 'hidden',  # no scrolling in X
                'display': 'flex',
                'flexWrap': 'wrap',
                'justifyContent': 'center',
                'gap': '20px',
                'maxWidth': '60%',
                'margin': 'auto',
                'padding': '20px 40px',
                'borderRadius': '25px'
            }

    @staticmethod
    def get_landing_style():
        return {
            'display': 'flex',
            'flexDirection': 'column',
            'justifyContent': 'center',
            'alignItems': 'center',
            'height': '100vh'
        }

    @staticmethod
    def get_user_input_style():
        return {
            'width': '100%',
            'height': '60px',
            'fontSize': '2rem',
            'textAlign': 'center',
            'borderRadius': '25px',
            'margin-right': '14px'
        }

    @staticmethod
    def get_enter_button_style():
        return {
            'fontSize': '1.6rem',
            'borderRadius': '30px',
            'backgroundColor': DashStyle.CYBORG_ORANGE,
            'color': 'white',
            'border': 'none',
        }

    @staticmethod
    def get_collapsable_button_style():
        return {
            'color': DashStyle.CYBORG_BLUE,
            'borderColor': DashStyle.CYBORG_BLUE,
            'width': '100%'
        }

    @staticmethod
    def get_header_style(style, font_size='20px'):
        style.update({'fontWeight': 'bold',
                      'fontSize': font_size})  # make headers bold
        return style

    @staticmethod
    def get_header_div_style(width):
        style = DashStyle.get_div_style(width, height='50px', border_bottom='3px solid gray')
        return DashStyle.get_header_style(style)

    @staticmethod
    def get_div_style(width='15%', height='auto', border_bottom='1px solid gray'):
        return {
            'width': width,
            'display': 'flex',
            'alignItems': 'center',
            'justifyContent': 'center',
            'height': height,
            'borderBottom': border_bottom
        }

    @staticmethod
    def get_column_options_style():
        return {
            'display': 'flex',
            'alignItems': 'center',
            'gap': '30px',
            'justifyContent': 'flex-start'
        }

    @staticmethod
    def get_div_a_style():
        return {
            'textDecoration': 'underline',
            'color': DashStyle.CYBORG_GREEN,
            'cursor': 'pointer',
            'textAlign': 'center',
            'whiteSpace': 'normal',
            'flexDirection': 'column',
            'justifyContent': 'center',
            'width': 'auto',
            'display': 'inline'
        }

    @staticmethod
    def get_class_style(margin='5px'):
        return {
            'display': 'flex',
            'flexDirection': 'row',
            'justifyContent': 'space-between',
            'marginBottom': margin
        }

    @staticmethod
    def get_alert_style():
        return {
            'width': 'fit-content',
            'font-size': '20px',
            'textAlign': 'center'
        }

    @staticmethod
    def get_navbar_style(hide: bool):
        display = 'none' if hide else 'block'
        return {
            'color': 'white',
            'border-radius': '5px',
            'borderColor': DashStyle.CYBORG_GREEN,
            'margin-top': '20px',
            'margin-left': '20px',
            'display': display,
            'font-size': '30px'
        }

    @staticmethod
    def get_navbar_full_style():
        return {
            'position': 'absolute',
            'top': '10px',
            'left': '10px',
            'zIndex': '999'  # always on top
        }

    @staticmethod
    def get_nav_bar_ind_style():
        return {
            'font-size': '20px',
            'border': '1px solid #666'
        }

    @staticmethod
    def get_navbar_div_style():
        return {
            'marginTop': '80px'
        }

    @staticmethod
    def get_page_style():
        return {
            'padding': '20px',
            'border': '1px solid #444',
            'border-radius': '5px',
            'background-color': '#222',
            'color': '#ddd',
            'margin-top': '20px',
            'font-size': '18px',
            'box-shadow': '2px 2px 10px rgba(0,0,0,0.5)'
        }

    @staticmethod
    def get_input_style():
        return {
            'margin-right': '10px',
            'margin-left': '10px',
            'margin-bottom': '30px',
            'cursor': 'pointer'
        }