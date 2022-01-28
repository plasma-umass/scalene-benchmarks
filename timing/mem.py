#!/usr/bin/env python3

import time
import numpy as np
from sys import argv

ITS = 10
SIZE = 100000

def test_memory(no_touch):
    for i in range(ITS):
        print(f"=== {i} {time.monotonic_ns()}")
        x0 = np.zeros((1000, 10000)) # alloc
        if not no_touch:
            for it in range(1000):
                for j in range(10000):
                    x0[it][j] += 1
    print(f"=== {ITS} {time.monotonic_ns()}")
            

if __name__ == '__main__':
    x = test_memory('-n' in argv)

    