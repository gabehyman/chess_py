"""
### handle parallelization of the processing of user games
"""

from concurrent.futures import ProcessPoolExecutor
import os
import signal
import atexit
from game import Game


class Parallelize:
    _pid_to_engine = {}  # class-level dict to track engines by process ID

    @classmethod
    def get_engine(cls):
        """get engine for current process"""
        pid = os.getpid()
        return cls._pid_to_engine.get(pid)

    @classmethod
    def set_engine(cls, engine):
        """set engine for current process"""
        pid = os.getpid()
        cls._pid_to_engine[pid] = engine

    @classmethod
    def cleanup_engine(cls, *args):
        """clean up the engine for the current process"""
        pid = os.getpid()
        if pid in cls._pid_to_engine:
            engine = cls._pid_to_engine[pid]
            if engine is not None:
                engine[0].quit()
            del cls._pid_to_engine[pid]

    @classmethod
    def init_worker(cls, username):
        """init worker process"""
        engine = Game.create_engine()
        cls.set_engine(engine)

        # register cleanup handlers so engine is properly killed at termination
        atexit.register(cls.cleanup_engine)
        signal.signal(signal.SIGINT, cls.cleanup_engine)
        signal.signal(signal.SIGTERM, cls.cleanup_engine)

    @staticmethod
    def process_game(args):
        """process a single game using  worker's engine"""
        game_data, username = args  # unpack game_data and username args
        pid = os.getpid()

        if len(game_data.pgn_arr) == len(game_data.eval_per_move):
            return game_data

        engine = Parallelize.get_engine()
        if engine is None:
            raise RuntimeError(f'no engine found for process {pid}.')

        try:
            game_data.get_eval_per_move(engine)
            return game_data

        except Exception as e:
            print(f'error processing game in PID {pid}: {e}.')
            raise

    @classmethod
    def process_all_games(cls, games_to_process: list, username: str) -> list:
        """process all games in parallel using multiple workers"""
        if not games_to_process:
            return []

        # hard coded to be half the #num cores
        num_workers = min(len(games_to_process), max(1, os.cpu_count() // 2))

        # create argument pairs for each game
        game_args = [(game, username) for game in games_to_process]

        try:
            # create ProcessPoolExecutor with initializer and init args properly set
            with ProcessPoolExecutor(
                    max_workers=num_workers,
                    initializer=cls.init_worker,
                    initargs=(username,)
            ) as executor:
                # process games
                processed_games = list(executor.map(cls.process_game, game_args))

                # force cleanup by submitting a dummy task to each worker and wait for cleanup tasks to complete
                cleanup_tasks = [executor.submit(cls.cleanup_engine) for _ in range(num_workers)]
                for task in cleanup_tasks:
                    task.result()

        finally:
            # ensure any remaining cleanup happens
            for pid in list(cls._pid_to_engine.keys()):
                cls.cleanup_engine()

            return processed_games