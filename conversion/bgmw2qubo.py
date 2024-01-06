from collections import defaultdict
import argparse
from typing import Tuple
import re
import json
import networkx as nx
import random


def sort_pair(x: int, y: int):
    if x <= y:
        return x, y
    else:
        return y, x

def conflict(match0, match1):
    if match0[0] in match1:
        return True
    elif match0[1] in match1:
        return True
    else:
        return False


class Bigraph:
    def __init__(self, m, n, p, edges_num, Min, Max, seed):
        # random.seed(seed)
        # self.G = nx.bipartite.random_graph(m, n, p, seed)
        # for u, v in self.G.edges():
        #     self.G[u][v]['weight'] = random.randint(Min, Max)
        # #self.G = nx.bipartite.gnmk_random_graph(m, n, e)
        # #self.matching = nx.algorithms.matching.max_weight_matching(self.G)
        # self.matching = nx.algorithms.matching.max_weight_matching(self.G, maxcardinality=False)
        # self.total_weight = sum(self.G[u][v]['weight'] for (u, v) in self.matching)

        random.seed(seed)
        self.G = nx.bipartite.random_graph(m,n,p,seed)
        perfect_matching = min(m, n)
        #self.G = nx.bipartite.complete_bipartite_graph(m, n)
        while self.G.number_of_edges() > edges_num:
            u, v = random.choice(list(self.G.edges()))
            self.G.remove_edge(u, v)
            if not nx.is_connected(self.G):
                self.G.add_edge(u, v)
            matching = nx.bipartite.maximum_matching(self.G)
            max_matching = int(len(matching) / 2)
            if max_matching != perfect_matching:
                self.G.add_edge(u, v)
        for u, v in self.G.edges():
            self.G[u][v]['weight'] = random.randint(Min, Max)
        self.matching = nx.algorithms.matching.max_weight_matching(self.G, maxcardinality=False)
        self.max_matching = int(len(self.matching)/2)
        self.total_weight = sum(self.G[u][v]['weight'] for (u, v) in self.matching)


class QUBO:

    def __init__(self, bg, penalty):
        self.bg = bg.G
        self.penalty = penalty
        self.sets = nx.bipartite.sets(bg.G)
        self.matching = bg.matching
        self.max_matching = bg.max_matching
        self.weight = bg.total_weight
        self.qubo = defaultdict(int)
        self.nodes_num = len(bg.G.nodes())
        self.edges_num = len(bg.G.edges())
        self.size = self.edges_num
        self.index = defaultdict(int)
        edges = list(self.bg.edges())
        k = 0
        for i in range(self.edges_num):
            self.index[edges[i]] = k
            k = k + 1


    def generate(self) -> None:
        self.qubo = {((i, j), (i, j)) : -w for i, j, w in self.bg.edges.data('weight')}
        self.qubo_out = defaultdict(int)
        edges = list(self.bg.edges())
        for i in range(self.edges_num):
            for j in range(i+1, self.edges_num):
                if conflict(edges[i], edges[j]):
                    self.qubo[(edges[i], edges[j])] = self.penalty
                else:
                    self.qubo[(edges[i], edges[j])] = 0
            
        for key in self.qubo:
            new_key = (self.index[key[0]], self.index[key[1]])
            self.qubo_out[new_key] = self.qubo[key]

    def print(self) -> None:
        jsonQUBO = {}
        jsonQUBO['problem'] = f'{self.nodes_num} nodes bipartite graph matching problem'
        jsonQUBO['nbit'] = self.size
        #jsonQUBO['maximum matching'] = self.matching
        jsonQUBO['number of maximum matching'] = self.max_matching
        jsonQUBO['total weight'] = self.weight
        jsonQUBO['base'] = 0
        jsonQUBO['qubo'] = [
            [key[0], key[1], val] for key, val in sorted(self.qubo_out.items())]
        jsonString = re.sub('[\r\n]\s+(-{0,1}\d+)\s*',
                            '\\1', json.dumps(jsonQUBO, sort_keys=False, indent=4))
        with open(rf'{self.nodes_num}-{self.edges_num}-bgmw.json','w') as obj:
            obj.write(jsonString)


def main():
    parser = argparse.ArgumentParser(
        description='Generate maximum weight matching problem of bipartite graph')
    parser.add_argument('-m', '--Group1', type=int, help='number of vertice in group 1')
    parser.add_argument('-n', '--Group2', type=int, help='number of vertice in group 2')
    parser.add_argument('-p', '--Pos', type=float, help='possibility of edge generation')
    parser.add_argument('-e', '--Edges', type=int, help='number of edges')
    parser.add_argument('-Min', '--Min_weight', type=int, help='Minimum value of weights')
    parser.add_argument('-Max', '--Max_weight', type=int, help='Maximum value of weights')
    parser.add_argument('-P', '--penalty', type=int, help='Penalty of QUBO')
    args = parser.parse_args()
    seed = 0
    bigraph = Bigraph(args.Group1, args.Group2, args.Pos, args.Edges, args.Min_weight, args.Max_weight, seed)
    qubo = QUBO(bigraph, args.penalty)
    qubo.generate()
    qubo.print()


if __name__ == "__main__":
    main()
