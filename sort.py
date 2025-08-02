"""
### facilitate the pulling/reading/sorting/storing of games of a user
"""
import requests
import re
import os
import json
import time
import threading

from game import Game
from parallelize import Parallelize

# needed for chess.com api call
hdr = {'User-Agent': 'gabejohnsmith@gmail.com'}
valid_initial_fen = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'


class Sort:
    def __init__(self, username: str):
        start_sort_time = time.time()

        self.username: str = username
        self.archive_urls: list[str] = Sort.pull_archive_urls(self.username)

        # wd of where this file is
        self.wd: str = os.path.dirname(os.path.realpath(__file__))

        # where we store user info
        self.db_path: str = f'{self.wd}/db'
        if not os.path.isdir(self.db_path):
            os.makedirs(self.db_path)

        # db for specific user
        self.user_db_path: str = f'{self.db_path}/{self.username}'
        self.is_new_user = not os.path.isdir(self.user_db_path)
        if self.is_new_user:
            os.makedirs(self.user_db_path)

        # info to help only pull new games
        self.last_archive_index: int = -1
        self.last_game_number: int = -1
        self.local_games_count: int = -1

        # games played in the early hours of the first day of the month are stored in the previous month's archive
        # this is used to keep track of those games so that they can be properly added to the next (correct) month
        self.games_leftover: list = []

        # store as container so reassignments are tracked in Dash
        self.games_container: dict[str, list[Game]] = {'games': []}

        # read thru local files and determine when the last pull was (get archive url)
        self.set_last_pull_info()

        # read in local games and populate program data
        self.read_local_games()

        # populate games and worry about eval later
        for archive_url in self.archive_urls:
            self.update_games(archive_url)

        # add any leftover games
        if self.games_leftover:
            self.add_new_games(self.games_leftover)
            self.games_leftover = []

        # sort games in chrono order
        self.games_container['games'].sort(key=lambda game: game.start_time)
        self.first_month_index = self.games_container['games'][0].month_index
        self.last_month_index = self.games_container['games'][-1].month_index
        self.num_months_active = self.last_month_index - self.first_month_index + 1

        self.time_to_sort: float = time.time() - start_sort_time

        # create a mutex lock for self.games to avoid concurrent read/writes
        self.games_lock = threading.Lock()
        self.time_to_eval: float = 0
        self.is_eval_done_container = {'is_eval_done': self.local_games_count == len(self.games_container['games'])}

        # evaluate all games in parallel
        threading.Thread(target=self.eval_games_in_parallel, daemon=False).start()

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
        if not self.is_new_user:
            for root, dirs, filenames in os.walk(self.user_db_path):
                # skip hidden dirs/files like .git, .DS_Store, etc. and just focus on .json
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                filenames = [f for f in filenames if f.startswith('game')]

                for filename in filenames:
                    file_path = os.path.join(root, filename)
                    with open(file_path, 'r') as file:
                        self.games_container['games'].append(Game(json.load(file), self.username))

        self.local_games_count = len(self.games_container['games'])

    def update_games(self, archive_url: str):
        """
        ### updates locally stored games to be up-to-date with remote and returns #games in archive
        ### only look at games after the last game written
        """
        if self.is_new_user:
            return self.pull_games(archive_url)

        # if we are looking at archives from the same month or after the last pull
        archive_url_index: int = Sort.archive_url_to_index(archive_url)
        if archive_url_index >= self.last_archive_index:
            last_game_in_folder = -1  # set to -1 because we will add 1 and we want the first name to be game0
            if archive_url_index == self.last_archive_index:
                last_game_in_folder = self.last_game_number  # only update new games since last pull
            self.pull_games(archive_url, last_game_in_folder)

    def pull_games(self, archive, last_game_in_folder: int = -1):
        """get all the games played in that archive"""
        response = requests.get(archive, headers=hdr)
        if response.status_code != 200:
            print(f'error fetching games at {archive}')
            return

        # valid games = new valid games + leftover games from previous archive (which are actually from this month)
        all_games = response.json().get('games', [])
        valid_games = [game for game in all_games if Sort.is_valid_game(game)] + self.games_leftover

        # month archives can have games from the first day of the next month so we need to make
        # sure that we only look at the number of games in the archive from the actual month
        num_games_in_month = Sort.get_num_games_in_month(valid_games, archive.split('/')[-1])

        # dont need to do anythjng if we have all the games in the folder already
        if num_games_in_month == last_game_in_folder:
            return

        start_of_new_valid_games: int = last_game_in_folder + 1
        valid_games_month = valid_games[start_of_new_valid_games:num_games_in_month]

        # add new games to prgram data
        self.add_new_games(valid_games_month)

        # keep track of leftover games for next month
        self.games_leftover = valid_games[num_games_in_month:]

    def add_new_games(self, games):
        for game in games:
            self.games_container['games'].append(Game(game, self.username, False))

    def write_games(self):
        """write games to local database"""
        game_number_counter: int = 0
        last_index: int = -1

        # whats the last month we have in the database
        start_index = -1 if self.local_games_count == 0 else self.games_container['games'][self.local_games_count - 1].month_index
        for game in self.games_container['games'][self.local_games_count:]:
            archive_path = self.archive_year_month_to_path(game.start_time.year, game.start_time.month)

            # if the game we are writing is from the last month in db, modify game number to start after last game
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
        if not self.is_new_user:
            self.last_archive_index = -1
            self.last_game_number = -1

            last_month: str = ''
            last_year: str = ''
            most_recent_index: int = -1

            # go through files in users db and get info of last pull
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

    def eval_games_in_parallel(self):
        """wrapper function for parallelization"""
        # only need to evaluate games if we have newly pulled games (all evals already calc)
        if self.is_eval_done_container['is_eval_done']:
            return

        # time how long the parallelized eval takes
        start_eval_time = time.time()

        new_games: list[Game] = self.games_container['games'][self.local_games_count:]

        # start multi-threaded eval of all new games
        processor = Parallelize()
        games_w_eval = processor.process_all_games(self.games_container['games'][self.local_games_count:], self.username)

        # save timing
        self.time_to_eval: float = time.time() - start_eval_time

        # use lock to avoid access conflicts with webpage
        with self.games_lock:
            # sort new games so we can just stick in self.games
            games_w_eval.sort(key=lambda game: game.start_time)

            # just reassign reference if new user (all games were just processed)
            if self.is_new_user:
                self.games_container['games'] = games_w_eval
                self.is_new_user = False
            # otherwise extend
            else:
                self.games_container['games'][self.local_games_count:] = games_w_eval

            self.write_games()

        self.is_eval_done_container['is_eval_done'] = True

        print('evals updated and games written to mem')

    @staticmethod
    def get_user_archive_url(username):
        """get url for the users archives on chess.com"""
        return f'https://api.chess.com/pub/player/{username}/games/archives'

    @staticmethod
    def pull_archive_urls(username) -> list[str]:
        """get urls for archives per month"""
        response = requests.get(Sort.get_user_archive_url(username), headers=hdr)
        if response.status_code != 200:
            print(f'error fetching archives: {response.status_code}')
            return [-1]

        archive_urls = response.json().get('archives', [])

        return archive_urls

    @staticmethod
    def is_user_valid(username) -> int:
        """checks if the user exists and has games played"""
        response = requests.get(Sort.get_user_archive_url(username), headers=hdr)
        if response.status_code != 200:
            return 1

        archive_urls = response.json().get('archives', [])

        if not archive_urls:
            return 2

        return 0

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
        """only process normal chess games with a pgn and normal starting pos"""
        return 'pgn' in game and game['rules'] == 'chess' and game['initial_setup'] == valid_initial_fen

    @staticmethod
    def get_num_games_in_month(games_in_archive: list, archive_month: int):
        """get how many games in the current archive are from that month"""
        for i in reversed(range(len(games_in_archive))):
            pgn = games_in_archive[i]['pgn']

            # element 1 is the month
            month = Game.get_time_or_date_components(pgn.splitlines(), pgn, 'UTCDate', '.')[1]
            if int(month) != int(archive_month):
                return i

        return len(games_in_archive)

    @staticmethod
    def preloaded_usernames() -> list[str]:
        """find all users that we already have stored/processed"""
        db_path: str = f'{os.path.dirname(os.path.realpath(__file__))}/db'
        preloaded_users: list[str] = []

        if os.path.exists(db_path):
            preloaded_users: list[str] = [username for username in os.listdir(db_path)
                                          if os.path.isdir(os.path.join(db_path, username))]

        return preloaded_users