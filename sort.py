import requests
import os
import json
import time

from game import Game

valid_time_classes = ['rapid', 'bullet', 'blitz']

class Sort:
    def __init__(self, username: str):
        start_time = time.time()

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

        self.engine_limit = Game.create_engine()

        self.read_last_pull()
        self.read_local_games()

        for archive_url in self.archive_urls:
            tot_games_in_month = self.update_games(archive_url)

            if archive_url == self.archive_urls[-1]:
                self.write_last_pull(archive_url, tot_games_in_month-1)

        # TODO: what if no games
        self.games.sort(key=lambda game: game.start_time)

        self.first_month_year = Game.date_to_month_index(self.games[0].start_time)
        self.last_month_year = Game.date_to_month_index(self.games[-1].start_time)
        self.num_months_active = self.last_month_year - self.first_month_year + 1

        self.new_user = False

        Game.quit_engine(self.engine_limit[0])

        end_time = time.time()

        self.time_to_sort: float = end_time - start_time

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
                        self.games.append(Game(json.load(file), self.username, self.engine_limit, True))

    # updates locally stored games to be up-to-date with remote and returns #games in archive
    def update_games(self, archive_url: str) -> int:
        if self.new_user:
            return self.pull_games(archive_url)

        # if we are looking at archives from the same month or after the last pull
        if Game.compare_archive_dates(self.last_archive_url, archive_url) <= 0:
            last_game_in_folder = 0
            if archive_url == self.last_archive_url:
                last_game_in_folder = self.last_game  # only update new games since last pull
            return self.pull_games(archive_url, last_game_in_folder)

        return 0

    # get all the games played in that archive and returns #valid games
    def pull_games(self, archive, last_game_in_folder: int = 0) -> int:
        response = requests.get(archive, headers=self.hdr)
        if response.status_code != 200:
            print(f'error fetching games: {response.status_code}')
            return -1

        all_games = response.json().get('games', [])

        return self.write_games(all_games, archive, last_game_in_folder)

    # write games to program data and database
    def write_games(self, games: list, archive: str, last_game_in_folder: int) -> int:
        tot_games_in_folder: int = 0

        # save in program data
        for game in games:
            if Sort.is_valid_game(game):
                if tot_games_in_folder > last_game_in_folder:
                    self.games.append(Game(game, self.username, self.engine_limit))
                tot_games_in_folder += 1

        # get user db path
        archive_split = archive.split('/')
        archive_path = self.user_db_path + f'/{archive_split[-2]}_{archive_split[-1]}'
        if not (os.path.isdir(archive_path)):
            os.makedirs(archive_path)

        # index of first game in games for those just added
        start_of_new_games: int = len(self.games) - (tot_games_in_folder - (last_game_in_folder + 1))
        for i, game in enumerate(self.games[start_of_new_games:]):
            with open(archive_path + f'/game{i + last_game_in_folder}.json', 'w') as file:
                json.dump(game.dump, file, indent=4)

        return tot_games_in_folder

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

    @staticmethod
    def is_valid_game(game: list):
        return game['time_class'] in valid_time_classes and 'pgn' in game and game['rules'] == 'chess'
