from collections import defaultdict
import argparse
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


class General_Graph:
    def __init__(self, nodes_num, edges_num, Min, Max, seed):

        random.seed(seed)
        self.G = nx.gnm_random_graph(nodes_num, edges_num)
        for u, v in self.G.edges():
            self.G[u][v]['weight'] = random.randint(Min, Max)
            #print(self.G[u][v]['weight'])
        self.matching = nx.algorithms.matching.max_weight_matching(self.G, maxcardinality=False)
        self.max_matching = len(self.matching)
        self.total_weight = sum(self.G[u][v]['weight'] for (u, v) in self.matching)


class QUBO:

    def __init__(self, Graph, penalty):
        self.G = Graph.G
        self.penalty = penalty
        self.matching = Graph.matching
        self.max_matching = Graph.max_matching
        self.weight = Graph.total_weight
        self.qubo = defaultdict(int)
        self.nodes_num = len(Graph.G.nodes())
        self.edges_num = len(Graph.G.edges())
        self.size = self.edges_num
        self.index = defaultdict(int)
        edges = list(self.G.edges())
        k = 0
        for i in range(self.edges_num):
            self.index[edges[i]] = k
            k = k + 1

    def generate(self) -> None:
        self.qubo = {((i, j), (i, j)): -w for i, j, w in self.G.edges.data('weight')}
        self.qubo_out = defaultdict(int)
        edges = list(self.G.edges())
        for i in range(self.edges_num):
            for j in range(i + 1, self.edges_num):
                if conflict(edges[i], edges[j]):
                    self.qubo[(edges[i], edges[j])] = self.penalty

        for key in self.qubo:
            new_key = (self.index[key[0]], self.index[key[1]])
            self.qubo_out[new_key] = self.qubo[key]

    def print(self) -> None:
        jsonQUBO = {}
        jsonQUBO['problem'] = f'{self.edges_num} edges maximum weight matching problem'
        jsonQUBO['number of nodes'] = self.nodes_num
        jsonQUBO['number of edges'] = self.edges_num
        jsonQUBO['edges'] = list(self.G.edges())
        jsonQUBO['nbit'] = self.size
        jsonQUBO['number of maximum matching'] = self.max_matching
        jsonQUBO['total weight'] = self.weight
        jsonQUBO['base'] = 0
        jsonQUBO['qubo'] = [[key[0], key[1], val] for key, val in sorted(self.qubo_out.items()) if val != 0]

        jsonString = re.sub('[\r\n]\s+(-{0,1}\d+)\s*',
                            '\\1', json.dumps(jsonQUBO, sort_keys=False, indent=4))
        with open(rf'{self.nodes_num}-{self.edges_num}-mwm.json', 'w') as obj:
            obj.write(jsonString)


def main():
    parser = argparse.ArgumentParser(
        description='Generate QUBO matrix for maximum weight matching problem')
    parser.add_argument('-n', '--Nodes', type=int, help='number of vertice in group 1')
    parser.add_argument('-e', '--Edges', type=int, help='number of edges')
    parser.add_argument('-Min', '--Min_weight', type=int, help='Minimum value of weights')
    parser.add_argument('-Max', '--Max_weight', type=int, help='Maximum value of weights')
    parser.add_argument('-s', '--Seed', type=int, default=0, help='random seed')
    parser.add_argument('-P', '--Penalty', type=int, help='Penalty of QUBO')
    
    args = parser.parse_args()
    nodes_num = args.Nodes
    edges_num = args.Edges
    min_w = args.Min_weight
    max_w = args.Max_weight
    seed = args.Seed
    penalty = args.Penalty
    
    Graph = General_Graph(nodes_num, edges_num, min_w, max_w, seed)
    qubo = QUBO(Graph, penalty)
    qubo.generate()
    qubo.print()


if __name__ == "__main__":
    main()
