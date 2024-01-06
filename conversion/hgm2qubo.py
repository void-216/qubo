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


class Hyper_Graph:
    def __init__(self, m, n, p, edges_num, seed):
        random.seed(seed)
        self.G = nx.bipartite.random_graph(m, n, p)
        while self.G.number_of_edges() > edges_num:
            u, v = random.choice(list(self.G.edges()))
            self.G.remove_edge(u, v)
            if not nx.is_connected(self.G):
                self.G.add_edge(u, v)

class QUBO:

    def __init__(self, hg, penalty):
        self.hg = hg.G
        self.penalty = penalty
        self.sets = list(nx.bipartite.sets(hg.G))
        set1 = list(self.sets[1])
        self.qubo = defaultdict(int)
        self.nodes_num = len(hg.G.nodes())
        self.edges_num = len(hg.G.edges())
        self.size = len(self.sets[1])
        self.index = defaultdict(int)
        k = 0
        for i in range(self.size):
            self.index[set1[i]] = k
            k = k + 1


    def generate(self) -> None:
        self.qubo = {(i, i) : -1 for i in self.sets[1]}
        self.qubo_out = defaultdict(int)
        edges = list(self.hg.edges())
        record = []
        for i in self.sets[0]:
            edges = list(self.hg.edges(i))
            for j in range(len(edges)):
                for k in range(j+1, len(edges)):
                    if sort_pair(edges[j][1], edges[k][1]) not in record:
                        self.qubo[sort_pair(edges[j][1], edges[k][1])] = self.penalty
                        record.append(sort_pair(edges[j][1], edges[k][1]))

        for key in self.qubo:
            new_key = (self.index[key[0]], self.index[key[1]])
            self.qubo_out[new_key] = self.qubo[key]

    def print(self) -> None:
        jsonQUBO = {}
        jsonQUBO['problem'] = f'{self.nodes_num} nodes bipartite graph matching problem'
        jsonQUBO['nbit'] = self.size
        jsonQUBO['base'] = 0
        jsonQUBO['edges'] = list(self.hg.edges())
        jsonQUBO['qubo'] = [
            [key[0], key[1], val] for key, val in sorted(self.qubo_out.items())]
        jsonString = re.sub('[\r\n]\s+(-{0,1}\d+)\s*',
                            '\\1', json.dumps(jsonQUBO, sort_keys=False, indent=4))
        with open(rf'{self.size}-hgm.json','w') as obj:
            obj.write(jsonString)


def main():
    parser = argparse.ArgumentParser(
        description='Generate QUBO matrix for hyper graph matching problem')
    parser.add_argument('-m', '--Group1', type=int, help='number of vertice')
    parser.add_argument('-n', '--Group2', type=int, help='number of hyperedges')
    parser.add_argument('-Po', '--Pos', type=float, help='possibility of edge generation')
    parser.add_argument('-e', '--Edges', type=int, help='number of edges')
    parser.add_argument('-Pe', '--Penalty', type=int, default=100, help='Penalty value')
    args = parser.parse_args()
    seed = 0
    hypergraph = Hyper_Graph(args.Group1, args.Group2, args.Pos, args.Edges, seed)
    qubo = QUBO(hypergraph, args.Penalty)
    qubo.generate()
    qubo.print()


if __name__ == "__main__":
    main()
