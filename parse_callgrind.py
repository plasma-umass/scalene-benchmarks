
from typing import TextIO
from enum import Enum
from collections import defaultdict
import os


class States(Enum):
    INIT = 0
    FL_BLOCK_FL = 1
    FL_BLOCK_FN = 2
    FL_BLOCK_INNER = 3
    CFL_BLOCK = 4
    FL_BLOCK_IGNORE = 5


def parse_callgrind(f: TextIO):
    state = States.INIT
    line = f.readline()
    func_names_to_runtime = defaultdict(lambda: defaultdict(lambda: 0))
    func_name = ''
    file_name = ''
    while line:
        if state is States.INIT:
            if not line.startswith("fl"):
                pass
            else:
                state = States.FL_BLOCK_FL
                continue
        elif state is States.FL_BLOCK_FL:
            file_path = line.strip().split('=')[1]
            file_name = os.path.basename(file_path)
            state = States.FL_BLOCK_FN
        elif state is States.FL_BLOCK_FN:
            splitline = line.strip().split('=')
            func_name = splitline[1].split(':')[0]
            state = States.FL_BLOCK_INNER
        elif state is States.FL_BLOCK_INNER:
            if line.startswith('cfl'):
                state = States.CFL_BLOCK
                continue
            if line.startswith('fn'):
                state = States.FL_BLOCK_FN
                continue
            elif line.startswith('fl'):
                state = States.FL_BLOCK_FL
                continue
            splitline = line.split(' ')
            tottime = float(splitline[2])
            func_names_to_runtime[file_name][func_name] += tottime
        elif state is States.CFL_BLOCK:
            if line.startswith('cfl') or line.startswith('cfn') or line.startswith('calls'):
                pass
            else:
                state = States.FL_BLOCK_INNER
                continue
        else:
            raise RuntimeError("RU")
        line = f.readline()
    return func_names_to_runtime


if __name__ == '__main__':
    f = open('callgrind.out', 'r')
    res = parse_callgrind(f)
    print(res)
