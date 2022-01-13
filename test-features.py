import argparse
import sys
import threading
import multiprocessing
import numpy as np

try:
    profile
except NameError:
    def profile(f):
        return f

@profile
def do_work(n):
    print(f"thread {n}")
    x = 0
    for i in range(1000):
        for j in range(1000):
            for k in range(10):
                x += 1

@profile
def test_threading():
    # Threads?
    t1 = threading.Thread(target=do_work, args=(1,))
    t2 = threading.Thread(target=do_work, args=(2,))
    t1.start()
    t2.start()

@profile
def test_multiprocessing():
    # Multiprocessing?
    handles = [multiprocessing.Process(target=do_work, args=(i,)) for i in range(2)]

    for handle in handles:
        print("Starting", handle)
        handle.start()

    for handle in handles:
        print("Joining", handle)
        handle.join()

@profile
def test_memory():
    XDIM = 10000
    YDIM = 1000
    def allocate():
        return np.zeros((XDIM,YDIM))
    x = allocate()
    for i in range(XDIM):
        for j in range(YDIM):
            x[0,0] += 1 # was x[i,j]

@profile
def test_leak():
    ITS = 1000000
    NON_LEAK = 20
    acc = [None] * ITS
    leak = []
    for i in range(ITS):
        acc[i] = []
        for j in range(NON_LEAK):
            acc[i].append(j)
        leak.append(1000)
            
if __name__ == '__main__':
    multiprocessing.freeze_support()
    parser = argparse.ArgumentParser(description='Test profiler support for various Python features.')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--threading', action="store_const", const=True, help='Test threading support.', required=False)
    group.add_argument('--multiprocessing', action="store_const", const=True, help='Test multiprocessing support.', required=False)
    group.add_argument('--memory', action="store_const", const=True, help='Test memory attribution support.', required=False)
    group.add_argument('--leak', action="store_const", const=True, help='Test leak detection support.', required=False)
    args = parser.parse_args()

    import time
    start = time.perf_counter()
    if args.threading:
        test_threading()
    elif args.multiprocessing:
        test_multiprocessing()
    elif args.memory:
        test_memory()
    elif args.leak:
        test_leak()
    stop = time.perf_counter()
    print("Time elapsed: ", stop - start, " seconds")
        
