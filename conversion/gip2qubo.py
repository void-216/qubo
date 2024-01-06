from collections import defaultdict
import argparse
import sys
import json
import re
import random
import time
from typing import Tuple


def rand_select(nbit: int, s=-1):
    if s == -1:
        s = nbit
    pool = list(range(nbit))
    for i in range(s):
        j = random.randrange(nbit - i)
        yield pool[j]
        pool[j] = pool[nbit - i - 1]

class GIP:

    def __init__(self, filename: str) -> None:
        with open(filename, "rt") as f:
            lines = f.read()
        vertices = lines.split('number of vertices  : ')
        end = vertices[1].index('\n')
        self.vertices_num = int(vertices[1][0:end])
        self.G1 = []
        edge_pair = []
        all = lines.split('\ne ')
        for i in range(len(all) - 1):
            edge = []
            edge_str = all[i + 1].split()
            edge.append(int(edge_str[0]))
            edge.append(int(edge_str[1]))
            if edge[0] > edge[1]:
                edge[0], edge[1] = edge[1], edge[0]
            edge = tuple(edge)
            edge_pair.append(edge)
        edge_pair.sort(key=lambda edge_pair:edge_pair[0])
        self.edge_num = len(edge_pair)
        for j in range(len(edge_pair)):
            self.G1.append(edge_pair[j])
        self.G2_gen()


    def G2_gen(self):
        self.G2 = []
        edge_pair = []
        p = list(rand_select(self.vertices_num))
        p = [x + 1 for x in p]
        self.mapping = {x+1:p[x] for x in range(self.vertices_num)}
        for i in range(self.edge_num):
            edge = []
            edge.append(self.mapping.get(self.G1[i][0]))
            edge.append(self.mapping.get(self.G1[i][1]))
            if edge[0] > edge[1]:
                edge[0], edge[1] = edge[1], edge[0]
            edge = tuple(edge)
            edge_pair.append(edge)
        edge_pair.sort(key=lambda edge_pair:edge_pair[0])
        for j in range(len(edge_pair)):
            self.G2.append(edge_pair[j])


class QUBO:


    def __init__(self, gip):
        self.qubo = defaultdict(int)
        self.vertices_num = gip.vertices_num
        self.edge_num = gip.edge_num
        self.G1 = {x:0 for x in gip.G1}
        self.G2 = {x:0 for x in gip.G2}
        self.mapping = gip.mapping

    @staticmethod
    def conflict(x: Tuple[int, int], y: Tuple[int, int], G1, G2) -> bool:

        if x[0] > y[0]:
            G1_edge = (y[0],x[0])
        else:
            G1_edge = (x[0],y[0])
        if x[1] > y[1]:
            G2_edge = (y[1],x[1])
        else:
            G2_edge = (x[1],y[1])

        #if x[0] == y[0]:
            #return True
        #if x[1] == y[1]:
            #return True
        #if G1_edge in G1 and G2_edge not in G2:
            #return True
        #if G2_edge in G2 and G1_edge not in G1:
            #return True
        #return False

        G1_judge = G1_edge in G1
        G2_judge = G2_edge in G2

        if x[0] != y[0] and x[1] != y[1]:
            if G1_judge and G2_judge:
                return False
            elif not G1_judge and not G2_judge:
                return False
            else:
                return True
        return True



    def generate(self) -> None:
        for i in range(self.vertices_num):
            for j in range(self.vertices_num):
                for k in range(self.vertices_num):
                    for l in range(self.vertices_num):
                            x = (i+1, j+1)
                            y = (k+1, l+1)
                            if self.index(x)<=self.index(y):
                                if x == y:
                                    self.qubo[(x, y)] = -1
                                elif QUBO.conflict(x, y, self.G1, self.G2):
                                    self.qubo[(x, y)] = 1

    def index(self, key: Tuple[int, int]) -> int:
        return (key[0]-1)*self.vertices_num+(key[1]-1)+1


    def write(self) -> None:
        jsonQUBO = {}
        jsonQUBO['problem'] = 'GIP'
        jsonQUBO['vertices'] = self.vertices_num
        jsonQUBO['edge'] = self.edge_num
        jsonQUBO['nbit'] = self.vertices_num*self.vertices_num
        jsonQUBO['mapping'] = self.mapping
        jsonQUBO['base'] = 1
        jsonQUBO['qubo'] = [[self.index(key[0]), self.index(key[1]), val] for key, val in sorted(self.qubo.items())]
        jsonString = re.sub('[\r\n]\s+(-{0,1}\d+)\s*','\\1', json.dumps(jsonQUBO, sort_keys=False, indent=4))
        #print(jsonString)
        with open(rf'v{self.vertices_num}-e{self.edge_num}-gip.json', 'w') as obj:
            obj.write(jsonString)


def main():
    tic = time.perf_counter()
    random.seed(0)
    parser = argparse.ArgumentParser(
        description='Convert GIP into QUBO problem instances')
    parser.add_argument('GIP', help='GIP File')


    args = parser.parse_args()
    gip = GIP(args.GIP)
    
    problem = QUBO(gip)
    problem.generate()
    problem.write()
    toc = time.perf_counter()
    print(f"该程序耗时: {toc - tic:0.4f} seconds")


if __name__ == "__main__":
    main()
