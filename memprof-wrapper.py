#!/usr/bin/env python3
_CLEAN_GLOBALS = globals().copy()
# Copied from https://github.com/pythonprofilers/memory_profiler/blob/master/memory_profiler.py
# to output in a JSON format
import argparse
from collections import defaultdict
import memory_profiler 
from memory_profiler import choose_backend, _CMD_USAGE, LineProfiler, __version__, run_module_with_profiler
import builtins
import sys
import os

try:
    import tracemalloc

    has_tracemalloc = True
except ImportError:
    has_tracemalloc = False



def _find_script(script_name):
    """ Find the script.
    If the input is not a file, then $PATH will be searched.
    """
    if os.path.isfile(script_name):
        return script_name
    path = os.getenv('PATH', os.defpath).split(os.pathsep)
    for folder in path:
        if not folder:
            continue
        fn = os.path.join(folder, script_name)
        if os.path.isfile(fn):
            return fn

    sys.stderr.write('Could not find script {0}\n'.format(script_name))
    raise SystemExit(1)

def show_results(prof, stream=None, precision=1):
    import sys
    import linecache
    if stream is None:
        stream = sys.stdout
    template = '{0:>6}  {2:>12}'
    ret = {}
    for (filename, lines) in prof.code_map.items():
        lines_to_write = []
        # header = template.format('Line #', 'Mem usage', 'Increment', 'Occurrences',
        #                          'Line Contents')

        # stream.write(u'Filename: ' + filename + '\n\n')
        # stream.write(header + u'\n')
        # stream.write(u'=' * len(header) + '\n')

        # all_lines = linecache.getlines(filename)

        # float_format = u'{0}.{1}f'.format(precision + 4, precision)
        # template_mem = u'{0:' + float_format + '} MiB'
        for (lineno, mem) in lines:
            if mem:
                inc = mem[0]
                total_mem = mem[1]
                # total_mem = template_mem.format(total_mem)
                occurrences = mem[2]
                # inc = template_mem.format(inc)
            else:
                total_mem = u''
                inc = 0.0
                occurrences = u''
            lines_to_write.append({"lineno": lineno, "inc": inc})
            # tmp = template.format(lineno, total_mem, inc, occurrences, all_lines[lineno - 1])
            # stream.write(tmp)
        ret[filename] = lines_to_write
    import json
    stream.write(json.dumps(ret))

def exec_with_profiler(filename, profiler, backend, passed_args=[]):
    from runpy import run_module
    builtins.__dict__['profile'] = profiler
    ns = dict(_CLEAN_GLOBALS,
              profile=profiler,
             # Make sure the __file__ variable is usable
             # by the script we're profiling
              __file__=filename)
    # Make sure the script's directory in on sys.path
    # credit to line_profiler
    sys.path.insert(0, os.path.dirname(script_filename))

    _backend = memory_profiler.choose_backend(backend)
    sys.argv = [filename] + passed_args
    try:
        if _backend == 'tracemalloc' and has_tracemalloc:
            tracemalloc.start()
        with open(filename, encoding='utf-8') as f:
            exec(compile(f.read(), filename, 'exec'), ns, ns)
    finally:
        if has_tracemalloc and tracemalloc.is_tracing():
            tracemalloc.stop()
if __name__ == '__main__':
    from argparse import ArgumentParser, REMAINDER

    parser = ArgumentParser(usage=_CMD_USAGE)
    parser.add_argument('--version', action='version', version=__version__)
    parser.add_argument(
        '--pdb-mmem', dest='max_mem', metavar='MAXMEM',
        type=float, action='store',
        help='step into the debugger when memory exceeds MAXMEM')
    parser.add_argument(
        '--precision', dest='precision', type=int,
        action='store', default=3,
        help='precision of memory output in number of significant digits')
    parser.add_argument('-o', dest='out_filename', type=str,
        action='store', default=None,
        help='path to a file where results will be written')
    parser.add_argument('--timestamp', dest='timestamp', default=False,
        action='store_true',
        help='''print timestamp instead of memory measurement for
        decorated functions''')
    parser.add_argument('--include-children', dest='include_children',
        default=False, action='store_true',
        help='also include memory used by child processes')
    parser.add_argument('--backend', dest='backend', type=str, action='store',
        choices=['tracemalloc', 'psutil', 'psutil_pss', 'psutil_uss', 'posix'], default='psutil',
        help='backend using for getting memory info '
             '(one of the {tracemalloc, psutil, posix, psutil_pss, psutil_uss, posix})')
    parser.add_argument("program", nargs=REMAINDER,
        help='python script or module followed by command line arguements to run')
    args = parser.parse_args()

    if len(args.program) == 0:
        print("A program to run must be provided. Use -h for help")
        sys.exit(1)

    target = args.program[0]
    script_args = args.program[1:]
    _backend = choose_backend(args.backend)
    if args.timestamp:
        pass
        # prof = TimeStamper(_backend, include_children=args.include_children)
    else:
        prof = LineProfiler(max_mem=args.max_mem, backend=_backend)

    try:
        if args.program[0].endswith('.py'):
            script_filename = _find_script(args.program[0])
            exec_with_profiler(script_filename, prof, args.backend, script_args)
        else:
            exit(1)
            # run_module_with_profiler(target, prof, args.backend, script_args)
    finally:
        if args.out_filename is not None:
            out_file = open(args.out_filename, "a")
        else:
            out_file = sys.stdout

        if args.timestamp:
            prof.show_results(stream=out_file)
        else:
            show_results(prof, precision=args.precision, stream=out_file)
