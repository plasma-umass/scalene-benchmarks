import argparse
import operator
import os
import subprocess
import time
from jinja2 import FileSystemLoader, Environment
import json
import statistics
from matplotlib import pyplot as plt
import numpy as np

loops = list(range(0, 10000, 1000))
NUM_TO_AVERAGE = 30
loader = FileSystemLoader('templates')
fname = 'rendered/measure_time_with_loops_e2e.py'
env = Environment(loader=loader)

mem_template = env.get_template(
    'test_time_in_loop_varying_calls_e2e.py.jinja2')


def run_profiler(cmd, n_iters):
    rendered = mem_template.render(n_iters=n_iters)
    with open(fname, 'w+') as f:
        f.write(rendered)
    os.chmod(fname, 0o766)
    start = time.perf_counter_ns()
    p = subprocess.run(
        cmd + [fname], capture_output=True)
    end = time.perf_counter_ns()
    stderr = p.stderr.decode('utf-8')
    if p.returncode != 0 and not 'os error 10' in stderr:
        print("ERROR RUNNING PROGRAM")
        print("STDOUT:", p.stdout.decode('utf-8'))
        print("STDERR: ", stderr)
        exit(1)
    # line = next(line for line in p.stdout.decode(
    #     'utf-8').split('\n') if line.strip().startswith("==="))
    return end - start, stderr


def run_extractor():
    params = ['python3', '-m', 'memray', 'flamegraph', '-f', 'out.bin']
    start = time.perf_counter_ns()
    p = subprocess.run(params, capture_output=True)
    end = time.perf_counter_ns()
    return end - start


def run_cmd_and_average(cmd, is_memray=False):
    # cmd = ["python3", "-m", "scalene"]
    ret = []
    ret_analysis = []
    ret_fsizes = []
    for loop in loops:
        runtimes = []
        runtimes_analysis = []
        fsizes = []
        print("RUNNING", cmd, NUM_TO_AVERAGE, "TIMES")
        for _ in range(NUM_TO_AVERAGE):

            time_to_run, _ = run_profiler(cmd, loop)
            # print(json_str)
            # json_dict = json.loads(json_str.split('===')[1].strip())
            runtimes.append(time_to_run)
            if is_memray:
                extractor_time = run_extractor()
                runtimes_analysis.append(extractor_time)
                ret_fsizes.append('out.bin')
            else:
                ret_fsizes.append(os.path.getsize('out.json'))
        ret.append((loop, runtimes))
        ret_analysis.append((loop, runtimes_analysis))
    return ret, ret_analysis, ret_fsizes


def run_tests(filename):
    scalene_cmd = ["python3", "-m", "scalene", '--json', '--outfile', 'out.json']
    memray_cmd = ["python3", "-m", "memray", "run", "-f", "-o", "out.bin"]
    memray_pymem_cmd = ["python3", "-m", "memray", "run",
                        "--trace-python-allocators", "-f", "-o", "out.bin"]
    noop_cmd = ["python3", "-c", "pass"]

    base_cmd = ["python3"]
    to_write = {}
    scalene_runtimes, _, scalene_fsizes = run_cmd_and_average(scalene_cmd)
    to_write['scalene'] = {"run": scalene_runtimes, 'fsizes': scalene_fsizes}
    times, an_times, fsizes = run_cmd_and_average(memray_cmd, is_memray=True)
    to_write['memray'] = {"run": times, "analysis": an_times, 'fsizes': fsizes}
    pymem_times, pymem_an_times, pymem_fsizes = run_cmd_and_average(
        memray_pymem_cmd, is_memray=True)
    to_write['memray_w_pymem'] = {
        "run": pymem_times, "analysis": pymem_an_times, 'fsizes': pymem_fsizes}

    to_write['base'] ={"run": run_cmd_and_average(base_cmd)[0]}
    to_write['noop'] = {'run': run_cmd_and_average(noop_cmd)[0]}
    with open(f'data/{filename}.json', 'w+') as f:
        json.dump(to_write, f, indent='\t')


