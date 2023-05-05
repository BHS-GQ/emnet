import pandas as pd
import matplotlib.pyplot as plt
import json
import argparse
import os
import shutil

from glob import glob
from copy import deepcopy
from pathlib import Path
from bs4 import BeautifulSoup


parser = argparse.ArgumentParser()
parser.add_argument('-t', '--target', type=Path, required=True)
args = parser.parse_args()

TEST_DIR = args.target
TEST_ID_COLS = ['Name', 'n', 'algo', 'tps_param', 'cpu_limit', 'delay', 'rate_limit']
PLOT_DESIGNS = {
    'algo': {        
        'hotstuff': {'color': 'tab:blue', 'marker': 'o', 'ls': 'solid'},
        'ibft': {'color': 'tab:green', 'marker': 'x', 'ls': 'dashed'},
        'qbft': {'color': 'tab:orange', 'marker': '^', 'ls': ':'}
    },
    'n': {
        4: {'marker': 'o', 'ls': 'solid'},
        8: {'marker': 'x', 'ls': 'dashed'},
        12: {'marker': '^', 'ls': ':'},
        16: {'marker': 's', 'ls': 'dashdot'}
    }
}


def compile_reports():
    dfs = []
    result_dirs = glob(f'{str(TEST_DIR.resolve())}/*/report_*/')
    for result_dir in result_dirs:
        print(f'Processing {result_dir}...')
        rd_path = Path(result_dir)
        result_idx = rd_path.name.split('_')[-1]
        report_file = rd_path / 'report.html'
        params_file = rd_path / 'params.json'

        with open(report_file, 'r') as f:
            soup = BeautifulSoup(f, "html.parser")
        with open(params_file, 'r') as f:
            test_params = json.load(f)

        # Process results
        summary = soup.find(id="benchmarksummary").table
        df = pd.read_html(str(summary))[0]

        to_numeric_cols = [
            'CPU%(avg)',
            'CPU%(max)',
            'Traffic In [MB]',
            'Traffic Out [MB]',
        ]
        tables = soup.findAll("table")
        
        has_open = False
        has_trans = False
        new_cols: dict = {
            'cpu%_max_all': [],
            'cpu%_max_avg_all': [],
            'neti_total_mb': [],
            'neto_total_mb': [],
            'n': [],
            'algo': [],
            'tps_param': [],
            'cpu_limit': [],
            'delay': [],
            'rate_limit': [],
            'r_idx': [],
        }
        rate_limit_convert = {
            '5mbit': 5,
            '10mbit': 10,
            '25mbit': 25,
            '2500kbit': 2.5,
            '5000kbit': 5,
            '10000kbit': 10,
            '15000kbit': 15,
            '20000kbit': 20,
            '25000kbit': 25,
        }
        if len(tables) < 4:
            print('Failed open!')
        else:
            has_open = True

            df_open_perf = pd.read_html(str(tables[3]))[0]
            df_open_perf[to_numeric_cols] = df_open_perf[to_numeric_cols].apply(pd.to_numeric, errors='coerce', axis=1)
            new_cols['cpu%_max_all'].append(df_open_perf['CPU%(max)'].max())
            new_cols['cpu%_max_avg_all'].append(df_open_perf['CPU%(avg)'].max())

            open_i_sum = df_open_perf.loc[df_open_perf['Name'] != '/nginx', 'Traffic Out [MB]'].sum()
            new_cols['neti_total_mb'].append(open_i_sum)

            open_o_sum = df_open_perf.loc[df_open_perf['Name'] != '/nginx', 'Traffic Out [MB]'].sum()
            new_cols['neto_total_mb'].append(open_o_sum)

            new_cols['n'].append(test_params['N_VALIDATORS'])
            new_cols['algo'].append(test_params['CONSENSUS_ALGO'])
            new_cols['tps_param'].append(int(test_params['TPS']))
            new_cols['cpu_limit'].append(test_params['CPU_LIMIT'])
            new_cols['r_idx'].append(result_idx)
            if 'PUMBA_DELAY' in test_params:
                new_cols['delay'].append(test_params['PUMBA_DELAY'])
            else:
                new_cols['delay'].append(None)
            if 'PUMBA_RATE' in test_params:
                rate_limit_converted = rate_limit_convert[test_params['PUMBA_RATE']]
                new_cols['rate_limit'].append(rate_limit_converted)
            else:
                new_cols['rate_limit'].append(None)

        if len(tables) < 7:
            print('Failed transfer!')
        else:
            has_trans = True

            df_trans_perf = pd.read_html(str(tables[6]))[0]
            df_trans_perf[to_numeric_cols] = df_trans_perf[to_numeric_cols].apply(pd.to_numeric, errors='coerce', axis=1)

            new_cols['cpu%_max_all'].append(df_trans_perf['CPU%(max)'].max())
            new_cols['cpu%_max_avg_all'].append(df_trans_perf['CPU%(avg)'].max())

            trans_i_sum = df_trans_perf.loc[df_trans_perf['Name'] != '/nginx', 'Traffic Out [MB]'].sum()
            new_cols['neti_total_mb'].append(trans_i_sum)

            trans_o_sum = df_trans_perf.loc[df_trans_perf['Name'] != '/nginx', 'Traffic Out [MB]'].sum()
            new_cols['neto_total_mb'].append(trans_o_sum)

            new_cols['n'].append(test_params['N_VALIDATORS'])
            new_cols['algo'].append(test_params['CONSENSUS_ALGO'])
            new_cols['tps_param'].append(int(test_params['TPS']))
            new_cols['cpu_limit'].append(test_params['CPU_LIMIT'])
            new_cols['r_idx'].append(result_idx)
            if 'PUMBA_DELAY' in test_params:
                new_cols['delay'].append(test_params['PUMBA_DELAY'])
            else:
                new_cols['delay'].append(None)
            if 'PUMBA_RATE' in test_params:
                rate_limit_converted = rate_limit_convert[test_params['PUMBA_RATE']]
                new_cols['rate_limit'].append(rate_limit_converted)
            else:
                new_cols['rate_limit'].append(None)

        for key, value in new_cols.items():
            df.loc[:, key] = value

        dfs.append(df)

    master_df = pd.concat(dfs)
    master_df = master_df.fillna(value=0)

    return master_df


