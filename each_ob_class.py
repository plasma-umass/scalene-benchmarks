import resource
a = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
print(a)
a = object()
b = b''
c = b"abcdefgh"
d = bytes(b'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa')
e = bytes(b'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa')
f = bytes(b'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa')
g = bytes(b'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa')
h = bytes(b'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa')
# i = bytes(500000)
b = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
print(b)

