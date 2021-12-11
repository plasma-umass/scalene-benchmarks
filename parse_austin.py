
from typing import TextIO
from collections import defaultdict

def parse_austin(austin_pipe_out: TextIO, is_full=False, filename_prefix='bias'):
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
        if is_full:
            runtime = metrics.split(',')[0]
        else:
            runtime = metrics
        runtime_cpu = int(runtime)
        for frame in frames.split(';'):
            filename, fn_name, _ = frame.split(':')
            if filename_prefix in filename and fn_name != '<module>':
                function_runtimes[fn_name] += runtime_cpu
    return function_runtimes

if __name__ == '__main__':
    f = open('austin.out', 'r')
    res = parse_austin(f, is_full=False, filename_prefix='test-features')
    print(res)