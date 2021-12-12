
from constants import MEM_PROFILER, SCALENE_MEM, TRACEMALLOC, AUSTIN_MEM, FIL
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


def run_mem(profiler_dict: Dict[str, bool], prog: List[str] = ['python3'], render_only: bool = False):
    fname = f'rendered/memory-{next(k for k in profiler_dict if profiler_dict[k])}.py'
    rendered = mem_template.render(profiler_dict=profiler_dict)
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

def run_memory_profiler(render_only=False, backend_flags=None):
    program = ['python3', 'memprof-wrapper.py']
    if backend_flags:
        program += ['--backend', backend_flags]
    stdout, _ = run_mem(MEM_PROFILER, program, render_only=render_only)
    mem_profiler_json = json.loads(stdout)
    print(mem_profiler_json)


def run_scalene(render_only: bool = False):
    program = ['python3', '-m', 'scalene', '--json', '--off']
    stdout, _ = run_mem(SCALENE_MEM, prog=program, render_only=render_only)
    scalene_json = json.loads(stdout)
    print(scalene_json)


def run_tracemalloc(render_only: bool = False):
    stdout, _ = run_mem(TRACEMALLOC, render_only=render_only)
    tmalloc_json = json.loads(stdout)
    print(tmalloc_json)


def run_austin(render_only: bool = False):
    cmd = ['austin', '-s', '--pipe', '-m']
    res_stdout, _ = run_mem(AUSTIN_MEM, prog=cmd, render_only=render_only)
    res_dict = parse_austin(io.StringIO(res_stdout))
    print(default_dict_to_dict(res_dict))


def run_fil(render_only):
    cmd = ['fil-profile', '-o', 'results', 'run']
    stdout, stderr = run_mem(FIL, prog=cmd, render_only=render_only)
    stdout_lines = stderr.split('\n')
    line = next(line for line in stdout_lines if 'Preparing to write to' in line)
    _, _, base_path = line.rpartition(' ')
    prof_path = os.path.join(base_path, 'peak-memory.prof')
    with open(prof_path, 'r') as f:
        fil_dict = parse_fil(f, filename_discriminator='memory-')
    print(default_dict_to_dict(fil_dict))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-b', '--benchmark', choices=['tracemalloc', 'scalene', 'fil', 'austin', 'memory_profiler']
    )
    parser.add_argument('-r', '--render-only', action='store_true')
    parser.add_argument('-s', '--store-intermediates', action='store_true')
    args = parser.parse_args()
    profiler = args.benchmark
    if profiler == 'tracemalloc':
        run_tracemalloc(render_only=args.render_only)
    elif profiler == 'memory_profiler':
        run_memory_profiler(render_only=args.render_only)
    elif profiler == 'scalene':
        run_scalene(render_only=args.render_only)
    elif profiler == 'fil':
        run_fil(render_only=args.render_only)
    elif profiler == 'austin':
        run_austin(render_only=args.render_only)
    if not args.store_intermediates and not args.render_only:
        g = glob.glob('rendered/*')
        for fname in g:
            if fname != '.gitkeep':
                os.remove(fname)
    if not args.store_intermediates:
        if os.path.exists('results'):
            shutil.rmtree('results')