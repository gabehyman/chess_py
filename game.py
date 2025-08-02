"""
### processes and stores game information
"""

from datetime import datetime
from enum import Enum

from chess.engine import MateGiven
from dateutil.relativedelta import relativedelta
import re
import chess.pgn
import chess.svg
import chess.engine
import webbrowser
import urllib.parse
import io

chess_com_launch_date = datetime(2007, 5, 1)
stockfish_path = '/opt/homebrew/Cellar/stockfish/17/bin/stockfish' # how to put on cloud??
# https://github.com/official-stockfish/Stockfish/blob/master/src/types.h has VALUE_MATE = 32000;
check_mate_eval = 32000
mate_eval = 31900  # mate in 100 moves (superfluous)

class Result(Enum):
    WIN = 0
    DRAW = 1
    LOSS = 2

class Color(Enum):
    WHITE = 0
    BLACK = 1

class Game:
    def __init__(self, game: list, username: str, local: bool = True):
        if local:  # read locally stored game json
            self.game_url: str = game['game_url']
            self.color_str: str = game['color_str']
            self.color: Color = Color(game['color'])
            self.result_str: str = game['result_str']
            self.result: Result = Result(game['result'])
            self.final_elo: int = game['final_elo']
            self.opp: str = game['opp']
            self.result_str_opp: str = game['result_str_opp']
            self.time_class: str = game['time_class']
            self.game_time: float = game['game_time']
            self.time_per_move: list[float] = game['time_per_move']
            self.pgn_str: str = game['pgn_str']
            self.pgn_arr: list[str] = game['pgn_arr']
            self.eval_per_move: list[float] = game['eval_per_move']
            self.start_time: datetime = datetime.fromtimestamp(game['start_time'])
            self.end_time: datetime = datetime.fromtimestamp(game['end_time'])
            self.duration: float = game['duration']
            self.month_index: int = game['month_index']
            self.dump = game
            return

        # json pulled from chess.com archive
        self.game_url: str = game['url']
        self.color_str: str = 'white' if game['white']['username'].lower() == username else 'black'
        self.color: Color = Color.WHITE if self.color_str == 'white' else Color.BLACK
        self.result_str: str = game[self.color_str]['result']
        self.result: Result = Game.determine_result(self.result_str)
        self.final_elo: int = game[self.color_str]['rating']

        # opponent info
        color_str_opp: str = 'white' if self.color_str == 'black' else 'black'
        self.opp: str = game[color_str_opp]['username']
        self.result_str_opp: str = game[color_str_opp]['result']

        self.time_class: str = game['time_class']
        time_control_info: list[str] = game['time_control'].split('+')
        self.game_time: float = 0.0 if self.time_class == 'daily' else float(time_control_info[0])
        time_inc: float = 0.0 if (len(time_control_info) == 1) else float(time_control_info[1])

        # get pgn (last line after all description related stuff)
        pgn_dirty: list[str] = game['pgn'].splitlines()

        # ignore time per move for daily games (inflates numbers/trivial)
        self.time_per_move = []
        if self.time_class != 'daily':
            self.time_per_move: list[float] = Game.get_time_per_move(pgn_dirty[-1], self.game_time, time_inc)

        # clean pgn (no clocks or result)
        self.pgn_str: str = Game.get_clean_pgn(pgn_dirty[-1])

        # each move an ind element, remove numbering and result
        self.pgn_arr: list[str] = Game.pgn_str_to_arr(self.pgn_str)

        # initially store as empty array, all games evaluated in separate thread
        self.eval_per_move: list[float] = []

        # start date info
        year, month, day = Game.get_time_or_date_components(pgn_dirty, game['pgn'], 'UTCDate', '.')
        hour, minute, sec = Game.get_time_or_date_components(pgn_dirty, game['pgn'], 'UTCTime', ':')
        self.start_time: datetime = Game.make_datetime_obj(int(year), int(month), int(day), int(hour), int(minute), int(sec))
        # end date info
        year, month, day = Game.get_time_or_date_components(pgn_dirty, game['pgn'], 'EndDate', '.')
        hour, minute, sec = Game.get_time_or_date_components(pgn_dirty, game['pgn'], 'EndTime', ':')
        self.end_time: datetime = Game.make_datetime_obj(int(year), int(month), int(day), int(hour), int(minute), int(sec))
        self.month_index: int = Game.date_to_month_index(self.start_time)

        # ignore how long daily games go for (inflates numbers/trivial)
        self.duration = 0.0
        if self.time_class != 'daily':
            self.duration: float = (self.end_time - self.start_time).total_seconds()

        self.dump = {
            'game_url': self.game_url,
            'color_str': self.color_str,
            'color': self.color.value,
            'result_str': self.result_str,
            'result': self.result.value,
            'final_elo': self.final_elo,
            'opp': self.opp,
            'result_str_opp': self.result_str_opp,
            'time_class': self.time_class,
            'game_time': self.game_time,
            'time_per_move': self.time_per_move,
            'pgn_str': self.pgn_str,
            'pgn_arr': self.pgn_arr,
            'eval_per_move': self.eval_per_move,
            'start_time': self.start_time.timestamp(),
            'end_time': self.end_time.timestamp(),
            'month_index': self.month_index,
            'duration': self.duration }

    def get_eval_per_move(self, engine_limit: list):
        """
        ### populate an array with eval at each board position
        ### (called in parallelize when evals are calculated via asycnh multi-threading)
        """
        # if we have a pgn (i.e., we have moves)
        if self.pgn_str:
            # set up board
            node = Game.pgn_str_to_node(self.pgn_str)
            board = node.board()

            # go through each board position of game and eval
            while node.variations:
                next_node = node.variation(0)
                board.push(next_node.move)
                self.eval_per_move.append(Game.evaluate_board(board, self.color, engine_limit))
                node = next_node

        # len(eval) should always = len(pgn)
        assert len(self.eval_per_move) == len(self.pgn_arr), (
                f'len(eval) != len(pgn): {self.game_url}')

    @staticmethod
    def evaluate_board(board, color: Color, engine_limit: list = None) -> float:
        """evaluate board based on user color"""
        if engine_limit is None:
            engine_limit = Game.create_engine()

        info = engine_limit[0].analyse(board, engine_limit[1])

        # get score relative to player (if winning +, if losing -)
        if color == Color.WHITE:
            score = info['score'].white()
        else:
            score = info['score'].black()

        if score.is_mate():
            if score == MateGiven:  # mated
                evaluation = check_mate_eval
            else:
                evaluation = check_mate_eval - abs(score.moves)
        else:  # centipawn to pawn units
            evaluation = score.cp / 100.0

        return evaluation

    @staticmethod
    def eval_to_mate_str(evaluation, color: int):
        """turn eval value into str (converting mates to wM/bM#moves)"""
        # if we don't have the evals yet show them as loading
        if evaluation is None:
            return 'loading...'

        abs_eval = abs(evaluation)
        if abs_eval < mate_eval:
            return str(evaluation)

        mate_in: float = check_mate_eval - abs_eval
        mate_str: str = 'wM' if evaluation > 0 else 'bM'

        return f'{mate_str}{int(mate_in)}'

    @staticmethod
    def determine_result(result: str) -> Result:
        """determine win draw or loss based on string"""
        if result == 'win':
            return Result.WIN
        if (result == 'checkmated' or result == 'resigned' or result == 'timeout' or
                result == 'abandoned' or result == 'lose'):
            return Result.LOSS

        # the rest are draws: 'stalemate', 'repetition', 'agreed', '50move', 'timevsinsufficient'
        return Result.DRAW

    @staticmethod
    def get_clean_pgn(pgn_dirty):
        """use regular expressions to remove clock info and result from pgn (some pgns dont have result)"""
        # get where the last space is (if == -1, empty pgn. if not, may be used to remove result)
        last_space_index = pgn_dirty.rfind(' ')
        if last_space_index == -1:  # no spaces, i.e., one word
            return ''

        # remove everything after last bracket (incl bracket in case last char but add back)
        last_bracket_index = pgn_dirty.rfind('}')
        if last_bracket_index != -1:
            pgn_dirty_no_result = pgn_dirty[:last_bracket_index] + '}'
        # older games dont use brackets (e.g., https://api.chess.com/pub/player/calvinp/games/2010/04) so remove last word
        else:
            pgn_dirty_no_result = pgn_dirty[:last_space_index]

        pgn_no_clocks: list[str] = re.sub(r'\s*\{\[%clk [^\}]+\]\}', '', pgn_dirty_no_result)
        pgn_clean: str = re.sub(r'\d+\.\.\.\s*', '', pgn_no_clocks).strip()

        return pgn_clean

    @staticmethod
    def pgn_str_to_arr(pgn_st: str):
        """convert pgn str to an array"""
        # if we have an empty pgn, dont include
        return [move for move in pgn_st.split(' ') if '.' not in move and move]

    @staticmethod
    def pgn_arr_to_str(pgn_arr: list[str], num_moves: int = -1) -> str:
        """make a normal pgn from a serialized arr of moves"""
        num_moves = min(num_moves, len(pgn_arr))  # avoid inputting a num_move higher than total
        num_moves = len(pgn_arr) if num_moves == -1 else num_moves

        pgn_str: str = ''
        for i in range(num_moves):
            move_num: int = int(i/2) + 1
            if move_num > num_moves:
                break

            # add move# if both moves have been made
            if i%2 == 0:
                pgn_str += f'{str(move_num)}. '
            pgn_str += pgn_arr[i] + ' '

        return pgn_str

    @staticmethod
    def create_engine(depth: int = 10):
        """create a stockfish engine with certain depth for eval (default to 10)"""
        engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)
        limit = chess.engine.Limit(depth=depth)

        return [engine, limit]

    @staticmethod
    def quit_engine(engine):
        """kill engine process"""
        engine.quit()

    @staticmethod
    def pgn_str_to_node(pgn_str: str):
        """convert a pgn str into a stockfish parsable node"""
        pgn_stream = io.StringIO(pgn_str)
        node = chess.pgn.read_game(pgn_stream)

        return node

    @staticmethod
    def make_datetime_obj(year: int, month: int, day: int = 1,
                          hour: int = 22, minute: int = 22, second: int = 22) -> datetime:
        """create datetime obj (only import here and can use in other places)"""
        return datetime(year, month, day, hour, minute, second)

    @staticmethod
    def get_time_or_date_components(pgn_dirty: list[str], pgn: str, time_type: str, delimiter: str):
        """get broken down components (d/m/y or h:m:s) of date and time from json"""
        return pgn_dirty[Game.find_line_number(pgn, time_type)].split('\"')[1].split(delimiter)

    @staticmethod
    def date_to_month_index(date: datetime) -> int:
        """create a month index relative to when chess.com was launched"""
        return ((date.month - chess_com_launch_date.month)
                + (date.year - chess_com_launch_date.year) * 12)

    @staticmethod
    def month_index_to_date(month_index) -> datetime:
        """convert from month index to a datetime obj"""
        return chess_com_launch_date + relativedelta(months=+month_index)

    @staticmethod
    def month_index_to_str_months(month_index) -> str:
        """convert month index into nice month str (aug99, feb66, etc)"""
        date: datetime = Game.month_index_to_date(month_index)
        return date.strftime('%b').lower() + str(date.year)[-2:]

    @staticmethod
    def find_line_number(full_str: str, sub_str: str) -> int:
        """find at which line number a substr appears"""
        index = full_str.find(sub_str)
        if index == -1:
            return -1

        line_number = full_str.count('\n', 0, index)
        return line_number

    @staticmethod
    def get_time_per_move(dirty_pgn: list[str], game_time: float, time_inc: float) -> list[float]:
        """turn pgn with clock info into time per move"""
        # extract clock times using regular expressions
        clock_times: list[str] = re.findall(r'\{\[%clk ([^]]+)]}', dirty_pgn)

        # store time per move for user and opponent
        time_per_move: list[float] = []
        prev_time: list[float] = [game_time + time_inc] * 2
        for i, clock_time in enumerate(clock_times):
            seconds_time: float = Game.clock_to_seconds(clock_time)
            time_per_move.append(prev_time[i%2] - seconds_time)
            prev_time[i%2] = seconds_time + time_inc

        return time_per_move

    @staticmethod
    def clock_to_seconds(clock_time: str) -> float:
        """convert clock time into seconds"""
        hours, minutes, seconds = clock_time.split(':')
        return float(int(hours) * 3600 + int(minutes) * 60 + float(seconds))

    @staticmethod
    def show_svg_board_of_pgn(pgn_str: str, wd: str):
        """show the svg of the board given a pgn string"""
        svg_data = chess.svg.board(board=Game.pgn_str_to_node(pgn_str).board())

        svg_file: str = 'board.svg'
        with open(svg_file, 'w') as f:
            f.write(svg_data)
        webbrowser.open('file://' + wd + svg_file)

    @staticmethod
    def get_length_of_pgn(pgn: str) -> int:
        # count number of spaces
        # 3 spaces per complete 2 moves (e.g., 1.%20e4%20e5%20)
        # 2 spaces per 1 move (e.g., 1.%20e4%20)
        num_spaces: int = pgn.count(' ')

        num_moves: int = int(num_spaces / 3) * 2
        if num_spaces % 3 != 0:
            num_moves += 1

        print(pgn)
        print(num_spaces)

        return num_moves

    @staticmethod
    def open_pgn_in_chess_com(pgn: str):
        """opens pgn on chess.com's analysis page at the last move"""
        # get total number of moves (doesn't need to be exact, just always >= real# so we open at end)
        num_moves = Game.get_length_of_pgn(pgn)
        encoded_pgn = urllib.parse.quote(pgn)
        url = f'https://www.chess.com/analysis?tab=analysis&setup=fen&pgn={encoded_pgn}&move={num_moves}'
        print(url)
        webbrowser.open(url)


