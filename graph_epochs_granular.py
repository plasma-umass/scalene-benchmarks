import argparse
from jinja2 import FileSystemLoader, Environment
import json
from austin_reader import AustinReader
from pympler_reader import PymplerReader
from scalene_reader import ScaleneReader
import matplotlib.pyplot as plt
import subprocess
import io
import numpy as np
import os
import random 
from itertools import accumulate
import textwrap
N_EPOCHS = 10
N_ALLOCS_PER_EPOCH = 50
N_FREES_PER_EPOCH = 20


loader = FileSystemLoader('templates')

env = Environment(loader=loader)

mem_template = env.get_template(
    'test_yrustt.py.jinja2')

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
        reader.read_line_delta(line.strip().decode("utf-8"))
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
    reader = PymplerReader()
    fname = gen_randomness(epochs, is_pympler=True)
    print("RUNNING PYMPLER")
    print(' '.join(['python3',
         fname,
         '-y'
         ]))
    proc = subprocess.run(
        ['python3',
         fname,
         '-y'
         ],
        capture_output=True
    )

    fname = proc.stderr.decode('utf-8').strip().split(' ')[0].strip()
    stdout = proc.stdout.decode('utf-8')
    loop_boundaries = []
    for line in io.StringIO(stdout).readlines():
        if line.strip().startswith('==='):
            _, _, timestamp = line.rpartition(' ')
            loop_boundaries.append(int(timestamp))
    with open('/tmp/pympler_samples', 'r') as f:
        while True:
            line = f.readline().strip()
            if len(line) == 0:
                break
            reader.read_line(line)
    return reader, loop_boundaries


def run_tests(filename_base, n_epochs, n_allocs_per_epoch, n_frees_per_epoch):
    epochs = gen_epochs(n_epochs, n_allocs_per_epoch, n_frees_per_epoch)
    austin, austin_loop_starts = run_austin(epochs)
    scalene, scalene_loop_starts = run_scalene(epochs)
    # print("AAA")
    pympler, pympler_loop_starts = run_pympler(epochs)
    # print("uwu")
    with open(f'data/{filename_base}.json', 'w+') as f:
        json.dump({
            'scalene': scalene.items_gen_delta(),
            'scalene_loop_starts': scalene_loop_starts,
            'austin': austin.items_gen_delta(),
            'austin_loop_starts': austin_loop_starts,
            'pympler': pympler.items_gen(),
            'pympler_loop_starts': pympler_loop_starts
        }, f, indent='\t')

# largest timestamp should exist


def get_and_normalize_record(monotonic_time, loop_boundaries):
    current_idx = 0
    if monotonic_time < loop_boundaries[0] or monotonic_time > loop_boundaries[-1]:
        return None
    while current_idx < len(loop_boundaries) and monotonic_time > loop_boundaries[current_idx] :
        current_idx += 1
    if current_idx == len(loop_boundaries):
        return None
    val = current_idx - 1 + ((monotonic_time - loop_boundaries[current_idx - 1]) / (loop_boundaries[current_idx] - loop_boundaries[current_idx - 1]))
    if val > len(loop_boundaries) + 1:
        print(monotonic_time, current_idx, len(loop_boundaries), val, loop_boundaries[current_idx - 1], loop_boundaries[current_idx])
    return val

def put_record_in_row(monotonic_time, loop_boundaries):
    current_idx = 0
    if monotonic_time < loop_boundaries[0] or monotonic_time > loop_boundaries[-1]:
        return None, -1
    while current_idx < len(loop_boundaries) and monotonic_time > loop_boundaries[current_idx] :
        current_idx += 1
    x =  current_idx - 1 + ((monotonic_time - loop_boundaries[current_idx - 1]) / (loop_boundaries[current_idx] - loop_boundaries[current_idx - 1]))
    return x, current_idx - 1
# def get_austin_deltas(austin_records, austin_boundaries):
#     idx = 0
#     deltas = []
#     while austin_records[idx][2] <= austin_boundaries[0]:
#         idx += 1
#     print("=== AUSTIN ===")
#     for boundary in austin_boundaries[1:]:
#         print(f"starting at {austin_records[idx]}")
#         max_time = boundary
#         initial_footprint = austin_records[idx][1]
#         footprint = initial_footprint
#         while austin_records[idx][2] < max_time:
#             footprint = austin_records[idx][1]
#             idx += 1
            
#         print(f"Stopping at {austin_records[idx - 1]}")
#         delta = footprint # - initial_footprint
#         print(f"For epoch ending at {boundary}: {delta}")
#         deltas.append(delta)
#     return deltas
    

