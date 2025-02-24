from datetime import datetime
from dateutil.relativedelta import relativedelta
import re
import chess.pgn
import chess.svg
import chess.engine
import webbrowser
import io

chess_com_launch_date = datetime(2007, 5, 1)
stockfish_path = "/opt/homebrew/Cellar/stockfish/17/bin/stockfish"

class Game:

    def __init__(self, game: list, username: str, engine_limit: list = None, local: bool = True):
        if local:  # read locally stored game json
            self.color: str = game['color']
            self.opponent: str = game['opponent']
            self.result: bool = game['result']
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
        self.color: str = 'white' if game['white']['username'].lower() == username else 'black'
        self.opponent: str = game['white']['username'] if self.color != 'white' else game['black']['username']
        self.result: bool = game[self.color]['result']
        self.final_elo: int = game[self.color]['rating']

        time_control_info: list[str] = game['time_control'].split('+')
        self.game_time: float = float(time_control_info[0])
        self.time_inc: float = 0.0 if (len(time_control_info) == 1) else float(time_control_info[1])

        pgn_dirty: list[str] = game['pgn'].splitlines()
        pgn_no_clocks: list[str] = re.sub(r"\s*\{\[%clk [^\}]+\]\}", "", pgn_dirty[-1])

        self.time_per_move: list[float] = Game.time_per_move(pgn_dirty[-1], self.game_time, self.time_inc, self.color)
        pgn_str_w_result: str = re.sub(r'\d+\.\.\.\s*', '', pgn_no_clocks).strip()
        index_start_index: int = pgn_str_w_result.rfind(' ')  # remove result at end
        self.pgn_str: str = pgn_str_w_result[:index_start_index] if index_start_index != -1 else pgn_str_w_result

        # each move an ind element, remove numbering and result
        self.pgn_arr: list[str] = [move for move in self.pgn_str.split(' ') if '.' not in move]
        self.eval_per_move: list[float] = Game.get_eval_per_move(self.pgn_str, engine_limit)

        year, month, day = pgn_dirty[Game.find_line_number(game['pgn'], 'UTCDate')].split('\"')[1].split('.')
        hour, minute, sec = pgn_dirty[Game.find_line_number(game['pgn'], 'UTCTime')].split('\"')[1].split(':')
        self.start_time: datetime = Game.make_datetime_obj(int(year), int(month), int(day), int(hour), int(minute), int(sec))

        year, month, day = pgn_dirty[Game.find_line_number(game['pgn'], 'EndDate')].split('\"')[1].split('.')
        hour, minute, sec = pgn_dirty[Game.find_line_number(game['pgn'], 'EndTime')].split('\"')[1].split(':')
        self.end_time: datetime = Game.make_datetime_obj(int(year), int(month), int(day), int(hour), int(minute), int(sec))
        self.month_index: int = Game.date_to_month_index(self.start_time)

        self.duration: float = (self.end_time - self.start_time).total_seconds()

        self.dump = {
            'color': self.color,
            'opponent': self.opponent,
            'result': self.result,
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
    def pgn_arr_to_str(pgn_arr: list[str], num_moves: int = -1) -> str:
        num_moves = min(num_moves, len(pgn_arr))  # avoid inputting a num_move higher than total
        num_moves = len(pgn_arr) if num_moves == -1 else num_moves

        pgn_str: str = ''
        for i in range(num_moves):
            move_num: int = int(i/2) + 1
            if move_num > num_moves:
                break

            if i%2 == 0:
                pgn_str += f'{str(move_num)}. '
            pgn_str += pgn_arr[i] + ' '

        return pgn_str

    @staticmethod
    def create_engine(depth: int = 10):
        engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)
        limit = chess.engine.Limit(depth=depth)

        return [engine, limit]

    @staticmethod
    def quit_engine(engine):
        engine.quit()

    @staticmethod
    def pgn_str_to_node(pgn_str: str):
        pgn_stream = io.StringIO(pgn_str)
        node = chess.pgn.read_game(pgn_stream)

        return node

    @staticmethod
    def evaluate_board(board, engine_limit: list = None) -> float:
        if engine_limit is None:
            engine_limit = Game.create_engine()

        info = engine_limit[0].analyse(board, engine_limit[1])
        score = info["score"]

        if score.is_mate():
            evaluation = float('inf')
        else:
            evaluation = score.relative.cp / 100.0  # centipawn to pawn units

        return evaluation

    @staticmethod
    def get_eval_per_move(pgn_str: str, engine_limit: list) -> list[float]:
        eval_per_move: list[float] = []
        node = Game.pgn_str_to_node(pgn_str)
        board = node.board()

        while node.variations:
            next_node = node.variation(0)
            board.push(next_node.move)
            eval_per_move.append(Game.evaluate_board(board, engine_limit))
            node = next_node

        return eval_per_move

    @staticmethod
    def show_scg_board_of_pgn(pgn_str: str):
        svg_data = chess.svg.board(board=Game.pgn_str_to_node(pgn_str).board())

        svg_file: str = 'board.svg'
        with open(svg_file, "w") as f:
            f.write(svg_data)
        webbrowser.open('file://' + svg_file)

    @staticmethod
    def make_datetime_obj(year: int, month: int, day: int = 1,
                          hour: int = 22, minute: int = 22, second: int = 22) -> datetime:
        return datetime(year, month, day, hour, minute, second)

    @staticmethod
    def date_to_month_index(date: datetime) -> int:
        return ((date.month - chess_com_launch_date.month)
                + (date.year - chess_com_launch_date.year) * 12)

    @staticmethod
    def month_index_to_date(month_index) -> datetime:
        return chess_com_launch_date + relativedelta(months=+month_index)

    @staticmethod
    def month_index_to_str_months(month_index) -> str:
        date: datetime = Game.month_index_to_date(month_index)
        return date.strftime('%b').lower() + str(date.year)[-2:]

    # find at which line number a substr appears
    @staticmethod
    def find_line_number(full_str: str, sub_str: str) -> int:
        index = full_str.find(sub_str)
        if index == -1:
            return -1

        line_number = full_str.count('\n', 0, index)
        return line_number

    # turn pgn with clock info into time per move
    @staticmethod
    def time_per_move(dirty_pgn: list[str], game_time: float, time_inc: float, color: str) -> list[float]:
        # extract clock times
        clock_times: list[str] = re.findall(r'\{\[%clk ([^\]]+)\]\}', dirty_pgn)

        start_clock: int = 0 if color == 'white' else 1

        time_per_move: list[float] = []
        prev_time: float = game_time + time_inc
        for clock_time in clock_times[start_clock::2]:
            seconds_time: float = Game.clock_to_seconds(clock_time)
            time_per_move.append(prev_time - seconds_time)
            prev_time = seconds_time + time_inc

        return time_per_move

    # convert clock time into seconds
    @staticmethod
    def clock_to_seconds(clock_time: str) -> float:
        hours, minutes, seconds = clock_time.split(':')
        return float(int(hours) * 3600 + int(minutes) * 60 + float(seconds))


