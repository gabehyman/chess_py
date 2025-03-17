"""
### facilitate the pulling/reading/storing of games of a user
"""
import requests
import re
import os
import json
import time

from game import Game
from parallelize import Parallelize

valid_time_classes = ['rapid', 'bullet', 'blitz']

class Sort:
    def __init__(self, username: str):
        start_time = time.time()

        self.wd: str = os.path.dirname(os.path.realpath(__file__))

        # needed for chess.com api call
        self.hdr_path: str = f'{self.wd}/hdr.json'
        self.hdr = {'User-Agent': self.get_user_hdr()}

        self.db_path: str = f'{self.wd}/db'
        if not os.path.isdir(self.db_path):
            os.makedirs(self.db_path)

        self.username: str = username
        self.user_db_path: str = f'{self.db_path}/{self.username}'
        self.user_url = f'https://api.chess.com/pub/player/{self.username}/games'
        self.archive_urls: list[str] = self.pull_archive_urls()

        self.new_user =  not os.path.isdir(self.user_db_path)
        if self.new_user:
            os.makedirs(self.user_db_path)

        self.last_archive_index: int = -1
        self.last_game_number: int = -1
        self.local_games_count: int = -1
        self.games: list[Game] = []

        # read thru local files and determine when the last pull was (get archive url)
        self.set_last_pull_info()

        # read in local games and populate porgram data
        self.read_local_games()

        # populate games info to pass into parallelizer to make game objects
        self.games_to_process = []
        for archive_url in self.archive_urls:
            self.update_games(archive_url)

        # process all games in parallel
        processor = Parallelize()
        self.games.extend(processor.process_all_games(self.games_to_process, self.username))
        self.games_to_process = []

        # sort games in chrono order
        self.games.sort(key=lambda game: game.start_time)
        self.first_month_index = self.games[0].month_index
        self.last_month_index = self.games[-1].month_index
        self.num_months_active = self.last_month_index - self.first_month_index + 1

        # save program data in json files
        self.write_games(self.games)
        self.new_user = False

        end_time = time.time()

        self.time_to_sort: float = end_time - start_time

    def get_user_hdr(self) -> str:
        """"get hdr info for chess.com api and write to file"""
        if not os.path.exists(self.hdr_path):
            hdr = input('enter a valid chess.com email to query api: ').strip()
            with open(self.hdr_path, 'w') as file:
                json.dump({'hdr': hdr}, file, indent=4)

        else:
            with open(self.hdr_path, 'r') as file:
                hdr = json.load(file)['hdr']

        return hdr

    def pull_archive_urls(self) -> list[str]:
        """get urls for archives per month"""
        response = requests.get(f'{self.user_url}/archives', headers=self.hdr)
        if response.status_code != 200:
            print(f'error fetching archives: {response.status_code}')
            return []

        archive_urls = response.json().get('archives', [])

        return archive_urls

    def archive_url_to_archive_path(self, archive_url: str) -> str:
        """"get the associated dir path of an archive url"""
        archive_url_split = archive_url.split('/')
        if len(archive_url_split) > 2:
            if archive_url_split[-2].isdigit() and archive_url_split[-1].isdigit():
                year: int = int(archive_url_split[-2])
                month: int = int(archive_url_split[-1])

                return self.archive_year_month_to_path(year, month)

        return ''

    def archive_year_month_to_path (self, year: str, month: str):
        """take year and month of archive and get associated dir path"""
        return f'{self.user_db_path}/{year}_{month:02d}'

    def read_local_games(self):
        """read games stored locally and save to program data"""
        if not self.new_user:
            for root, dirs, filenames in os.walk(self.user_db_path):
                # skip hidden dirs/files like .git, .DS_Store, etc. and just focus on .json
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                filenames = [f for f in filenames if f.startswith('game')]

                for filename in filenames:
                    file_path = os.path.join(root, filename)
                    with open(file_path, 'r') as file:
                        self.games.append(Game(json.load(file), self.username))

        self.local_games_count = len(self.games)

    def update_games(self, archive_url: str):
        """# updates locally stored games to be up-to-date with remote and returns #games in archive
        only look at games after the last game written"""
        if self.new_user:
            return self.pull_games(archive_url)

        # if we are looking at archives from the same month or after the last pull
        archive_url_index: int = Sort.archive_url_to_index(archive_url)
        if archive_url_index >= self.last_archive_index:
            last_game_in_folder = -1
            if archive_url_index == self.last_archive_index:
                last_game_in_folder = self.last_game_number  # only update new games since last pull
            self.pull_games(archive_url, last_game_in_folder)

    def pull_games(self, archive, last_game_in_folder: int = -1):
        """get all the games played in that archive"""
        response = requests.get(archive, headers=self.hdr)
        if response.status_code != 200:
            print(f'error fetching games: {response.status_code}')

        all_games = response.json().get('games', [])
        valid_games = [game for game in all_games if Sort.is_valid_game(game)]
        if (len(valid_games) - 1) == last_game_in_folder:
            return

        # save in program data to be processed
        start_of_new_valid_games: int = last_game_in_folder + 1
        for game_number, game in enumerate(valid_games[start_of_new_valid_games:], start=start_of_new_valid_games):
            if Sort.is_valid_game(game):
                if game_number > last_game_in_folder:
                    self.games_to_process.append(game)

    def write_games(self, games: list):
        """write games to local database"""
        game_number_counter: int = 0
        last_index: int = -1

        # correct indexing of .json file names (start with game0)
        start_index = -1 if self.local_games_count == 0 else games[self.local_games_count - 1].month_index
        for game in self.games[self.local_games_count:]:
            archive_path = self.archive_year_month_to_path(game.start_time.year, game.start_time.month)

            # increases correctly based on last game in db
            game_num_mod = 0
            if game.month_index == start_index:
                game_num_mod = self.last_game_number + 1
            if game.month_index != last_index:
                game_number_counter = 0
                last_index = game.month_index

                if not os.path.isdir(archive_path):
                    os.makedirs(archive_path)

            with open(archive_path + f'/game{game_number_counter + game_num_mod}.json', 'w') as file:
                json.dump(game.dump, file, indent=4)

            game_number_counter += 1

    def set_last_pull_info(self):
        """set info of when last pull was based on present files"""
        if not self.new_user:
            self.last_archive_index = -1
            self.last_game_number = -1

            last_month: str = ''
            last_year: str = ''
            most_recent_index: int = -1

            archive_months: list[str] = os.listdir(self.user_db_path)
            for archive_month in archive_months:
                archive_month_split = archive_month.split('_')
                if len(archive_month_split) == 2:
                    if archive_month_split[0].isdigit() and archive_month_split[0].isdigit():
                        year: str = archive_month_split[0]
                        month: str = archive_month_split[1]
                        index: int = Game.date_to_month_index(Game.make_datetime_obj(int(year), int(month)))
                        if index > most_recent_index:
                            last_year = year
                            last_month = month
                            most_recent_index = index

            if most_recent_index != -1:
                self.last_archive_index = most_recent_index

                # use reg exp to extract all game#s of all files and store as array
                game_numbers_str = os.listdir(f'{self.user_db_path}/{last_year}_{last_month}')
                pattern = re.compile(r'game(\d+)\.json')
                game_numbers = [int(match.group(1)) for game_number in game_numbers_str
                           if (match := pattern.search(game_number))]

                if game_numbers:
                    self.last_game_number = max(game_numbers)  # max = last

    def find_games_against(self, opponent: str):
        games_against: list[Game] = []
        for game in self.games:
            if game.opponent == opponent:
                games_against.append(game)

        return games_against

    @staticmethod
    def archive_url_to_index(archive_url: str) -> int:
        """convert archive url to month index"""
        index = -1

        archive_url_split = archive_url.split('/')
        if len(archive_url_split) > 2:
            if archive_url_split[-2].isdigit() and archive_url_split[-1].isdigit():
                year: str = archive_url_split[-2]
                month: str = archive_url_split[-1]
                index: int = Game.date_to_month_index(Game.make_datetime_obj(int(year), int(month)))

        return index

    @staticmethod
    def is_valid_game(game: list):
        """only process normal chess games of valid time classes with pgn and normal starting pos"""
        return (game['time_class'] in valid_time_classes
                and 'pgn' in game
                and game['rules'] == 'chess'
                and game['initial_setup'] == '')

    @staticmethod
    def preloaded_usernames() -> list[str]:
        db_path: str = f'{os.path.dirname(os.path.realpath(__file__))}/db'
        preloaded_users: list[str] = [username for username in os.listdir(db_path)
                                      if os.path.isdir(os.path.join(db_path, username))]

        return preloaded_users