def make_lineplot(
    df: pd.DataFrame,
    groupby_cols: list,
    x_col: str,
    x_label: str,
    y_col: str,
    y_label: str,
    file_tag: str,
    transaction_types: list,
    img_dir: Path,
):
    _df = df.copy()
    _df = _df.groupby(TEST_ID_COLS)
    _df = _df[y_col].mean().reset_index()
    for transaction_type in transaction_types:
        _dft = _df.loc[_df['Name'] == transaction_type]
        fig, ax = plt.subplots(figsize=(10,8))
        for key, grp in _dft.groupby(groupby_cols):
            grp = grp.sort_values(by=[x_col])
            color = PLOT_DESIGNS[groupby_cols[0]][key[0]]['color']
            marker = PLOT_DESIGNS[groupby_cols[0]][key[0]]['marker']
            linestyle = PLOT_DESIGNS[groupby_cols[0]][key[0]]['ls']

            ax.plot(
                grp[x_col],
                grp[y_col],
                color=color,
                marker=marker,
                linestyle=linestyle,
                linewidth=1,
                label=f"{key[0]}"
            )
        ax.set_title(f'{x_label} vs. {y_label} of {transaction_type}')
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)

        ax.legend()
        img_path = img_dir / f'{file_tag}_{transaction_type}.png'
        plt.savefig(img_path)


