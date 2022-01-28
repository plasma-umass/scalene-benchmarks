# import tracemalloc
# import numpy as np
# from pympler import asizeof
# tracemalloc.start()
# snapshot1 = tracemalloc.take_snapshot()
# x = np.zeros((1000,1000))
# snapshot2 = tracemalloc.take_snapshot()
# stats = snapshot2.compare_to(snapshot1, 'traceback')
# print(stats[0].size_diff)
# print(asizeof.asizeof(x))

def get_and_normalize_record(monotonic_time, loop_boundaries, smallest_timestamp, largest_timestamp):
    current_idx = 0
    while current_idx < len(loop_boundaries) and monotonic_time > loop_boundaries[current_idx] :
        current_idx += 1
    if current_idx == 0:
        val =  ((monotonic_time - smallest_timestamp) / ((loop_boundaries[0] - smallest_timestamp)))
    elif current_idx == len(loop_boundaries):
        val = len(loop_boundaries) + (( monotonic_time- loop_boundaries[-1] ) / (largest_timestamp - loop_boundaries[-1]))
    else:
        val = loop_boundaries[current_idx - 1] + ((monotonic_time - loop_boundaries[current_idx - 1]) / (loop_boundaries[current_idx] - loop_boundaries[current_idx - 1]))
    if val > len(loop_boundaries) + 1:
        print(monotonic_time, current_idx, len(loop_boundaries), val,  loop_boundaries[current_idx])
    return val

ll = [1,4,9,16,25]

print(get_and_normalize_record(3, ll, 0, 30))