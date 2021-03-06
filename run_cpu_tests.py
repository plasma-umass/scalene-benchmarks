import io
import argparse
from collections import defaultdict
from typing import Dict, List
from jinja2 import Environment, FileSystemLoader
import subprocess
import os
import glob
import statistics
import json
from enum import Enum

from constants import INTERNAL, CPROFILE, PROFILE, SCALENE, PPROFILE_DET, PPROFILE_STAT, YAPPI_CPU, YAPPI_WALL, \
    PYINSTRUMENT, LINE_PROFILER, AUSTIN, PYSPY
from parse_callgrind import parse_callgrind
from parse_austin import parse_austin
from parse_speedscope import parse_speedscope

INTERNAL['use_internal_time'] = True
CPROFILE['use_cprofile'] = True
PROFILE['use_profile'] = True
SCALENE['use_scalene'] = True
PPROFILE_DET['use_pprofile_det'] = True
PPROFILE_STAT['use_pprofile_stat'] = True
YAPPI_CPU['use_yappi_cpu'] = True
YAPPI_WALL['use_yappi_wall'] = True
PYINSTRUMENT['use_pyinstrument'] = True
LINE_PROFILER['use_line_profiler'] = True
AUSTIN['use_austin'] = True
PYSPY['use_pyspy'] = True

SEPARATOR = 'buttonmashbuttonmashbuttonmash'


class EvalMethod(Enum):
    # The total time spent in fn_call_loop
    ABS_TIME = 'absolute_time'
    # The percent of the full time of the program spent in
    # fn_call_loop
    PERCENT_TIME = 'percent_time'
    # The total time spent in the ENTIRE PROGRAM
    TOTAL_RUNTIME = 'total_runtime'

    def __str__(self):
        return self.value


