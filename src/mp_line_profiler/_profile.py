import os
import time
import functools
from pathlib import Path
from contextlib import contextmanager

import line_profiler

def profile(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        profiler = line_profiler.LineProfiler()
        profiler.add_function(func)

        output_file = os.path.join(
            os.getcwd(),
            f"{func.__name__}_{os.getpid()}_{os.getppid()}.lprof",
        )

        profiler.enable_by_count()
        try:
            return func(*args, **kwargs)
        finally:
            profiler.disable_by_count()
            profiler.dump_stats(output_file)

    return wrapper

@contextmanager
def profile_context(filename=None):
    try:
        yield
    finally:
        files = [Path(f) for f in os.listdir(os.getcwd()) if f.endswith(f"_{os.getpid()}.lprof")]
        if files:
            line_stats = line_profiler.LineStats.from_files(*files)

            if filename is None:
                filename = f"profile_{time.strftime('%Y%m%d_%H%M%S')}_.txt"

            with open(filename, "w") as f:
                line_profiler.show_text(line_stats.timings, unit=line_stats.unit, stream=f)

            for file in files:
                file.unlink()  # Remove the individual .lprof files after processing

