
from typing import TextIO
from collections import defaultdict

def parse_austin(austin_pipe_out: TextIO):
    function_runtimes = defaultdict(lambda : 0)
    for sample in austin_pipe_out:
        # print(sample)
        if sample.startswith('#'):
            continue
        head, _, metrics = sample.rpartition(" ")
        _, _, rest = head.partition(";")
        _, _, frames = rest.partition(";")
        if frames == '':
            continue
        runtime_cpu = int(metrics)
        for frame in frames.split(';'):
            filename, fn_name, _ = frame.split(':')
            if 'bias' in filename and fn_name != '<module>':
                function_runtimes[fn_name] += runtime_cpu
    return function_runtimes

if __name__ == '__main__':
    f = open('out.txt', 'r')
    res = parse_austin(f)
    print(res)