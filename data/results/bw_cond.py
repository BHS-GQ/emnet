#%%

import tikzplotlib
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

from constants import *

CSV_SCALE = '/home/derick/eth1/emnet/data/bw_scale/compiled.csv'
CSV_RATE = '/home/derick/eth1/emnet/data/bw_rate/compiled.csv'
CSV_BL_SCALE = '/home/derick/eth1/emnet/data/bl_scale/compiled.csv'
CSV_BL_RATE = '/home/derick/eth1/emnet/data/bl_rate/compiled.csv'

df_s = pd.read_csv(CSV_SCALE)
df_r = pd.read_csv(CSV_RATE)
df_sb = pd.read_csv(CSV_BL_SCALE)
df_rb = pd.read_csv(CSV_BL_RATE)
ldf = [df_s, df_r]
df = pd.concat(ldf, ignore_index=True)
df.head(3)

#%%
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

df_sg = get_grouped_df(df_s)
df_rg = get_grouped_df(df_r)
df_sbg = get_grouped_df(df_sb)
df_rbg = get_grouped_df(df_rb)
df_g = get_grouped_df(df)
df_g = df_g[df_g['tput_all'].map(len) >= 8]
df_g['cpu_max_avg'] = df_g['cpu_max_avg'].div(100)

#%%
TO_TITLE = {
    'tput_mean': 'Throughput',
    'lat_mean': 'Latency',
    'neto_mean': 'Net. Usage',
    'cpu_max_avg': 'CPU Usage',
}

designs = {
    'algo': {        
        'bhs': {'color': 'tab:blue', 'marker': 'o'},
        'ibft': {'color': 'tab:green', 'marker': 'x'},
        'qbft': {'color': 'tab:orange', 'marker': '^'}
    },
    'Name': {        
        'open': {'ls': 'solid'},
        'query': {'ls': 'dashed'},
        'transfer': {'ls': ':'}
    },
}

df_bhs = (df_g[df_g['algo'] == 'bhs']).copy()
df_iq = (df_g[df_g['algo'] != 'bhs']).copy()

#%%
x_col = 'n'
y_cols = ['tput_mean', 'lat_mean', 'neto_mean', 'cpu_max_avg']
groupby_cols = ['n', 'Name']
df_others = df_sg.loc[df_sg['algo'] != 'bhs']
bhs = df_sg[df_sg['algo'] == 'bhs'].set_index(groupby_cols)[y_cols]
iq = df_others.groupby(groupby_cols).agg(
    tput_mean=('tput_mean', 'max'),
    lat_mean=('lat_mean', 'min'),
    neto_mean=('neto_mean', 'min'),
    cpu_max_avg=('cpu_max_avg', 'min'),
)[y_cols]
iq = iq.swaplevel(0, 1, axis=0)
bhs = bhs.reset_index(level=[0,1])
iq = iq.reset_index(level=[0,1])
fig, axs = plt.subplots(4, 2)
for i, y_col in enumerate(y_cols):
    for key, grp in bhs.groupby(['Name']):
        if key[0] == 'query':
            continue
        if y_col == 'cpu_max_avg':
            grp[y_col] = grp[y_col] / 100
        axs[i][0].plot(
            grp[x_col].values,
            grp[y_col].values,
            label=f'bhs-{key[0]}',
            linewidth=1,
            markerfacecolor='none',
            **({**designs['algo']['bhs'], **designs['Name'][key[0]]})
        )
    for key, grp in iq.groupby(['Name']):
        if key[0] == 'query':
            continue
        if y_col == 'cpu_max_avg':
            grp[y_col] = grp[y_col] / 100
        axs[i][0].plot(
            grp[x_col].values,
            grp[y_col].values,
            label=f'i/qbft-{key[0]}',
            linewidth=1,
            markerfacecolor='none',
            **({**designs['algo']['qbft'], **designs['Name'][key[0]]})
        )