# def get_scalene_deltas(scalene_records, scalene_boundaries):
#     idx = 0
#     deltas = []
#     while scalene_records[idx][3] <= scalene_boundaries[0]:
#         idx += 1
#     print("=== Scalene ===")
    
#     for boundary in scalene_boundaries[1:]:
#         print(f"Starting at {scalene_records[idx]}")
#         max_time = boundary
#         initial_footprint = scalene_records[idx][1]
#         footprint = initial_footprint
#         while scalene_records[idx][3] < max_time:
#             footprint = scalene_records[idx][1]
#             idx += 1
            
#         print(f"Stopping at {scalene_records[idx - 1]}, {footprint}, {initial_footprint}")
#         delta = footprint # - initial_footprint
#         print(f"For epoch ending at {boundary}: {delta}")
#         deltas.append(delta)
#     return deltas

def graph_results(filename_base):
    with open(f'data/{filename_base}.json', 'r') as f:
        dd = json.load(f)
    scalene_loop_boundaries = dd['scalene_loop_starts']
    austin_loop_boundaries = dd['austin_loop_starts']
    pympler_loop_boundaries = dd['pympler_loop_starts']
    scalene_records = []
    # scalene_deltas = get_scalene_deltas(scalene_records, scalene_loop_boundaries)
    austin_records = []
    # austin_deltas = get_austin_deltas(austin_records, austin_loop_boundaries)
    scalene_records = []
    for monotime, delta in dd['scalene']:
        q = get_and_normalize_record(monotime, scalene_loop_boundaries)
        if q:
            scalene_records.append([q, delta])
    austin_records = []
    for monotime, delta in dd['austin']:
        aa = get_and_normalize_record(monotime, austin_loop_boundaries)
        if aa:
            austin_records.append([aa, delta])
    pympler_records = []
    for monotime, delta in dd['pympler']:
        cc = get_and_normalize_record(monotime, pympler_loop_boundaries)
        if cc:
            pympler_records.append([cc, delta])
    print(pympler_records)
    # # scalene_times, scalene_footprints, scalene_monotimes = list(
    # #     zip(*dd['scalene']))
    scalene_times, scalene_footprints = list(zip(*scalene_records))
    # # austin_times, austin_footprints, austin_monotimes = list(
    # #     zip(*dd['austin']))
    austin_times, austin_footprints = list(zip(*austin_records))
    pympler_times, pympler_footprints = list(zip(*pympler_records))
    # print(scalene_times)

    fig, axs = plt.subplots(3, sharex=True)
    z, = axs[0].plot(pympler_times, list(accumulate(pympler_footprints)))
    # print(axs[2].get_xticklabels())
    axs[0].axvline(x=1, linestyle=':')
    axs[0].axvline(x=2, linestyle=':')
    x, = axs[1].plot(scalene_times, list(accumulate(scalene_footprints)))
    axs[1].axvline(x=1, linestyle=':')
    axs[1].axvline(x=2, linestyle=':')
    # axs[0].get_xaxis().set_visible(False)
    # x.set_label('scalene')
    y, = axs[2].plot(austin_times, list(accumulate(austin_footprints)))
    # axs[1].get_xaxis().set_visible(False)
    # y.set_label('austin')
    axs[2].axvline(x=1, linestyle=':')
    axs[2].axvline(x=2, linestyle=':')
    
    rows = ['Pympler', 'Scalene', 'Austin']
    for ax, row in zip(axs, rows):
        ax.set_ylabel(row, rotation=0, size='small')
    plt.setp(axs, xticks=[0, 1, 2, 3])
    # axs[0].set_xticklabels([])
    # axs[1].set_xticklabels([])
    q = axs[2].set_xticklabels([
        textwrap.fill("Allocate array of 2e6 dicts", 20), 
        textwrap.fill("Put every 100th item in new array, free original array", 20), 
        textwrap.fill('Add item to each dict in array', 20), 
        ''], fontsize=9, ha='left')
    fig.suptitle('Memory footprint over time under fragmentation')
    print(q)
    print(3)
    # y.set_label('pympler')
    # plt.legend()
    # plt.xlabel("Program milestone")
    # plt.ylabel("Recorded footprint (bytes)")
    # plt.title('Memory footprint over time with fragmentation')
    plt.savefig(f'plots/{filename_base}.png')

def accumulate_deltas(ll):
    accum = 0
    for i in range(len(ll)):
        accum += ll[i][1]
        ll[i][1] = accum

