import multiprocessing as mp
from pathlib import Path

from mp_line_profiler import profile, profile_context

@profile
def worker(n):
    """Worker function that performs some computation."""
    total = 0
    for i in range(n):
        total += i * i
    return total

def test_worker_profile():
    """Test the profiling of the worker function."""
    n = 1000000

    with mp.Pool(processes=2) as pool, profile_context("profile_output.txt"):
        results = pool.map(worker, [n, n])

    try:
        assert results == [sum(i * i for i in range(n))] * 2
        assert Path("profile_output.txt").exists(), "Profile output file was not created."
        assert open("profile_output.txt").read(), "Profile output file is empty."
    finally:
        pass
        if Path("profile_output.txt").exists():
            Path("profile_output.txt").unlink()


if __name__ == "__main__":
    test_worker_profile()
    print("Test completed successfully.")