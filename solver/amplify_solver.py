from amplify import Solver
from amplify.client import FixstarsClient
from amplify import BinaryIntMatrix
import sys
import gzip
import argparse
import re
import tqdm
import json

class QUBO:

    def __init__(self, fname: str):
        """QUBOファイルの読み込み

        Args:
            fname (str): ファイル名
        """
        self.fname = fname
        """ファイル名
        """
        if fname.lower().endswith('.mm.gz'):
            try:
                file = gzip.open(fname, 'rt')
            except:
                print(f'Error: Cannot open {fname}.', file=sys.stderr)
                sys.exit(1)
            self.readMM(file)
        elif fname.lower().endswith('.mm'):
            try:
                file = open(fname, 'rt')
            except:
                print(f'Error: Cannot open {fname}.', file=sys.stderr)
                sys.exit(1)
            self.readMM(file)
        elif fname.lower().endswith('.json.gz'):
            try:
                file = gzip.open(fname, 'rt')
            except:
                print(f'Error: Cannot open {fname}.', file=sys.stderr)
                sys.exit(1)
            self.readJSON(file)
        elif fname.lower().endswith('.json'):
            try:
                file = open(fname, 'rt')
            except:
                print(f'Error: Cannot open {fname}.', file=sys.stderr)
                sys.exit(1)
            self.readJSON(file)
        else:
            print(f'Error: {fname} must be .mm or .mm.gz', file=sys.stderr)
            sys.exit(1)

    def readMM(self, file):
        m = re.match(r'(\d+)\s+(\d+)', file.readline())
        self.nbit = int(m.group(1))
        self.nelement = int(m.group(2))
        self.base = 1
        self.Q = {}
        self.BIM = BinaryIntMatrix(self.nbit)
        for i in tqdm.tqdm(range(self.nelement), desc='Reading', unit_scale=True):
            x, y, w = map(lambda x: int(x), file.readline().split())
            self.Q[(x, y)] = w
            self.BIM[x-1, y-1] = w

    def readJSON(self, file):
        jsonData = json.load(file)
        self.nbit = jsonData['nbit']
        self.nelement = len(jsonData['qubo'])
        self.base = jsonData.get('base')
        self.BIM = BinaryIntMatrix(self.nbit)
        if self.base is None:
            self.base = 0
        self.Q = {(x, y): w for x, y, w in jsonData['qubo']}
        for x, y, w in jsonData['qubo']:
            self.BIM[x-self.base, y-self.base] = w

    def energy(self, solution):
        return sum([solution[x-self.base]*solution[y-self.base]*self.Q[(x, y)] for x, y in self.Q.keys()])


def main():
    parser = argparse.ArgumentParser(description='QUBO solver using D-Wave')
    parser.add_argument(
        'QUBOfile', help='QUBO file (mm/mm.gz or json/json.gz)')
    parser.add_argument('-o', '--output', default='result.json',
                        help='Soution file to be output')
    parser.add_argument('-t', '--time_limit', type=int, default=1,
                        help='Maximum run time in seconds')

    args = parser.parse_args()

    output = args.output
    time_limit = args.time_limit

    inst = QUBO(args.QUBOfile)

    client = FixstarsClient()  # Fixstars Option
    client.parameters.timeout = time_limit*1000
    client.token = "4IPdS3AVxB4WYnahcwMygcWYj5S9T4CI" #ライセンスを入力


    solver = Solver(client)
    solver.sort_solution = True
    solver.deduplicate = False
    result = solver.solve(inst.BIM)
    first =result[0]
    solution = [first.values[i] for i in sorted(first.values)]

    JSONdata = {}
    JSONdata['solver'] = 'Amplify'
    JSONdata['nbit'] = inst.nbit
    JSONdata['time_limit'] = time_limit
    JSONdata['energy'] = first.energy
    JSONdata['energy_computed'] = inst.energy(solution)
    JSONdata['solution'] = solution
    resultString = re.sub('[\r\n]\s+(-{0,1}\d+)\s*',
                          '\\1', json.dumps(JSONdata, sort_keys=False, indent=4))

    with open(output, 'wt') as f:
        print(resultString, file=f)

    print(resultString)


if __name__ == "__main__":
    main()
