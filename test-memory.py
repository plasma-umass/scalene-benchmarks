import numpy as np
from pympler import asizeof
# import gc
import sys

try:
    profile
except NameError:
    def profile(f):
        return f

ITS = 1000000
SIZE = 100000

#@profile
def memory_test_python():
    x = list(range(SIZE))
    for i in range(ITS):
        x[0] = 258 # Force allocation of an object
    return x
    # print("python", asizeof.asizeof(x))

#@profile
def memory_test_native():
    y = np.zeros((1000, SIZE// 100))
    for i in range(ITS):
        y[0] = 1 # No object allocation for Python
    return y
    #print(sys.getsizeof(x))
    #print("native", asizeof.asizeof(x))

#@profile
def memory_test_both():
    x = np.empty((1000, SIZE// 100))
    for i in range(ITS):
        x[0] = 1
    # print(asizeof.asizeof(x))
    x = list(range(SIZE))
    for i in range(ITS):
        x[0] = 258 # Force allocation of an object
    # print(asizeof.asizeof(x))
    return x

#memory_test_both()
#memory_test_both()
memory_test_both()
