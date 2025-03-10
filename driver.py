"""
### run chess_py program
"""
from sort import Sort
from stats import Stats
from ui import UI


def main():
    # username = input('enter chess.com username: ').strip()
    username = 'majella10'
    username = 'enpassantethyb'
    username = 'grootmeestergabe'

    sorter: Sort = Sort(username)

    print(f'total time to load = {sorter.time_to_sort:.2f} seconds')
    print(f'total# games = {len(sorter.games)}')

    statser: Stats = Stats(sorter)
    # statser.plotly_plot_game_time_per_month()
    # print(statser.opening_stats)
    # print(statser.opponent_stats)

    ui = UI(statser)
    ui.show_layout()

if __name__ == '__main__':
    main()