def separate_list_by_int(ll):
    len_new_list = int(max(ll, key=lambda x : x[0])[0]) + 1
    ret = []
    for i in range(len_new_list):
        ret.append([])

    for q in ll:
        timestamp = q[0]
        ret[int(q[0])].append([timestamp, q[1]])
    # print(ret)
    return ret

def pad_lists(ll):
    ll[0] = [[0,0]] + ll[0]
    for i in range(1, len(ll) - 1):
        ll[i] = [ll[i-1][-1]] + ll[i] + [ll[i+1][0]]
    # print(ll[-1] )

    ll[-1] = [ll[-2][-2]] + ll[-1]

def graph_results_grid(filename_base):
    with open(f'data/{filename_base}.json', 'r') as f:
        dd = json.load(f)
    scalene_loop_boundaries = dd['scalene_loop_starts']
    austin_loop_boundaries = dd['austin_loop_starts']
    pympler_loop_boundaries = dd['pympler_loop_starts']
    scalene_records = []
    austin_records = []
    pympler_records = []
    # for i in range(len(scalene_loop_boundaries) - 1):
    #     scalene_records.append([])
    # # scalene_records = [[]] * len(scalene_loop_boundaries)
    # # scalene_deltas = get_scalene_deltas(scalene_records, scalene_loop_boundaries)
    # # austin_records = [[]] * len(austin_loop_boundaries)
    # for i in range(len(austin_loop_boundaries) - 1):
    #     austin_records.append([])
    # # austin_deltas = get_austin_deltas(austin_records, austin_loop_boundaries)
    # # pympler_records = [[]] * len(pympler_loop_boundaries)
    # for i in range(len(pympler_loop_boundaries) - 1):
    #     pympler_records.append([])
    for monotime, delta in dd['scalene']:
        q= get_and_normalize_record(monotime, scalene_loop_boundaries)
        # print(i)
        if q:
            scalene_records.append([q, delta])
    for monotime, delta in dd['austin']:
        aa = get_and_normalize_record(monotime, austin_loop_boundaries)
        if aa:
            austin_records.append([aa, delta])
    for monotime, delta in dd['pympler']:
        cc = get_and_normalize_record(monotime, pympler_loop_boundaries)
        if cc:
            pympler_records.append([cc, delta])
    accumulate_deltas(scalene_records)
    accumulate_deltas(austin_records)
    # accumulate_deltas(pympler_records)

    new_scalene_records = separate_list_by_int(scalene_records)
    new_austin_records = separate_list_by_int(austin_records)
    new_pympler_records = separate_list_by_int(pympler_records)
    print(new_pympler_records)
    pad_lists(new_scalene_records)
    pad_lists(new_austin_records)
    pad_lists(new_pympler_records)
    # print(new_pympler_records)
    fig, axs = plt.subplots(3, 3, sharex=False, sharey=True)

    for i in range(len(new_scalene_records)):
        # print(new_scalene_records[i])
        # print('aaa')
        times1, footprints1 = list(zip(*new_scalene_records[i]))
        
        axs[1, i].plot(times1, footprints1)
        # print()
        # if i == 0:
        #     print(times1, list(accumulate(footprints1)))
    # print('bbb', len(austin_loop_boundaries))
    for j in range(len(new_austin_records)):
        times2, footprints2 = list(zip(*new_austin_records[j]))
        axs[2,j].plot(times2, footprints2)
        # print()
        # if j == 0:
        # print(times2[:10], list(accumulate(footprints2))[:10])
        # print(len(times2), len(footprints2))
    for k in range(len(new_pympler_records)):
        times3, footprints3 = list(zip(*new_pympler_records[k]))
        # print(times3, footprints3)
        axs[0,k].plot(times3, footprints3)
    for ax in axs.flat:
        ax.set_xticklabels([])
    cols = ["List initialization", "Slicing and freeing", "Adding to dictionaries"]
    rows = ["Pympler", "Scalene", "Austin"]
    for ax, col in zip(axs[0], cols):
        ax.set_title(col)

    for ax, row in zip(axs[:,0], rows):
        ax.set_ylabel(row, rotation=0, size='large')
    # for ax in axs.flat:
    #     ax.label_outer()
    plt.savefig(f'plots/{filename_base}.png')
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['run', 'graph', 'both'])
    parser.add_argument('-f', '--filename', default="results")
    args = parser.parse_args()
    print("ARGS", args.filename)
    if args.action == 'run' or args.action == 'both':
        run_tests(args.filename, 10, 6, 6)
    if args.action == 'graph' or args.action == 'both':
        graph_results(args.filename)
