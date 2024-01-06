import random
import json
import re
import networkx as nx
import argparse
from collections import defaultdict



class MIS:

    def __init__(self, nodes, mis_num, seed) -> None:
        random.seed(seed)
        self.nodes = nodes
        self.mis_num = mis_num
        self.G = nx.Graph()
        self.G.add_nodes_from(range(self.nodes))
        self.mis = set(random.sample(range(self.nodes), self.mis_num))
        for i in range(self.nodes):
            for j in range(self.nodes):
                if i < j:
                    if i not in self.mis and j in self.mis:
                        self.G.add_edge(i, j)
                    elif i in self.mis and j not in self.mis:
                        self.G.add_edge(i, j)
                    elif i not in self.mis and j not in self.mis:
                        self.G.add_edge(i, j)

class QUBO:

    def __init__(self, MIS, penalty) -> None:
        self.G = MIS.G
        self.mis_num = MIS.mis_num
        self.penalty = penalty
        self.size = len(self.G.nodes())
    
    def generate(self):
        self.qubo=defaultdict(int)
        for i in range(self.size):
            self.qubo[(i, i)] = -1
            for j in range(i + 1, self.size):
                if (i, j) in self.G.edges():
                    self.qubo[(i, j)] = self.penalty
                else:
                    self.qubo[(i, j)] = 0


    def write(self) -> None:
        jsonQUBO = {}
        jsonQUBO['problem'] = 'MIS'
        jsonQUBO['nodes'] = self.size
        jsonQUBO['edges'] = len(self.G.edges())
        jsonQUBO['MIS'] = self.mis_num
        jsonQUBO['nbit'] = self.size
        jsonQUBO['base'] = 0
        jsonQUBO['qubo'] = [[key[0], key[1], val] for key, val in sorted(self.qubo.items())]
        jsonString = re.sub('[\r\n]\s+(-{0,1}\d+)\s*','\\1', json.dumps(jsonQUBO, sort_keys=False, indent=4))
        #print(jsonString)
        with open(rf'{self.size}-MIS.json', 'w') as obj:
            obj.write(jsonString)

def main():
    parser = argparse.ArgumentParser(
        description='Convert MIS into QUBO problem instances')
    parser.add_argument('-n', '--Nodes', type=int, help='nodes number')
    parser.add_argument('-m', '--Mis', type=int, help='MIS')
    parser.add_argument('-P', '--Penalty', type=int, default=100, help='Penalty value')

    args = parser.parse_args()
    nodes = args.Nodes
    mis = args.Mis
    penalty = args.Penalty
    seed = 0

    problem = MIS(nodes, mis, seed)
    qubo = QUBO(problem, penalty)
    qubo.generate()
    qubo.write()

if __name__ == "__main__":
    main()