x_col = 'tps_param'
y_cols = ['tput_mean', 'lat_mean', 'neto_mean', 'cpu_max_avg']
groupby_cols = ['tps_param', 'Name']
df_others = df_rg.loc[df_rg['algo'] != 'bhs']
bhs = df_rg[df_rg['algo'] == 'bhs'].set_index(groupby_cols)[y_cols]
iq = df_others.groupby(groupby_cols).agg(
    tput_mean=('tput_mean', 'max'),
    lat_mean=('lat_mean', 'min'),
    neto_mean=('neto_mean', 'min'),
    cpu_max_avg=('cpu_max_avg', 'min'),
)[y_cols]
iq = iq.swaplevel(0, 1, axis=0)
bhs = bhs.reset_index(level=[0,1])
iq = iq.reset_index(level=[0,1])
for i, y_col in enumerate(y_cols):
    for key, grp in bhs.groupby(['Name']):
        if key[0] == 'query':
            continue
        if y_col == 'cpu_max_avg':
            grp[y_col] = grp[y_col] / 100
        axs[i][1].plot(
            grp[x_col].values,
            grp[y_col].values,
            label=f'bhs-{key[0]}',
            linewidth=1,
            markerfacecolor='none',
            **({**designs['algo']['bhs'], **designs['Name'][key[0]]})
        )
    for key, grp in iq.groupby(['Name']):
        if key[0] == 'query':
            continue
        if y_col == 'cpu_max_avg':
            grp[y_col] = grp[y_col] / 100
        axs[i][1].plot(
            grp[x_col].values,
            grp[y_col].values,
            label=f'i/qbft-{key[0]}',
            linewidth=1,
            markerfacecolor='none',
            **({**designs['algo']['qbft'], **designs['Name'][key[0]]})
        )
axs[0][0].legend(loc='upper center', bbox_to_anchor=(0.5,1.5), ncol=2)
axs[0,0].get_ylim()

tikzplotlib.save("_test.tex")


#%%
x_col = 'n'
y_cols = ['tput_mean', 'lat_mean', 'neto_mean', 'cpu_max_avg']
groupby_cols = ['n', 'Name']
df_others = df_sg.loc[df_sg['algo'] != 'bhs']

bhs = df_sg[df_sg['algo'] == 'bhs'].set_index(groupby_cols)[y_cols]
iq = df_others.groupby(groupby_cols).agg(
    tput_mean=('tput_mean', 'max'),
    lat_mean=('lat_mean', 'min'),
    neto_mean=('neto_mean', 'min'),
    cpu_max_avg=('cpu_max_avg', 'min'),
)[y_cols]
df_cc = pd.concat([iq, bhs], axis=1, keys=['iq', 'bhs'], join="inner")
df_cc.columns = df_cc.columns.swaplevel(0, 1)
for y_col in y_cols:
    # df_cc.loc[:, (y_col, 'delta')] = df_cc[y_col]['bhs'] - df_cc[y_col]['iq']
    df_cc.loc[:, (y_col, 'delta')] = (
        df_cc[y_col]['bhs'] - df_cc[y_col]['iq']
    ) / df_cc[y_col]['iq']
    # df_cc.drop(columns=(y_col, 'bhs'), inplace=True)
    # df_cc.drop(columns=(y_col, 'iq'), inplace=True)
df_cc.sort_index(axis=1, level=0, inplace=True)
df_cc = df_cc.unstack(-1)

fig, axs = plt.subplots(4, 1)
for i, y_col in enumerate(y_cols):
    df_cc[y_col]['delta'][['open', 'transfer']].plot.bar(
        ax=axs[i], legend=False, linewidth=1,
    )
axs[0].legend(loc='upper center', bbox_to_anchor=(0.5,1.5), ncol=3)

#%%
x_col = 'tps_param'
y_cols = ['tput_mean', 'lat_mean', 'neto_mean', 'cpu_max_avg']
groupby_cols = ['tps_param', 'Name']
df_others = df_rg.loc[df_rg['algo'] != 'bhs']

