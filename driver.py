"""
### run chess_py program
"""
from sort import Sort


def main():
    username = input('enter chess.com username: ').strip()
    sorter: Sort = Sort(username)

    print(f'total time to load = {sorter.time_to_sort:.2f} seconds')
    print(f'total# games = {len(sorter.games)}')


if __name__ == '__main__':
    main()
