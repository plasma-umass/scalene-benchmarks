

from collections import defaultdict
from enum import Enum
from math import inf


class Action(Enum):
    MALLOC = 1
    FREE = 2

    @classmethod
    def from_str(cls, text):
        if text.strip().lower() == 'm':
            return cls.MALLOC
        elif text.strip().lower() == 'f':
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
                int(reported_lineno), 
                time_num
            ])
    def aggregate_lines(self):
        lines = defaultdict(lambda : [])
        for (action, count, pointer, fname, lineno, timestamp) in self.items:
            if action == Action.MALLOC:
                lines[lineno].append(count)
                

            elif action == Action.FREE:
                lines[lineno].append(-count)
        for line in lines:
            print(f"{line}: {sum(lines[line])/len(lines[line])}")
    def items_gen(self):
        alive = {}
        footprint = 0
        graph_entries = []
        for (action, count, pointer, fname, lineno, timestamp) in self.items:
            # if count == 1549479:
            #     continue
            if action == Action.MALLOC:
                footprint += count
                alive[pointer] = count

            elif action == Action.FREE:
                footprint -= count
            
                if pointer in alive:
                    if alive[pointer] != count:

                        print(f"Difference: {alive[pointer] - count}")
                    del alive[pointer]

            time_percent = (timestamp - self.min_timestamp) / (self.max_timestamp - self.min_timestamp)
            graph_entries.append([time_percent, footprint])
        print(alive)
        return graph_entries


if __name__ == '__main__':
    import sys
    reader = ScaleneReader()
    with open(sys.argv[1], 'r') as f:
        while True:
            line = f.readline().strip()
            if len(line) == 0:
                break
            reader.read_line(line)
    reader.aggregate_lines()