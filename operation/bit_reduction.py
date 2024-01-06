import random
import argparse
import json
import re
import sys
import gzip
from collections import defaultdict
import time


def errorExit(s: str):
    """エラーメッセージを表示して強制終了

    Args:
        s (str): 表示するエラーメッセージ
    """
    print(s, file=sys.stderr)
    sys.exit(1)

def sort_pair(x: int, y: int):
    if x <= y:
        return x, y
    else:
        return y, x

def rand_select(nbit: int, s=-1):
    if s == -1:
        s = nbit
    pool = list(range(nbit))
    for i in range(s):
        j = random.randrange(nbit-i)
        yield pool[j]
        pool[j]=pool[nbit-i-1]


class QUBO:

    def __init__(self, qubo, nbit):

        self.W = defaultdict(int)
        self.nbit = nbit
        self.adj = [[] for _ in range(nbit)]
        for x, y, v in qubo:
            if v == 0:
                continue
            if x <= y:
                self.W[(x, y)] = v
                if x != y:
                    self.adj[x].append(y)
                    self.adj[y].append(x)
            else:
                self.W[(y, x)] = v
                self.adj[x].append(y)
                self.adj[y].append(x)

        for i in range(nbit):
            self.adj[i].sort()
        

    def bit_reduction(self, reduction_num, solution_vector, total_01, selected_bits_idx):
        self.reduction_num = reduction_num
        self.sol = solution_vector
        self.target_nbit = self.nbit - self.reduction_num
        self.record = []
        self.offset = 0
        self.total_01 = total_01
        self.all_0 = []
        self.all_1 = []
        self.indices_0 = []
        self.indices_1 = []
        self.indices_01 = []
        flag = {}
        if selected_bits_idx == -1:
            self.selected_bits_idx = []
            bit_list = list(range(self.nbit))
        else:
            self.selected_bits_idx = selected_bits_idx
            bit_list = [x for x in list(range(self.nbit)) if x not in selected_bits_idx]
        num_01 = 0
        selected_bits_num = 0

        for i in range(self.nbit):
            if self.sol[i] == 0:
                self.all_0.append(i)
            else:
                self.all_1.append(i)
        real_indices_1 = self.all_1
        selected_0 = random.sample(self.all_0, total_01)
        selected_1 = random.sample(self.all_1, total_01)
        for i in range(total_01):
            if selected_0[i] < selected_1[i]:
                self.indices_01.append([selected_0[i], selected_1[i]])
                self.selected_bits_idx.append(selected_0[i])
                flag[(selected_0[i], selected_1[i])] = [0, 1]
            else:
                self.indices_01.append([selected_1[i], selected_0[i]])
                self.selected_bits_idx.append(selected_1[i])
                flag[(selected_1[i], selected_0[i])] = [1, 0]
            bit_list.remove(selected_0[i])
            bit_list.remove(selected_1[i])
            sorted_flag = dict(sorted(flag.items(), key=lambda item: item[0][0]))
            sorted_flag = list(sorted_flag.values())

        while selected_bits_num < self.reduction_num - total_01:
            selected_bits = random.sample(bit_list, 2)
            if self.sol[selected_bits[0]] == 0 and self.sol[selected_bits[1]] == 0:
                if selected_bits[0] < selected_bits[1]:
                    self.indices_0.append([selected_bits[0], selected_bits[1]])
                    self.selected_bits_idx.append(selected_bits[0])
                else:
                    self.indices_0.append([selected_bits[1], selected_bits[0]])
                    self.selected_bits_idx.append(selected_bits[1])
                bit_list.remove(selected_bits[0])
                bit_list.remove(selected_bits[1])
                selected_bits_num += 1
            elif self.sol[selected_bits[0]] == 1 and self.sol[selected_bits[1]] == 1:
                if selected_bits[0] < selected_bits[1]:
                    self.indices_1.append([selected_bits[0], selected_bits[1]])
                    self.selected_bits_idx.append(selected_bits[0])
                else:
                    self.indices_1.append([selected_bits[1], selected_bits[0]])
                    self.selected_bits_idx.append(selected_bits[1])
                bit_list.remove(selected_bits[0])
                bit_list.remove(selected_bits[1])
                selected_bits_num += 1

 
        
        self.indices_0 = sorted(self.indices_0, key=lambda x: x[0])
        self.indices_1 = sorted(self.indices_1, key=lambda x: x[0])
        self.indices_01 = sorted(self.indices_01, key=lambda x: x[0])
        self.selected_bits_idx = sorted(self.selected_bits_idx)

        num_0 = len(self.indices_0)
        num_1 = len(self.indices_1)
        num_01 = len(self.indices_01)
        num_selected_bits = len(self.selected_bits_idx)
        print('number of [1,1] bits: ', num_1)
        print('number of [0,0] bits: ', num_0)
        print('number of [0,1] bits: ', num_01)
        print('total reduction number: ', num_selected_bits)
        
        #[0,0] bit reduction
        if num_0 > 0:
            real_len = self.nbit
            next_idx = 0
            for k in range(num_0):
                for i in range(real_len):
                    total_val = 0
                    if i not in self.indices_0[k]:
                        for j in self.indices_0[k]:
                            if self.W[sort_pair(i,j)] is not None:
                                total_val += self.W[sort_pair(i,j)]
                                del self.W[sort_pair(i,j)]
                        if total_val != 0:
                            self.W[sort_pair(i,self.indices_0[k][0])] = total_val
                    elif i == self.indices_0[k][0]:
                        for j in self.indices_0[k]:
                            if self.W[sort_pair(i,j)] is not None:
                                total_val += self.W[sort_pair(i,j)]
                                del self.W[sort_pair(i,j)]
                        if total_val != 0:
                            self.W[sort_pair(i,i)] = total_val
                    else:
                        for j in self.indices_0[k]:
                            if i <= j and self.W[(i,j)] is not None:
                                total_val += self.W[(i,j)]
                                del self.W[(i,j)]
                        if total_val != 0 and self.W[(self.indices_0[k][0], self.indices_0[k][0])] is not None:
                            self.W[(self.indices_0[k][0], self.indices_0[k][0])] += total_val
                        elif total_val != 0 and self.W[(self.indices_0[k][0], self.indices_0[k][0])] is None:
                            self.W[(self.indices_0[k][0], self.indices_0[k][0])] = total_val
                    
                for key in list(sorted(self.W.keys())):
                    x, y = key
                    if x > self.indices_0[k][1]:
                        new_key = (x - 1, y - 1)
                    elif x < self.indices_0[k][1] and y > self.indices_0[k][1]:
                        new_key = (x, y - 1)
                    else:
                        new_key = key
                    self.W[new_key] = self.W.pop(key)
                
                for i in range(len(real_indices_1)):
                    if real_indices_1[i] > self.indices_0[k][1]:
                        real_indices_1[i] -= 1 

                if k != num_0 - 1:
                    next_idx += 1
                    for m in range(next_idx, num_0):
                        if self.indices_0[m][0] > self.indices_0[k][1]:
                            self.indices_0[m][0] -= 1
                            self.indices_0[m][1] -= 1
                        elif self.indices_0[m][0] < self.indices_0[k][1] and self.indices_0[m][1] > self.indices_0[k][1]:
                            self.indices_0[m][1] -= 1
                for m in range(num_1):
                    if self.indices_1[m][0] > self.indices_0[k][1]:
                        self.indices_1[m][0] -= 1
                        self.indices_1[m][1] -= 1
                    elif self.indices_1[m][0] < self.indices_0[k][1] and self.indices_1[m][1] > self.indices_0[k][1]:
                        self.indices_1[m][1] -= 1
                for m in range(num_01):
                    if self.indices_01[m][0] > self.indices_0[k][1]:
                        self.indices_01[m][0] -= 1
                        self.indices_01[m][1] -= 1
                    elif self.indices_01[m][0] < self.indices_0[k][1] and self.indices_01[m][1] > self.indices_0[k][1]:
                        self.indices_01[m][1] -= 1
                for m in range(num_selected_bits):
                    if self.selected_bits_idx[m] > self.indices_0[k][1]:
                        self.selected_bits_idx[m] -= 1
                real_len -= 1
        
        #[1,1] bit reduction
        if num_1 > 0:
            real_len = self.nbit - num_0
            next_idx = 0
            for k in range(num_1):
                for i in range(real_len):
                    total_val = 0
                    if i not in self.indices_1[k]:
                        for j in self.indices_1[k]:
                            if self.W[sort_pair(i,j)] is not None:
                                total_val += self.W[sort_pair(i,j)]
                                del self.W[sort_pair(i,j)]
                        if total_val != 0:
                            self.W[sort_pair(i,self.indices_1[k][0])] = total_val
                    elif i == self.indices_1[k][0]:
                        for j in self.indices_1[k]:
                            if self.W[sort_pair(i,j)] is not None:
                                total_val += self.W[sort_pair(i,j)]
                                del self.W[sort_pair(i,j)]
                        if total_val != 0:
                            self.W[sort_pair(i,i)] = total_val
                    else:
                        for j in self.indices_1[k]:
                            if i <= j and self.W[(i,j)] is not None:
                                total_val += self.W[(i,j)]
                                del self.W[(i,j)]
                        if total_val != 0 and self.W[(self.indices_1[k][0], self.indices_1[k][0])] is not None:
                            self.W[(self.indices_1[k][0], self.indices_1[k][0])] += total_val
                        elif total_val != 0 and self.W[(self.indices_1[k][0], self.indices_1[k][0])] is None:
                            self.W[(self.indices_1[k][0], self.indices_1[k][0])] = total_val
                    
                for key in list(sorted(self.W.keys())):
                    x, y = key
                    if x > self.indices_1[k][1]:
                        new_key = (x - 1, y - 1)
                    elif x < self.indices_1[k][1] and y > self.indices_1[k][1]:
                        new_key = (x, y - 1)
                    else:
                        new_key = key
                    self.W[new_key] = self.W.pop(key)

                real_indices_1.remove(self.indices_1[k][1])
                for i in range(len(real_indices_1)):
                    if real_indices_1[i] > self.indices_1[k][1]:
                        real_indices_1[i] -= 1

                if k != num_1 - 1:
                    next_idx += 1
                    for m in range(next_idx, num_1):
                        if self.indices_1[m][0] > self.indices_1[k][1]:
                            self.indices_1[m][0] -= 1
                            self.indices_1[m][1] -= 1
                        elif self.indices_1[m][0] < self.indices_1[k][1] and self.indices_1[m][1] > self.indices_1[k][1]:
                            self.indices_1[m][1] -= 1
                for m in range(num_01):
                    if self.indices_01[m][0] > self.indices_1[k][1]:
                        self.indices_01[m][0] -= 1
                        self.indices_01[m][1] -= 1
                    elif self.indices_01[m][0] < self.indices_1[k][1] and self.indices_01[m][1] > self.indices_1[k][1]:
                        self.indices_01[m][1] -= 1
                for m in range(num_selected_bits):
                    if self.selected_bits_idx[m] > self.indices_1[k][1]:
                        self.selected_bits_idx[m] -= 1
                real_len -= 1
        

        #[1,0] bit reduction
        if num_01 > 0:
            real_len = self.nbit - num_0 - num_1
            next_idx = 0
            for k in range(num_01):
                #flip one bit in indices_01
                v = self.W[(self.indices_01[k][1], self.indices_01[k][1])]
                self.offset += v
                self.W[(self.indices_01[k][1], self.indices_01[k][1])] = -v
                edges_with_selected_0_bit = [key for key in self.W.keys() if self.indices_01[k][1] in key \
                                                and key != (self.indices_01[k][1], self.indices_01[k][1])]
                for edge in edges_with_selected_0_bit:
                    v = self.W[edge]
                    self.W[edge] = -v
                    if self.indices_01[k][1] == edge[0]:
                        self.W[(edge[1],edge[1])] += v
                    else:
                        self.W[(edge[0],edge[0])] += v

                if sorted_flag[k][1] == 1:
                    real_indices_1.remove(self.indices_01[k][1])
                
                self.indices_01[k].sort()
                for i in range(real_len):
                    total_val = 0
                    if i not in self.indices_01[k]:
                        for j in self.indices_01[k]:
                            if self.W[sort_pair(i,j)] is not None:
                                total_val += self.W[sort_pair(i,j)]
                                del self.W[sort_pair(i,j)]
                        if total_val != 0:
                            self.W[sort_pair(i,self.indices_01[k][0])] = total_val
                    elif i == self.indices_01[k][0]:
                        for j in self.indices_01[k]:
                            if self.W[sort_pair(i,j)] is not None:
                                total_val += self.W[sort_pair(i,j)]
                                del self.W[sort_pair(i,j)]
                        if total_val != 0:
                            self.W[sort_pair(i,i)] = total_val
                    else:
                        for j in self.indices_01[k]:
                            if i <= j and self.W[(i,j)] is not None:
                                total_val += self.W[(i,j)]
                                del self.W[(i,j)]
                        if total_val != 0 and self.W[(self.indices_01[k][0], self.indices_01[k][0])] is not None:
                            self.W[(self.indices_01[k][0], self.indices_01[k][0])] += total_val
                        elif total_val != 0 and self.W[(self.indices_01[k][0], self.indices_01[k][0])] is None:
                            self.W[(self.indices_01[k][0], self.indices_01[k][0])] = total_val
                    
                for key in list(sorted(self.W.keys())):
                    x, y = key
                    if x > self.indices_01[k][1]:
                        new_key = (x - 1, y - 1)
                    elif x < self.indices_01[k][1] and y > self.indices_01[k][1]:
                        new_key = (x, y - 1)
                    else:
                        new_key = key
                    self.W[new_key] = self.W.pop(key)

                for i in range(len(real_indices_1)):
                    if real_indices_1[i] > self.indices_01[k][1]:
                        real_indices_1[i] -= 1

                if k != num_01 - 1:
                    next_idx += 1
                    for m in range(next_idx, num_01):
                        if self.indices_01[m][0] > self.indices_01[k][1]:
                            self.indices_01[m][0] -= 1
                            self.indices_01[m][1] -= 1
                        elif self.indices_01[m][0] < self.indices_01[k][1] and self.indices_01[m][1] > self.indices_01[k][1]:
                            self.indices_01[m][1] -= 1
                for m in range(num_selected_bits):
                    if self.selected_bits_idx[m] > self.indices_01[k][1]:
                        self.selected_bits_idx[m] -= 1
                real_len -= 1
        real_len = self.nbit - num_0 - num_1 - num_01
        self.solution_after_reduction = [0]*real_len
        for i in real_indices_1:
            self.solution_after_reduction[i] += 1
        

