#!/bin/bash
PROFILERS=(
    # 'baseline'
    # 'profile'
    # 'cProfile'
    # 'scalene'
    # 'pprofile_det'
    # 'yappi_cpu'
    # 'yappi_wall'
    # 'pyinstrument'
    # 'line_profiler'
    # 'austin'
    'pprofile_statistic'
)
METRIC=$1
for profiler in "${PROFILERS[@]}"; do
    echo "$profiler"
    python3 run_tests.py -b $profiler  -e $METRIC -t 10000000
    printf "\n"
done