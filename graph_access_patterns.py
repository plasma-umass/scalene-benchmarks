import matplotlib.pyplot as plt
import argparse
import json
import subprocess
import seaborn as sns
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


    sns.set()
    monospace_font = 'Andale Mono' # 'Courier New'
    default_font = 'Arial'

    sns.set(font=default_font,
        rc={
            'font.size' : 16,
            'axes.titlesize' : 24,
            'axes.labelsize' : 14,
            'axes.axisbelow': False,
            'axes.edgecolor': 'lightgrey',
            'axes.facecolor': 'None',
            'axes.grid': False,
            'axes.labelcolor': 'dimgrey',
            'axes.spines.right': False,
            'axes.spines.top': False,
            'figure.facecolor': 'white',
            'lines.solid_capstyle': 'round',
            'patch.edgecolor': 'w',
            'patch.force_edgecolor': True,
            'text.color': 'black',
            'xtick.bottom': False,
            'xtick.color': 'dimgrey',
            'xtick.direction': 'out',
            'xtick.top': False,
            'ytick.color': 'dimgrey',
            'ytick.direction': 'out',
            'ytick.left': False,
            'ytick.right': False})

    # from graphdefaults import *
    plt.style.use('ggplot')
    with open(f'data/{filename_base}.json', 'r') as f:
        results = json.loads(f.read())
    xvals = [((i * 512) / results['arr_size']) * 100 for i in results['xvals']]
    x, = plt.plot(xvals, [r / 1048576 for r in results['scalene']])
    x.set_label('Snoopy')
    y, = plt.plot(xvals, [r / 1048576 for r in results['austin']])
    y.set_label('Austin')
    # z, = plt.plot(xvals, results['pympler'])
    # z.set_label('pympler')
    a, = plt.plot(xvals, [r / 1048576 for r in results['memory_profiler']])
    a.set_label('memory_profiler')
    legend = plt.legend() # loc="upper left")
    plt.setp(legend.get_texts(), fontsize='14', family=monospace_font)
    plt.ylim(bottom=0)
    plt.xlabel("Percent of array accessed")# , pad=20, fontweight='bold', font=default_font, fontsize=18)
    plt.ylabel("Reported allocation size (MB)")#, pad=20, fontweight='bold', font=default_font, fontsize=18)
    plt.title('Memory accounting, Snoopy vs. RSS-based proxies')
    plt.savefig(f'plots/{filename_base}.pdf')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['run', 'graph', 'both'])
    parser.add_argument('-f', '--filename', default='results')
    args = parser.parse_args()
    if args.action == 'run' or args.action == 'both':
        run_tests(args.filename)
    if args.action == 'graph' or args.action == 'both':
        graph_results(args.filename)
