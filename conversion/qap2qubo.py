from collections import defaultdict
import argparse
import sys
import json
import re


class QAP:

    def __init__(self, filename: str) -> None:
        with open(filename, "rt") as f:
            lines = f.read()
            all = [int(x) for x in lines.split()]
            self.nsite = all[0]
            self.nbit = self.nsite*self.nsite
            self.A = []
            self.B = []
            for i in range(1, self.nbit, self.nsite):
                self.A.append(all[i:i+self.nsite])
                self.B.append(all[i+self.nbit:i+self.nsite+self.nbit])


class QUBO:

    def __init__(self, qap, penalty: int) -> None:
        self.qubo = defaultdict(int)
        self.nsite = qap.nsite
        self.nbit = qap.nbit
        self.maxval = 0
        for i in range(qap.nsite):
            for j in range(qap.nsite):
                for k in range(qap.nsite):
                    for l in range(qap.nsite):
                        # 場所iに工場jに置き，場所kに工場lに置く．A[i][j]:場所iと場所jの距離，B[k][l]工場kと工場lの物流量
                        val = qap.A[i][k] * qap.B[j][l] + \
                            qap.A[k][i] * qap.B[l][j]
                        if val!=0:
                            self.qubo[(i, j, k, l)] = val
                            if val > self.maxval:
                                self.maxval = val
        for i in range(qap.nsite):
            for j in range(qap.nsite):
                for k in range(qap.nsite):
                    for l in range(qap.nsite):
                        if i == k:
                            if j == l:
                                self.qubo[(i, j, k, l)] -= penalty #場所i==kに工場j==lを置くのは矛盾しない
                            else:
                                self.qubo[(i, j, k, l)] += penalty #場所i==kに工場j!=lを置くのは矛盾する．
                                self.qubo[(j, i, l, k)] += penalty #場所j!=lに工場i==lを置くのは矛盾する．

    def write(self) -> None:
        jsonQUBO = {}
        jsonQUBO['problem'] = 'QAP'
        jsonQUBO['nbit'] = self.nbit
        jsonQUBO['base'] = 0
        jsonQUBO['maxval'] = self.maxval
        jsonQUBO['qubo'] = [[index[0]*self.nsite+index[1], index[2]*self.nsite + index[3], val] for index,
                            val in sorted(self.qubo.items()) if index[0]*self.nsite+index[1] <= index[2]*self.nsite + index[3]]
        jsonString = re.sub('[\r\n]\s+(-{0,1}\d+)\s*',
                            '\\1', json.dumps(jsonQUBO, sort_keys=False, indent=4))
        #print(jsonString)
        with open(r'/home/xiaotian/QUBO_json/qap.json','w') as obj:
            obj.write(jsonString)


def main():
    parser = argparse.ArgumentParser(
        description='Convert QAP into QUBO problem instances')
    parser.add_argument('QAP', help='QAP File')
    parser.add_argument('-p', '--penalty', type=int,
                        required=True, help='Penalty value')
    args = parser.parse_args()
    qap = QAP(args.QAP)
    problem = QUBO(qap, args.penalty)
    problem.write()


if __name__ == "__main__":
    main()
