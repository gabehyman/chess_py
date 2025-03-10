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
import io

chess_com_launch_date = datetime(2007, 5, 1)
stockfish_path = "/opt/homebrew/Cellar/stockfish/17/bin/stockfish"  # may have to change for others
# https://github.com/official-stockfish/Stockfish/blob/master/src/types.h has VALUE_MATE = 32000;
check_mate_eval = 32000

class Result(Enum):
    WIN = 0
    DRAW = 1
    LOSS = 2

class Color(Enum):
    WHITE = 0
    BLACK = 1

class Game:

    def __init__(self, game: list, username: str, engine_limit: list = None, local: bool = True):
        if local:  # read locally stored game json
            self.game_url: str = game['game_url']
            self.color_str: str = game['color_str']
            self.color: Color = Color(game['color'])
            self.opponent: str = game['opponent']
            self.result_str: str = game['result_str']
            self.result: Result = Result(game['result'])
            self.final_elo: int = game['final_elo']
            self.game_time: float = game['game_time']
            self.time_inc: float = game['time_inc']
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
        self.opponent: str = game['white']['username'] if self.color != Color.WHITE else game['black']['username']
        self.result_str: str = game[self.color_str]['result']
        self.result: Result = Game.determine_result(self.result_str)
        self.final_elo: int = game[self.color_str]['rating']

        time_control_info: list[str] = game['time_control'].split('+')
        self.game_time: float = float(time_control_info[0])
        self.time_inc: float = 0.0 if (len(time_control_info) == 1) else float(time_control_info[1])

        # use reg exp to parse pgn stirng and extract relevant info
        pgn_dirty: list[str] = game['pgn'].splitlines()
        pgn_no_clocks: list[str] = re.sub(r"\s*\{\[%clk [^\}]+\]\}", "", pgn_dirty[-1])

        self.time_per_move: list[float] = Game.time_per_move(pgn_dirty[-1], self.game_time, self.time_inc, self.color)
        pgn_str_w_result: str = re.sub(r'\d+\.\.\.\s*', '', pgn_no_clocks).strip()
        index_start_index: int = pgn_str_w_result.rfind(' ')  # remove result at end
        self.pgn_str: str = pgn_str_w_result[:index_start_index] if index_start_index != -1 else pgn_str_w_result

        # each move an ind element, remove numbering and result
        self.pgn_arr: list[str] = [move for move in self.pgn_str.split(' ') if '.' not in move]
        self.eval_per_move: list[float] = Game.get_eval_per_move(self.pgn_str, self.color, engine_limit)

        year, month, day = pgn_dirty[Game.find_line_number(game['pgn'], 'UTCDate')].split('\"')[1].split('.')
        hour, minute, sec = pgn_dirty[Game.find_line_number(game['pgn'], 'UTCTime')].split('\"')[1].split(':')
        self.start_time: datetime = Game.make_datetime_obj(int(year), int(month), int(day), int(hour), int(minute), int(sec))

        year, month, day = pgn_dirty[Game.find_line_number(game['pgn'], 'EndDate')].split('\"')[1].split('.')
        hour, minute, sec = pgn_dirty[Game.find_line_number(game['pgn'], 'EndTime')].split('\"')[1].split(':')
        self.end_time: datetime = Game.make_datetime_obj(int(year), int(month), int(day), int(hour), int(minute), int(sec))
        self.month_index: int = Game.date_to_month_index(self.start_time)

        self.duration: float = (self.end_time - self.start_time).total_seconds()

        self.dump = {
            'game_url': self.game_url,
            'color_str': self.color_str,
            'color': self.color.value,
            'opponent': self.opponent,
            'result_str': self.result_str,
            'result': self.result.value,
            'final_elo': self.final_elo,
            'game_time': self.game_time,
            'time_inc': self.time_inc,
            'time_per_move': self.time_per_move,
            'pgn_str': self.pgn_str,
            'pgn_arr': self.pgn_arr,
            'eval_per_move': self.eval_per_move,
            'start_time': self.start_time.timestamp(),
            'end_time': self.end_time.timestamp(),
            'month_index': self.month_index,
            'duration': self.duration }

    @staticmethod
    def determine_result(result: str) -> Result:
        if result == 'win':
            return Result.WIN
        if (result == 'checkmated' or result == 'resigned' or result == 'timeout' or
                result == 'abandoned' or result == 'lose'):
            return Result.LOSS

        # the rest are draws: 'stalemate', 'repetition', 'agreed', '50move', 'timevsinsufficient'
        return Result.DRAW

    @staticmethod
    def pgn_str_to_arr(pgn_st: str):
        return [move for move in pgn_st.split(' ') if '.' not in move]

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
        """create a stockfish engine with certain depth for eval"""
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
    def evaluate_board(board, color: Color, engine_limit: list = None) -> float:
        """evaluate board based on user color"""
        if engine_limit is None:
            engine_limit = Game.create_engine()

        info = engine_limit[0].analyse(board, engine_limit[1])

        # get score relative to player (if winning +, if losing -)
        if color == Color.WHITE:
            score = info["score"].white()
        else:
            score = info["score"].black()

        if score.is_mate():
            if score == MateGiven:  #mated
                evaluation = check_mate_eval
            else:  # follow stockfish
                evaluation = (check_mate_eval - score.moves) / 100.0
        else:  # centipawn to pawn units
            evaluation = score.cp / 100.0

        return evaluation

    @staticmethod
    def get_eval_per_move(pgn_str: str, color: Color, engine_limit: list) -> list[float]:
        """populate an array with eval at each board position"""
        eval_per_move: list[float] = []
        node = Game.pgn_str_to_node(pgn_str)
        board = node.board()

        # go through each board position of game
        while node.variations:
            next_node = node.variation(0)
            board.push(next_node.move)
            eval_per_move.append(Game.evaluate_board(board, color, engine_limit))
            node = next_node

        return eval_per_move

    @staticmethod
    def make_datetime_obj(year: int, month: int, day: int = 1,
                          hour: int = 22, minute: int = 22, second: int = 22) -> datetime:
        """create datetime obj (only import here and can use in other places)"""
        return datetime(year, month, day, hour, minute, second)

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
    def time_per_move(dirty_pgn: list[str], game_time: float, time_inc: float, color: Color) -> list[float]:
        """turn pgn with clock info into time per move"""
        # extract clock times using reg exp
        clock_times: list[str] = re.findall(r'\{\[%clk ([^\]]+)\]\}', dirty_pgn)

        time_per_move: list[float] = []
        prev_time: float = game_time + time_inc
        for clock_time in clock_times[color.value::2]:  # iterate thru only users moves (skip 1)
            seconds_time: float = Game.clock_to_seconds(clock_time)
            time_per_move.append(prev_time - seconds_time)
            prev_time = seconds_time + time_inc

        return time_per_move

    @staticmethod
    def clock_to_seconds(clock_time: str) -> float:
        """convert clock time into seconds"""
        hours, minutes, seconds = clock_time.split(':')
        return float(int(hours) * 3600 + int(minutes) * 60 + float(seconds))

    @staticmethod
    def show_svg_board_of_pgn(pgn_str: str):
        """show the svg of the board given a pgn string"""
        svg_data = chess.svg.board(board=Game.pgn_str_to_node(pgn_str).board())

        svg_file: str = 'board.svg'
        with open(svg_file, "w") as f:
            f.write(svg_data)
        webbrowser.open('file://' + svg_file)

