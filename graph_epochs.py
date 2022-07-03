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
import random 
import string

# Can't quite figure out what this one is, it seems important

N_EPOCHS = 10
N_ALLOCS_PER_EPOCH = 50
N_FREES_PER_EPOCH = 20

loader = FileSystemLoader('templates')

env = Environment(loader=loader)

mem_template = env.get_template(
    'mem_epochs.py.jinja2')

np.random.seed(8980)
random.seed(8980)

n_rand_accesses = 65536
n_rows = 10000

def get_random_size():
    return np.random.randint(131072, (20 * 131072) + 1) * 8

# To gen a multiple of 8 between 1K and 1M--
# (random(128, 131072) * 8)
def gen_epochs(n_epochs, n_allocs_per_epoch, n_frees_per_epoch):
    vars = set()
    epochs = []
    for epoch in range(n_epochs):
        allocs = []
        frees = []
        for alloc_n in range(n_allocs_per_epoch):
            var_name = f"epoch_{epoch}_{alloc_n}"
            vars.add(var_name)
            allocs.append({
                'var': var_name,
                'size': get_random_size()
            })
        # if epoch > 0:
        for _ in range(n_frees_per_epoch):
            to_free = random.sample(vars, 1)[0]
            vars.remove(to_free)
            frees.append({'var': to_free})
        epochs.append({'id': epoch, 'allocs': allocs, 'frees': frees})
    print(len(epochs))
    return epochs

def gen_randomness(epochs, is_pympler=False):
    fname = f"rendered/mem_epochs{'_pympler' if is_pympler else ''}.py"
    # epochs = gen_epochs(n_epochs, n_allocs_per_epoch, n_frees_per_epoch)
    rendered = mem_template.render(epochs=epochs, is_pympler=is_pympler)
    with open(fname, 'w+') as f:
        f.write(rendered)
    os.chmod(fname, 0o766)
    return fname




