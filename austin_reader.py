

class AustinReader:
    def __init__(self):
        self.min = 0
        self.max = 0
        self.footprint = 0
        self.items = []
    
    def read_line(self, line: str):
        line = line.strip()
        if line.startswith('#') or len(line) == 0:
            return
        (frame, _, metrics) = line.rpartition(' ')
        timedelta_s,_,memdelta_s,mono_s = metrics.split(',')
        timedelta = int(timedelta_s)
        memdelta = int(memdelta_s)
        mono = int(mono_s)
        self.max += timedelta
        self.footprint += memdelta
        self.items.append([self.max, self.footprint, mono])

    def items_gen(self):
        items = []
        for item in self.items:
            items.append([item[0] / self.max, item[1], item[2]])
        return items