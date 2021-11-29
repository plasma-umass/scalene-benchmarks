# Scalene Benchmarks

Currently contains benchmarks comparing several profilers' CPU attribution times

Initial run may be conducted by:

```bash
python3 run_tests.py -b {profiler_name} -e percent_time -t 1000000
```

Where `profiler_name` is one of:

`baseline`, `profile`, `cProfile`, `scalene`, `pprofile_det`, `yappi_cpu`, `yappi_wall`, `pyinstrument`, `line_profiler`

with `baseline` using `perf_counter_ns`