def graph_results(filename):
    CONFIDENCE = 0.95

    with open(f'data/{filename}.json', 'r') as f:
        results = json.loads(f.read())
    plt.figure()
    last_vals = []
    for name in results:
        print(name)
        # if 'pymem' in name:
        #     continue
        xs, ys = zip(*(results[name]['run']))
        np_ys = np.array(ys)
        ys_means = list(map(np.mean, np_ys))
        last_vals.append(ys_means[-1])
        ys_stdevs = list(map(np.std, np_ys))
        ys_ci = CONFIDENCE * \
            (ys_stdevs / np.sqrt(np.fromiter(map(len, np_ys), dtype=float)))
        st = plt.errorbar(xs, ys_means, yerr=ys_ci)
        st.set_label(name)
        if 'memray' in name:
            xs_analysis, ys_analysis = zip(*(results[name]['analysis']))
            # print(ys_analysis)
            # return
            # print(ys)
            # print(ys_analysis)
            # print(list(zip(ys, ys_analysis)))
            # ys_tot = list(map(operator.add, ys, ys_analysis))
            ys_tot = [[x + y for x, y in zip(ys_inner, ys_analysis_inner)] for ys_inner, ys_analysis_inner in zip(ys, ys_analysis)]
            
            # print(list(zip(ys, ys_analysis)))
            # for i in range(len(ys_analysis)):
            #     # for j in range(len(i)):
            #     print('===')
            #     print( ys_tot[i])
            #     print(ys_analysis[i])
            #     print(ys[i])
                
            #     assert ys_tot[i] == ys_analysis[i] + ys[i]
            np_analysis = np.array(ys_analysis, dtype=np.int64)
            np_tot = np.array(ys_tot, dtype=np.int64)

            analysis_means = list(map(np.mean, np_analysis))
            analysis_stdevs = list(map(np.std, np_analysis))
            analysis_ci = CONFIDENCE * \
                (analysis_stdevs / np.sqrt(np.fromiter(map(len, np_analysis), dtype=float)))
            last_vals.append(analysis_means[-1])
            st_a = plt.errorbar(xs_analysis, analysis_means, yerr=analysis_ci)
            st_a.set_label(name + " Analysis")
            # print(xs_tot)
            tot_means = list(map(statistics.mean, np_tot))
            # print(np_tot)
            tot_stdevs = list(map(np.std, np_tot))
            tot_ci = CONFIDENCE * \
                (tot_stdevs / np.sqrt(np.fromiter(map(len, np_tot), dtype=float)))
            last_vals.append(tot_means[-1])
            st_b = plt.errorbar(xs_analysis, tot_means, yerr=tot_ci)
            st_b.set_label(name + " e2e")
    plt.legend()
    plt.xlabel("Number of iterations of loop")
    plt.ylabel("Runtime (ns)")
    plt.title("Number of iterations vs runtime")
    order = np.argsort(last_vals)[::-1]
    h, l = plt.gca().get_legend_handles_labels()
    # print(h)
    # print(l)
    # print(len(h))
    new_handles = [None] * len(h)
    new_labels = [None] * len(l)
    # print(new_handles)
    print(order)
    for idx, ord in enumerate(order):
        print(idx, ord)
        # print(len(new_handles))
        new_handles[ord] = h[idx]
        new_labels[ord] = l[idx]
    print(last_vals)
    plt.legend(handles=new_handles, labels=new_labels)
    plt.savefig(f'plots/{filename}_loops_vs_runtime.png')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['run', 'graph', 'both'])
    parser.add_argument('-f', '--filename', default="results")
    args = parser.parse_args()
    if args.action == 'run' or args.action == 'both':
        run_tests(args.filename)
    if args.action == 'graph' or args.action == 'both':
        graph_results(args.filename)
