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
    # runner.sh test runner
    lines = ['docker system prune -f; sleep 2\n']
    valglob = sorted(glob(f'{args.test_dir}/*'))
    for test_dir in valglob:
        if not os.path.isdir(test_dir):
            continue

        test_dir_name = Path(test_dir).name
        line = f'(cd "{test_dir_name}" && ./test.sh {args.delay} {args.jitter} "{args.rate}")\n'
        lines.append(line)
        line = 'docker system prune -f; sleep 10\n'
        lines.append(line)
    
    runner_file = args.test_dir / 'runner.sh'
    with open(runner_file, 'w') as f:
        f.writelines(lines)
    
    st = os.stat(runner_file)
    os.chmod(runner_file, st.st_mode | stat.S_IEXEC)

    # report_fetcher.sh report.html fetcher
    lines = ['mkdir $1\n']
    valglob = sorted(glob(f'{args.test_dir}/*'))
    for test_dir in valglob:
        if not os.path.isdir(test_dir):
            continue

        test_dir = Path(test_dir)
        test_dir_name = test_dir.name
        new_name = f'{test_dir_name}.html'
        line = f'cp "{test_dir_name}/*.html" "$1/"\n'
        lines.append(line)

    fetcher_file = args.test_dir / 'report_fetcher.sh'
    with open(fetcher_file, 'w') as f:
        f.writelines(lines)

    st = os.stat(fetcher_file)
    os.chmod(fetcher_file, st.st_mode | stat.S_IEXEC)

    # logs_fetcher.sh
    lines = ['mkdir -p $1\nmkdir $1/logs\n']
    valglob = sorted(glob(f'{args.test_dir}/*'))
    for test_dir in valglob:
        if not os.path.isdir(test_dir):
            continue

        test_dir = Path(test_dir)
        test_dir_name = test_dir.name
        new_name = f'{test_dir_name}'
        line = f'mkdir "$1/logs/{new_name}/"\n'
        lines.append(line)
        line = f'cp {test_dir_name}/logs/quorum/*.log $1/logs/{new_name}/\n'
        lines.append(line)
    lines.append(
        '(cd $1 && tar -czvf logs.tar.gz $1/logs && rm -rf $1/logs)'
    )

    fetcher_file = args.test_dir / 'logs_fetcher.sh'
    with open(fetcher_file, 'w') as f:
        f.writelines(lines)

    st = os.stat(fetcher_file)
    os.chmod(fetcher_file, st.st_mode | stat.S_IEXEC)
