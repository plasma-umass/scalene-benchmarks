#!/usr/bin/env python3

import numpy as np

ITS = 10
SIZE = 100000

def test_memory():
    for i in range(ITS):
        x0 = np.zeros((1000, 10000)) # alloc1
        for i in range(1000):
            for j in range(10000):
                x0[i][j] += 1
            

if __name__ == '__main__':
    x = test_memory()

    