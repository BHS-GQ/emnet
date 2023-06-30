
import os
import shutil
import argparse
import pandas as pd
import matplotlib.pyplot as plt

from constants import *
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('-t', '--target', type=Path, required=True)
parser.add_argument('-k', '--test_kind', type=str, required=True)
args = parser.parse_args()

PLOTS_DIR = args.target / 'plots'
if os.path.exists(PLOTS_DIR):
    shutil.rmtree(PLOTS_DIR, ignore_errors=True)
os.makedirs(PLOTS_DIR)


def get_grouped_df(df: pd.DataFrame):
    _df = df.copy().groupby(TEST_ID_COLS)

    df_out = _df[['Throughput (TPS)', 'neto_total_mb', 'Avg Latency (s)', 'cpu_max_all', 'cpu_max_avg_all']].agg(
        tput_max=('Throughput (TPS)', 'max'),
        tput_mean=('Throughput (TPS)', 'mean'),
        tput_all=('Throughput (TPS)', lambda x: list(x)),
        tput_std=('Throughput (TPS)', 'std'),
        neto_mean=('neto_total_mb', 'mean'),
        neto_all=('neto_total_mb', lambda x: list(x)),
        neto_std=('neto_total_mb', 'std'),
        lat_mean=('Avg Latency (s)', 'mean'),
        lat_all=('Avg Latency (s)', lambda x: list(x)),
        cpu_max_avg=('cpu_max_all', 'mean'),
        cpu_max_avg_avg=('cpu_max_avg_all', 'mean'),
    ).reset_index()

    return df_out


def make_lineplot(
    df: pd.DataFrame,
    groupby_cols: list,

    ax,
    x_col: str,
    x_label: str,
    y_col: str,
    y_label: str,

    transaction_type: str,
    img_fname: str,

    x_range: list = None,
    y_range: list = None,

    boxplot: bool = False,
):
    _df = df.copy()
    _dft = _df.loc[_df['Name'] == transaction_type]

    main_grp = groupby_cols[0]
    for key, grp in _dft.groupby(groupby_cols):
        grp = grp.sort_values(by=[x_col])
        main_key = key[0]

        if y_range:
            ax.set_ylim(y_range)

        ax.plot(
            grp[x_col],
            grp[y_col],
            linewidth=1,
            markerfacecolor='none',
            label=f"{key[0]}",
            **PLOT_DESIGNS[main_grp][main_key]
        )

        if boxplot:
            color = PLOT_DESIGNS[main_grp][main_key]['color']
            if '_mean' not in y_col:
                raise Exception(f'Cannot generate boxplot from {y_col}')
            y_col_all = f'{y_col.split("_")[0]}_all'
            ax.boxplot(
                grp[y_col_all],
                positions=grp[x_col].values,
                sym='k+',
                showfliers=False,
                showmeans=False,
                patch_artist=True,
                boxprops=dict(facecolor=color, alpha=0.5),
                zorder=1
            )

    ax.set_title(f'{x_label} vs. {y_label} of {transaction_type}')
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.title.set_size(11)

if __name__ == "__main__":
    df_raw = pd.read_csv(args.target / CSV_NAME)
    df = get_grouped_df(df_raw)
    df = df[df['tput_all'].map(len) >= 2]
    df['cpu_max_avg'] = df['cpu_max_avg'].div(100)

    for ttype in ['open', 'query', 'transfer']:
        fig, ax = plt.subplots(4, 1, figsize=(5, 10))
        idx = 0
        # ijcombs = [(0,0), (0,1), (1,0), (1,1)]
        for key, kwargs in PLOT_KWARGS[args.test_kind].items():
            print(f'Processing {args.test_kind} {ttype} {key}')
            kwargs['df'] = df
            # i, j =ijcombs[idx]
            make_lineplot(ax=ax[idx], transaction_type=ttype, **kwargs)
            if idx == 0:
                ax[0].legend()
            idx += 1
        plt.subplots_adjust(hspace=0.5)
        img_path = PLOTS_DIR / f'{ttype}.png'
        plt.savefig(img_path, bbox_inches='tight')