bhs = df_rg[df_rg['algo'] == 'bhs'].set_index(groupby_cols)[y_cols]
iq = df_others.groupby(groupby_cols).agg(
    tput_mean=('tput_mean', 'max'),
    lat_mean=('lat_mean', 'min'),
    neto_mean=('neto_mean', 'min'),
    cpu_max_avg=('cpu_max_avg', 'min'),
)[y_cols]
df_cc = pd.concat([iq, bhs], axis=1, keys=['iq', 'bhs'], join="inner")
df_cc.columns = df_cc.columns.swaplevel(0, 1)
for y_col in y_cols:
    df_cc.loc[:, (y_col, 'delta')] = (
        df_cc[y_col]['bhs'] - df_cc[y_col]['iq']
    ) / df_cc[y_col]['iq']
    # df_cc.drop(columns=(y_col, 'bhs'), inplace=True)
    # df_cc.drop(columns=(y_col, 'iq'), inplace=True)
df_cc.sort_index(axis=1, level=0, inplace=True)
df_cc = df_cc.unstack(-1)

fig, axs = plt.subplots(4, 1)
for i, y_col in enumerate(y_cols):
    df_cc[y_col]['delta'][['open', 'transfer']].plot.bar(
        ax=axs[i], legend=False, linewidth=1,
    )
axs[0].legend(loc='upper center', bbox_to_anchor=(0.5,1.5), ncol=3)



#%%
x_col = 'n'
y_cols = ['neto_mean']
groupby_cols = ['n', 'Name']
df_others = df_sg.loc[df_sg['algo'] != 'bhs']
bhs = df_sg[df_sg['algo'] == 'bhs'].set_index(groupby_cols)[y_cols]
iq = df_others.groupby(groupby_cols).agg(
    tput_mean=('tput_mean', 'max'),
    lat_mean=('lat_mean', 'min'),
    neto_mean=('neto_mean', 'min'),
    cpu_max_avg=('cpu_max_avg', 'min'),
)[y_cols]
iq = iq.swaplevel(0, 1, axis=0)
bhs = bhs.reset_index(level=[0,1])
iq = iq.reset_index(level=[0,1])
fig, axs = plt.subplots(1, 2)
for i, y_col in enumerate(y_cols):
    for key, grp in bhs.groupby(['Name']):
        if key[0] != 'query':
            continue
        if y_col == 'cpu_max_avg':
            grp[y_col] = grp[y_col] / 100
        axs[0].plot(
            grp[x_col].values,
            grp[y_col].values,
            label=f'bhs-{key[0]}',
            linewidth=1,
            markerfacecolor='none',
            **({**designs['algo']['bhs'], **designs['Name'][key[0]]})
        )
    for key, grp in iq.groupby(['Name']):
        if key[0] != 'query':
            continue
        if y_col == 'cpu_max_avg':
            grp[y_col] = grp[y_col] / 100
        axs[0].plot(
            grp[x_col].values,
            grp[y_col].values,
            label=f'i/qbft-{key[0]}',
            linewidth=1,
            markerfacecolor='none',
            **({**designs['algo']['qbft'], **designs['Name'][key[0]]})
        )

x_col = 'tps_param'
y_cols = ['neto_mean']
groupby_cols = ['tps_param', 'Name']
df_others = df_rg.loc[df_rg['algo'] != 'bhs']
bhs = df_rg[df_rg['algo'] == 'bhs'].set_index(groupby_cols)[y_cols]
iq = df_others.groupby(groupby_cols).agg(
    tput_mean=('tput_mean', 'max'),
    lat_mean=('lat_mean', 'min'),
    neto_mean=('neto_mean', 'min'),
    cpu_max_avg=('cpu_max_avg', 'min'),
)[y_cols]
iq = iq.swaplevel(0, 1, axis=0)
bhs = bhs.reset_index(level=[0,1])
iq = iq.reset_index(level=[0,1])
for i, y_col in enumerate(y_cols):
    for key, grp in bhs.groupby(['Name']):
        if key[0] != 'query':
            continue
        if y_col == 'cpu_max_avg':
            grp[y_col] = grp[y_col] / 100
        axs[1].plot(
            grp[x_col].values,
            grp[y_col].values,
            label=f'bhs-{key[0]}',
            linewidth=1,
            markerfacecolor='none',
            **({**designs['algo']['bhs'], **designs['Name'][key[0]]})
        )
    for key, grp in iq.groupby(['Name']):
        if key[0] != 'query':
            continue
        if y_col == 'cpu_max_avg':
            grp[y_col] = grp[y_col] / 100
        axs[1].plot(
            grp[x_col].values,
            grp[y_col].values,
            label=f'i/qbft-{key[0]}',
            linewidth=1,
            markerfacecolor='none',
            **({**designs['algo']['qbft'], **designs['Name'][key[0]]})
        )