def main():
    random.seed(0)
    parser = argparse.ArgumentParser(
        description='Bit reduction for reducing bits of QUBO problems')
    parser.add_argument(
        '-Q', '--QUBOfile', type=str, help='QUBO problem file. must be .json/.json.gz. stdin if omitted')
    parser.add_argument('-n', '--reduction_num', type=int, help='number of reduced bits') 
    parser.add_argument('-sol', '--Solutionfile', type=str, help='solution file.')
    parser.add_argument('-t', '--total_01_num', type=int, default=0, help='total number of 01 bits')
    parser.add_argument('-s', '--seed', type=int, default=0, help='Random seed')

    args = parser.parse_args()
    random.seed(args.seed)
    reduction_num = args.reduction_num
    total_01 = args.total_01_num


    QUBOfile = args.QUBOfile
    Solutionfile = args.Solutionfile

    with open(Solutionfile, "rt") as f:
        solution = json.load(f)
    if 'offset' in solution:
        accumulation_offset = solution.get('offset')
    else:
        accumulation_offset = 0
    if 'selected bits indices' in solution:
        selected_bits_idx = solution.get('selected bits indices')
    else:
        selected_bits_idx = -1
    
    solution_vector = solution.get('solution')
    indices_0 = []
    indices_1 = []
    for i in range(len(solution_vector)):
        if solution_vector[i] == 1:
            indices_1.append(i)
        else:
            indices_0.append(i)
    print('number of 1 bits:',len(indices_1))
    print('number of 0 bits:',len(indices_0))

    with open(QUBOfile, "rt") as f:
        problem = json.load(f)
        
    
    if QUBOfile is None:
        qubofile = sys.stdin
    elif re.search('.json.gz$', args.QUBOfile, flags=re.IGNORECASE) is not None:
        qubofile = gzip.open(args.QUBOfile, 'rt')
    elif re.search('.json$', args.QUBOfile, flags=re.IGNORECASE) is not None:
        qubofile = open(args.QUBOfile, 'rt')
    else:
        errorExit(f'QUBO Problem file must be .json or .json.gz')

    problem = json.load(qubofile)

    nbit = problem.get('nbit')
    if nbit is None:
        errorExit('<nbit> is missing')
    qubo = problem.get('qubo')
    if qubo is None:
        errorExit('<qubo> is missing')
    base = problem.get('base')
    if base is None:
        base = 0
 
    

    start_time = time.time()
    model = QUBO(qubo, nbit)
    model.bit_reduction(reduction_num, solution_vector, total_01, selected_bits_idx)

    end_time = time.time()
    total_time = end_time - start_time
    print('total time:', total_time)


    result = {'operation': 'bit reduction',
                'nbit': nbit - reduction_num, 
                'base': 0}
    result['reduction number'] = reduction_num
    result['offset'] = model.offset + accumulation_offset
    result['number of 01 bits'] = model.total_01
    result['selected bits indices'] = model.selected_bits_idx
    result['solution'] = model.solution_after_reduction
    result['qubo'] = []
    for x, y in sorted(model.W):
        if model.W[(x, y)] != 0:
            result['qubo'].append([x, y, int(model.W[(x, y)])])    
    jsonString = re.sub('[\r\n]\s+(-{0,1}\d+)\s*',
                            '\\1', json.dumps(result, sort_keys=False, indent=4))
    with open(rf'{nbit-reduction_num}-bit_reduction.json', 'w') as obj:
        obj.write(jsonString)
    


if __name__ == "__main__":
    main()
