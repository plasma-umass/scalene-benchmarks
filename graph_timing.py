import argparse
import json
from austin_reader import AustinReader
from scalene_reader import ScaleneReader
import matplotlib.pyplot as plt
import subprocess
import io

def run_austin():
    reader = AustinReader()
    proc = subprocess.run(
            ['austin', 
            '--pipe', 
            '-f', 
            'timing/mem.py'], 
        capture_output=True)
    stdout = io.BytesIO(proc.stdout)
    for line in stdout.readlines():
        reader.read_line(line.strip().decode("utf-8"))
    return reader

def run_scalene():
    reader = ScaleneReader()
    proc = subprocess.run(
        ['python3',
        '-m',
        'scalene',
        'timing/mem.py'
        ],
        capture_output=True
    )
    fname = proc.stdout.decode('utf-8').strip().split(' ')[0].strip()
    print(fname)
    with open(fname, 'r') as f:
        while True:
            line = f.readline().strip()
            if len(line) == 0:
                break
            reader.read_line(line)
    return reader

def run_tests():
    austin = run_austin()
    scalene = run_scalene()
    with open('results-mem.json', 'w+') as f:
        json.dump({
            'scalene': scalene.items_gen(),
            'austin': austin.items_gen()
        }, f)

def graph_results():
    with open('results-mem.json', 'r') as f:
        dd = json.load(f)
    scalene_times,scalene_footprints = list(zip(*dd['scalene']))
    austin_times,austin_footprints = list(zip(*dd['austin']))
    x, = plt.plot(scalene_times, scalene_footprints)
    x.set_label('scalene')
    y, = plt.plot(austin_times, austin_footprints)
    y.set_label('austin')
    plt.legend()
    plt.xlabel("Percent of run")
    plt.ylabel("Recorded footprint/sum of allocations and frees")
    plt.savefig('plots/memory-time.png')



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['run', 'graph', 'both'])
    args = parser.parse_args()
    if args.action == 'run' or args.action == 'both':
        run_tests()
    if args.action == 'graph' or args.action == 'both':
        graph_results()