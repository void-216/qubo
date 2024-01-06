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
    random.seed(0)
    parser = argparse.ArgumentParser(
        description='Randomly shuffle all elemnets of QUBO problems')
    parser.add_argument(
        '-Q', '--QUBOfile', help='QUBO problem file. must be .json/.json.gz. stdin if omitted')
    parser.add_argument('-s', '--seed', type=int,
                        default=0, help='Random seed')
    args = parser.parse_args()
    random.seed(args.seed)

    if args.QUBOfile is None:
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

    p = list(rand_select(nbit))
    W = {(p[x-base], p[y-base]): v for x, y, v in qubo}

    result = {'operation': 'bit shuffle',
              'nbit': nbit, 'base': 0}
    result['mapping'] = p
    result['qubo'] = []
    for x, y in sorted(W):
        if W[(x, y)] != 0:
            result['qubo'].append([x, y, int(W[(x, y)])])
    del problem['qubo']
    result['original'] = problem
    jsonString = re.sub('[\r\n]\s+(-{0,1}\d+)\s*',
                        '\\1', json.dumps(result, sort_keys=False, indent=4))
    #print(jsonString)
    with open(rf'{nbit}-shuffle.json', 'w') as obj:
        obj.write(jsonString)


if __name__ == "__main__":
    main()
