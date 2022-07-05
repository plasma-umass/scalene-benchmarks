import matplotlib.pyplot as plt
import argparse
import json
import subprocess

# This is meant to show how RSS is a bad metric for memory usage

# This varies the number of random accesses for an array of a fixed size

PROFILERS = ['scalene', 'austin', 'memory_profiler']# ,'memory_profiler']
# ITERS = [20] # [1, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
iter = 10
size_of_array = 131072 * 512
accesses = [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768, 65536, 131072]
def get_cmd(profiler_name, num_iters, access):
    return ['python3', 'run_access_patterns.py', '-b', profiler_name, '-i', str(num_iters), '-l', 'index,loop1,alloc,loop2,touch1', '-a', str(access), '-s', '-n', str(size_of_array)]

def run_test(profiler_name, iter, access):
    print(f"Running {profiler_name} {iter} {access}")
    print(' '.join(get_cmd(profiler_name, iter, access)))
    proc = subprocess.run(get_cmd(profiler_name, iter, access), capture_output=True)
    if proc.returncode != 0:
        print("ERROR IN RUN")
        print(proc.stderr.decode('utf-8'))
        print(proc.stdout.decode('utf-8'))
        return None
    q = proc.stdout.decode('utf-8')
    # print(q, proc.stderr.decode('utf-8'))
    ret_json = json.loads(q)
    if profiler_name == 'pympler':
        return sum(ret_json.values())
    print(ret_json)
    # By default, this simply takes the things in the JSON and sums them or gets the max--
    # If we do multiple runs, we can just average with error bars
    # Possibly just run this multiple times
    return max(ret_json.values()) if len(ret_json.values()) > 0 else 0

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
    profiler_lists['arr_size'] = size_of_array
    with open(f'data/{filename_base}.json', 'w+') as f:
        json.dump(profiler_lists, f, indent='\t')

def graph_results(filename_base):
    with open(f'data/{filename_base}.json', 'r') as f:
        results = json.loads(f.read())
    xvals = [((i * 512) / results['arr_size']) * 100 for i in results['xvals']]
    x, = plt.plot(xvals, results['scalene'])
    x.set_label('scalene')
    y, = plt.plot(xvals, results['austin'])
    y.set_label('austin')
    # z, = plt.plot(xvals, results['pympler'])
    # z.set_label('pympler')
    a, = plt.plot(xvals, results['memory_profiler'])
    a.set_label('memory_profiler')
    plt.legend()
    plt.ylim(bottom=0)
    plt.xlabel("Allocated pages of array accessed (%)")
    plt.ylabel("Allocation footprint (bytes)")
    plt.title('Allocated pages accessed vs allocation footprint')
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
