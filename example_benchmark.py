# from pympler import asizeof
# import gc
import tracemalloc
tracemalloc.start()
SINGLETON_MAX = 257


# @profile
def allocate_numbers(arr, count, arr_len = 0):
    rng = range(count)
    for i in rng:
        arr[i] = [None] * arr_len

# @profile
def main(num_to_allocate):
    q = 1048576 
    arr = [None] * q 
    # size0 = asizeof.asizeof(arr) 
    # print(size0)
    # print(size0 + asizeo.asizeof(q) + asizeof.asizeof(65536) + asizeof.asizeof(2) + asizeof.asizeof(32768))
    snapshot1 = tracemalloc.take_snapshot()
    allocate_numbers(arr, num_to_allocate, arr_len=32768)
    snapshot2 = tracemalloc.take_snapshot()
    stats = snapshot2.compare_to(snapshot1, 'lineno')
    relevant_stats = [stat for stat in stats if __file__ in stat.traceback._frames[0][0]]
    # print(stats.__class__)
    for stat in relevant_stats:
        print(stat)
    # size1 = asizeof.asizeof(arr)
    # print(size1-size0)

if __name__ == '__main__':
    main(32768 )