from math import inf
import numpy as np
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
    'vary_access_pattern.py.jinja2')


def get_fname(profiler_dict):
    return f'access_pattern-{next(k for k in profiler_dict if profiler_dict[k])}.py'


def get_lineno_with_label(label, fname):
    with open(f"rendered/{fname}", 'r') as f:
        for num, line in enumerate(f, 1):
            if label in line:
                return num
    return -1


np.random.seed(8980)


def get_indices(nrows, num):
    return np.random.randint(0, nrows, num)


def run_mem(profiler_dict: Dict[str, bool], indices: List[int], nrows, ncols, prog: List[str] = ['python3'], render_only: bool = False, num_iters: int = 50):

    fname = f"rendered/{get_fname(profiler_dict)}"
    rendered = mem_template.render(
        profiler_dict=profiler_dict, num_iters=num_iters, indices=indices, nrows=nrows, ncols=ncols)
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


def run_scalene(num_iters: int, nrows: int, ncols: int, num_accesses, labels, render_only: bool = False):
    program = ['python3', '-m', 'scalene', '--json', '--off']
    indices = get_indices(nrows, num_accesses)
    stdout, stderr = run_mem(SCALENE_MEM, prog=program,
                             render_only=render_only, num_iters=num_iters, nrows=nrows, ncols=ncols, indices=indices)
    scalene_json = json.loads(stdout)
    filename = f'{get_fname(SCALENE_MEM)}'
    ret = {}
    lines = scalene_json['files'][f'rendered/{filename}']['lines']
    linenos = set(map(lambda x: get_lineno_with_label(x, filename), labels))
    for line in lines:
        if line['lineno'] in linenos:
            ret[line['lineno']] = line['n_peak_mb'] * 1024 * 1024
    print(json.dumps(ret))


def run_austin(labels, nrows, ncols, num_accesses, num_iters: int = 50, render_only: bool = False):
    cmd = ['austin', '-s', '--pipe', '-m']
    indices = get_indices(nrows, num_accesses)
    res_stdout, _ = run_mem(AUSTIN_MEM, prog=cmd,
                            render_only=render_only, num_iters=num_iters,
                            nrows=nrows, ncols=ncols, indices=indices)
    res_dict = parse_austin(io.StringIO(res_stdout),
                            filename_prefix='access_pattern')
    
    fname = get_fname(AUSTIN_MEM)
    linenos = set(map(lambda x: str(get_lineno_with_label(x, fname)), labels))
    # print(json.dumps(
    #     {k: v for k, v in res_dict['watermarks'][fname].items() if k in linenos}))
    print(json.dumps({'high_watermark': res_dict['high_watermark']}))

def run_memory_profiler(labels, nrows, ncols, num_accesses, render_only=False, backend_flags=None, num_iters: int = 50):
    program = ['python3', 'memprof-wrapper.py']
    if backend_flags:
        program += ['--backend', backend_flags]
    indices = get_indices(nrows, num_accesses)
    stdout, stderr = run_mem(MEM_PROFILER, prog=program,
                            render_only=render_only, num_iters=num_iters,
                            nrows=nrows, ncols=ncols, indices=indices)
    fname = get_fname(MEM_PROFILER)
    mem_profiler_json = json.loads(stdout)

    lines = mem_profiler_json[f'rendered/{get_fname(MEM_PROFILER)}']
    linenos = set(map(lambda x: get_lineno_with_label(x, fname), labels))
    
    high_watermark = -inf
    for line in lines:
        total_mem = line['total_mem'] if not isinstance(line['total_mem'], str) else 0
        if  total_mem * 1024 * 1024 > high_watermark:
            high_watermark = total_mem * 1024 * 1024
    #     if line['lineno'] in linenos:
    #         ret[line['lineno']] = line['total_mem'] * 1024 * 1024
    print(json.dumps({'high_watermark': high_watermark}))


# Note: labels automatically discovered in here


def run_pympler(num_iters: int, nrows, ncols, num_accesses, render_only: bool = False):
    indices = get_indices(nrows, num_accesses)
    stdout, _ = run_mem(PYMPLER, render_only=render_only,
                        num_iters=num_iters, nrows=nrows, ncols=ncols, indices=indices)
    pympler_json = json.loads(stdout)
    print(json.dumps(pympler_json))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-b', '--benchmark', choices=['scalene', 'austin', 'pympler', 'memory_profiler']
    )
    parser.add_argument('-r', '--render-only', action='store_true')
    parser.add_argument('-s', '--store-intermediates', action='store_true')
    parser.add_argument('-i', '--num-iters', default=50, type=int)
    parser.add_argument('-l', '--labels-list', default="alloc", type=str)
    parser.add_argument('-t', '--template-base', default="vary_access_pattern")
    parser.add_argument('-n', '--nrows', type=int, default=10000)
    parser.add_argument('-c', '--ncols', type=int, default=1000)
    parser.add_argument('-a', '--num-accesses', type=int, default=10)
    args = parser.parse_args()
    mem_template = env.get_template(f'{args.template_base}.py.jinja2')
    profiler = args.benchmark
    labels = args.labels_list.split(',')
    if profiler == 'scalene':
        run_scalene(render_only=args.render_only, labels=labels,
                    nrows=args.nrows, ncols=args.ncols,
                    num_iters=args.num_iters, num_accesses=args.num_accesses)
    elif profiler == 'austin':
        run_austin(labels=labels, render_only=args.render_only,
                   nrows=args.nrows, ncols=args.ncols,
                   num_iters=args.num_iters, num_accesses=args.num_accesses)
    elif profiler == 'pympler':
        run_pympler(render_only=args.render_only,
                    nrows=args.nrows, ncols=args.ncols,
                    num_iters=args.num_iters, num_accesses=args.num_accesses)
    elif profiler == 'memory_profiler':
        run_memory_profiler(labels=labels,
                            render_only=args.render_only,
                            nrows=args.nrows, 
                            ncols=args.ncols, 
                            num_iters=args.num_iters, num_accesses=args.num_accesses)
    if not args.store_intermediates and not args.render_only:
        g = glob.glob('rendered/*')
        for fname in g:
            if fname != '.gitkeep':
                os.remove(fname)
    if not args.store_intermediates:
        if os.path.exists('results'):
            shutil.rmtree('results')
