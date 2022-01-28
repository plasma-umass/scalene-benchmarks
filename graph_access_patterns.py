import matplotlib.pyplot as plt
import argparse
import json
import subprocess

PROFILERS = ['scalene', 'austin', 'pympler', 'memory_profiler']
# ITERS = [20] # [1, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
iter = 20
accesses = [2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192]
def get_cmd(profiler_name, num_iters, access):
    return ['python3', 'run_access_patterns.py', '-b', profiler_name, '-i', str(num_iters), '-l', 'index,loop1,alloc,loop2,touch1', '-a', str(access), '-s']

def run_test(profiler_name, iter, access):
    print(f"Running {profiler_name} {iter} {access}")
    print(' '.join(get_cmd(profiler_name, iter, access)))
    proc = subprocess.run(get_cmd(profiler_name, iter, access), capture_output=True)
    assert proc.returncode == 0
    ret_json = json.loads(proc.stdout.decode('utf-8'))
    if profiler_name == 'pympler':
        return sum(ret_json.values())
    return max(ret_json.values())

def run_tests(filename_base):
    profiler_lists = {
            prof: []
            for prof in PROFILERS           
    }
    for access in accesses:
        for prof_name in PROFILERS:
            high_watermark = run_test(prof_name, iter, access)
            profiler_lists[prof_name].append(high_watermark)


    profiler_lists['xvals'] =  accesses
    with open(f'data/{filename_base}.json', 'w+') as f:
        json.dump(profiler_lists, f, indent='\t')

def graph_results(filename_base):
    with open(f'data/{filename_base}.json', 'r') as f:
        results = json.loads(f.read())
    xvals = results['xvals']
    x, = plt.plot(xvals, results['scalene'])
    x.set_label('scalene')
    y, = plt.plot(xvals, results['austin'])
    y.set_label('austin')
    z, = plt.plot(xvals, results['pympler'])
    z.set_label('pympler')
    a, = plt.plot(xvals, results['memory_profiler'])
    a.set_label('memory_profiler')
    plt.legend()
    plt.xscale('log')
    plt.xlabel("Number of rows accessed")
    plt.ylabel("High watermark")
    plt.savefig(f'plots/{filename_base}.png')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['run', 'graph', 'both'])
    parser.add_argument('-f', '--filename', default='results')
    args = parser.parse_args()
    if args.action == 'run' or args.action == 'both':
        run_tests(args.filename)
    if args.action == 'graph' or args.action == 'both':
        graph_results(args.filename)
