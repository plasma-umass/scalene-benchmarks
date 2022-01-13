

from enum import Enum
from math import inf


class Action(Enum):
    MALLOC = 1
    FREE = 2

    @classmethod
    def from_str(cls, text):
        if text.strip() == 'M':
            return cls.MALLOC
        elif text.strip() == 'F':
            return cls.FREE


class ScaleneReader:
    def __init__(self):
        self.min_timestamp = inf
        self.max_timestamp = -inf
        self.items = []

    def read_line(self, line):
        (
            action,
            _alloc_time_str,
            count_str,
            _python_fraction_str,
            _pid,
            pointer,
            reported_fname,
            reported_lineno,
            _bytei_str,
            timestamp,
        ) = line.split(",")
        time_num = int(timestamp)
        if time_num < self.min_timestamp:
            self.min_timestamp = time_num
        if time_num > self.max_timestamp:
            self.max_timestamp = time_num
        self.items.append(
            [
                Action.from_str(action), 
                int(count_str), 
                pointer, 
                reported_fname, 
                reported_lineno, 
                time_num
            ])
    def items_gen(self):
        alive = {}
        footprint = 0
        graph_entries = []
        for (action, count, pointer, fname, lineno, timestamp) in self.items:
            if action == Action.MALLOC:
                footprint += count
                alive[pointer] = count
            elif action == Action.FREE:
                footprint -= count
                
                # del alive[pointer]
            time_percent = (timestamp - self.min_timestamp) / (self.max_timestamp - self.min_timestamp)
            graph_entries.append([time_percent, footprint])
        return graph_entries
