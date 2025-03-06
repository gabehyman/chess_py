from sort import Sort


def main():
    username = input('enter chess.com username: ').strip()

    sorter: Sort = Sort(username)


if __name__ == '__main__':
    main()
