import subprocess
import os
import argparse

from glob import glob
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('-o', '--output', type=Path, required=True)
args = parser.parse_args()

PWD = Path(__file__).parent
ALL_RESULTS_DIR = PWD / args.output


if __name__ == "__main__":
    # Make output dir
    if not os.path.exists(ALL_RESULTS_DIR):
        os.makedirs(ALL_RESULTS_DIR)
    else:
        raise Exception('Results dir already exists!')

    report_dirs = glob('./*/report_*')
    for report_dir in report_dirs:
        x = ['cp', '--parents', '-r', report_dir, ALL_RESULTS_DIR]
        subprocess.run(x)
