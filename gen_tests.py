import argparse
import subprocess

from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('-t', '--tps', type=int, nargs='+', required=True)
parser.add_argument('-n', '--n_validators', type=int, nargs='+', required=True)
parser.add_argument('-c', '--cpu_limit', type=str, required=True)
parser.add_argument('-a', '--algos', type=str, nargs='+', required=True)
parser.add_argument('-d', '--delay', type=str)
parser.add_argument('-j', '--jitter', type=str)
parser.add_argument('-r', '--rate', type=str)
parser.add_argument('-o', '--output_dir', type=Path)
args = parser.parse_args()


def generate_name(args):
    joined_n = ','.join(map(lambda x: str(x), args.n_validators))
    joined_tps = ','.join(map(lambda x: str(x), args.tps))
    joined_algos = ','.join(args.algos)
    
    name = f'_{joined_algos}_n={joined_n}_tps={joined_tps}'
    if args.delay or args.jitter or args.rate:
        name += '_net='
    if args.delay:
        name += f'd{args.delay}'
    if args.jitter:
        name += f'j{args.delay}'
    if args.rate:
        name += f'r{args.delay}'
    
    return name


if __name__ == "__main__":
    if args.output_dir is None:
        output_dir = generate_name(args)
    else:
        output_dir = str(args.output_dir)   

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
                    x.extend(['-d', args.delay])
                if args.jitter:
                    x.extend(['-j', args.jitter])
                if args.rate:
                    x.extend(['-r', args.rate])
                subprocess.run(x)

    # copy runner/fetcher scripts
    full_output_dir = Path('./generator') / output_dir
    subprocess.run(['cp', './generator/templates/batch_testing/fetch_results.py', full_output_dir])
    subprocess.run(['cp', './generator/templates/batch_testing/runner.py', full_output_dir])
