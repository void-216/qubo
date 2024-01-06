import gurobipy as gp
from gurobipy import GRB
import argparse
import re
import json
import gzip
import sys

def errorExit(message:str):
    print(message, file=sys.stderr)
    sys.exit(1)    


parser = argparse.ArgumentParser(description='QUBO solver using Gurobi')
parser.add_argument('-m', '--mip_focus', default=1,
                    type=int, help='MIPFocus value')
parser.add_argument('-t', '--time_limit',
                    type=int, help='Time Limit')
parser.add_argument('-T', '--threads',
                    type=int, help='maximum thread count')
parser.add_argument('-p', '--lp', type=str, help='LP file to be written')
parser.add_argument('-o', '--output', type=str,
                    help='Solution (JSON) file to be written')
parser.add_argument('-l', '--log', type=str, help='LOG file to be written')
parser.add_argument('QUBO', help='QUBO problem JSON file')

args = parser.parse_args()

if args.QUBO is None:
    errorExit('QUBO problem file is missing')
if re.search('.json.gz$', args.QUBO, flags=re.IGNORECASE) is not None:
    file = gzip.open(args.QUBO, 'rt')
elif re.search('.json$', args.QUBO, flags=re.IGNORECASE) is not None:
    file = open(args.QUBO, 'rt')
else:
    errorExit('QUBO problem must be .json or .json.gz')

try:
    problem = json.load(file)
except:
    errorExit('QUBO file cannot be read as a JSON file')

nbit = problem.get('nbit')
if nbit is None:
    errorExit('<nbit> is missing')
qubo = problem.get('qubo')
if qubo is None:
    errorExit('<nbit> is missing')
base = problem.get('base')
if base is None:
    base = 0

env = gp.Env()
if args.log is not None:
    env.setParam('LogFile', args.log)
env.setParam('MIPFocus', args.mip_focus)
if args.time_limit is not None:
    env.setParam('TimeLimit', args.time_limit)
if args.threads is not None:
    env.setParam('Threads', args.threads)

model = gp.Model(env=env, name='QUBO')

x = model.addVars(nbit, vtype=GRB.BINARY, name='x')

model.setObjective(gp.quicksum(val * x[i-base] * x[j-base]
                   for i, j, val in qubo), sense=gp.GRB.MINIMIZE)

if args.lp is not None:
    model.write(args.lp)

model.optimize()

result = {}
result['nbit'] = nbit
result['energy'] = int(model.ObjVal)
#result['bound'] = int(model.ObjBound)
result['mipgap'] = model.MIPGap
result['runtime'] = model.RunTime
if args.time_limit:
    result['time_limit'] = args.time_limit
if args.threads:
    result['threads'] = args.threads
result['solcount'] = model.SolCount
result['GRB.OPTIMAL'] = gp.GRB.OPTIMAL
result['solution'] = [int(v.X) for v in model.getVars()]
jsonString = re.sub('[\r\n]\s*(-{0,1}\d+)\s*',
                    '\\1', json.dumps(result, sort_keys=False, indent=4))
if args.output:
    with open(args.output, 'wt') as f:
        print(jsonString, file=f)
else:
    print(jsonString)
