
from typing import TextIO
from collections import defaultdict
import os

def parse_austin(austin_pipe_out: TextIO, is_full=False, filename_prefix='bias'):
    function_runtimes = defaultdict(lambda : defaultdict(lambda : []))
    line_runtimes = defaultdict(lambda : defaultdict(lambda : []))
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
            filename, fn_name, lineno = frame.split(':')
            if filename_prefix in filename and fn_name != '<module>':
                function_runtimes[os.path.basename(filename)][fn_name].append(runtime_cpu)
                line_runtimes[os.path.basename(filename)][lineno].append(runtime_cpu)
    return {
            'functions': function_runtimes,
            'lines': line_runtimes
        }

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--file', type=str, default='austin.out')
    args = parser.parse_args()
    f = open(args.file, 'r')
    res = parse_austin(f, is_full=False, filename_prefix='test-features')
    print(res)