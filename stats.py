from game import Game, mate_eval
from sort import Sort
import plotly.graph_objects as go

from game import Color
from game import Result

class Stats:
     # all time classes
    time_classes: list[str] = ['bullet', 'blitz', 'rapid', 'daily']

    def __init__(self, sorter: Sort):
        """for now we have an init but ultimately just a static class??"""
        # have reference to sorter object for data
        self.sorter: Sort = sorter

        self.game_time_per_month: list[float] = [0] * self.sorter.num_months_active
        self.num_games_per_month: list[int] = [0] * self.sorter.num_months_active
        self.month_indices_str: list[str] = [Game.month_index_to_str_months(self.sorter.first_month_index + i)
                                             for i in range(self.sorter.num_months_active)]
        self.calc_game_time_per_month()
        self.total_time_player = sum(self.game_time_per_month)

        self.opening_stats = Stats.get_opening_stats(self.sorter.games_container['games'])
        self.opp_stats = self.get_opp_stats()

    def calc_game_time_per_month(self):
        for game in self.sorter.games_container['games']:
            self.game_time_per_month[game.month_index - self.sorter.first_month_index] += 1  # num games
            self.game_time_per_month[game.month_index - self.sorter.first_month_index] += game.duration # total secs

        self.game_time_per_month = [time for time in self.game_time_per_month]

    def plotly_plot_game_time_per_month(self):
        Stats.plotly_plot([Stats.seconds_to_hrs(time) for time in self.game_time_per_month], self.month_indices_str,
                          ['month', 'time played (hrs)'],
                          f'{self.sorter.username}\'s game time per month'
                          f' (total time = {Stats.seconds_to_days_str(self.total_time_player)})')

    def get_opp_stats(self):
        opp_stats: dict[str, list[list[int]]] = {}

        for game in self.sorter.games_container['games']:
            if game.opp not in opp_stats:
                opp_stats[game.opp] = [[0, 0, 0], [0, 0, 0]]

            opp_stats[game.opp][game.color.value][game.result.value] += 1

        return opp_stats

    @staticmethod
    def get_opening_stats(games: list[Game], depth: int = 10, color: int = -1,
                          selected_time_classes: list[str] = None) -> dict[str, list[list]]:
        """sorts through openings at given depth and gets record and eval from a given position"""
        # default to all time classes (handle as mutable default param)
        if selected_time_classes is None:
            selected_time_classes = Stats.time_classes

        # convert to dict for constant time lookup (not huge deal because only 4 classes but op principe)
        selected_time_class_dict = {key: True for key in selected_time_classes}

        opening_stats: dict[str, list[list]] = {}

        for game in games:
            # exclude all games that don't match user criteria for time class and color (color = -1 -> both b&w)
            if color == -1 or game.color.value == color:
                if game.time_class in selected_time_class_dict:
                    if len(game.pgn_arr) >= depth:
                        pgn: str = Game.pgn_arr_to_str(game.pgn_arr, depth)

                        if pgn not in opening_stats:
                            # default if evals not loaded
                            white_eval = None
                            if game.eval_per_move:
                                # all evals saved as white position to be consistent
                                white_eval = (game.eval_per_move[depth-1] if game.color == Color.WHITE
                                    else game.eval_per_move[depth-1] * -1)

                            # make new entry for the opening to track
                            opening_stats[pgn] = [[0, 0, 0], [0, 0, 0], [white_eval]]

                        # increment record of color/result
                        opening_stats[pgn][game.color.value][game.result.value] += 1

        return opening_stats

    @staticmethod
    def get_total_record(stats: dict[str, list[list[int]]]):
        """calculate total record across all games"""
        wins = 0
        draws = 0
        losses = 0
        num_games = 0
        for key, value in stats.items():
            for lst in value[0:2]:  # only the first two inner lists (white and black records)
                wins += lst[0]
                draws += lst[1]
                losses += lst[2]
                num_games += sum(lst)

        return wins, draws, losses, num_games

    @staticmethod
    def sort_opening_stats(stats: dict[str, list[list[int]]], filter_type: int, color: int, mates: int, result: int,
                           high_low: bool) -> dict[str, list[list[int]]]:
        """sort through openings based on a variety of user input"""
        # store all stats we are interested in sorting
        filtered_stats = stats.items()

        # sorting by eval
        if not filter_type:  # eval == 0
            if mates != -1:
                if mates == 0:  # only show mates
                    filtered_stats = (item for item in filtered_stats if abs(item[1][len(Color)][0]) > mate_eval)
                else:  # exclude mates
                    filtered_stats = (item for item in filtered_stats if abs(item[1][len(Color)][0]) < mate_eval)

            if color != -1:
                # if we sort by black eval, reverse inputted order (as high black eval is negative)
                if color == Color.BLACK.value:
                    high_low = not high_low


                sorted_stats = sorted(filtered_stats, key=lambda item: item[1][len(Color)][0], reverse=high_low)

            else:  # if color == -1, we sort for both so we are just interested in absolute value
                sorted_stats = sorted(filtered_stats, key=lambda item: abs(item[1][len(Color)][0]), reverse=high_low)

        # sorting by record
        elif color != -1 and result != -1:
            if result == len(Result)+1:  # wins - losses
                sorted_stats = sorted(filtered_stats, key=lambda item: (item[1][color][0] - item[1][color][0]),
                                      reverse=high_low)
            elif result == len(Result)+2:  # losses - wins
                sorted_stats = sorted(filtered_stats, key=lambda item: (item[1][color][2] - item[1][color][0]),
                                      reverse=high_low)
            else:
                # sort by value at stats[key][color][result]
                sorted_stats = sorted(filtered_stats, key=lambda item: item[1][color][result], reverse=high_low)

        elif color != -1:
            # sort by sum of all results as the specified color (exclude anything after, eg eval)
            sorted_stats = sorted(filtered_stats, key=lambda item: sum(item[1][color][:len(Result)]), reverse=high_low)

        elif result != -1:
            if result == len(Result) + 1:  # wins - losses
                sorted_stats = sorted(filtered_stats,
                                      key=lambda item: sum(item[1][x][0] - item[1][x][2] for x in range(len(Color))),
                                      reverse=high_low)
            elif result == len(Result) + 2:  # losses - wins
                sorted_stats = sorted(filtered_stats,
                                      key=lambda item: sum(item[1][x][2] - item[1][x][0] for x in range(len(Color))),
                                      reverse=high_low)
            else:
                # sort by sum of all games with the specified result across both colors
                sorted_stats = sorted(filtered_stats, key=lambda item: sum(item[1][x][result] for x in range(len(Color))),
                                      reverse=high_low)

        else:
            # sort by sum of all entries' results in the stats
            sorted_stats = sorted(filtered_stats, key=lambda item: sum(sum(inner_list) for inner_list in item[1][:len(Color)]),
                                  reverse=high_low)

        return dict(sorted_stats)



    @staticmethod
    def plotly_plot(data: list, labels: list[str], axis_titles: list[str], title: str):
        """create interactive bar chart"""
        fig = go.Figure(data=[
            go.Bar(x=labels, y=data)])

        # update layout to make the x-axis scrollable
        fig.update_layout(
            xaxis=dict(
                rangeslider=dict(visible=True),
                type='category'),
                title=title,
                xaxis_title=axis_titles[0],
                yaxis_title=axis_titles[1])

        # display the plot
        fig.show()

    @staticmethod
    def seconds_to_hrs(seconds: float) -> float:
        """convert seconds to hours"""
        return seconds / (60 * 60)

    @staticmethod
    def seconds_to_days_str(seconds: float) -> str:
        """convert seconds to amount of days (days/hrs/mins/seconds)"""
        days: int = int(seconds // (24 * 3600))
        seconds %= (24 * 3600)
        hours: int = int(seconds // 3600)
        seconds %= 3600
        minutes: int = int(seconds // 60)
        seconds %= 60

        return f'{days}days {hours}hrs, {minutes}mins {int(seconds)}secs'