axs[0].legend(loc='upper center', bbox_to_anchor=(0.5,1.5), ncol=2)
axs[0].get_ylim()

tikzplotlib.save("_test.tex")

#%%
designs = {
    'type': {        
        'baseline': {'color': 'tab:gray', 'marker': 'o'},
        'bw': {'color': 'tab:blue', 'marker': '^'}
    },
    'Name': {        
        'open': {'ls': 'solid'},
        'query': {'ls': 'dashed'},
        'transfer': {'ls': 'dashed'}
    },
}




x_col = 'n'
y_cols = ['tput_mean', 'lat_mean', 'neto_mean', 'cpu_max_avg']
groupby_cols = ['n', 'Name']
df_others = df_sg.loc[df_sg['algo'] != 'bhs']

bhs = df_sg[df_sg['algo'] == 'bhs'].set_index(groupby_cols)[y_cols]
iq = df_others.groupby(groupby_cols).agg(
    tput_mean=('tput_mean', 'max'),
    lat_mean=('lat_mean', 'min'),
    neto_mean=('neto_mean', 'min'),
    cpu_max_avg=('cpu_max_avg', 'min'),
)[y_cols]
df_cc = pd.concat([iq, bhs], axis=1, keys=['iq', 'bhs'], join="inner")
df_cc.columns = df_cc.columns.swaplevel(0, 1)
for y_col in y_cols:
    # df_cc.loc[:, (y_col, 'delta')] = df_cc[y_col]['bhs'] - df_cc[y_col]['iq']
    df_cc.loc[:, (y_col, 'delta')] = 100 * (
        df_cc[y_col]['bhs'] - df_cc[y_col]['iq']
    ) / df_cc[y_col]['iq']
    if y_col != 'tput_mean':
        df_cc.loc[:, (y_col, 'delta')] = -df_cc.loc[:, (y_col, 'delta')]
    # df_cc.drop(columns=(y_col, 'bhs'), inplace=True)
    # df_cc.drop(columns=(y_col, 'iq'), inplace=True)
df_cc.sort_index(axis=1, level=0, inplace=True)
df_cc = df_cc.unstack(-1)



x_col = 'tps_param'
y_cols = ['tput_mean', 'lat_mean', 'neto_mean', 'cpu_max_avg']
groupby_cols = ['tps_param', 'Name']
df_others = df_rg.loc[df_rg['algo'] != 'bhs']

bhs = df_rg[df_rg['algo'] == 'bhs'].set_index(groupby_cols)[y_cols]
iq = df_others.groupby(groupby_cols).agg(
    tput_mean=('tput_mean', 'max'),
    lat_mean=('lat_mean', 'min'),
    neto_mean=('neto_mean', 'min'),
    cpu_max_avg=('cpu_max_avg', 'min'),
)[y_cols]
df_cc2 = pd.concat([iq, bhs], axis=1, keys=['iq', 'bhs'], join="inner")
df_cc2.columns = df_cc2.columns.swaplevel(0, 1)
for y_col in y_cols:
    df_cc2.loc[:, (y_col, 'delta')] = 100 * (
        df_cc2[y_col]['bhs'] - df_cc2[y_col]['iq']
    ) / df_cc2[y_col]['iq']
    if y_col != 'tput_mean':
        df_cc2.loc[:, (y_col, 'delta')] = -df_cc2.loc[:, (y_col, 'delta')]
    # df_cc.drop(columns=(y_col, 'bhs'), inplace=True)
    # df_cc.drop(columns=(y_col, 'iq'), inplace=True)
df_cc2.sort_index(axis=1, level=0, inplace=True)
df_cc2 = df_cc2.unstack(-1)











