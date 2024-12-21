from fuzzywuzzy import fuzz
from statistics import mean


class WORDCAN(object):
    def __init__(self, eps=0, min_words=2, ratio=''):
        self.eps = eps
        self.min_words = min_words
        self.ratio = ratio
        self.noise = []
        self.clusters = []
        self.dp = []
        self.near_neighbours = []
        self.wp = set()
        self.proto_cores = set()
        self.words = []

    def cluster(self, words):
        c = 0
        self.dp = words
        self.near_neighbours = self.nn(words)
        while self.proto_cores:
            near_words = set(self.proto_cores)
            for p in near_words:
                c += 1
                core = self.add_core(self.near_neighbours[p])
                complete_cluster = self.expand_cluster(core)
                self.clusters.append([mean([x for x, _, _ in complete_cluster]),
                                      mean([y for _, y, _ in complete_cluster]),
                                      complete_cluster])
                self.proto_cores -= core
                break
        for pt in self.dp:
            flag = True
            for c in self.clusters:
                if pt in c[2]:
                    flag = False
            if flag:
                self.noise.append(pt)

    # set up dictionary of near neighbours,create working_point and proto_core sets
    def nn(self, words):
        self.wp = set()
        self.proto_cores = set()
        i = -1
        near_neighbours = {}
        for p in words:
            i += 1
            j = -1
            neighbours = []
            for q in words:
                j += 1
                try:
                    if self.ratio == 'ratio':
                        distance = 100 - fuzz.ratio(p[2], q[2])
                        # print('ratio', distance, p[2], q[2])
                    else:
                        distance = 100 - fuzz.partial_ratio(p[2], q[2])
                        # print('partial_ratio', distance, p[2], q[2])
                    if distance < self.eps:
                        neighbours.append(j)
                except IndexError:
                    continue
            near_neighbours[i] = neighbours
            if len(near_neighbours[i]) > 1:
                self.wp |= {i}
            if len(near_neighbours[i]) >= self.min_words:
                self.proto_cores |= {i}
        return near_neighbours

    # add cluster core words
    def add_core(self, neighbours):
        core_words = set(neighbours)
        visited = set()
        while neighbours:
            words = set(neighbours)
            neighbours = set()
            for p in words:
                visited |= {p}
                if len(self.near_neighbours[p]) >= self.min_words:
                    core_words |= set(self.near_neighbours[p])
                    neighbours |= set(self.near_neighbours[p])
            neighbours -= visited
        return core_words

    # expand cluster to reachable words and rebuild actual values
    def expand_cluster(self, core):
        core_words = set(core)
        full_cluster = []
        for p in core_words:
            core |= set(self.near_neighbours[p])
        for point_number in core:
            full_cluster.append(self.dp[point_number])
        return full_cluster
