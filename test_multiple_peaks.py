import gc
iterations = 200000 * 5

l = list(range(iterations))
for i in range(iterations):
    l[i] = {}

s = l[::63]  # [4]

del l
gc.collect()
r = bytearray(57600056)
del r
t = list(range(iterations))
for i in range(iterations):
    t[i] = {}