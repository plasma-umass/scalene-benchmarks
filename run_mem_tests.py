from constants import MEM_PROFILER, SCALENE_MEM, TRACEMALLOC, AUSTIN_MEM, FIL, PYMPLER
from typing import Dict, List
import subprocess

import os
import io
import shutil

import glob 
from jinja2 import FileSystemLoader, Environment

import json

from parse_austin import parse_austin
from parse_fil import parse_fil

import argparse


loader = FileSystemLoader('templates')

env = Environment(loader=loader)
# TODO: this experiment was never written
# cpu_attrib_action_template = env.get_template(
#     'cpu-attribution-actionability.py.jinja2')
mem_template = env.get_template(
        'memory.py.jinja2')

def get_fname(profiler_dict):
    return f'memory-{next(k for k in profiler_dict if profiler_dict[k])}.py'

def get_lineno_with_label(label, fname):
    with open(f"rendered/{fname}", 'r') as f:
        for num, line in enumerate(f, 1):
            if label in line:
                return num
    return -1

def run_mem(profiler_dict: Dict[str, bool], prog: List[str] = ['python3'], render_only: bool = False, num_iters: int = 50, template_base: str = 'memory'):
    
    fname = f"rendered/{get_fname(profiler_dict)}"
    rendered = mem_template.render(profiler_dict=profiler_dict, num_iters=num_iters)
    with open(fname, 'w+') as f:
        f.write(rendered)
    os.chmod(fname, 0o766)
    if render_only:
        return '', ''
    p = subprocess.run(
        prog + [fname], capture_output=True)
    stderr = p.stderr.decode('utf-8')
    if p.returncode != 0 and not 'os error 10' in stderr:
        print("ERROR RUNNING PROGRAM")
        print("STDOUT:", p.stdout.decode('utf-8'))
        print("STDERR: ", p.stderr.decode('utf-8'))
        exit(1)
    return p.stdout.decode('utf-8'), stderr

def default_dict_to_dict(d):
    return {k: dict(v) for k, v in d.items()}

def run_memory_profiler(render_only=False, backend_flags=None, num_iters: int = 50, high_watermark: bool = False):
    program = ['python3', 'memprof-wrapper.py']
    if backend_flags:
        program += ['--backend', backend_flags]
    
    stdout, stderr = run_mem(MEM_PROFILER, program, render_only=render_only, num_iters=num_iters)
    fname = get_fname(MEM_PROFILER)
    mem_profiler_json = json.loads(stdout)

    if high_watermark:
        lines = mem_profiler_json[f'rendered/{get_fname(MEM_PROFILER)}']
        linenos = set(map(lambda x : get_lineno_with_label(x, fname), labels))
        ret = {}
        for line in lines:
            if line['lineno'] in linenos:
                ret[line['lineno']] = line['total_mem']
        print(ret)
    else:
        print(mem_profiler_json)


def run_scalene(num_iters: int, labels, render_only: bool = False, high_watermark: bool = False):
    program = ['python3', '-m', 'scalene', '--json', '--off']
    stdout, _ = run_mem(SCALENE_MEM, prog=program, render_only=render_only, num_iters=num_iters)

    scalene_json = json.loads(stdout)
    filename = f'rendered/{get_fname(SCALENE_MEM)}'
    if high_watermark:
        ret = {}
        
        lines = scalene_json['files'][filename]['lines']
        for line in lines:
            ret[line['lineno']] = line['n_peak_mb'] * 1024 * 1024
        print(json.dumps(ret))
    else:
        lines_out = {}
        for label in labels:
            line = next(line for line in scalene_json['files'][filename]['lines'] if label in line['line'])
            lines_out[label] = {'total': line['n_malloc_mb'] * 1024 * 1024, 'average': line['n_avg_mb'] * 1024 * 1024}
        print(json.dumps(lines_out))
    # print(scalene_json)


def run_tracemalloc(num_iters, render_only: bool = False):
    stdout, _ = run_mem(TRACEMALLOC, render_only=render_only)
    tmalloc_json = json.loads(stdout)
    print(tmalloc_json)