def runtime_mean(runtimes):
    sorted_runtimes = sorted(runtimes)
    len_runtimes = len(sorted_runtimes)
    to_avg_runtimes = sorted_runtimes[len_runtimes // 4:-len_runtimes // 4]
    mean = statistics.mean(to_avg_runtimes)
    return mean


loader = FileSystemLoader('templates')

env = Environment(loader=loader)
# TODO: this experiment was never written
# cpu_attrib_action_template = env.get_template(
#     'cpu-attribution-actionability.py.jinja2')
function_call_bias_template = env.get_template(
    'function-call-bias-separate-loops.py.jinja2')


def split_on_json(s):
    first, second = s.split(SEPARATOR)
    return first.strip(), second.strip()

def get_filename(iters_inline, iters_fn, profiler_dict):
    return f"bias-{iters_inline}-{iters_fn}-{next(k for k in profiler_dict if profiler_dict[k])}.py"
def run_bias(iters_inline: int, iters_fn: int,  profiler_dict: Dict[str, bool], prog: List[str] = ['python3'], render_only: bool = False):
    """
    Renders the test template with instrumentation specified in `profiler_dict` with option
    to override executable (needed in Scalene tests)

    Profiler dict has keys "use_internal_time", "use_cprofile", "use_scalene",
                           "use_pprofile_det", "use_yappi_cpu", "use_yappi_wall", "use_pyinstrument", "use_profile", 'line_profiler'

    NOTE THAT EXACTLY ONE OF THESE SHOULD BE TRUE. THE PROGRAM DOES NOT CHECK THIS

    Returns: stdout and stderr of the process, decoded as UTF-8
    """
    fname = f'rendered/{get_filename(iters_inline, iters_fn, profiler_dict)}'

    rendered = function_call_bias_template.render(
        iters_inline=iters_inline, iters_fn=iters_fn, profiler_dict=profiler_dict)
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


def run_baselines(num_to_average, total_runs, percent_incr, eval_method: EvalMethod = EvalMethod.ABS_TIME):
    for percent_in_calls in range(percent_incr, 100, percent_incr):
        amount_work_in_calls = int(total_runs * (percent_in_calls / 100))
        amount_work_inline = total_runs - amount_work_in_calls
        runtimes = []
        for _ in range(num_to_average):
            res_stdout, _ = run_bias(
                amount_work_inline, amount_work_in_calls, INTERNAL)
            baseline_json = json.loads(res_stdout)
            if eval_method is EvalMethod.ABS_TIME:
                runtimes.append(baseline_json['actual_elapsed_fn'])
            elif eval_method is EvalMethod.PERCENT_TIME:
                runtimes.append((baseline_json['actual_elapsed_fn'] / (
                    baseline_json['actual_elapsed_fn'] + baseline_json['actual_elapsed_inline'])) * 100)
        mean = runtime_mean(runtimes)
        print(
            f"{percent_in_calls}, {mean}")


def get_fn_percent_scalene(fn_json):
    return fn_json['n_cpu_percent_c'] + \
        fn_json['n_cpu_percent_python'] + fn_json['n_sys_percent']


def get_fn_percent_cprofile(ret_json, fn_name):
    return ret_json['func_profiles'][fn_name]['tot_time'] / ret_json['tot_tt']


def run_profile_or_cprofile(num_to_average, total_runs, percent_incr, eval_method: EvalMethod = EvalMethod.ABS_TIME, use_cprofile=True):
    for percent_in_calls in range(percent_incr, 100, percent_incr):
        amount_work_in_calls = int(total_runs * (percent_in_calls / 100))
        amount_work_inline = total_runs - amount_work_in_calls
        reported_runtimes = []
        measured_runtimes = []
        for i in range(num_to_average):
            res_stdout, _ = run_bias(
                amount_work_inline, amount_work_in_calls, CPROFILE if use_cprofile else PROFILE)
            cprofile_json = json.loads(res_stdout)
            if eval_method is EvalMethod.ABS_TIME:
                reported_runtimes.append(
                    cprofile_json['func_profiles']['fn_call_loop']['cumtime'])
            elif eval_method is EvalMethod.PERCENT_TIME:
                reported_runtimes.append(
                    (cprofile_json['func_profiles']['fn_call_loop']['cumtime'] / cprofile_json['total_tt']) * 100)
                measured_runtimes.append((cprofile_json['actual_elapsed_fn'] / (
                    cprofile_json['actual_elapsed_fn'] + cprofile_json['actual_elapsed_inline'])) * 100)
            elif eval_method is EvalMethod.TOTAL_RUNTIME:
                reported_runtimes.append(cprofile_json['total_tt'])
        mean = runtime_mean(reported_runtimes)
        measured_mean = runtime_mean(measured_runtimes)
        print(
            f"{percent_in_calls}, {mean}, {measured_mean}")


def get_function_json_scalene(functions, fn_name):
    # print(functions)
    try:
        function_ret = next(fn for fn in functions if fn['line'] == fn_name)
    except StopIteration:
        function_ret = defaultdict(lambda: 0)
    return function_ret


def run_scalene(num_to_average, total_runs, percent_incr, eval_method: EvalMethod = EvalMethod.ABS_TIME, with_memory=False):

    for percent_in_calls in range(percent_incr, 100, percent_incr):
        amount_work_in_calls = int(total_runs * (percent_in_calls / 100))
        amount_work_inline = total_runs - amount_work_in_calls
        runtimes = []
        measured_runtimes = []
        cmd = [
            'python3', '-m', 'scalene', '--json', '--cli', '--off']
        if not with_memory:
            cmd += ['--cpu-only']
        for i in range(num_to_average):
            res_stdout, _ = run_bias(
                amount_work_inline, amount_work_in_calls, SCALENE, prog=cmd)
            scalene_str, internal_time_str = split_on_json(res_stdout)
            scalene_json = json.loads(scalene_str)
            internal_json = json.loads(internal_time_str)
            fname = list(scalene_json['files'])[0]
            elapsed_time_ns = scalene_json['elapsed_time_sec']  # * (10 ** 9)
            functions = scalene_json['files'][fname]['functions']
            function_main = get_function_json_scalene(functions, 'main')
            function_do_work_fn = get_function_json_scalene(
                functions, 'do_work_fn')
            function_fn_call_loop = get_function_json_scalene(
                functions, 'fn_call_loop')
            function_inline_loop = get_function_json_scalene(
                functions, 'inline_loop')
            if eval_method is EvalMethod.ABS_TIME:

                if eval_method is EvalMethod.ABS_TIME:
                    total_amt = get_fn_percent_scalene(function_main) + get_fn_percent_scalene(
                        function_do_work_fn) + get_fn_percent_scalene(function_fn_call_loop)
                    total_amt /= 100
                    time_ns = elapsed_time_ns * total_amt
                    runtimes.append(time_ns)
            elif eval_method is EvalMethod.PERCENT_TIME:
                percent_fn_call_loop = get_fn_percent_scalene(function_fn_call_loop) + get_fn_percent_scalene(function_do_work_fn)
                percent_main = percent_fn_call_loop + get_fn_percent_scalene(function_main) + get_fn_percent_scalene(function_inline_loop)
                runtimes.append(
                    (percent_fn_call_loop / percent_main) * 100
                    
                    )
                measured_runtimes.append((internal_json['actual_elapsed_fn'] / (
                    internal_json['actual_elapsed_fn'] + internal_json['actual_elapsed_inline'])) * 100)
            elif eval_method is EvalMethod.TOTAL_RUNTIME:
                runtimes.append(elapsed_time_ns)
        mean = runtime_mean(runtimes)
        measured_mean = runtime_mean(measured_runtimes)
        print(
            f"{percent_in_calls}, {mean}, {measured_mean}")


def run_pprofile_deterministic(num_to_average, total_runs, percent_incr, eval_method: EvalMethod = EvalMethod.ABS_TIME):
    for percent_in_calls in range(percent_incr, 100, percent_incr):
        amount_work_in_calls = int(total_runs * (percent_in_calls / 100))
        amount_work_inline = total_runs - amount_work_in_calls
        reported_runtimes = []
        measured_runtimes = []
        for i in range(num_to_average):
            res_stdout, _ = run_bias(
                amount_work_inline, amount_work_in_calls, PPROFILE_DET)
            internal_json_str, callgrind_str = split_on_json(res_stdout)
            res_dict, _ = parse_callgrind(io.StringIO(callgrind_str))
            internal_json = json.loads(internal_json_str)
            filename = next(key for key in res_dict if 'bias-' in key)
            # print(filename)
            main_time = res_dict[filename]['main']
            fn_loop_time = res_dict[filename]['fn_call_loop']
            if eval_method == EvalMethod.ABS_TIME:
                reported_runtimes.append(fn_loop_time)
            elif eval_method == EvalMethod.TOTAL_RUNTIME:
                reported_runtimes.append(main_time)
            elif eval_method == EvalMethod.PERCENT_TIME:
                reported_runtimes.append((fn_loop_time / main_time) * 100)
                measured_runtimes.append((internal_json['actual_elapsed_fn'] / (
                    internal_json['actual_elapsed_fn'] + internal_json['actual_elapsed_inline'])) * 100)
        reported_mean = runtime_mean(reported_runtimes)
        measured_mean = runtime_mean(measured_runtimes)
        print(
            f"{percent_in_calls}, {reported_mean}, {measured_mean}")


def run_pprofile_statistical(num_to_average, total_runs, percent_incr, eval_method: EvalMethod = EvalMethod.ABS_TIME):
    for percent_in_calls in range(percent_incr, 100, percent_incr):
        amount_work_in_calls = int(total_runs * (percent_in_calls / 100))
        amount_work_inline = total_runs - amount_work_in_calls
        reported_runtimes = []
        measured_runtimes = []
        for i in range(num_to_average):
            res_stdout, _ = run_bias(
                amount_work_inline, amount_work_in_calls, PPROFILE_STAT)
            internal_json_str, callgrind_str = split_on_json(res_stdout)
            _, res_dict = parse_callgrind(io.StringIO(callgrind_str))
            filename = next(key for key in res_dict if 'bias-' in key)
            main_hits = res_dict[filename]['main']
            fn_loop_hits = res_dict[filename]['fn_call_loop']
            internal_json = json.loads(internal_json_str)

            if eval_method == EvalMethod.ABS_TIME:
                raise RuntimeError("Cannot measure actual time")
                # reported_runtimes.append(fn_loop_hits)
            elif eval_method == EvalMethod.TOTAL_RUNTIME:
                # reported_runtimes.append(main_hits)
                raise RuntimeError("Cannot measure actual time")
            elif eval_method == EvalMethod.PERCENT_TIME:
                reported_runtimes.append((fn_loop_hits / main_hits) * 100)
                measured_runtimes.append((internal_json['actual_elapsed_fn'] / (
                    internal_json['actual_elapsed_fn'] + internal_json['actual_elapsed_inline'])) * 100)
        reported_mean = runtime_mean(reported_runtimes)
        measured_mean = runtime_mean(measured_runtimes)
        print(
            f"{percent_in_calls}, {reported_mean}, {measured_mean}")


def run_yappi(num_to_average, total_runs, percent_incr, use_cpu, eval_method: EvalMethod = EvalMethod.ABS_TIME):
    for percent_in_calls in range(percent_incr, 100, percent_incr):
        # print(percent_in_calls)
        # for amount_work_per_iter in range(1, 24 // num_iters):
        amount_work_in_calls = int(total_runs * (percent_in_calls / 100))
        amount_work_inline = total_runs - amount_work_in_calls
        reported_runtimes = []
        measured_runtimes = []
        for i in range(num_to_average):
            res_stdout, _ = run_bias(
                amount_work_inline, amount_work_in_calls, YAPPI_CPU if use_cpu else YAPPI_WALL)
            # print(res_stdout)
            yappi_json = json.loads(res_stdout)
            main_tottime = yappi_json['main']['ttot']
            loop_tottime = yappi_json['fn_call_loop']['ttot']
            if eval_method is EvalMethod.ABS_TIME:
                reported_runtimes.append(loop_tottime)
            elif eval_method is EvalMethod.PERCENT_TIME:
                reported_runtimes.append((loop_tottime / main_tottime) * 100)
                measured_runtimes.append((yappi_json['actual_elapsed_fn'] / (
                    yappi_json['actual_elapsed_fn'] + yappi_json['actual_elapsed_inline'])) * 100)
        mean = runtime_mean(reported_runtimes)
        measured_mean = runtime_mean(measured_runtimes)
        print(
            f"{percent_in_calls}, {mean}, {measured_mean}")


def run_pyinstrument(num_to_average, total_runs, percent_incr, eval_method: EvalMethod = EvalMethod.ABS_TIME, render_only=False):
    for percent_in_calls in range(percent_incr, 100, percent_incr):
        # print(percent_in_calls)
        # for amount_work_per_iter in range(1, 24 // num_iters):
        amount_work_in_calls = int(total_runs * (percent_in_calls / 100))
        amount_work_inline = total_runs - amount_work_in_calls
        runtimes = []
        measured_runtimes = []
        for i in range(num_to_average):
            res_stdout, _ = run_bias(
                amount_work_inline, amount_work_in_calls, PYINSTRUMENT, render_only=render_only)
            if render_only:
                break
            internal_str, pyinstr_str = split_on_json(res_stdout)
            pyinstr_json = json.loads(pyinstr_str)
            internal_json = json.loads(internal_str)
            main_fn = pyinstr_json['root_frame']['children'][0]
            main_fn_time = main_fn['time']
            fn_call_loop = next(
                fn for fn in main_fn['children'] if fn['function'] == 'fn_call_loop')
            fn_call_loop_time = fn_call_loop['time']
            if eval_method is EvalMethod.PERCENT_TIME:
                runtimes.append((fn_call_loop_time / main_fn_time) * 100)
                measured_runtimes.append((internal_json['actual_elapsed_fn'] / (
                    internal_json['actual_elapsed_fn'] + internal_json['actual_elapsed_inline'])) * 100)
            elif eval_method is EvalMethod.ABS_TIME:
                runtimes.append(fn_call_loop_time)
            elif eval_method is EvalMethod.TOTAL_RUNTIME:
                runtimes.append(main_fn_time)
        mean = runtime_mean(runtimes)
        measured_mean = runtime_mean(measured_runtimes)
        print(
            f"{percent_in_calls}, {mean}, {measured_mean}")


def run_line_profiler(num_to_average, total_runs, percent_incr, eval_method: EvalMethod = EvalMethod.ABS_TIME, render_only=False):
    for percent_in_calls in range(percent_incr, 100, percent_incr):
        # print(percent_in_calls)
        # for amount_work_per_iter in range(1, 24 // num_iters):
        amount_work_in_calls = int(total_runs * (percent_in_calls / 100))
        amount_work_inline = total_runs - amount_work_in_calls
        runtimes = []
        measured_runtimes = []
        for i in range(num_to_average):
            res_stdout, _ = run_bias(
                amount_work_inline, amount_work_in_calls, LINE_PROFILER, render_only=render_only)
            if render_only:
                break
            pprofile_json = json.loads(res_stdout)
            # print(pprofile_json)
            lines = pprofile_json['lines']
            # This is the second line in the current benchmark
            # Line numbers are 22 and 25 for fn_call_loop and inline_loop respectively
            fn_call_loop = next(line for line in lines if line['lineno'] == 22)
            fn_call_loop_time = fn_call_loop['time']
            total_time = sum([x['time'] for x in lines])
            if eval_method is EvalMethod.PERCENT_TIME:
                runtimes.append((fn_call_loop_time / total_time) * 100)
                measured_runtimes.append((pprofile_json['actual_elapsed_fn'] / (
                    pprofile_json['actual_elapsed_fn'] + pprofile_json['actual_elapsed_inline'])) * 100)
            elif eval_method is EvalMethod.ABS_TIME:
                runtimes.append(fn_call_loop_time)
        mean = runtime_mean(runtimes)
        measured_mean = runtime_mean(measured_runtimes)
        print(
            f"{percent_in_calls}, {mean}, {measured_mean}")


def run_austin(num_to_average, total_runs, percent_incr, eval_method: EvalMethod = EvalMethod.ABS_TIME, render_only=False, use_full=False):
    for percent_in_calls in range(percent_incr, 100, percent_incr):
        amount_work_in_calls = int(total_runs * (percent_in_calls / 100))
        amount_work_inline = total_runs - amount_work_in_calls
        runtimes = []
        cmd = [
                'austin', '-s', '--pipe']
        if use_full:
            cmd += ['-f']

        measured_runtimes = []
        for i in range(num_to_average):
            res_stdout, _ = run_bias(amount_work_inline, amount_work_in_calls, AUSTIN, prog=cmd, render_only=render_only)
            # internal_time_str, austin_str = split_on_json(res_stdout)
            initial_res_dict = parse_austin(io.StringIO(res_stdout), is_full=use_full)
            res_dict = initial_res_dict['functions'][get_filename(amount_work_inline, amount_work_in_calls, AUSTIN)]
            # internal_json = json.loads(internal_time_str)
            total_time = sum(res_dict['main'])
            fn_call_loop_time = sum(res_dict['fn_call_loop'])
            runtimes.append((fn_call_loop_time / total_time) * 100)
            # measured_runtimes.append((internal_json['actual_elapsed_fn'] / (
            #         internal_json['actual_elapsed_fn'] + internal_json['actual_elapsed_inline'])) * 100)

        mean = runtime_mean(runtimes)
        measured_mean = 0
        # measured_mean = runtime_mean(measured_runtimes)
        print(
            f"{percent_in_calls}, {mean}, {measured_mean}")


def run_pyspy(num_to_average, total_runs, percent_incr, eval_method: EvalMethod = EvalMethod.ABS_TIME, render_only=False, store_intermediates=False):
    for percent_in_calls in range(percent_incr, 100, percent_incr):
        amount_work_in_calls = int(total_runs * (percent_in_calls / 100))
        amount_work_inline = total_runs - amount_work_in_calls
        runtimes = []
        measured_runtimes = []
        for i in range(num_to_average):
            fname = f'rendered/dat-{i}.json'
            res_stdout, _ = run_bias(amount_work_inline, amount_work_in_calls, PYSPY, prog=[
                'py-spy', 'record', '--format', 'speedscope', '-o', fname, '--', 'python3'], render_only=render_only)
            # internal_time_str, austin_str = split_on_json(res_stdout)
            internal_time_str = res_stdout.split(SEPARATOR)[1]
            internal_json = json.loads(internal_time_str)
            with open(fname, 'r') as f:
                res_dict = parse_speedscope(f)
            if not store_intermediates:
                os.remove(fname)
            # res_dict = parse_austin(io.StringIO(res_stdout))
            # internal_json = json.loads(internal_time_str)
            # print(res_dict)
            profiled_filename = next(key for key in res_dict if 'bias-' in key)
            main_fn_time = res_dict[profiled_filename]['main']
            fn_call_loop_time = res_dict[profiled_filename]['fn_call_loop']
            # measured_runtimes.append((internal_json['actual_elapsed_fn'] / (
            #         internal_json['actual_elapsed_fn'] + internal_json['actual_elapsed_inline'])) * 100)
            if eval_method is EvalMethod.PERCENT_TIME:
                runtimes.append((fn_call_loop_time / main_fn_time) * 100)
                measured_runtimes.append((internal_json['actual_elapsed_fn'] / (
                    internal_json['actual_elapsed_fn'] + internal_json['actual_elapsed_inline'])) * 100)
            elif eval_method is EvalMethod.ABS_TIME:
                runtimes.append(fn_call_loop_time)
            elif eval_method is EvalMethod.TOTAL_RUNTIME:
                runtimes.append(main_fn_time)
        mean = runtime_mean(runtimes)
        measured_mean = runtime_mean(measured_runtimes)
        # measured_mean = runtime_mean(measured_runtimes)
        print(
            f"{percent_in_calls}, {mean}, {measured_mean}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--num_to_average', type=int, default=8)
    parser.add_argument(
        '-b', '--benchmark', choices=['baseline', 'profile', 'cProfile', 'scalene', 'scalene-mem', 'pprofile_det',
                                      'yappi_cpu', 'yappi_wall', 'pyinstrument', 'line_profiler', 'austin',
                                      'pprofile_stat', 'py_spy', "austin-mem"], default='baseline')
    parser.add_argument('-s', '--store-intermediates', action='store_true')
    parser.add_argument('-r', '--render-only', action='store_true')
    parser.add_argument('-t', '--total-runs', type=int, default=1000000)
    parser.add_argument('-p', '--percent-incr', type=int, default=5)
    parser.add_argument('-e', '--eval-method', type=EvalMethod,
                        default=EvalMethod.ABS_TIME, choices=list(EvalMethod))
    args = parser.parse_args()
    if not (args.total_runs * (args.percent_incr / 100)).is_integer():
        print("ERROR: Percentage must evenly divide number of runs")
        exit(1)
    if args.num_to_average % 8 != 0:
        print("ERROR: number of runs must be a multiple of 4")
        exit(1)
    to_run = args.benchmark
    if to_run == 'baseline':
        run_baselines(args.num_to_average, args.total_runs,
                      args.percent_incr,  eval_method=args.eval_method)
    elif to_run == 'cProfile':
        run_profile_or_cprofile(args.num_to_average, args.total_runs,
                                args.percent_incr, eval_method=args.eval_method)
    elif to_run == 'profile':
        run_profile_or_cprofile(args.num_to_average, args.total_runs,
                                args.percent_incr, eval_method=args.eval_method, use_cprofile=False)
    elif to_run == 'scalene':
        run_scalene(args.num_to_average, args.total_runs,
                    args.percent_incr, eval_method=args.eval_method)
    elif to_run == 'scalene-mem':
        run_scalene(args.num_to_average, args.total_runs,
                    args.percent_incr, eval_method=args.eval_method, with_memory=True)
    elif to_run == 'pprofile_det':
        run_pprofile_deterministic(
            args.num_to_average, args.total_runs, args.percent_incr, eval_method=args.eval_method)
    elif to_run == 'pprofile_stat':
        run_pprofile_statistical(
            args.num_to_average, args.total_runs, args.percent_incr, eval_method=args.eval_method)
    elif to_run == 'yappi_cpu':
        run_yappi(args.num_to_average, args.total_runs,
                  args.percent_incr, True, eval_method=args.eval_method)
    elif to_run == 'yappi_wall':
        run_yappi(args.num_to_average, args.total_runs,
                  args.percent_incr, False, eval_method=args.eval_method)
    elif to_run == 'pyinstrument':
        run_pyinstrument(args.num_to_average, args.total_runs,
                         args.percent_incr, eval_method=args.eval_method, render_only=args.render_only)
    elif to_run == 'line_profiler':
        run_line_profiler(args.num_to_average, args.total_runs,
                          args.percent_incr, eval_method=args.eval_method, render_only=args.render_only)
    elif to_run == 'austin':
        run_austin(args.num_to_average, args.total_runs,
                   args.percent_incr, eval_method=args.eval_method, render_only=args.render_only)
    elif to_run == 'austin-mem':
        run_austin(args.num_to_average, args.total_runs,
                   args.percent_incr, eval_method=args.eval_method, render_only=args.render_only, use_full=True)
    elif to_run == 'py_spy':
        run_pyspy(args.num_to_average, args.total_runs,
                   args.percent_incr, eval_method=args.eval_method, render_only=args.render_only, store_intermediates=args.store_intermediates)
    else:
        pass
    if not args.store_intermediates and not args.render_only:
        g = glob.glob('rendered/*')
        for fname in g:
            if fname != '.gitkeep':
                os.remove(fname)