x_col = 'n'
y_cols = ['tput_mean', 'lat_mean', 'neto_mean', 'cpu_max_avg']
groupby_cols = ['n', 'Name']
df_others = df_sbg.loc[df_sbg['algo'] != 'bhs']

bhs = df_sbg[df_sbg['algo'] == 'bhs'].set_index(groupby_cols)[y_cols]
iq = df_others.groupby(groupby_cols).agg(
    tput_mean=('tput_mean', 'max'),
    lat_mean=('lat_mean', 'min'),
    neto_mean=('neto_mean', 'min'),
    cpu_max_avg=('cpu_max_avg', 'min'),
)[y_cols]
df_ccb = pd.concat([iq, bhs], axis=1, keys=['iq', 'bhs'], join="inner")
df_ccb.columns = df_ccb.columns.swaplevel(0, 1)
for y_col in y_cols:
    # df_cc.loc[:, (y_col, 'delta')] = df_cc[y_col]['bhs'] - df_cc[y_col]['iq']
    df_ccb.loc[:, (y_col, 'delta')] = 100 * (
        df_ccb[y_col]['bhs'] - df_ccb[y_col]['iq']
    ) / df_ccb[y_col]['iq']
    if y_col != 'tput_mean':
        df_ccb.loc[:, (y_col, 'delta')] = -df_ccb.loc[:, (y_col, 'delta')]
    # df_cc.drop(columns=(y_col, 'bhs'), inplace=True)
    # df_cc.drop(columns=(y_col, 'iq'), inplace=True)
df_ccb.sort_index(axis=1, level=0, inplace=True)
df_ccb = df_ccb.unstack(-1)

x_col = 'tps_param'
y_cols = ['tput_mean', 'lat_mean', 'neto_mean', 'cpu_max_avg']
groupby_cols = ['tps_param', 'Name']
df_others = df_rbg.loc[df_rbg['algo'] != 'bhs']

bhs = df_rbg[df_rbg['algo'] == 'bhs'].set_index(groupby_cols)[y_cols]
iq = df_others.groupby(groupby_cols).agg(
    tput_mean=('tput_mean', 'max'),
    lat_mean=('lat_mean', 'min'),
    neto_mean=('neto_mean', 'min'),
    cpu_max_avg=('cpu_max_avg', 'min'),
)[y_cols]
df_ccb2 = pd.concat([iq, bhs], axis=1, keys=['iq', 'bhs'], join="inner")
df_ccb2.columns = df_ccb2.columns.swaplevel(0, 1)
for y_col in y_cols:
    df_ccb2.loc[:, (y_col, 'delta')] = 100 * (
        df_ccb2[y_col]['bhs'] - df_ccb2[y_col]['iq']
    ) / df_ccb2[y_col]['iq']
    if y_col != 'tput_mean':
        df_ccb2.loc[:, (y_col, 'delta')] = -df_ccb2.loc[:, (y_col, 'delta')]
    # df_cc.drop(columns=(y_col, 'bhs'), inplace=True)
    # df_cc.drop(columns=(y_col, 'iq'), inplace=True)
df_ccb2.sort_index(axis=1, level=0, inplace=True)
df_ccb2 = df_ccb2.unstack(-1)

fig, axs = plt.subplots(4, 2)
for i, y_col in enumerate(y_cols):
    for txn in ['open', 'transfer']:
        df_cc[y_col]['delta'][txn].plot.line(
            ax=axs[i][0], legend=False, linewidth=1,
            markerfacecolor='none',
            **({**designs['type']['bw'], **designs['Name'][txn]})
        )
        df_cc2[y_col]['delta'][txn].plot.line(
            ax=axs[i][1], legend=False, linewidth=1,
            markerfacecolor='none',
            **({**designs['type']['bw'], **designs['Name'][txn]})
        )
        df_ccb[y_col]['delta'][txn].plot.line(
            ax=axs[i][0], legend=False, linewidth=1,
            markerfacecolor='none',
            **({**designs['type']['baseline'], **designs['Name'][txn]})
        )
        df_ccb2[y_col]['delta'][txn].plot.line(
            ax=axs[i][1], legend=False, linewidth=1,
            markerfacecolor='none',
            **({**designs['type']['baseline'], **designs['Name'][txn]})
        )
