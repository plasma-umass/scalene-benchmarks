import matplotlib.pyplot as plt
import argparse
import json
import subprocess

PROFILERS = ['scalene', 'austin'] # , 'memory_profiler']
ITERS = [20] # [1, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]

def get_cmd(profiler_name, num_iters):
    return ['python3', 'run_mem_tests.py', '-b', profiler_name, '-i', str(num_iters), '-l', 'loop1,alloc,loop2,loop3,touch1', '-w', '-s']

def run_test(profiler_name, iter):
    print(f"Running {profiler_name} {iter}")
    print(' '.join(get_cmd(profiler_name, iter)))
    proc = subprocess.run(get_cmd(profiler_name, iter), capture_output=True)
    assert proc.returncode == 0
    ret_json = json.loads(proc.stdout.decode('utf-8'))
    return max(ret_json.values())

def run_tests():
    profiler_lists = {
            prof: []
            for prof in PROFILERS           
    }
    for iter in ITERS:
        for prof_name in PROFILERS:
            high_watermark = run_test(prof_name, iter)
            profiler_lists[prof_name].append(high_watermark)


    profiler_lists['xvals'] =  ITERS
    with open('results.json', 'w+') as f:
        json.dump(profiler_lists, f, indent='\t')

def graph_results():
    with open('results.json', 'r') as f:
        results = json.loads(f.read())
    xvals = results['xvals']
    x, = plt.plot(xvals, results['scalene'])
    x.set_label('scalene')
    y, = plt.plot(xvals, results['austin'])
    y.set_label('austin')
    z, = plt.plot(xvals, results['memory_profiler'])
    z.set_label('memory_profiler')
    plt.legend()
    plt.xlabel("Number of loops")
    plt.ylabel("High watermark")
    plt.savefig('plots/timing.png')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['run', 'graph', 'both'])
    args = parser.parse_args()
    if args.action == 'run' or args.action == 'both':
        run_tests()
    if args.action == 'graph' or args.action == 'both':
        graph_results()
