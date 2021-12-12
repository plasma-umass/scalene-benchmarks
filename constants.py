BASE_DICT = {q: False for q in ["use_internal_time", "use_cprofile", "use_scalene",
                                "use_pprofile_det", "use_pprofile_stat", "use_yappi_cpu", "use_yappi_wall", "use_pyinstrument", "use_profile", 'line_profiler', 'use_austin', 'use_pyspy']}
INTERNAL = BASE_DICT.copy()
CPROFILE = BASE_DICT.copy()
PROFILE = BASE_DICT.copy()
SCALENE = BASE_DICT.copy()
PPROFILE_DET = BASE_DICT.copy()
PPROFILE_STAT = BASE_DICT.copy()
YAPPI_CPU = BASE_DICT.copy()
YAPPI_WALL = BASE_DICT.copy()
PYINSTRUMENT = BASE_DICT.copy()
LINE_PROFILER = BASE_DICT.copy()
AUSTIN = BASE_DICT.copy()
PYSPY = BASE_DICT.copy()

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

BASE_MEM_DICT = {k: False for k in [
    'use_memory_profiler', 'use_scalene', 'use_tracemalloc', 'use_austin', 'use_fil']}
MEM_PROFILER = BASE_MEM_DICT.copy()
MEM_PROFILER['use_memory_profiler'] = True

SCALENE_MEM = BASE_MEM_DICT.copy()
SCALENE_MEM['use_scalene'] = True
TRACEMALLOC = BASE_MEM_DICT.copy()
TRACEMALLOC['use_tracemalloc'] = True
AUSTIN_MEM = BASE_MEM_DICT.copy()
AUSTIN_MEM['use_austin'] = True
FIL = BASE_MEM_DICT.copy()
FIL['use_fil'] = True