#!/bin/bash
PROFILERS=(
    # 'baseline'
    # 'profile'
    # 'cProfile'
    'scalene'
    'scalene-mem'
    # 'pprofile_det'
    # 'yappi_cpu'
    # 'yappi_wall'
    # 'pyinstrument'
    # 'line_profiler'
    # 'austin'
    # 'pprofile_stat'
)
METRIC=$1
for profiler in "${PROFILERS[@]}"; do
    echo "$profiler"
    echo python3 run_cpu_tests.py -b $profiler -e $METRIC -t 10000000
    python3 run_cpu_tests.py -b $profiler  -e $METRIC -t 10000000
    printf "\n"
done