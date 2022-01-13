import matplotlib.pyplot as plt
import argparse
import json
import subprocess

PROFILERS = ['scalene', 'pympler', 'austin']
ITERS = [1, 10, 20, 30, 40, 50]

def get_cmd(profiler_name, num_iters):
    return ['python3', 'run_mem_tests.py', '-b', profiler_name, '-i', str(num_iters), '-s']

def run_test(profiler_name, iter):
    print(f"Running {profiler_name} {iter}")
    proc = subprocess.run(get_cmd(profiler_name, iter), capture_output=True)
    assert proc.returncode == 0
    ret_json = json.loads(proc.stdout.decode('utf-8'))
    if profiler_name == 'austin':
        return ret_json['touch1']['average'], ret_json['touch1']['total']
    else:
        return ret_json['alloc1']['average'], ret_json['alloc1']['total']
    
def run_tests():
    profiler_lists = {
            prof: {
                'averages': [],
                'totals': []
            }
            for prof in PROFILERS
            
    }

    for iter in ITERS:
        for prof_name in PROFILERS:
            average, total = run_test(prof_name, iter)
            profiler_lists[prof_name]['averages'].append(average)
            profiler_lists[prof_name]['totals'].append(total)

    profiler_lists['xvals'] =  ITERS
    with open('results.json', 'w+') as f:
        json.dump(profiler_lists, f, indent='\t')

def graph_results():
    with open('results.json', 'r') as f:
        results = json.loads(f.read())
    xvals = results['xvals']
    sa, = plt.plot(xvals, results['scalene']['averages'])
    sa.set_label("Scalene")
    pa, = plt.plot(xvals, results['pympler']['averages'])
    pa.set_label('Pympler')
    pf, = plt.plot(xvals, results['austin']['totals'])
    pf.set_label('austin')
    plt.legend()
    plt.title("1000x1000 array allocations vs average memory consumption")
    plt.xlabel("Number of array allocations")
    plt.ylabel("Reported average memory consumption (bytes)")
    # plt.ylim(bottom=0)
    plt.savefig('plots/averages.png')
    
    plt.figure()
    st, = plt.plot(xvals, results['scalene']['totals'])
    st.set_label('Scalene')
    pt, = plt.plot(xvals, results['pympler']['totals'])
    pt.set_label("Pympler")
    pf, = plt.plot(xvals, results['austin']['totals'])
    pf.set_label('Austin')
    plt.legend()
    plt.title("1000x1000 array allocations vs total memory consumption")
    plt.xlabel("Number of array allocations")
    plt.ylabel("Reported average memory consumption (bytes)")
    plt.ylim(bottom=0)
    plt.savefig('plots/totals.png')
    plt.figure()
    diffs = [i - j for i,j in zip(results['scalene']['totals'], results['pympler']['totals'])]
    plt.title("Differences in reported memory consumption for 1000x1000 array")
    plt.plot(xvals, diffs)
    plt.xlabel("Number of array allocations")
    plt.ylabel("Difference (bytes)")
    plt.savefig('plots/differences.png')
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['run', 'graph', 'both'])
    args = parser.parse_args()
    if args.action == 'run' or args.action == 'both':
        run_tests()
    if args.action == 'graph' or args.action == 'both':
        graph_results()