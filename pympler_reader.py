class PymplerReader:
    def __init__(self):
        self.items = []
    def read_line(self, line):
        # print("LINE", line)
        timestamp, delta = line.split(' ')
        self.items.append([int(timestamp), int(delta)])
    def items_gen(self):
        return self.items