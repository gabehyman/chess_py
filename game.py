from datetime import datetime
import re

chess_com_launch_date = datetime(2007, 5, 1)

class Game:

    def __init__(self, game: list, username: str, local: bool = False):
        if local:  # read locally stored game json
            self.color: str = game['color']
            self.result: bool = game['result']
            self.final_elo: int = game['final_elo']
            self.game_time: float = game['game_time']
            self.time_inc: float = game['time_inc']
            self.time_per_move: list[float] = game['time_per_move']
            self.pgn: str = game['pgn']
            self.start_time: datetime = datetime.fromtimestamp(game['start_time'])
            self.end_time: datetime = datetime.fromtimestamp(game['end_time'])
            self.duration: float = game['duration']
            self.dump = game
            return

        # json pulled from chess.com archive
        self.color: str = 'white' if game['white']['username'] == username else 'black'
        self.result: bool = game[self.color]['result']
        self.final_elo: int = game[self.color]['rating']

        time_control_info: list[str] = game['time_control'].split('+')
        self.game_time: float = float(time_control_info[0])
        self.time_inc: float = 0.0 if (len(time_control_info) == 1) else float(time_control_info[1])

        pgn_dirty: list[str] = game['pgn'].splitlines()
        pgn_no_clocks: list[str] = re.sub(r"\s*\{\[%clk [^\}]+\]\}", "", pgn_dirty[-1])
        pgn_normalized: list[str] = re.sub(r'\d+\.\.\.\s*', '', pgn_no_clocks)

        self.time_per_move: list[float] = Game.time_per_move(pgn_dirty[-1], self.game_time, self.time_inc, self.color)
        self.pgn: str = re.sub(r'\s+', ' ', pgn_normalized).strip()

        year, month, day = pgn_dirty[Game.find_line_number(game['pgn'], 'UTCDate')].split('\"')[1].split('.')
        hour, minute, sec = pgn_dirty[Game.find_line_number(game['pgn'], 'UTCTime')].split('\"')[1].split(':')
        self.start_time: datetime = datetime(int(year), int(month), int(day), int(hour), int(minute), int(sec))

        year, month, day = pgn_dirty[Game.find_line_number(game['pgn'], 'EndDate')].split('\"')[1].split('.')
        hour, minute, sec = pgn_dirty[Game.find_line_number(game['pgn'], 'EndTime')].split('\"')[1].split(':')
        self.end_time: datetime = datetime(int(year), int(month), int(day), int(hour), int(minute), int(sec))

        self.duration: float = (self.end_time - self.start_time).total_seconds()

        self.dump = {
            'color': self.color,
            'result': self.result,
            'final_elo': self.final_elo,
            'game_time': self.game_time,
            'time_inc': self.time_inc,
            'time_per_move': self.time_per_move,
            'pgn': self.pgn,
            'start_time': self.start_time.timestamp(),
            'end_time': self.end_time.timestamp(),
            'duration': self.duration }

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

    # compare the date of two archives
    @staticmethod
    def compare_archive_dates(base: str, comp: str) -> int:
        base_split = base.split('/')
        base_dt_obj: datetime = datetime(int(base_split[-2]), int(base_split[-1]), 1)

        comp_split = comp.split('/')
        comp_dt_obj: datetime = datetime(int(comp_split[-2]), int(comp_split[-1]), 1)

        return (base_dt_obj - comp_dt_obj).days

    @staticmethod
    def calc_month_index(date: datetime) -> int:
        return ((date.month - chess_com_launch_date.month)
                + (date.year - chess_com_launch_date.year) * 12)


