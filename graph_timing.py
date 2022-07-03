import argparse
from jinja2 import FileSystemLoader, Environment
import json
from austin_reader import AustinReader
from scalene_reader import ScaleneReader
import matplotlib.pyplot as plt
import subprocess
import io
import numpy as np
import os

loader = FileSystemLoader('templates')

env = Environment(loader=loader)

mem_template = env.get_template(
    'mem_rnd.py.jinja2')

np.random.seed(8980)
n_rand_accesses = 65536
n_rows = 10000
def get_indices(nrows, num):
    return np.random.randint(0, nrows, num)

def gen_randomness(nrows, n_accesses):
    fname = f"rendered/mem_rnd-{nrows}-{n_accesses}.py"
    indices = get_indices(nrows, n_accesses)
    rendered = mem_template.render(indices=indices, nrows=nrows)
    with open(fname, 'w+') as f:
        f.write(rendered)
    os.chmod(fname, 0o766)
    return fname

def run_austin(no_touch, is_random):
    reader = AustinReader()
    if is_random:
        fname = gen_randomness(n_rows, n_rand_accesses)
    else:
        # fname = 'timing/mem.py'
        fname = './test_yrustt.py'
    proc = subprocess.run(
        ['austin',
         '--pipe',
         '-f',
         fname,
         '-n' if no_touch else '-y'],
        capture_output=True)
    stdout = io.BytesIO(proc.stdout)
    for line in stdout.readlines():
        reader.read_line(line.strip().decode("utf-8"))
    loop_starts = []
    with open('/tmp/timestamp_file', 'r') as f:
        for line in f.readlines():
            if line.strip().startswith('==='):
                _, _, mono_s = line.rpartition(' ')
                loop_starts.append(int(mono_s))
    return reader, loop_starts


def run_scalene(no_touch, is_random):
    reader = ScaleneReader()
    if is_random:
        fname = gen_randomness(n_rows, n_rand_accesses)
    else:
        # fname = 'timing/mem.py'
        fname = 'test_yrustt.py'
    proc = subprocess.run(
        ['python3',
         '-m',
         'scalene',
         '--cli',
         fname,
         '-n' if no_touch else '-y'
         ],
        capture_output=True
    )
    print(' '.join(['python3',
         '-m',
         'scalene',
         fname,
         '-n' if no_touch else '-y'
         ]))
    fname = proc.stderr.decode('utf-8').strip().split(' ')[0].strip()
    stdout = proc.stdout.decode('utf-8')
    loop_starts = []
    for line in io.StringIO(stdout).readlines():
        if line.strip().startswith('==='):
            _, _, mono_s = line.rpartition(' ')
            loop_starts.append(int(mono_s))
    # fname = '/tmp/scalene-malloc-signal127802'
    print(fname)
    with open(fname, 'r') as f:
        while True:
            line = f.readline().strip()
            if len(line) == 0:
                break
            reader.read_line(line)
    return reader, loop_starts


def run_tests(filename_base, no_touch, is_random):
    austin, austin_loop_starts = run_austin(no_touch, is_random)
    scalene, scalene_loop_starts = run_scalene(no_touch, is_random)
    with open(f'data/{filename_base}.json', 'w+') as f:
        json.dump({
            'scalene': scalene.items_gen(),
            'scalene_loop_starts': scalene_loop_starts,
            'austin': austin.items_gen(),
            'austin_loop_starts': austin_loop_starts
        }, f, indent='\t')

# largest timestamp should exist


def get_and_normalize_record(monotonic_time, loop_boundaries):
    current_idx = 0
    while current_idx < len(loop_boundaries) and monotonic_time > loop_boundaries[current_idx] :
        current_idx += 1
    val = current_idx - 1 + ((monotonic_time - loop_boundaries[current_idx - 1]) / (loop_boundaries[current_idx] - loop_boundaries[current_idx - 1]))
    if val > len(loop_boundaries) + 1:
        print(monotonic_time, current_idx, len(loop_boundaries), val, loop_boundaries[current_idx - 1], loop_boundaries[current_idx])
    return val

def graph_results(filename_base, random, no_touch):
    with open(f'data/{filename_base}.json', 'r') as f:
        dd = json.load(f)
    scalene_loop_boundaries = dd['scalene_loop_starts']
    scalene_mintime = dd['scalene'][0][3]
    scalene_maxtime = dd['scalene'][-1][3]
    austin_mintime = dd['austin'][0][2]
    austin_maxtime = dd['austin'][-1][2]
    austin_loop_boundaries = dd['austin_loop_starts']
    scalene_records = []
    for _, footprint,time, monotime in dd['scalene']:
        scalene_records.append([get_and_normalize_record(monotime, [scalene_mintime] + scalene_loop_boundaries + [scalene_maxtime]), footprint])
    austin_records = []
    for _, footprint, monotime in dd['austin']:
        austin_records.append([get_and_normalize_record(monotime, [austin_mintime] + austin_loop_boundaries + [austin_maxtime]), footprint])
    # scalene_times, scalene_footprints, scalene_monotimes = list(
    #     zip(*dd['scalene']))
    scalene_times, scalene_footprints = list(zip(*scalene_records))
    # austin_times, austin_footprints, austin_monotimes = list(
    #     zip(*dd['austin']))
    austin_times, austin_footprints = list(zip(*austin_records))
    print(scalene_times)
    x, = plt.plot(scalene_times, scalene_footprints)
    x.set_label('scalene')
    y, = plt.plot(austin_times, austin_footprints)
    y.set_label('austin')
    plt.legend()
    plt.xlabel("Program milestone")
    plt.ylabel("Recorded footprint (bytes)")
    plt.title('Program milestone vs memory footprint')
    plt.savefig(f'plots/{filename_base}.png')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['run', 'graph', 'both'])
    parser.add_argument('-f', '--filename', default="results")
    parser.add_argument('-r', '--random', action='store_true')
    parser.add_argument('-n', '--no-touch', action='store_true')
    args = parser.parse_args()
    if args.action == 'run' or args.action == 'both':
        run_tests(args.filename, args.no_touch, args.random)
    if args.action == 'graph' or args.action == 'both':
        graph_results(args.filename, args.random, args.no_touch)