def run_austin(labels, num_iters: int = 50, render_only: bool = False, high_watermark: bool = False):
    cmd = ['austin', '-s', '--pipe', '-m']
    res_stdout, _ = run_mem(AUSTIN_MEM, prog=cmd, render_only=render_only, num_iters=num_iters)
    res_dict = parse_austin(io.StringIO(res_stdout), filename_prefix='memory')

    res_dict_lines = res_dict['lines']
    austin_dict = default_dict_to_dict(res_dict_lines)[get_fname(AUSTIN_MEM)]
    if high_watermark:
        fname = get_fname(AUSTIN_MEM)
        linenos = set(map(lambda x : str(get_lineno_with_label(x, fname)), labels))
        print(json.dumps({k: v for k,v in res_dict['watermarks'][fname].items() if k in linenos}))
    else:
        ret = {}
        for label in labels:
            lineno = str(get_lineno_with_label(label, get_fname(AUSTIN_MEM)))
            print(austin_dict)
            ret[label] = {
                'total': sum(austin_dict[lineno]),
                'average': sum(austin_dict[lineno]) / len(austin_dict[lineno])
            }
        print(json.dumps(ret))

# Note: labels automatically discovered in here
def run_pympler(num_iters: int, render_only: bool = False):
    stdout, _ = run_mem(PYMPLER, render_only=render_only, num_iters=num_iters)
    pympler_json = json.loads(stdout)
    print(json.dumps(pympler_json))


def run_fil(num_iters: int, labels, render_only: bool = False):
    cmd = ['fil-profile', '-o', 'results', 'run']
    stdout, stderr = run_mem(FIL, prog=cmd, render_only=render_only, num_iters=num_iters)
    stdout_lines = stderr.split('\n')
    line = next(line for line in stdout_lines if 'Preparing to write to' in line)
    _, _, base_path = line.rpartition(' ')
    prof_path = os.path.join(base_path, 'peak-memory.prof')
    with open(prof_path, 'r') as f:
        fil_dict = parse_fil(f, filename_discriminator='memory-')
    fil_lines = fil_dict[get_fname(FIL)]
    ret = {}
    for label in labels:
        lineno = get_lineno_with_label(label, get_fname(FIL))
        ret[label] = {'total': fil_lines[lineno], 'average': -1}
    print(json.dumps(ret))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-b', '--benchmark', choices=['tracemalloc', 'scalene', 'fil', 'austin', 'memory_profiler', 'pympler']
    )
    parser.add_argument('-r', '--render-only', action='store_true')
    parser.add_argument('-s', '--store-intermediates', action='store_true')
    parser.add_argument('-i', '--num-iters', default=50, type=int)
    parser.add_argument('-l', '--labels-list', default="alloc1", type=str)
    parser.add_argument('-t', '--template-base', default="memory")
    parser.add_argument('-w', '--high-watermark', action='store_true')
    args = parser.parse_args()
    mem_template = env.get_template(f'{args.template_base}.py.jinja2')
    profiler = args.benchmark
    labels = args.labels_list.split(',')
    if profiler == 'tracemalloc':
        run_tracemalloc(render_only=args.render_only)
    elif profiler == 'memory_profiler':
        run_memory_profiler(render_only=args.render_only, num_iters=args.num_iters, high_watermark=args.high_watermark)
    elif profiler == 'scalene':
        run_scalene(render_only=args.render_only, labels=labels, num_iters=args.num_iters, high_watermark=args.high_watermark)
    elif profiler == 'fil':
        run_fil(render_only=args.render_only, labels=labels, num_iters=args.num_iters)
    elif profiler == 'austin':
        run_austin(labels=labels, render_only=args.render_only, num_iters=args.num_iters, high_watermark=args.high_watermark)
    elif profiler == 'pympler':
        run_pympler(render_only=args.render_only, num_iters=args.num_iters)
    if not args.store_intermediates and not args.render_only:
        g = glob.glob('rendered/*')
        for fname in g:
            if fname != '.gitkeep':
                os.remove(fname)
    if not args.store_intermediates:
        if os.path.exists('results'):
            shutil.rmtree('results')