from statistics import mean

class LINESCAN(object):
    def __init__(self, eps=0):
        self.eps = eps
        self.noise = []
        self.clusters = []
        self.dp = []
        self.near_neighbours = []
        self.wp = set()
        self.cores = set()
        self.lines = []

    def cluster(self, lines):
        c = 0
        self.dp = lines
        self.near_neighbours = self.nn(lines)
        while self.cores:
            near_points = set(self.cores)
            for p in near_points:
                c += 1
                core = self.add_core(self.near_neighbours[p])
                complete_cluster = self.expand_cluster(core)
                self.clusters.append([mean([x for x, _, _ in complete_cluster]),
                                      mean([y for _, y, _ in complete_cluster]),
                                      complete_cluster])
                self.cores -= core
                break
        for pt in self.dp:
            flag = True
            for c in self.clusters:
                if pt in c[2]:
                    flag = False
            if flag:
                self.noise.append(pt)

    # set up dictionary of near neighbours,create working_point and proto_core sets
    def nn(self, lines):
        self.wp = set()
        i = -1
        near_neighbours = {}
        for p in lines:
            i += 1
            j = -1
            neighbours = []
            for q in lines:
                j += 1
                try:
                    if abs(q[1] - p[1]) <= self.eps and abs(q[0] - p[0]) <= 4 * self.eps:
                        neighbours.append(j)
                except IndexError:
                    continue
            near_neighbours[i] = neighbours
            if len(near_neighbours[i]) > 1:
                self.wp |= {i}
            if len(near_neighbours[i]) >= 2:
                self.cores |= {i}
        return near_neighbours

    # add cluster core lines
    def add_core(self, neighbours):
        core_points = set(neighbours)
        visited = set()
        while neighbours:
            points = set(neighbours)
            neighbours = set()
            for p in points:
                visited |= {p}
                if len(self.near_neighbours[p]) >= 2:
                    core_points |= set(self.near_neighbours[p])
                    neighbours |= set(self.near_neighbours[p])
            neighbours -= visited
        return core_points

    # expand cluster to reachable lines and rebuild actual point values
    def expand_cluster(self, core):
        core_points = set(core)
        full_cluster = []
        for p in core_points:
            core |= set(self.near_neighbours[p])
        for point_number in core:
            full_cluster.append(self.dp[point_number])
        return full_cluster
