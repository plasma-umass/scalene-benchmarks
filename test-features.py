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
    def allocate():
        return np.zeros((10000,1000))
    x = allocate()
    for i in range(10000):
        for j in range(1000):
            x[0,0] += 1 # was x[i,j]
    
if __name__ == '__main__':
    multiprocessing.freeze_support()
    parser = argparse.ArgumentParser(description='Test profiler support for various Python features.')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--threading', action="store_const", const=True, help='Test threading support.', required=False)
    group.add_argument('--multiprocessing', action="store_const", const=True, help='Test multiprocessing support.', required=False)
    group.add_argument('--memory', action="store_const", const=True, help='Test memory attribution support.', required=False)
    args = parser.parse_args()

    if args.threading:
        test_threading()
    elif args.multiprocessing:
        test_multiprocessing()
    elif args.memory:
        test_memory()
        
