import os
import time
import pickle
import operator
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

def write_stats(line_stats: line_profiler.LineStats, f):
    line_profiler.show_text(line_stats.timings, unit=line_stats.unit, stream=f)

def average(stats_objs: line_profiler.LineStats, f):
    if len(stats_objs) > 1:
        # Add from small scaling factors to large to minimize
        # rounding errors
        stats_objs = sorted(stats_objs, key=operator.attrgetter('unit'))
        unit = stats_objs[-1].unit
        timing_dict = {}
        count_dict = {}
        for stats in stats_objs:
            factor = stats.unit / unit
            for key, entries in stats.timings.items():
                entry_dict = timing_dict.setdefault(key, {})
                prev_count = count_dict.get(key, 0)
                for lineno, nhits, time in entries:
                    prev_nhits, prev_time = entry_dict.get(lineno, (0, 0))
                    entry_dict[lineno] = (
                        prev_nhits + nhits,
                        prev_time + factor * time,
                    )
                count_dict[key] = prev_count + 1
        timings = {
            key: [
                (lineno, nhits / count_dict[key], int(round(time / count_dict[key], 0)))
                for lineno, (nhits, time) in sorted(entry_dict.items())
            ]
            for key, entry_dict in timing_dict.items()
        }
        stats = line_profiler.LineStats(timings, unit)
    else:
        stats = stats_objs[0]

    write_stats(stats, f)

@contextmanager
def profile_context(filename=None, agg=None):
    try:
        yield
    finally:
        files = [Path(f) for f in os.listdir(os.getcwd()) if f.endswith(f"_{os.getpid()}.lprof")]
        if files:

            if filename is None:
                filename = f"profile_{time.strftime('%Y%m%d_%H%M%S')}_.txt"

            with open(filename, "w") as f:
                line_stats = line_profiler.LineStats.from_files(*files)
                if agg is None or agg == "sum":
                    write_stats(line_stats, f)
                elif agg == "average":
                    stats_objs = []
                    for file in files:
                        with open(file, 'rb') as _f:
                            stats_objs.append(pickle.load(_f))
                    average(stats_objs, f)
                else:
                    raise ValueError(f"Invalid aggregation method: {agg}")

            for file in files:
                file.unlink()  # Remove the individual .lprof files after processing

