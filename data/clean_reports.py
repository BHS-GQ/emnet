import glob
import os
import argparse
import shutil
import pandas as pd
import matplotlib.pyplot as plt

from copy import deepcopy
from pathlib import Path
from bs4 import BeautifulSoup

parser = argparse.ArgumentParser()
parser.add_argument('-d', '--input-dir', type=Path, required=True)
parser.add_argument('-x', '--x-lim', type=int, required=True)
parser.add_argument('-y', '--y-lim', type=int, required=True)
parser.add_argument('-s', '--show', action='store_true')
args = parser.parse_args()


ADDITIONAL_HEADERS=['consensus', 'n']
FILE_DIR = os.path.dirname(os.path.realpath(__file__))
INPUT_DIR = Path(f'{FILE_DIR}/{args.input_dir}')
OUTPUT_DIR = INPUT_DIR / 'cleaned'

if os.path.exists(OUTPUT_DIR):
    shutil.rmtree(OUTPUT_DIR, ignore_errors=True)

os.makedirs(OUTPUT_DIR)


def get_headers(path):
    with open(path, "r") as f:
        soup = BeautifulSoup(f, "html.parser")

    summary = soup.find(id="benchmarksummary").table

    headers = [header.text for header in summary.find_all('th')]

    return headers


def get_rows(path):
    with open(path, "r") as f:
        soup = BeautifulSoup(f, "html.parser")

    summary = soup.find(id="benchmarksummary").table

    rows = []
    for row in summary.find_all('tr'):
        rows.append([val.text for val in row.find_all('td')])

    return rows


def main(args):
    flag = False
    headers = deepcopy(ADDITIONAL_HEADERS)
    rows = []
    for path in glob.glob(f'{INPUT_DIR}/*.html'):
        print(path)
        path = Path(path)
        if not flag:
            headers.extend(get_headers(path))
            flag = True


        filename = path.name
        tmp = filename.split("_")
        prepend = [tmp[0], tmp[1].split('=')[-1]]
        raw_rows = get_rows(path)
        del(raw_rows[0])
        rows.extend([prepend + row for row in raw_rows])


    df_raw = pd.DataFrame(rows, columns=headers)
    df_raw['Send Rate (TPS)']=df_raw['Send Rate (TPS)'].astype(float)
    df_raw['Throughput (TPS)']=df_raw['Throughput (TPS)'].astype(float)
    df_raw['Avg Latency (s)']=df_raw['Avg Latency (s)'].astype(float)
    df_raw['n']=df_raw['n'].astype(int)
    csv_path = OUTPUT_DIR / 'compiled.csv'
    df_raw.to_csv(csv_path)

    PLOT_DESIGNS = {
        'consensus': {        
            'hotstuff': {'color': 'cornflowerblue'},
            'ibft': {'color': 'orange'},
            'qbft': {'color': 'orangered'}
        },
        'n': {
            4: {'marker': 'o', 'ls': 'solid'},
            8: {'marker': 'x', 'ls': 'dashed'},
            12: {'marker': '^', 'ls': ':'},
            16: {'marker': 'd', 'ls': 'dashdot'}
        }
    }

    transaction_types = ['open', 'query', 'transfer']
    for transaction_type in transaction_types:
        df = df_raw.copy()
        df = df.loc[df['Name'] == transaction_type]
        fig, ax = plt.subplots(figsize=(10,8))
        ax.set_xlim([0, args.x_lim])
        ax.set_ylim([0, args.y_lim])
        for key, grp in df.groupby(['consensus', 'n']):
            ax.plot(
                grp['Send Rate (TPS)'],
                grp['Throughput (TPS)'],
                color=PLOT_DESIGNS['consensus'][key[0]]['color'],
                marker=PLOT_DESIGNS['n'][key[1]]['marker'],
                linestyle=PLOT_DESIGNS['n'][key[1]]['ls'],
                linewidth=1,
                label=f"{key[0]}_{key[1]}"
            )
        ax.set_title(f'Send Rate (TPS) vs. Throughput (ms) of {transaction_type}')
        ax.set_xlabel('Send Rate (TPS)')
        ax.set_ylabel('Throughput (TPS)')

        ax.legend()
        img_path = OUTPUT_DIR / f'throughput_{transaction_type}.png'
        plt.savefig(img_path)
        if args.show:
            plt.show()
    for transaction_type in transaction_types:
        df = df_raw.copy()
        df = df.loc[df['Name'] == transaction_type]
        fig, ax = plt.subplots(figsize=(10,8))
        for key, grp in df.groupby(['consensus', 'n']):
            ax.plot(
                grp['Send Rate (TPS)'],
                grp['Avg Latency (s)'],
                color=PLOT_DESIGNS['consensus'][key[0]]['color'],
                marker=PLOT_DESIGNS['n'][key[1]]['marker'],
                linestyle=PLOT_DESIGNS['n'][key[1]]['ls'],
                linewidth=1,
                label=f"{key[0]}_{key[1]}"
            )
        ax.set_title(f'Send Rate (TPS) vs. Latency (TPS) of {transaction_type}')
        ax.set_xlabel('Send Rate (TPS)')
        ax.set_ylabel('Avg Latency (s)')

        ax.legend()
        img_path = OUTPUT_DIR / f'latency_{transaction_type}.png'
        plt.savefig(img_path)
        if args.show:
            plt.show()

if __name__ == "__main__":
    main(args)
