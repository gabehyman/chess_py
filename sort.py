import requests
import os
import json

from game import Game

valid_time_classes = ['rapid', 'bullet', 'blitz']

class Sort:
    def __init__(self, username: str):
        self.hdr_path: str = os.path.dirname(os.path.realpath(__file__)) + '/hdr.json'
        self.hdr = {'User-Agent': self.get_user_hdr()}

        self.db_path: str = os.path.dirname(os.path.realpath(__file__)) + '/db'
        if not os.path.isdir(self.db_path):
            os.makedirs(self.db_path)

        self.username: str = username
        self.user_db_path: str = self.db_path + f'/{self.username}'
        self.archive_urls: list[str] = self.pull_archive_urls()

        self.new_user =  not os.path.isdir(self.user_db_path)
        if self.new_user:
            os.makedirs(self.user_db_path)

        self.last_archive_url: str = ''
        self.last_game: int = 0
        self.games: list[Game] = []

        self.read_last_pull()
        self.read_local_games()

        for archive_url in self.archive_urls:
            tot_games_in_month = self.update_games(archive_url)

            if archive_url == self.archive_urls[-1]:
                self.write_last_pull(archive_url, tot_games_in_month-1)

        # TODO: what if no games
        self.games.sort(key=lambda game: game.start_time)

        self.first_month_year = Game.calc_month_index(self.games[0].start_time)

        self.new_user = False

    def get_user_hdr(self) -> str:
        if not os.path.exists(self.hdr_path):
            hdr = input('enter a valid chess.com email to query api: ').strip()
            with open(self.hdr_path, 'w') as file:
                json.dump({'hdr': hdr}, file, indent=4)

        else:
            with open(self.hdr_path, 'r') as file:
                hdr = json.load(file)['hdr']

        return hdr


    # get urls for archives per month
    def pull_archive_urls(self) -> list[str]:
        url = f'https://api.chess.com/pub/player/{self.username}/games/archives'
        response = requests.get(url, headers=self.hdr)
        if response.status_code != 200:
            print(f'error fetching archives: {response.status_code}')
            return []

        archives = response.json().get('archives', [])
        return archives

    # read games stored locally
    def read_local_games(self):
        if not self.new_user:
            for root, dirs, filenames in os.walk(self.user_db_path):
                # skip hidden dirs/files like .git, .DS_Store, etc. and just focus on .json
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                filenames = [f for f in filenames if f.startswith('game')]

                for filename in filenames:
                    file_path = os.path.join(root, filename)
                    with open(file_path, 'r') as file:
                        self.games.append(Game(json.load(file), self.username, True))

    # updates locally stored games to be up-to-date with remote and returns #games in archive
    def update_games(self, archive_url: str) -> int:
        if self.new_user:
            return self.pull_games(archive_url)

        # if we are looking at archives from the same month or after the last pull
        if Game.compare_archive_dates(self.last_archive_url, archive_url) <= 0:
            start_game = 0
            if archive_url == self.last_archive_url:
                start_game = self.last_game  # only update new games since last pull
            return self.pull_games(archive_url, start_game)

        return 0

    # get all the games played in that archive and rturns #valid games
    def pull_games(self, archive, start_game: int = 0) -> int:
        response = requests.get(archive, headers=self.hdr)
        if response.status_code != 200:
            print(f'error fetching games: {response.status_code}')
            return -1

        # filter to only look at valid games after the inputted start_game
        all_games = response.json().get('games', [])
        valid_games = [game for game in all_games if game['time_class'] in valid_time_classes]
        tot_valid_games: int = len(valid_games)
        games_to_write = valid_games[start_game:]

        self.write_games(games_to_write, archive, start_game)

        return tot_valid_games

    # write games to program data and database
    def write_games(self, games: list, archive: str, start_game: int):
        # save in program data
        for game in games:
            self.games.append(Game(game, self.username))

        # get user db path
        archive_split = archive.split('/')
        archive_path = self.user_db_path + f'/{archive_split[-2]}_{archive_split[-1]}'
        if not (os.path.isdir(archive_path)):
            os.makedirs(archive_path)

        # index of first game in games for those just added
        start_of_new_games: int = len(self.games) - len(games)
        for i, game in enumerate(self.games[start_of_new_games:]):
            with open(archive_path + f'/game{i+start_game}.json', 'w') as file:
                json.dump(game.dump, file, indent=4)

    # get info of when last pull was and read local games
    def read_last_pull(self):
        if not self.new_user:
            with open(self.user_db_path + '/last_pull.json', 'r') as file:
                last_pull = json.load(file)
                self.last_archive_url = last_pull['archive_url']
                self.last_game = last_pull['last_game']

    # update last_pull.json
    def write_last_pull(self, archive_url: str, last_game: int):
        last_pull = {
            'archive_url': archive_url,
            'last_game': last_game
        }

        with open(self.user_db_path + '/last_pull.json', 'w') as file:
            json.dump(last_pull, file, indent=4)

