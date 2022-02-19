import statistics
import matplotlib.pyplot as plt
import argparse
import json
import subprocess

import numpy as np

PROFILERS = ['scalene', 'pympler' , 'austin']
ITERS = range(1, 11) # , 20, 30, 40, 50]# , 60, 70, 80, 90, 100]
NUM_TO_AVERAGE = 10


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
            avgs = []
            tots = []
            for _ in range(NUM_TO_AVERAGE):
                average, total = run_test(prof_name, iter)
                avgs.append(average)
                tots.append(total)
            profiler_lists[prof_name]['averages'].append(avgs)# .append(sum(avgs) / len(avgs))
            profiler_lists[prof_name]['totals'].append(tots)# .append(sum(tots) / len(tots))

    profiler_lists['xvals'] =  list(ITERS)
    print(profiler_lists)
    with open(f'data/{json_filename}.json', 'w+') as f:
        json.dump(profiler_lists, f, indent='\t')

def graph_results(filename):
    CONFIDENCE = 0.95
    
    with open(f'data/{filename}.json', 'r') as f:
        results = json.loads(f.read())
    xvals = results['xvals']
    # sa, = plt.plot(xvals, results['scalene']['averages'])
    # sa.set_label("Scalene")
    # pa, = plt.plot(xvals, results['pympler']['averages'])
    # pa.set_label('Pympler')
    # # pf, = plt.plot(xvals, results['austin']['totals'])
    # # pf.set_label('austin')
    # plt.legend()
    # plt.title("Iterations vs average memory consumption")
    # plt.xlabel("Number of array allocations")
    # plt.ylabel("Reported average memory consumption (bytes)")
    # plt.ylim(bottom=0)
    # plt.savefig(f'plots/{filename}_averages.png')
    
    plt.figure()
    scalene_tots = results['scalene']['totals']
    pympler_tots = results['pympler']['totals']
    austin_tots = results['austin']['totals']
    np_scalene_tots = np.array(scalene_tots)
    np_pympler_tots = np.array(pympler_tots)
    np_austin_tots = np.array(austin_tots)
    scalene_tot_means = list(map(statistics.mean, scalene_tots))
    scalene_tot_stdevs = list(map(statistics.stdev, scalene_tots))
    scalene_tot_ci = CONFIDENCE * (scalene_tot_stdevs / np.sqrt(np.fromiter(map(len, np_scalene_tots), dtype=float)))
    # print(scalene_tot_stdevs)
    pympler_tot_means = list(map(statistics.mean, pympler_tots))
    # pympler_tot_stdevs = map(statistics.stdev, pympler_tots)

    austin_tot_means = list( map(statistics.mean, austin_tots))
    austin_tot_stdevs = list(map(statistics.stdev, austin_tots))
    austin_tot_ci = CONFIDENCE * (austin_tot_stdevs / np.sqrt(np.fromiter(map(len, np_austin_tots), dtype=float)))
    # print(xvals, scalene_tot_means)
    st = plt.errorbar(xvals, scalene_tot_means, yerr=scalene_tot_ci)
    st.set_label('Scalene')
    pt, = plt.plot(xvals, pympler_tot_means)
    pt.set_label("Pympler")
    pf = plt.errorbar(xvals, austin_tot_means, yerr=austin_tot_ci)
    pf.set_label('Austin')
    plt.legend()
    plt.title("10000x1000 array allocations vs total memory consumption")
    plt.xlabel("Number of array allocations")
    plt.ylabel("Reported average memory consumption (bytes)")
    plt.ylim(bottom=0)
    plt.savefig(f'plots/{filename}_totals.png')
    # plt.figure()
    # tot_diffs = [((i - j) / j) * 100 for i,j in zip(results['scalene']['averages'], results['pympler']['averages'])]
    # plt.title("Percent difference in averages between Pympler and Scalene")
    # plt.plot(xvals, tot_diffs)
    # plt.xlabel("Number of array allocations")
    # plt.ylabel("Difference (%)")
    # plt.ylim((0, 100))
    # plt.savefig(f'plots/{filename}_differences_averages.png')
    plt.figure()

    
    scalene_tot_diffs = ((np_scalene_tots - np_pympler_tots) / np_pympler_tots) * 100
    austin_tot_diffs = ((np_austin_tots - np_pympler_tots) / np_pympler_tots) * 100
    print(list(map(list, scalene_tot_diffs)))
    print(list(map(list, austin_tot_diffs)))
    scalene_diff_mean = list(map(np.mean, scalene_tot_diffs))
    scalene_diff_stdev = np.fromiter(map(np.std, scalene_tot_diffs), dtype=float)
    scalene_diff_ci = CONFIDENCE * (scalene_diff_stdev / np.sqrt(np.fromiter(map(len, np_scalene_tots), dtype=float)))

    austin_diff_mean = list(map(np.mean, austin_tot_diffs))
    austin_diff_stdev = np.fromiter(map(np.std, austin_tot_diffs), dtype=float)
    austin_diff_ci = CONFIDENCE * (austin_diff_stdev / np.sqrt(np.fromiter(map(len, np_austin_tots), dtype=float)))
    # tot_diffs = [((i - j) / j) * 100  for i,j in zip(scalene_tot_means, pympler_tot_means)]
    
    plt.title("Percent difference in totals between Pympler and Scalene")
    q = plt.errorbar(xvals, scalene_diff_mean, yerr=scalene_diff_ci)
    q.set_label('Pympler vs Scalene')
    # tot_diffs_austin = [((i - j) / j) * 100  for i,j in zip(austin_tot_means, pympler_tot_means)]
    r = plt.errorbar(xvals, austin_diff_mean, yerr=austin_diff_ci)
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