import argparse
import subprocess

from copy import deepcopy
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('-t', '--tps', type=int, nargs='+', required=True)
parser.add_argument('-n', '--n_validators', type=int, nargs='+', required=True)
parser.add_argument('-c', '--cpu_limit', type=str, required=True)
parser.add_argument('-a', '--algos', type=str, nargs='+', required=True)
parser.add_argument('-d', '--delay', type=int, nargs='+')
parser.add_argument('-j', '--jitter', type=str, nargs='+')
parser.add_argument('-r', '--rate', type=str, nargs='+')
parser.add_argument('-o', '--output_dir', type=Path)
args = parser.parse_args()

def joined_arg(arg):
    return ','.join(map(lambda x: str(x), arg))

def generate_name(args):

    joined_n = joined_arg(args.n_validators)
    joined_tps = joined_arg(args.tps)
    joined_algos = ','.join(args.algos)

    name = f'_{joined_algos}_n={joined_n}_tps={joined_tps}'
    if args.delay or args.jitter or args.rate:
        name += '_net='
    if args.delay:
        joined_delay = joined_arg(args.delay)
        name += f'd{joined_delay}'
    if args.jitter:
        joined_jitter = ','.join(args.jitter)
        name += f'j{joined_jitter}'
    if args.rate:
        joined_rate = ','.join(args.rate)
        name += f'r{joined_rate}'
    
    return name


if __name__ == "__main__":
    if args.output_dir is None:
        output_dir = generate_name(args)
    else:
        output_dir = str(args.output_dir)   

    n_tests = (
        len(args.n_validators) *
        len(args.algos) *
        len(args.tps)
    )
    if args.delay:
        n_tests *= len(args.delay)
    if args.rate:
        n_tests *= len(args.rate)

    print(f'Generating {n_tests} tests...')

    for n in args.n_validators:
        for algo in args.algos:
            for tps in args.tps:
                x = [
                    'python3',
                    '-m', 'generator.gen_network',
                    '-c', algo,
                    '-o', output_dir,
                    '-t', str(tps),
                    '-n', str(n),
                    '--cpu', args.cpu_limit,
                    '--ip', '172.16.239.',
                    '--disable-query'
                ]
                if args.delay:
                    for delay in args.delay:
                        x_net = deepcopy(x)
                        x_net.extend(['-d', str(delay)])
                        subprocess.run(x_net)
                elif args.rate:
                    for rate in args.rate:
                        x_net = deepcopy(x)
                        x_net.extend(['-r', rate])
                        subprocess.run(x_net)
                else:
                    subprocess.run(x)

    # copy runner/fetcher scripts
    full_output_dir = Path('./generator') / output_dir
    subprocess.run(['cp', './generator/templates/batch_testing/fetch_results.py', full_output_dir])
    subprocess.run(['cp', './generator/templates/batch_testing/runner.py', full_output_dir])
