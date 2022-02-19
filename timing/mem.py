#!/usr/bin/env python3

import time
import numpy as np
from sys import argv, platform


clock = time.CLOCK_UPTIME_RAW if platform == 'darwin' else time.CLOCK_MONOTONIC
ITS = 5

def test_memory(no_touch):
    for i in range(ITS):
        print(f"=== {i} {time.clock_gettime_ns(clock)}")
        x0 = np.zeros((10000, 10000)) # alloc
        if not no_touch:
            for it in range(10000):
                for j in range(10000):
                    x0[it][j] += 1
    print(f"=== {ITS} {time.clock_gettime_ns(clock)}")
            

if __name__ == '__main__':
    x = test_memory('-n' in argv)

    