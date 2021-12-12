from typing import TextIO
from collections import defaultdict
from os.path import basename

def parse_fil(input: TextIO, filename_discriminator = None):
    ret = defaultdict(lambda : defaultdict(lambda : 0))
    for line in input:
        head, _, alloc = line.rpartition(' ')
        _, _, callermost = head.rpartition(';')
        
        filename_w_line, _, fn_name = callermost.rpartition(' ')
        fn_name = fn_name.strip().removeprefix('(').removesuffix(')')
        filename, lineno = filename_w_line.split(':')
        file_basename = basename(filename)
        if filename_discriminator and filename_discriminator not in file_basename:
            continue
        ret[file_basename][int(lineno)] = int(alloc)
    return ret


if __name__ == '__main__':
    with open('peak-memory.prof', 'r') as f:
        res = parse_fil(f, 'testme')
    print(res)