def make_lineplot_boxplot(
    df: pd.DataFrame,
    groupby_cols: list,
    x_col: str,
    x_label: str,
    y_col: str,
    y_label: str,
    file_tag: str,
    transaction_types: list,
    img_dir: Path,
):
    for transaction_type in transaction_types:
        _df = df.copy()
        _df = _df.loc[_df['Name'] == transaction_type]
        fig, ax = plt.subplots(figsize=(10,8))
        for key, grp in _df.groupby(groupby_cols):
            grp = grp.sort_values(by=[x_col])
            color = PLOT_DESIGNS['algo'][key[0]]['color']
            marker = PLOT_DESIGNS['n'][key[1]]['marker']
            linestyle = PLOT_DESIGNS['n'][key[1]]['ls']

            x_vals = [int(e) for e in grp[x_col].values]
            mu = grp[f'{y_col}_mean'].values
            ax.plot(
                x_vals,
                mu,
                color=color,
                marker=marker,
                linestyle=linestyle,
                linewidth=1,
                label=f"{key[0]}_{key[1]}"
            )

            ax.boxplot(
                grp[f'{y_col}_all'],
                positions=x_vals,
                # notch=1,
                sym='k+',
                showfliers=False,
                showmeans=False,
                patch_artist=True,
                boxprops=dict(facecolor=color, alpha=0.5),
                widths=[3] * len(x_vals),
                zorder=1
            )


        ax.set_title(f'{x_label} vs. {y_label} of {transaction_type}')
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)

        ax.legend()
        img_path = img_dir / f'{file_tag}_{transaction_type}.png'
        plt.savefig(img_path)


def get_grouped_df(df: pd.DataFrame):
    _df = df.copy().groupby(TEST_ID_COLS)

    df_out = _df[['Throughput (TPS)', 'neto_total_mb']].agg(
        tput_mean=('Throughput (TPS)', 'mean'),
        tput_all=('Throughput (TPS)', lambda x: list(x)),
        tput_std=('Throughput (TPS)', 'std'),
        neto_mean=('neto_total_mb', 'mean'),
        neto_all=('neto_total_mb', lambda x: list(x)),
        neto_std=('neto_total_mb', 'std'),
    ).reset_index()

    return df_out

def generate_plots(df):
    plots_dir = TEST_DIR / 'plots'
    if os.path.exists(plots_dir):
        shutil.rmtree(plots_dir, ignore_errors=True)
    os.makedirs(plots_dir)

    # throughput plots
    df_grouped = get_grouped_df(df)
    # make_lineplot_boxplot(
    #     df_grouped,
    #     ['algo', 'n'],
    #     'tps_param',
    #     'Send Rate (TPS)',
    #     'tput',
    #     'Avg. Throughput (TPS)',
    #     'throughput',
    #     ['open', 'transfer'],
    #     plots_dir,
    # )

    # # latency plots
    # make_lineplot(
    #     df,
    #     ['algo', 'n'],
    #     'tps_param',
    #     'Send Rate (TPS)',
    #     'Avg Latency (s)',
    #     'Avg. Latency (s)',
    #     'latency',
    #     ['open', 'transfer'],
    #     plots_dir,
    # )

    # # metrics plots
    # make_lineplot(
    #     df,
    #     ['algo', 'n'],
    #     'tps_param',
    #     'Send Rate (TPS)',
    #     'neto_total_mb',
    #     'Total Network Out (MB)',
    #     'traffic_out',
    #     ['open', 'transfer'],
    #     plots_dir,
    # )
    make_lineplot(
        df,
        ['algo'],
        'n',
        'N',
        'cpu%_max_all',
        'Max. CPU%',
        'cpu_max_all',
        ['open', 'transfer'],
        plots_dir,
    )


if __name__ == "__main__":
    df_compiled = compile_reports()
    compiled_csv = TEST_DIR / 'compiled.csv'
    df_compiled.to_csv(compiled_csv)

    generate_plots(df_compiled)
