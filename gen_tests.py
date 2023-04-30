import argparse
import subprocess

from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('-t', '--tps', type=int, nargs='+', required=True)
parser.add_argument('-n', '--n_validators', type=int, nargs='+', required=True)
parser.add_argument('-d', '--delay', type=str, required=True)
parser.add_argument('-j', '--jitter', type=str, required=True)
parser.add_argument('-r', '--rate', type=str, required=True)
parser.add_argument('-c', '--cpu_limit', type=str, required=True)
parser.add_argument('-a', '--algos', type=str, nargs='+', required=True)
parser.add_argument('-o', '--output_dir', type=Path)
args = parser.parse_args()


def generate_name(args):
    joined_n = ','.join(map(lambda x: str(x), args.n_validators))
    joined_tps = ','.join(map(lambda x: str(x), args.tps))
    joined_algos = ','.join(args.algos)
    
    return f'_{joined_algos}_n={joined_n}_tps={joined_tps}_net=d{args.delay}-j{args.jitter}-{args.rate}'


if __name__ == "__main__":
    print(args)
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
                    '-d', args.delay,
                    '-j', args.jitter,
                    '-r', args.rate,
                    '--cpu', args.cpu_limit,
                    '--ip', '172.16.239.',
                    '--disable-query'
                ]
                subprocess.run(x)

    # copy runner/fetcher scripts
    full_output_dir = Path('./generator') / output_dir
    subprocess.run(['cp', './generator/templates/batch_testing/fetch_results.py', full_output_dir])
    subprocess.run(['cp', './generator/templates/batch_testing/runner.py', full_output_dir])
