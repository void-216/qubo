import random
import argparse
import json
import re
import sys
import gzip
from collections import defaultdict


def errorExit(s: str):
    """エラーメッセージを表示して強制終了

    Args:
        s (str): 表示するエラーメッセージ
    """
    print(s, file=sys.stderr)
    sys.exit(1)


def rand_select(nbit: int, s=-1):
    if s == -1:
        s = nbit
    pool = list(range(nbit))
    for i in range(s):
        j = random.randrange(nbit-i)
        yield pool[j]
        pool[j] = pool[nbit-i-1]


def main():

    parser = argparse.ArgumentParser(
        description='Convert a QUBO problem by flipping bits')
    parser.add_argument(
        '-Q', '--QUBOfile', help='QUBO problem file. must be .json/.json.gz. stdin if omitted')
    parser.add_argument('-r', '--ratio', type=str, required=True,
                        help='# of flipping bits if integer flip ratio if float')
    parser.add_argument('-s', '--seed', type=int,
                        default=0, help='Random seed')

    args = parser.parse_args()
    random.seed(args.seed)
    QUBOfile = args.QUBOfile
    if args.ratio.isdecimal():
        flip = int(args.ratio)
    else:
        flip = float(args.ratio)

    if QUBOfile is None:
        qubofile = sys.stdin
    elif re.search('.json.gz$', QUBOfile, flags=re.IGNORECASE) is not None:
        qubofile = gzip.open(QUBOfile, 'rt')
    elif re.search('.json$', QUBOfile, flags=re.IGNORECASE) is not None:
        qubofile = open(QUBOfile, 'rt')
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


    if isinstance(flip, float):
        flip = int(flip*nbit)

    adj = [[] for _ in range(nbit)]  # 隣接リスト

    W = defaultdict(int)
    for x, y, v in qubo:  # 隣接リストの作成．自分自身は含まない
        W[(x-base, y-base)] = v
        if x != y:
            adj[x-base].append(y-base)
            adj[y-base].append(x-base)

    for i in range(nbit):
        adj[i].sort()

    offset = 0

    flist = list(rand_select(nbit, flip))
    flist.sort()

    for x in flist:  # x番目のビットをフリップ
        v = W[(x, x)]  # W_{x,x}(1-X)= W_{x,x}-W_{x,x}X
        offset += v  # 定数W_{x,x}
        W[(x, x)] = -v  # -W_{x,x}を新たにW_{x,x}とする．
        for y in adj[x]:
            if x < y:
                # W_{x,y}(1-X_x) X_y = W_{x,y}X_y - W_{x,y}X_x X_y
                v = W[(x, y)]
                W[(x, y)] = -v  # -W_{x,y}X_x X_y (代入)
                W[(y, y)] += v  # W_{x,y}X_y (加算)
            else:
                v = W[(y, x)]
                W[(y, x)] = -v
                W[(y, y)] += v

    result = {'operation': 'bit flipping',
              'nbit': nbit, 'base': 0, 'offset': offset}
    result['flipped'] = flist
    result['qubo'] = []
    for x, y in sorted(W):
        if W[(x, y)] != 0:
            result['qubo'].append([x, y, int(W[(x, y)])])
    del problem['qubo']
    result['original'] = problem
    jsonString = re.sub('[\r\n]\s+(-{0,1}\d+)\s*',
                        '\\1', json.dumps(result, sort_keys=False, indent=4))
    #print(jsonString)
    with open(rf'{nbit}-{flip}-flip.json', 'w') as obj:
        obj.write(jsonString)


if __name__ == "__main__":
    main()
