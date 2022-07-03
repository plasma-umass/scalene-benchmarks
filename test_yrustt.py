#! /usr/bin/env python3
import time 
from sys import platform
clock = time.CLOCK_UPTIME_RAW if platform == 'darwin' else time.CLOCK_MONOTONIC
print(f"=== 0 {time.clock_gettime_ns(clock)}")

iterations = 2000000

l = []
for i in range(iterations):
    l.append(None)
        
for i in range(iterations):
    l[i] = {}

print(f"=== 1 {time.clock_gettime_ns(clock)}")
s = l[::100]  # [4]

del l
print(f"=== 2 {time.clock_gettime_ns(clock)}")
for i in range(len(s)):
    s[i]['a'] = 3

print(f"=== 3 {time.clock_gettime_ns(clock)}")