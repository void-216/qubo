import random
import argparse
import json
import re
import sys
import gzip
from collections import defaultdict
import numpy as np


def errorExit(s: str):
    print(s, file=sys.stderr)
    sys.exit(1)

def rand_val(n, val):
    abs_val = abs(val)
    while True:
        p = [random.randint(-abs_val, abs_val) for _ in range(n)]
        if sum(p) == val:
            break
    return p

def rand_select(nbit: int, s=-1):
    if s == -1:
        s = nbit
    pool = list(range(nbit))
    for i in range(s):
        j = random.randrange(nbit-i)
        yield pool[j]
        pool[j]=pool[nbit-i-1]


def randPerm(nbit: int):
    p = list(range(nbit))
    for i in range(nbit-1):
        j = random.randint(i, nbit-1)
        p[i], p[j] = p[j], p[i]
    return p

def sort_pair(x: int, y: int):
    if x <= y:
        return x, y
    else:
        return y, x




def main():
    random.seed(0)
    parser = argparse.ArgumentParser(
        description='Bit duplication for generating hard QUBO problem')
    parser.add_argument(
        '-Q', '--QUBOfile', type=str, help='QUBO problem file. must be .json/.json.gz. stdin if omitted')
    parser.add_argument('-P', '--Penalty', type=int, help='Penalty value')

    parser.add_argument('-r1', '--ratio', type=str,
                        help='bit duplication 1, duplicate bits if integer, duplicate ratio if float')

    parser.add_argument('-n1', '--duplicate_num', type=int, help='duplication number of one node')
    parser.add_argument('-r2', '--ratio2', type=str,
                        help='bit duplication 2, duplicate bits if integer, duplicate ratio if float')
    parser.add_argument('-n2', '--duplicate_num2', type=int, help='duplication number of one node')
    parser.add_argument('-s', '--seed', type=int,
                        default=0, help='Random seed')
    parser.add_argument(
        '-sol', '--solutionfile', type=str, help='solution file')

    args = parser.parse_args()
    random.seed(args.seed)
    penalty = args.Penalty
    duplicate_num = args.duplicate_num
    duplicate_num2 = args.duplicate_num2
    solfile = args.solutionfile


    QUBOfile = args.QUBOfile
    
    with open(QUBOfile, "rt") as f:
        problem = json.load(f)

  
    if args.ratio.isdecimal():
        dup_normal = int(args.ratio)
    else:
        dup_normal = float(args.ratio)
    
    if args.ratio2 is not None:
        if args.ratio2.isdecimal():
            dup_normal2 = int(args.ratio2)
        else:
            dup_normal2 = float(args.ratio2)
        
    
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

    if isinstance(dup_normal, float):
        dup_normal = int(dup_normal*nbit)
    
    if args.ratio2 is not None:
        if isinstance(dup_normal2, float):
            dup_normal2 = int(dup_normal2*nbit)



    # bit duplication + bit duplication
    p = list(rand_select(nbit, dup_normal + dup_normal2))
    p.sort()
    p_normal = p[0:dup_normal]
    p_normal2 = p[dup_normal:dup_normal + dup_normal2]
    q_normal = {v: k for k, v in enumerate(p_normal)}
    q_normal2 = {v: k for k, v in enumerate(p_normal2)}
    mapping_normal = np.zeros((dup_normal, duplicate_num), int)
    mapping_normal2 = np.zeros((dup_normal2, duplicate_num2), int)
    W = defaultdict(int)


    for x, y, v in qubo:
        if v == 0:
            continue
        if x <= y:
            W[(x, y)] = v
        else:
            W[(y, x)] = v

    for i in range(dup_normal):
        mapping_normal[i][0] = p[i]
        for j in range(duplicate_num - 1):
            W[(nbit + (duplicate_num - 1) * i + j, nbit + (duplicate_num - 1) * i + j)] = W[(p[i], p[i])]
            mapping_normal[i][j + 1] = nbit + (duplicate_num - 1) * i + j
    mapping1 = mapping_normal.tolist()

    for i in range(dup_normal2):
        mapping_normal2[i][0] = p[dup_normal + i]
        for j in range(duplicate_num2 - 1):
            W[(nbit + dup_normal * (duplicate_num - 1) + (duplicate_num2 - 1) * i + j,
                nbit + dup_normal * (duplicate_num - 1) + (duplicate_num2 - 1) * i + j)] = W[(p[dup_normal + i], p[dup_normal + i])]
            mapping_normal2[i][j + 1] = nbit + dup_normal * (duplicate_num - 1) + (duplicate_num2 - 1) * i + j
    mapping2 = mapping_normal2.tolist()


    # single rule
    for i in range(dup_normal):
        v = W.get((p_normal[i], p_normal[i]))

        if v is None:
            continue
        r = rand_val(int(duplicate_num*(duplicate_num + 1)/2), v)
        cnt = 0
        for j in range(duplicate_num):
            W[(mapping1[i][j], mapping1[i][j])] = r[cnt]
            cnt += 1
            if cnt < int(duplicate_num*(duplicate_num + 1)/2):
                for k in range(j+1, duplicate_num):
                    W[(mapping1[i][j], mapping1[i][k])] = r[cnt]
                    cnt += 1

    for i in range(dup_normal2):
        v = W.get((p_normal2[i], p_normal2[i]))

        if v is None:
            continue
        r = rand_val(int(duplicate_num2*(duplicate_num2 + 1)/2), v)
        cnt = 0
        for j in range(duplicate_num2):
            W[(mapping2[i][j], mapping2[i][j])] = r[cnt]
            cnt += 1
            if cnt < int(duplicate_num2*(duplicate_num2 + 1)/2):
                for k in range(j+1, duplicate_num2):
                    W[(mapping2[i][j], mapping2[i][k])] = r[cnt]
                    cnt += 1

    # pair rule
    for x, y, v in qubo:
        if x == y:
            continue
        if x > y:
            x, y = y, x
        ix_normal, iy_normal = q_normal.get(x), q_normal.get(y)
        ix_normal2, iy_normal2 = q_normal2.get(x), q_normal2.get(y)
        if ix_normal is not None:
            if iy_normal is not None:
                r = rand_val(duplicate_num * duplicate_num, v)
                k = 0
                for i in range(duplicate_num):
                    for j in range(duplicate_num):
                        W[sort_pair(mapping1[ix_normal][i], mapping1[iy_normal][j])] = r[k]
                        k += 1

            else:
                r = rand_val(duplicate_num, v)
                for i in range(duplicate_num):
                    W[sort_pair(mapping1[ix_normal][i], y)] = r[i]

        elif iy_normal is not None:
            r = rand_val(duplicate_num, v)
            for i in range(duplicate_num):
                W[sort_pair(x, mapping1[iy_normal][i])] = r[i]


        if ix_normal2 is not None:
            if iy_normal2 is not None:
                r = rand_val(duplicate_num2 * duplicate_num2, v)
                k = 0
                for i in range(duplicate_num2):
                    for j in range(duplicate_num2):
                        W[sort_pair(mapping2[ix_normal2][i], mapping2[iy_normal2][j])] = r[k]
                        k += 1

            else:
                r = rand_val(duplicate_num2, v)
                for i in range(duplicate_num2):
                    W[sort_pair(mapping2[ix_normal2][i], y)] = r[i]

        elif iy_normal2 is not None:
            r = rand_val(duplicate_num2, v)
            for i in range(duplicate_num2):
                W[sort_pair(x, mapping2[iy_normal2][i])] = r[i]


        if ix_normal is not None:
            if iy_normal2 is not None:
                r = rand_val(duplicate_num * duplicate_num2, v)
                k = 0
                for i in range(duplicate_num):
                    for j in range(duplicate_num2):
                        W[sort_pair(mapping1[ix_normal][i], mapping2[iy_normal2][j])] = r[k]
                        k += 1

        if iy_normal is not None:
            if ix_normal2 is not None:
                r = rand_val(duplicate_num * duplicate_num2, v)
                k = 0
                for i in range(duplicate_num):
                    for j in range(duplicate_num2):
                        W[sort_pair(mapping1[iy_normal][i], mapping2[ix_normal2][j])] = r[k]
                        k += 1

    # 制約式を追加
    #ペナルティを設定
    if penalty is not None:
        penalty_setting = penalty
        for i in range(dup_normal):
            for j in range(duplicate_num - 1):
                W[sort_pair(mapping1[i][j], mapping1[i][j])] += penalty
                W[sort_pair(mapping1[i][j + 1], mapping1[i][j + 1])] += penalty
                W[sort_pair(mapping1[i][j], mapping1[i][j + 1])] -= 2 * penalty

        for i in range(dup_normal2):
            for j in range(duplicate_num2 - 1):
                W[sort_pair(mapping2[i][j], mapping2[i][j])] += penalty
                W[sort_pair(mapping2[i][j + 1], mapping2[i][j + 1])] += penalty
                W[sort_pair(mapping2[i][j], mapping2[i][j + 1])] -= 2 * penalty
    
    #ペナルティを自動的に計算
    else:
        penalty_setting = []
        adj = [[] for _ in range(nbit + (duplicate_num - 1) * dup_normal)]

        for (x, y), v in W.items():
            if x != y:
                adj[x].append(y)
                adj[y].append(x)

        for i in range(nbit):
            adj[i].sort()

        for i in range(dup_normal):
            dE = [0]*4
            if W[(mapping1[i][0], mapping1[i][0])] is not None:
                dE[0] = W[(mapping1[i][0], mapping1[i][0])]
                dE[2] = W[(mapping1[i][0], mapping1[i][0])]
            if W[(mapping1[i][1], mapping1[i][1])] is not None:
                dE[1] = W[(mapping1[i][1], mapping1[i][1])]
                dE[3] = W[(mapping1[i][1], mapping1[i][1])]
            
            # if flipping x0
            for j in range(len(adj[mapping1[i][0]])):
                if W[sort_pair(mapping1[i][0], adj[mapping1[i][0]][j])] > 0:
                    dE[0] += W[sort_pair(mapping1[i][0], adj[mapping1[i][0]][j])]
                elif W[sort_pair(mapping1[i][0], adj[mapping1[i][0]][j])] < 0:
                    dE[2] += W[sort_pair(mapping1[i][0], adj[mapping1[i][0]][j])]
            if W[(mapping1[i][0], mapping1[i][1])] < 0:
                dE[0] += W[(mapping1[i][0], mapping1[i][1])]
                dE[2] -= W[(mapping1[i][0], mapping1[i][1])]
            dE[0] = -dE[0]

            # if flipping x1
            for j in range(len(adj[mapping1[i][1]])):
                if W[sort_pair(mapping1[i][1], adj[mapping1[i][1]][j])] > 0:
                    dE[1] += W[sort_pair(mapping1[i][1], adj[mapping1[i][1]][j])]
                elif W[sort_pair(mapping1[i][1], adj[mapping1[i][1]][j])] < 0:
                    dE[3] += W[sort_pair(mapping1[i][1], adj[mapping1[i][1]][j])]
            if W[(mapping1[i][0], mapping1[i][1])] < 0:
                dE[1] += W[(mapping1[i][0], mapping1[i][1])]
                dE[3] -= W[(mapping1[i][0], mapping1[i][1])]
            dE[1] = -dE[1]

            penalty = abs(min(dE))

            for j in range(duplicate_num - 1):
                W[sort_pair(mapping1[i][j], mapping1[i][j])] += penalty
                W[sort_pair(mapping1[i][j + 1], mapping1[i][j + 1])] += penalty
                W[sort_pair(mapping1[i][j], mapping1[i][j + 1])] -= 2 * penalty
            
            penalty_setting.append(penalty)
     
    if solfile is None:
        pass
    else:
        with open(solfile, "rt") as s:
            solutionfile = json.load(s)
        solution = solutionfile.get('solution')
        for _ in range(dup_normal + dup_normal2):
            solution.append(0)
        for i in range(dup_normal):
            solution[mapping1[i][1]] = solution[mapping1[i][0]]
        for j in range(dup_normal2):
            solution[mapping2[j][1]] = solution[mapping2[j][0]]

    

    result = {'operation': 'bit duplication',
                'nbit': nbit + (duplicate_num - 1) * dup_normal + (duplicate_num2 - 1) * dup_normal2, 'base': 0,
                'duplicated_bits': dup_normal + dup_normal2}
    result['normal duplicated'] = p_normal
    result['normal2 duplicated'] = p_normal2
    result['penalty'] = penalty_setting
    result['mapping normal'] = mapping1
    result['mapping normal2'] = mapping2
    if solfile is not None:
        result['solution'] = solution
    result['qubo'] = []
    for x, y in sorted(W):
        if W[(x, y)] != 0:
            result['qubo'].append([x, y, int(W[(x, y)])])
    del problem['qubo']
    result['original'] = problem
    jsonString = re.sub('[\r\n]\s+(-{0,1}\d+)\s*',
                        '\\1', json.dumps(result, sort_keys=False, indent=4))
    # print(jsonString)
    with open(rf'{nbit}-{dup_normal + dup_normal2}-bit_duplication.json',
                'w') as obj:
        obj.write(jsonString)


if __name__ == "__main__":
    main()
