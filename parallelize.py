from concurrent.futures import ProcessPoolExecutor
import os
import signal
import atexit
from contextlib import contextmanager
from game import Game


class Parallelize:
    _pid_to_engine = {}  # Class-level dict to track engines by process ID

    @classmethod
    def get_engine(cls):
        """Get the engine instance for the current process."""
        pid = os.getpid()
        return cls._pid_to_engine.get(pid)

    @classmethod
    def set_engine(cls, engine):
        """Set the engine instance for the current process."""
        pid = os.getpid()
        cls._pid_to_engine[pid] = engine

    @classmethod
    def cleanup_engine(cls, *args):
        """Clean up the engine for the current process."""
        pid = os.getpid()
        if pid in cls._pid_to_engine:
            engine = cls._pid_to_engine[pid]
            if engine is not None:
                engine[0].quit()  # Assuming engine is a tuple with engine instance at index 0
            del cls._pid_to_engine[pid]

        print(f'cleanup for {pid}')

    @classmethod
    def init_worker(cls, username):
        """Initialize worker process."""
        # Create engine for this worker
        engine = Game.create_engine()
        cls.set_engine(engine)

        # Register cleanup handlers
        atexit.register(cls.cleanup_engine)
        signal.signal(signal.SIGINT, cls.cleanup_engine)
        signal.signal(signal.SIGTERM, cls.cleanup_engine)

        pid = os.getpid()
        print(f'init for {pid}')

    @staticmethod
    def process_game(args):
        """Process a single game using the worker's engine."""
        game_data, username = args  # Unpack the arguments
        pid = os.getpid()
        engine = Parallelize.get_engine()
        if engine is None:
            raise RuntimeError(f"No engine found for process {pid}")

        try:
            result = Game(game_data, username, engine, False)
            return result
        except Exception as e:
            print(f"Error processing game in PID {pid}: {e}")
            raise

    @classmethod
    def process_all_games(cls, games_to_process: list, username: str) -> list:
        if not games_to_process:
            return []

        """Process all games in parallel using multiple workers."""
        num_workers = min(len(games_to_process), max(1, os.cpu_count() // 2))

        # Create argument pairs for each game
        game_args = [(game, username) for game in games_to_process]

        try:
            # Create ProcessPoolExecutor with initializer and initargs properly set
            with ProcessPoolExecutor(
                    max_workers=num_workers,
                    initializer=cls.init_worker,
                    initargs=(username,)
            ) as executor:
                # Process games
                processed_games = list(executor.map(cls.process_game, game_args))

                # Force cleanup by submitting a dummy task to each worker
                cleanup_tasks = [executor.submit(cls.cleanup_engine) for _ in range(num_workers)]
                # Wait for cleanup tasks to complete
                for task in cleanup_tasks:
                    task.result()

                print(f'about to return')

                return processed_games

        finally:
            # Ensure any remaining cleanup happens
            pass
            # for pid in list(cls._pid_to_engine.keys()):
            #     cls.cleanup_engine()