axs[0][0].legend([
    'open @ 10 Mbps',
    'open @ baseline',
    'trans. @ 10 Mbps',
    'trans. @ baseline',
], loc='upper center', bbox_to_anchor=(0.5,1.75), ncol=2)
tikzplotlib.save("_test.tex")
#%%
df_cc['neto_mean']

#%%
df_cc['lat_mean']
#%%
df_cc2['tput_mean']

#%%
df_cc2['lat_mean']

#%%
df_ccb['lat_mean']

#%%
x_col = 'n'
y_cols = ['tput_mean', 'lat_mean', 'neto_mean', 'cpu_max_avg']
groupby_cols = ['n', 'Name']
df_others = df_sg.loc[df_sg['algo'] != 'bhs']

bhs = df_sg[df_sg['algo'] == 'bhs'].set_index(groupby_cols)[y_cols]
iq = df_others.groupby(groupby_cols).agg(
    tput_mean=('tput_mean', 'max'),
    lat_mean=('lat_mean', 'min'),
    neto_mean=('neto_mean', 'min'),
    cpu_max_avg=('cpu_max_avg', 'min'),
)[y_cols]
df_cc = pd.concat([iq, bhs], axis=1, keys=['iq', 'bhs'], join="inner")
df_cc.columns = df_cc.columns.swaplevel(0, 1)
for y_col in y_cols:
    # df_cc.loc[:, (y_col, 'delta')] = df_cc[y_col]['bhs'] - df_cc[y_col]['iq']
    df_cc.loc[:, (y_col, 'delta')] = (
        df_cc[y_col]['bhs'] - df_cc[y_col]['iq']
    ) / df_cc[y_col]['iq']
    if y_col != 'tput_mean':
        df_cc.loc[:, (y_col, 'delta')] = -df_cc.loc[:, (y_col, 'delta')]
    # df_cc.drop(columns=(y_col, 'bhs'), inplace=True)
    # df_cc.drop(columns=(y_col, 'iq'), inplace=True)
df_cc.sort_index(axis=1, level=0, inplace=True)
df_cc = df_cc.unstack(-1)



x_col = 'tps_param'
y_cols = ['tput_mean', 'lat_mean', 'neto_mean', 'cpu_max_avg']
groupby_cols = ['tps_param', 'Name']
df_others = df_rg.loc[df_rg['algo'] != 'bhs']

bhs = df_rg[df_rg['algo'] == 'bhs'].set_index(groupby_cols)[y_cols]
iq = df_others.groupby(groupby_cols).agg(
    tput_mean=('tput_mean', 'max'),
    lat_mean=('lat_mean', 'min'),
    neto_mean=('neto_mean', 'min'),
    cpu_max_avg=('cpu_max_avg', 'min'),
)[y_cols]
df_cc2 = pd.concat([iq, bhs], axis=1, keys=['iq', 'bhs'], join="inner")
df_cc2.columns = df_cc2.columns.swaplevel(0, 1)
for y_col in y_cols:
    df_cc2.loc[:, (y_col, 'delta')] = (
        df_cc2[y_col]['bhs'] - df_cc2[y_col]['iq']
    ) / df_cc2[y_col]['iq']
    if y_col != 'tput_mean':
        df_cc2.loc[:, (y_col, 'delta')] = -df_cc2.loc[:, (y_col, 'delta')]
    # df_cc.drop(columns=(y_col, 'bhs'), inplace=True)
    # df_cc.drop(columns=(y_col, 'iq'), inplace=True)
df_cc2.sort_index(axis=1, level=0, inplace=True)
df_cc2 = df_cc2.unstack(-1)











x_col = 'n'
y_cols = ['tput_mean', 'lat_mean', 'neto_mean', 'cpu_max_avg']
groupby_cols = ['n', 'Name']
df_others = df_sbg.loc[df_sbg['algo'] != 'bhs']

