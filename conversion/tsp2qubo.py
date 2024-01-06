import networkx as nx
import numpy as np
import json
import re
from collections import defaultdict
from pyqubo import Array, Placeholder, Constraint
import argparse
from itertools import product
import random


def dist_gen(n, size):
    dist_matrix = np.zeros((n, n))
    for i in range(n):
        for j in range(i+1, n):
            d = random.randint(1, size)
            dist_matrix[i][j] = d
            dist_matrix[j][i] = d
    for i in range(n):
        for j in range(n):
            for k in range(n):
                if dist_matrix[i][j] + dist_matrix[j][k] < dist_matrix[i][k]:
                    dist_matrix[i][k] = dist_matrix[i][j] + dist_matrix[j][k]
    return dist_matrix


class TSP:

    def __init__(self, n, size):
        self.n_cities = n
        self.size = size
        self.dist_matrix = dist_gen(n, size)

    def write_city(self):
        TSP_cities = {}
        TSP_cities['number of cities'] = self.n_cities
        TSP_cities['distance_matrix'] = self.dist_matrix.tolist()
        cities_String = re.sub('[\r\n]\s+(-{0,1}\d+)\s*', '\\1', json.dumps(TSP_cities, sort_keys=False, indent=4))
        with open(rf'{self.n_cities}-info-tsp.json', 'w') as obj:
            obj.write(cities_String)



class QUBO:


    def __init__(self, tsp, penalty):
        p = tsp.n_cities
        self.n_cities = p
        self.dist_matrix = tsp.dist_matrix
        x = Array.create('Q', (p, p), 'BINARY')

        time_cons = 0
        for i in range(p):
            time_cons += Constraint((sum(x[i,j] for j in range(p)) - 1) ** 2, label = 'time{}'.format(i))

        city_cons = 0
        for j in range(p):
            city_cons += Constraint((sum(x[i,j] for i in range(p)) - 1) ** 2, label = "city{}".format(j))
        distance = 0
        for i in range(p):
            for j in range(p):
                for k in range(p):
                    d_ij = self.dist_matrix[i][j]
                    distance += d_ij * x[k,i] * x[(k+1)%p, j]
        A = Placeholder('A')
        H = distance + A * (time_cons + city_cons)
        model = H.compile()
        feed_dict = {'A': penalty}
        self.qubo_tup, self.offset = model.to_qubo(feed_dict=feed_dict)
        self.qubo_dict = dict(self.qubo_tup)
        self.qubo = []
        self.mapping = defaultdict()
        h = 0
        for i in range(p):
            for j in range(p):
                self.mapping[rf'Q[{i}][{j}]'] = h
                h += 1

        for key0, key1, in self.qubo_dict:
            val = int(self.qubo_dict[(key0, key1)])
            if key0 > key1:
                self.qubo.append([self.mapping[key1], self.mapping[key0], val])
            else:
                self.qubo.append([self.mapping[key0], self.mapping[key1], val])


    def write_json(self):
        jsonQUBO = {}
        jsonQUBO['problem'] = 'TSP'
        jsonQUBO['cities'] = self.n_cities
        jsonQUBO['nbit'] = self.n_cities * self.n_cities
        jsonQUBO['offset'] = self.offset
        jsonQUBO['base'] = 0
        jsonQUBO['qubo'] = sorted(self.qubo)
        jsonString = re.sub('[\r\n]\s+(-{0,1}\d+)\s*', '\\1', json.dumps(jsonQUBO, sort_keys=False, indent=4))
        with open(rf'{self.n_cities}-cities-tsp.json', 'w') as obj:
            obj.write(jsonString)


def main():
    np.random.seed(0)
    random.seed(0)
    parser = argparse.ArgumentParser(
        description='Reduce TSP to QUBO model')
    parser.add_argument('-n', '--n_cities', type=int, help='number of cities')
    parser.add_argument('-s', '--size', type=int, help='size of axis')
    parser.add_argument('-p', '--Penalty', type=int, help='Penalty value')

    args = parser.parse_args()
    n = args.n_cities
    size = args.size
    penalty = args.Penalty

    tsp = TSP(n, size)   
    tsp.write_city()
    model = QUBO(tsp, penalty)
    model.write_json()

if __name__ == "__main__":
    main()
