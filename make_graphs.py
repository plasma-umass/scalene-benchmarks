import matplotlib.pyplot as plt
import argparse
import json
import subprocess

PROFILERS = ['scalene', 'pympler' , 'austin']
ITERS = [1, 10, 20, 30, 40, 50]# , 60, 70, 80, 90, 100]

def get_cmd(profiler_name, num_iters):
    return ['python3', 'run_mem_tests.py', '-b', profiler_name, '-i', str(num_iters), '-s', '-l', 'touch1,alloc', '-n', '10000', '-c', '1000']

def run_test(profiler_name, iter):
    print(f"Running {profiler_name} {iter}")
    print(' '.join(get_cmd(profiler_name, iter)))
    proc = subprocess.run(get_cmd(profiler_name, iter), capture_output=True)
    assert proc.returncode == 0
    ret_json = json.loads(proc.stdout.decode('utf-8'))
    if profiler_name == 'austin':
        return ret_json['touch1']['average'], ret_json['touch1']['total']
    else:
        return ret_json['alloc']['average'], ret_json['alloc']['total']
    
def run_tests(json_filename):
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
    with open(f'data/{json_filename}.json', 'w+') as f:
        json.dump(profiler_lists, f, indent='\t')

def graph_results(filename):
    with open(f'data/{filename}.json', 'r') as f:
        results = json.loads(f.read())
    xvals = results['xvals']
    sa, = plt.plot(xvals, results['scalene']['averages'])
    sa.set_label("Scalene")
    pa, = plt.plot(xvals, results['pympler']['averages'])
    pa.set_label('Pympler')
    # pf, = plt.plot(xvals, results['austin']['totals'])
    # pf.set_label('austin')
    plt.legend()
    plt.title("Iterations vs average memory consumption")
    plt.xlabel("Number of array allocations")
    plt.ylabel("Reported average memory consumption (bytes)")
    plt.ylim(bottom=0)
    plt.savefig(f'plots/{filename}_averages.png')
    
    plt.figure()
    st, = plt.plot(xvals, results['scalene']['totals'])
    st.set_label('Scalene')
    pt, = plt.plot(xvals, results['pympler']['totals'])
    pt.set_label("Pympler")
    # pf, = plt.plot(xvals, results['austin']['totals'])
    # pf.set_label('Austin')
    plt.legend()
    plt.title("10000x1000 array allocations vs total memory consumption")
    plt.xlabel("Number of array allocations")
    plt.ylabel("Reported average memory consumption (bytes)")
    plt.ylim(bottom=0)
    plt.savefig(f'plots/{filename}_totals.png')
    plt.figure()
    tot_diffs = [((i - j) / j) * 100 for i,j in zip(results['scalene']['averages'], results['pympler']['averages'])]
    plt.title("Percent difference in averages between Pympler and Scalene")
    plt.plot(xvals, tot_diffs)
    plt.xlabel("Number of array allocations")
    plt.ylabel("Difference (%)")
    plt.ylim((0, 100))
    plt.savefig(f'plots/{filename}_differences_averages.png')
    plt.figure()
    tot_diffs = [((i - j) / j) * 100  for i,j in zip(results['scalene']['totals'], results['pympler']['totals'])]
    plt.title("Percent difference in totals between Pympler and Scalene")
    q, = plt.plot(xvals, tot_diffs)
    q.set_label('Pympler vs Scalene')
    tot_diffs_austin = [((i - j) / j) * 100  for i,j in zip(results['austin']['totals'], results['pympler']['totals'])]
    r, = plt.plot(xvals, tot_diffs_austin)
    r.set_label("Pympler vs Austin")
    plt.xlabel("Number of array allocations")
    plt.legend()
    plt.ylabel("Difference (%)")
    # plt.ylim((0, 100))
    plt.savefig(f'plots/{filename}_differences_totals.png')
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['run', 'graph', 'both'])
    parser.add_argument('-f', '--filename', default="results")
    args = parser.parse_args()
    if args.action == 'run' or args.action == 'both':
        run_tests(args.filename)
    if args.action == 'graph' or args.action == 'both':
        graph_results(args.filename)