bhs = df_sbg[df_sbg['algo'] == 'bhs'].set_index(groupby_cols)[y_cols]
iq = df_others.groupby(groupby_cols).agg(
    tput_mean=('tput_mean', 'max'),
    lat_mean=('lat_mean', 'min'),
    neto_mean=('neto_mean', 'min'),
    cpu_max_avg=('cpu_max_avg', 'min'),
)[y_cols]
df_ccb = pd.concat([iq, bhs], axis=1, keys=['iq', 'bhs'], join="inner")
df_ccb.columns = df_ccb.columns.swaplevel(0, 1)
for y_col in y_cols:
    # df_cc.loc[:, (y_col, 'delta')] = df_cc[y_col]['bhs'] - df_cc[y_col]['iq']
    df_ccb.loc[:, (y_col, 'delta')] = (
        df_ccb[y_col]['bhs'] - df_ccb[y_col]['iq']
    ) / df_ccb[y_col]['iq']
    if y_col != 'tput_mean':
        df_ccb.loc[:, (y_col, 'delta')] = -df_ccb.loc[:, (y_col, 'delta')]
    # df_cc.drop(columns=(y_col, 'bhs'), inplace=True)
    # df_cc.drop(columns=(y_col, 'iq'), inplace=True)
df_ccb.sort_index(axis=1, level=0, inplace=True)
df_ccb = df_ccb.unstack(-1)

x_col = 'tps_param'
y_cols = ['tput_mean', 'lat_mean', 'neto_mean', 'cpu_max_avg']
groupby_cols = ['tps_param', 'Name']
df_others = df_rbg.loc[df_rbg['algo'] != 'bhs']

bhs = df_rbg[df_rbg['algo'] == 'bhs'].set_index(groupby_cols)[y_cols]
iq = df_others.groupby(groupby_cols).agg(
    tput_mean=('tput_mean', 'max'),
    lat_mean=('lat_mean', 'min'),
    neto_mean=('neto_mean', 'min'),
    cpu_max_avg=('cpu_max_avg', 'min'),
)[y_cols]
df_ccb2 = pd.concat([iq, bhs], axis=1, keys=['iq', 'bhs'], join="inner")
df_ccb2.columns = df_ccb2.columns.swaplevel(0, 1)
for y_col in y_cols:
    df_ccb2.loc[:, (y_col, 'delta')] = (
        df_ccb2[y_col]['bhs'] - df_ccb2[y_col]['iq']
    ) / df_ccb2[y_col]['iq']
    if y_col != 'tput_mean':
        df_ccb2.loc[:, (y_col, 'delta')] = -df_ccb2.loc[:, (y_col, 'delta')]
    # df_cc.drop(columns=(y_col, 'bhs'), inplace=True)
    # df_cc.drop(columns=(y_col, 'iq'), inplace=True)
df_ccb2.sort_index(axis=1, level=0, inplace=True)
df_ccb2 = df_ccb2.unstack(-1)

fig, axs = plt.subplots(4, 2)
for i, y_col in enumerate(y_cols):
    for txn in ['query']:
        df_cc[y_col]['delta'][txn].plot.line(
            ax=axs[i][0], legend=False, linewidth=1,
            markerfacecolor='none',
            **({**designs['type']['bw'], **designs['Name'][txn]})
        )
        df_cc2[y_col]['delta'][txn].plot.line(
            ax=axs[i][1], legend=False, linewidth=1,
            markerfacecolor='none',
            **({**designs['type']['bw'], **designs['Name'][txn]})
        )
        df_ccb[y_col]['delta'][txn].plot.line(
            ax=axs[i][0], legend=False, linewidth=1,
            markerfacecolor='none',
            **({**designs['type']['baseline'], **designs['Name'][txn]})
        )
        df_ccb2[y_col]['delta'][txn].plot.line(
            ax=axs[i][1], legend=False, linewidth=1,
            markerfacecolor='none',
            **({**designs['type']['baseline'], **designs['Name'][txn]})
        )
axs[0][0].legend([
    'open @ 10 Mbps',
    'open @ baseline',
    'trans. @ 10 Mbps',
    'trans. @ baseline',
], loc='upper center', bbox_to_anchor=(0.5,1.75), ncol=2)