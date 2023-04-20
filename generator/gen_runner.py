import argparse
import os
import stat

from glob import glob
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('-t', '--test-dir', type=Path, required=True)
parser.add_argument('-d', '--delay', type=int, required=True)
parser.add_argument('-j', '--jitter', type=int, required=True)
parser.add_argument('-r', '--rate', type=str, required=True)
args = parser.parse_args()

if __name__ == "__main__":
    lines = []
    for test_dir in glob(f'{args.test_dir}/*'):
        if not os.path.isdir(test_dir):
            continue

        test_dir_name = Path(test_dir).name
        line = f'(cd "{test_dir_name}" && ./test.sh {args.delay} {args.jitter} "{args.rate}")\n'
        lines.append(line)
        line = 'sleep 1\n'
        lines.append(line)
    
    runner_file = args.test_dir / 'runner.sh'
    with open(runner_file, 'w') as f:
        f.writelines(lines)

    st = os.stat(runner_file)
    os.chmod(runner_file, st.st_mode | stat.S_IEXEC)
