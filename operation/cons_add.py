from collections import defaultdict
import argparse
import json
import re
import random
import numpy as np




def rand_pos_val(n, val):
    abs_val = abs(val)
    p = random.sample(range(1, abs_val), n - 1)
    p.sort()
    x = [p[i+1]-p[i] for i in range(n - 2)]
    x.append(p[0])
    x.append(abs_val-p[n-2])
    return x

def rand_select(nbit: int, s=-1):
    if s == -1:
        s = nbit
    pool = list(range(nbit))
    for i in range(s):
        j = random.randrange(nbit-i)
        yield pool[j]
        pool[j]=pool[nbit-i-1]

def sort_pair(x: int, y: int):
    if x <= y:
        return x, y
    else:
        return y, x

class Solution:

    def read(self, sol_file, qubo_file) -> None:
        with open(sol_file, "rt") as file0:
            sol = json.load(file0)
            self.solution = sol.get('solution')
            self.energy = sol.get('energy')
            self.nbit = len(self.solution)
        with open(qubo_file) as file1:
            self.W = defaultdict(int)
            qubo = json.load(file1)
            self.qubo = qubo.get('qubo')
            for x, y, v in self.qubo:
                if v == 0:
                    continue
                if x <= y:
                    self.W[(x, y)] = v
                else:
                    self.W[(y, x)] = v

class QUBO:

    def __init__(self, solution, W, energy, nbit, penalty):
        self.solution = solution
        self.W = W
        self.energy = energy
        self.nbit = nbit
        self.penalty = penalty

    def add_cons(self, cons_num, bit_num):
        self.group0 = []
        self.group1 = []
        self.cons_group = np.ones((cons_num, bit_num), int) * -1

        p = list(rand_select(self.nbit))
        for i in range(self.nbit):
            if self.solution[p[i]] == 0:
                self.group0.append(p[i])
            else:
                self.group1.append(p[i])

        self.offset = 0
        cnt1 = 0
        cnt0 = 0
        for i in range(cons_num):
            if cnt1 < len(self.group1):
                self.cons_group[i][0] = self.group1[cnt1]
                cnt1 += 1
                for j in range(bit_num - 1):
                    if cnt0 < len(self.group0):
                        self.cons_group[i][j + 1] = self.group0[cnt0]
                        cnt0 += 1
            else:
                break

        cons_group = self.cons_group.tolist()

        for i in range(cons_num):
            for j in range(bit_num):
                self.W[cons_group[i][j], cons_group[i][j]] -= self.penalty
        
        for i in range(cons_num):
            for j in range(bit_num - 1):
                for k in range(j + 1, bit_num):
                    self.W[sort_pair(cons_group[i][j], cons_group[i][k])] += 2*self.penalty
        
        self.offset = cons_num*self.penalty

        jsonQUBO = {}
        jsonQUBO['problem'] = 'hard QUBO problem'
        jsonQUBO['nbit'] = self.nbit
        jsonQUBO['base'] = 0
        jsonQUBO['offset'] = self.offset
        jsonQUBO['constraints'] = cons_group
        jsonQUBO['qubo'] = []
        for x, y in sorted(self.W):
            if self.W[(x, y)] != 0:
                jsonQUBO['qubo'].append([x, y, int(self.W[(x, y)])])
 
        jsonString = re.sub('[\r\n]\s+(-{0,1}\d+)\s*',
                        '\\1', json.dumps(jsonQUBO, sort_keys=False, indent=4))
        #print(jsonQUBO)
        with open(rf'{self.nbit}-{cons_num}-{bit_num}-cons_add.json',
                  'w') as obj:
            obj.write(jsonString)

def main():
    parser = argparse.ArgumentParser(
        description='generate hard QUBO problem by adding one-hot constraints')
    parser.add_argument('-S', '--SolutionFile', type = str, help='Solution File')
    parser.add_argument('-Q', '--QUBOFile', type = str, help='QUBO File')
    parser.add_argument('-p', '--penalty', type=int, help='Penalty value')
    parser.add_argument('-c', '--cons_num', type=int, help='Constraints number')
    parser.add_argument('-b', '--bit_num', type=int, help='number of bits in one constraint')
    args = parser.parse_args()
    penalty = args.penalty
    cons_num = args.cons_num
    bit_num = args.bit_num
    
    
    Sol = Solution()
    Sol.read(args.SolutionFile, args.QUBOFile)
    qubo = QUBO(Sol.solution, Sol.W, Sol.energy, Sol.nbit, penalty)
    qubo.add_cons(cons_num, bit_num)


if __name__ == "__main__":
    main()