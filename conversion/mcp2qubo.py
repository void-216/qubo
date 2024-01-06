import random
import json
import re
import time
import argparse




class MCP:

    def __init__(self, filename: str, penalty) -> None:
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
            edge_pair.append(edge)
        edge_pair.sort(key=lambda edge_pair:edge_pair[0])
        self.edge_num = len(edge_pair)
        for j in range(len(edge_pair)):
            self.G1.append(edge_pair[j])
        #print(self.G1)
        self.MCP_gen(penalty)

    def MCP_gen(self, penalty):
        self.MCP = []
        for i in range(self.vertices_num):
            for j in range(self.vertices_num):
                if i <= j:
                    if i == j:
                        self.MCP.append([i, j, -1])
                    else:
                        self.MCP.append([i, j, penalty])

        for i in range(self.edge_num):
            MIS_edge = [self.G1[i][0] - 1, self.G1[i][1] - 1]
            MIS_edge.append(penalty)
            self.MCP.remove(MIS_edge)

    def write(self) -> None:
        jsonQUBO = {}
        jsonQUBO['problem'] = 'MCP'
        jsonQUBO['vertices'] = self.vertices_num
        jsonQUBO['edge'] = self.edge_num
        jsonQUBO['nbit'] = self.vertices_num
        jsonQUBO['base'] = 0
        jsonQUBO['qubo'] = self.MCP
        jsonString = re.sub('[\r\n]\s+(-{0,1}\d+)\s*','\\1', json.dumps(jsonQUBO, sort_keys=False, indent=4))
        #print(jsonString)
        with open(rf'{self.vertices_num}-MCP.json', 'w') as obj:
            obj.write(jsonString)

def main():
    tic = time.perf_counter()
    parser = argparse.ArgumentParser(
        description='Convert MCP into QUBO problem instances')
    parser.add_argument('Graph', help='Graph File')
    parser.add_argument('-P', '--Penalty', type=int,
                        default=100, help='Penalty value')

    args = parser.parse_args()
    penalty = args.Penalty


    problem = MCP(args.Graph, penalty)
    problem.write()
    toc = time.perf_counter()
    print(f"该程序耗时: {toc - tic:0.4f} seconds")


if __name__ == "__main__":
    main()
