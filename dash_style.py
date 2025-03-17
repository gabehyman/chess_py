"""
### class that handles things related to dash style
"""

class DashStyle:
    small_width_int = 15
    SMALL_WIDTH = f'{small_width_int}%'
    BIG_WIDTH = f'{100 - (2 * small_width_int)}%'
    SLIDER_WIDTH = 8

    @staticmethod
    def get_landing_title_style():
        return {
            "textAlign": "center",
            "fontSize": "70px",
            "color": "#00bcd4"
        }

    @staticmethod
    def get_landing_sub_title_style():
        return {
            "textAlign": "center",
            "fontSize": "40px",
            'fontStyle': 'bold',
            "marginTop": "6rem",
            "marginBottom": "1rem",
            "color": "#00bcd4"  # cyborg blue
        }

    @staticmethod
    def get_user_button_style():
        return {
            'color': 'white',  # Cyborg orange
            'textDecoration': 'underline',
            'backgroundColor': 'rgba(243, 156, 0, 0.9)',
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
                'display': 'flex',
                'flexWrap': 'wrap',
                'justifyContent': 'center',
                'gap': '20px',
                'maxWidth': '60%',
                'margin': 'auto'
            }

    @staticmethod
    def get_landing_style():
        return {
            "display": "flex",
            "flexDirection": "column",
            "justifyContent": "center",
            "alignItems": "center",
            "height": "100vh"
        }

    @staticmethod
    def get_user_input_style():
        return {
            "width": "100%",
            "height": "60px",
            "fontSize": "2rem",
            "textAlign": "center",
            'borderRadius': '25px',
            'margin-right': '14px'
        }

    @staticmethod
    def get_enter_button_style():
        return {
            "fontSize": "1.6rem",
            "borderRadius": "30px",
            "backgroundColor": "#f39c12",
            "color": "white",
            "border": "none",
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
    def get_div_style(width='15%', height='90px', border_bottom='1px solid gray'):
        return {
            'width': width,
            'display': 'flex',
            'alignItems': 'center',
            'justifyContent': 'center',
            'height': height,
            'borderBottom': border_bottom
        }

    @staticmethod
    def get_div_a_style():
        return {
            'textDecoration': 'underline',
            'color': 'light blue',
            'cursor': 'pointer',
            'textAlign': 'center',
            'whiteSpace': 'normal',
            'display': 'flex',
            'flexDirection': 'column',
            'justifyContent': 'center',
            'width': '100%'
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
            'margin-bottom': '30px'
        }