def run_austin(epochs):
    reader = AustinReader()
    
    fname = gen_randomness(epochs)
    proc = subprocess.run(
        ['austin',
         '--pipe',
         '-f',
         fname,
        '-y'],
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


def run_scalene(epochs):
    reader = ScaleneReader()
    fname = gen_randomness(epochs)
    
    proc = subprocess.run(
        ['python3',
         '-m',
         'scalene',
         fname,
         '-y',
         '--cli'
         ],
        capture_output=True
    )
    print(' '.join(['python3',
         '-m',
         'scalene',
         fname,
         '-y',
         '--cli'
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

def run_pympler(epochs):
    fname = gen_randomness(epochs, is_pympler=True)

    proc = subprocess.run(
        ['python3',
         fname,
         '-y'
         ],
        capture_output=True
    )
    print(' '.join(['python3',
         fname,
         '-y'
         ]))
    assert proc.returncode == 0
    fname = proc.stderr.decode('utf-8').strip().split(' ')[0].strip()
    stdout = proc.stdout.decode('utf-8')
    deltas = []
    for line in io.StringIO(stdout).readlines():
        if line.strip().startswith('==='):
            _, _, delta = line.rpartition(' ')
            deltas.append(int(delta))
    # fname = '/tmp/scalene-malloc-signal127802'
    return deltas


def run_tests(filename_base, n_epochs, n_allocs_per_epoch, n_frees_per_epoch):
    epochs = gen_epochs(n_epochs, n_allocs_per_epoch, n_frees_per_epoch)
    austin, austin_loop_starts = run_austin(epochs)
    scalene, scalene_loop_starts = run_scalene(epochs)
    actual_deltas = run_pympler(epochs)
    with open(f'data/{filename_base}.json', 'w+') as f:
        json.dump({
            'scalene': scalene.items_gen(),
            'scalene_loop_starts': scalene_loop_starts,
            'austin': austin.items_gen(),
            'austin_loop_starts': austin_loop_starts,
            'actual_deltas': actual_deltas
        }, f, indent='\t')

# largest timestamp should exist


# def get_and_normalize_record(monotonic_time, loop_boundaries):
#     current_idx = 0
#     while current_idx < len(loop_boundaries) and monotonic_time > loop_boundaries[current_idx] :
#         current_idx += 1
#     val = current_idx - 1 + ((monotonic_time - loop_boundaries[current_idx - 1]) / (loop_boundaries[current_idx] - loop_boundaries[current_idx - 1]))
#     if val > len(loop_boundaries) + 1:
#         print(monotonic_time, current_idx, len(loop_boundaries), val, loop_boundaries[current_idx - 1], loop_boundaries[current_idx])
#     return val

def get_austin_deltas(austin_records, austin_boundaries):
    idx = 0
    deltas = []
    while austin_records[idx][2] <= austin_boundaries[0]:
        idx += 1
    print("=== AUSTIN ===")
    for boundary in austin_boundaries[1:]:
        print(f"starting at {austin_records[idx]}")
        max_time = boundary
        initial_footprint = austin_records[idx][1]
        footprint = initial_footprint
        while austin_records[idx][2] < max_time:
            footprint = austin_records[idx][1]
            idx += 1
            
        print(f"Stopping at {austin_records[idx - 1]}")
        delta = footprint # - initial_footprint
        print(f"For epoch ending at {boundary}: {delta}")
        deltas.append(delta)
    return deltas
    

def get_scalene_deltas(scalene_records, scalene_boundaries):
    idx = 0
    deltas = []
    while scalene_records[idx][3] <= scalene_boundaries[0]:
        idx += 1
    print("=== Scalene ===")
    
    for boundary in scalene_boundaries[1:]:
        print(f"Starting at {scalene_records[idx]}")
        max_time = boundary
        initial_footprint = scalene_records[idx][1]
        footprint = initial_footprint
        while scalene_records[idx][3] < max_time:
            footprint = scalene_records[idx][1]
            idx += 1
            
        print(f"Stopping at {scalene_records[idx - 1]}, {footprint}, {initial_footprint}")
        delta = footprint # - initial_footprint
        print(f"For epoch ending at {boundary}: {delta}")
        deltas.append(delta)
    return deltas

def graph_results(filename_base):
    with open(f'data/{filename_base}.json', 'r') as f:
        dd = json.load(f)
    scalene_loop_boundaries = dd['scalene_loop_starts']
    austin_loop_boundaries = dd['austin_loop_starts']
    scalene_records = dd['scalene']
    scalene_deltas = get_scalene_deltas(scalene_records, scalene_loop_boundaries)
    austin_records = dd['austin']
    austin_deltas = get_austin_deltas(austin_records, austin_loop_boundaries)
    actual_deltas = dd['actual_deltas'][1:]
    # scalene_records = []
    # # for _, footprint,time, monotime in dd['scalene']:
    # #     scalene_records.append([get_and_normalize_record(monotime, [scalene_mintime] + scalene_loop_boundaries + [scalene_maxtime]), footprint])
    # austin_records = []
    # # for _, footprint, monotime in dd['austin']:
    #     # austin_records.append([get_and_normalize_record(monotime, [austin_mintime] + austin_loop_boundaries + [austin_maxtime]), footprint])
    # # scalene_times, scalene_footprints, scalene_monotimes = list(
    # #     zip(*dd['scalene']))
    # scalene_times, scalene_footprints = list(zip(*scalene_records))
    # # austin_times, austin_footprints, austin_monotimes = list(
    # #     zip(*dd['austin']))
    # austin_times, austin_footprints = list(zip(*austin_records))
    # print(scalene_times)
    x, = plt.plot(range(len(scalene_deltas)), scalene_deltas)
    x.set_label('scalene')
    y, = plt.plot(range(len(austin_deltas)), austin_deltas)
    y.set_label('austin')
    y, = plt.plot(range(len(actual_deltas)), actual_deltas)
    y.set_label('pympler')
    plt.legend()
    plt.xlabel("Program milestone")
    plt.ylabel("Recorded footprint (bytes)")
    plt.title('Program milestone vs memory footprint')
    plt.savefig(f'plots/{filename_base}.png')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['run', 'graph', 'both'])
    parser.add_argument('-f', '--filename', default="results")
    args = parser.parse_args()
    if args.action == 'run' or args.action == 'both':
        run_tests(args.filename, 10, 5, 5)
    if args.action == 'graph' or args.action == 'both':
        graph_results(args.filename)
