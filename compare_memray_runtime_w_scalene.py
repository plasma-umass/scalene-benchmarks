import argparse
import os 
import subprocess
from jinja2 import FileSystemLoader, Environment
import json
import statistics
from matplotlib import pyplot as plt
import numpy as np

loops = list(range(0, 10000, 1000))
NUM_TO_AVERAGE = 30
loader = FileSystemLoader('templates')
fname = 'rendered/measure_time_with_loops.py'
env = Environment(loader=loader)

mem_template = env.get_template(
    'test_time_in_loop_varying_calls.py.jinja2')

def run_cmd_and_extract_json(cmd, n_iters):
    rendered = mem_template.render(n_iters=n_iters)
    with open(fname, 'w+') as f:
        f.write(rendered)
    os.chmod(fname, 0o766)

    p = subprocess.run(
        cmd + [fname], capture_output=True)
    stderr = p.stderr.decode('utf-8')
    if p.returncode != 0 and not 'os error 10' in stderr:
        print("ERROR RUNNING PROGRAM")
        print("STDOUT:", p.stdout.decode('utf-8'))
        print("STDERR: ", stderr)
        exit(1)
    line = next(line for line in p.stdout.decode('utf-8').split('\n') if line.strip().startswith("==="))
    return line, stderr
def run_cmd_and_average( cmd):
    # cmd = ["python3", "-m", "scalene"]
    ret = []
    for loop in loops:
        runtimes = []
        print("RUNNING", cmd, NUM_TO_AVERAGE, "TIMES")
        for _ in range(NUM_TO_AVERAGE):
            
            json_str, _ = run_cmd_and_extract_json(cmd, loop)
            # print(json_str)
            json_dict = json.loads(json_str.split('===')[1].strip())
            runtimes.append(json_dict['elapsed_time'])
        ret.append((loop, runtimes))
    return ret


def run_tests(filename):
    scalene_cmd = ["python3", "-m", "scalene"]
    memray_cmd = ["python3", "-m", "memray", "run", "-o", "/dev/null"]
    memray_pymem_cmd = ["python3", "-m", "memray", "run", "--trace-python-allocators", "-o", "/dev/null"]
    base_cmd = ["python3"]
    to_write = {}
    to_write['scalene'] = run_cmd_and_average(scalene_cmd)
    to_write['memray'] = run_cmd_and_average(memray_cmd)
    to_write['memray_w_pymem'] = run_cmd_and_average(memray_pymem_cmd)
    to_write['base'] = run_cmd_and_average(base_cmd)
    with open(f'data/{filename}.json', 'w+') as f:
        json.dump(to_write, f, indent='\t')


def graph_results(filename):
    CONFIDENCE = 0.95
    
    with open(f'data/{filename}.json', 'r') as f:
        results = json.loads(f.read())
    plt.figure()
    for name in results:
        print(name)
        
        xs, ys = zip(*results[name])
        np_ys = np.array(ys)
        tot_means = list(map(statistics.mean, np_ys))
        tot_stdevs = list(map(statistics.stdev, np_ys))
        tot_ci = CONFIDENCE * (tot_stdevs / np.sqrt(np.fromiter(map(len, np_ys), dtype=float)))
        st = plt.errorbar(xs, tot_means, yerr=tot_ci)
        st.set_label(name)
    plt.legend()
    plt.xlabel("Number of iterations of loop")
    plt.ylabel("Runtime (ns)")
    plt.title("Number of iterations vs runtime")
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