from dwave.samplers import SimulatedAnnealingSampler
import argparse
import re
import tqdm
import json
import time
import sys
import gzip


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
        for i in tqdm.tqdm(range(self.nelement), desc='Reading', unit_scale=True):
            x, y, w = map(lambda x: int(x), file.readline().split())
            self.Q[(x, y)] = w

    def readJSON(self, file):
        jsonData = json.load(file)
        self.nbit = jsonData['nbit']
        self.nelement = len(jsonData['qubo'])
        self.base = jsonData.get('base')
        if self.base is None:
            self.base = 0

        self.Q = {(x, y): w for x, y, w in jsonData['qubo']}

    def energy(self, solution):
        return sum([solution[x-self.base]*solution[y-self.base]*self.Q[(x, y)] for x, y in self.Q.keys()])

def main():
    parser = argparse.ArgumentParser(description='QUBO solver using D-Wave Sampler with SA')
    parser.add_argument(
        'QUBOfile', help='QUBO file (mm/mm.gz or json/json.gz)')
    parser.add_argument('-o', '--output', default='result.json',
                        help='Solution file to be output')
    parser.add_argument('-n', '--num_reads', default=1, type=int, help='num_reads')

    args = parser.parse_args()
    output = args.output
    num_reads = args.num_reads

    qubo = QUBO(args.QUBOfile)

    sampler = SimulatedAnnealingSampler()
    start = time.time()
    response = sampler.sample_qubo(qubo.Q, num_reads=num_reads)
    end = time.time()
    best_sample = response.first.sample
    energies = response.data_vectors['energy']
    best_energy = min(energies)


    #solution = [int(i) for i in list(result.first.sample.values())]
    solution = [int(best_sample[var]) for var in best_sample]
    JSONdata = {}
    JSONdata['solver'] = 'D-Wave Sampler with SA'
    JSONdata['nbit'] = qubo.nbit
    JSONdata['num_reads']=num_reads
    JSONdata['time']=end-start
    JSONdata['energies']=sorted(energies)
    JSONdata['energy'] = int(best_energy)
    JSONdata['solution'] = solution
    resultString = re.sub('[\r\n]\s+(-{0,1}\d+)\s*',
                          '\\1', json.dumps(JSONdata, sort_keys=False, indent=4))
    
    with open(output, 'wt') as f:
        print(resultString, file=f)

    print(resultString)

if __name__ == "__main__":
    main()
