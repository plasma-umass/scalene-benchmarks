import time

import numpy as np
import tracemalloc
tracemalloc.start()

# @profile
def allocate():
    return np.zeros((1000,1000))

# @profile
def test_memory():
    slast = None
    x = allocate()
    for n in range(1):
        for i in range(100):
            for j in range(100):
                x[i,j] += 1
                t0 = time.perf_counter()
                s = tracemalloc.take_snapshot().statistics('filename')
                
                t1 = time.perf_counter()
                # print(t1 - t0)
    return x

if __name__ == '__main__':

    x = test_memory()

    