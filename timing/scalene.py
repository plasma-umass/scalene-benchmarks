
import numpy as np

ITS = 1000000
SIZE = 100000

def test_memory():
    for i in range(50):
        x0 = np.empty((1000, SIZE// 100)) # alloc1
        for i in range(ITS // 100):
            x0[0] = 1 # touch1
        
        x = list(range(SIZE)) # alloc2
        for i in range(ITS):
            x[0] = 258 # alloc3
            

if __name__ == '__main__':
    x = test_memory()
