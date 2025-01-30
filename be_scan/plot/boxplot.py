"""
Author: Calvin XiaoYang Hu
Adapted from: Nicholas Lue - NZL10196_Screen_Analysis_v9b.py Created on Fri May 29 03:00:39 2020
Date: 231116

{Description: This function plots chosen guides by plot_column categories to show the distribution of guides}
"""

import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path
import matplotlib as mpl
import plotly.express as px
import plotly.graph_objects as go

from be_scan.plot._annotating_ import *

def boxplot(df_filepath, comparisons, # each comparison is a plot
            plot_column, plot_conditions, # each plot condition is a box in a plot
    
    xlab='', ylab='Log2 Fold Change', # boxplot labels
    neg_ctrl=False, neg_ctrl_col='', neg_ctrl_conditions=[], # neg control params
    savefig=True, show=True, out_name='boxes', out_type='png', out_dir='', # output params
    interactive=False, 

    # style params
    subplots_kws={}, 
    boxplot_kws = {'saturation':1, 'fliersize':4, 'width':0.4, 
                   'flierprops':{'marker':'o', 'mec':'black', 'lw':1, 'alpha':0.8}},
    axhline_kws = {'color':'k', 'ls':'--', 'lw':1},
    ):
    
    """[Summary]
    This function takes in a dataframe from count_reads, performs normalization, 
    and then plots chosen (ex control) guides by plot_column categories, 
    to show the distribution of categories of guides
    
    Parameters
    ------------
    df_filepath : str, required
        filepath to .csv data generated from count_reads
    comparisons : list of str, required
        list of comparisons that correspond to columns of data
    plot_column : str, required
        column of .csv, typically domain or mutation type
    plot_conditions : list of str, required
        category names of plot_column

    xlab : str, optional, defaults to ''
        name of x-axis label
    ylab : str, optional, defaults to 'Log2 Fold Change'
        name of y-axis label
    neg_ctrl : bool, optional, defaults to False
        whether or not to calulate negative control for normalization and line drawing
    neg_ctrl_col : str, optional, defaults to 'CtoT_win_overlap'
        column of .csv which correspond to normalization control
    neg_ctrl_conditions : list of str, optional, defaults to ['Intron', 'Control']
        name of categories of neg_ctrl_col to normalize dataframe
    savefig : boolean, optional, defaults to True
        option of saving figure to output or not
    show : bool, optional, defaults to True
        whether or not to show the plot
    out_name : str, optional, defaults to 'scatterplot'
        name of figure output
    out_type : str, optional, defaults to 'pdf'
        file type of figure output
    out_directory : str, optional, defaults to ''
        path to output directory

    subplots_kws : dict, optional, defaults to 
        {'figsize':(5,4)}
        input params for plt.subplots() 
        https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.subplots.html
    boxplot_kws : dict, optional, defaults to 
        {'saturation':1, 'fliersize':4, 'width':0.4, 
        'flierprops':{'marker':'o', 'mec':'black', 'lw':1, 'alpha':0.8}}
        input params for sns.boxplot() 
        https://seaborn.pydata.org/generated/seaborn.boxplot.html
    axhline_kws : dict, optional, defaults to 
        {'color':'k', 'ls':'--', 'lw':1}
        input params for plt.axhline() 
        https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.axhline.html

    Returns
    ------------
    """
    df_filepath = Path(df_filepath)
    df_data = pd.read_csv(df_filepath)

    # normalize data to intergenic controls if neg_ctrl is provided
    if neg_ctrl: 
        assert isinstance(neg_ctrl_col, str) and neg_ctrl_col in df_data.columns.tolist(), "check param: params_cols"
        assert isinstance(neg_ctrl_conditions, list), "check param: params_conditions"
        # calculate negative control stats
        _, list_ctrlstats, avg_dict = calc_neg_ctrls(df_data, comparisons, neg_ctrl_col, neg_ctrl_conditions)
        # calculate normalized log_fc scores for each comp condition
        df_data = norm_to_intergenic_ctrls(df_data, comparisons, avg_dict)

    df_data = df_data.loc[df_data[plot_column].isin(plot_conditions)].copy()

    # INTERACTIVE #
    if interactive: 

        figures = []
        for comp in comparisons:
            fig = go.Figure()
            fig.add_trace(go.Box(
                y=df_data[comp], 
                x=df_data[plot_column], 
                name=comp, marker=dict(color="blue"), boxmean="sd"
            ))

            # Overlay neg ctrl avg +/- 2 SD as dashed lines
            if neg_ctrl and list_ctrlstats is not None:
                tup_comp_stdev = [tup for tup in list_ctrlstats if tup[0] == comp][0][2]
                fig.add_hline(y=2*tup_comp_stdev, line=dict(dash="dash", color="black"))  # Top baseline
                fig.add_hline(y=-2*tup_comp_stdev, line=dict(dash="dash", color="black"))  # Bottom baseline

            # Adjust layout
            fig.update_layout(
                title=comp, xaxis_title=xlab, yaxis_title=ylab,
                xaxis=dict(tickangle=-45),
                yaxis=dict(range=[np.floor(df_data[comp].min()), np.ceil(df_data[comp].max())])
            )
            figures.append(fig)

        # Show all figures
        if show: 
            for fig in figures: fig.show()
        # Save as an HTML file instead of PDF (since Plotly is interactive)
        outpath = Path(out_dir)
        if savefig:
            for i, fig in enumerate(figures):
                out_name = f'{out_name}_{str(i)}.html'
                fig.write_html(outpath / out_name)

    else: # NON INTERACTIVE #
        mpl.rcParams.update({'font.size': 10}) # STYLE #
        fig, axes = plt.subplots(nrows=len(comparisons), ncols=1, figsize=(5, 3*len(comparisons)), 
                                **subplots_kws) # SETUP SUBPLOTS #
        if len(comparisons) == 1: axes = [axes]

        for ax, comp in zip(axes, comparisons):
            # Create box plot using Plotly Express
            fig = px.box(df_data, x=plot_column, y=comp) #, title=comp, color=plot_column) 
                        #, points="all")  # Show individual points
            # make plot for every comparison
            sns.boxplot(data=df_data, ax=ax, x=plot_column, y=comp, **boxplot_kws)
            plt.setp(ax.artists, edgecolor='black')
            plt.setp(ax.lines, color='black')

            # Overlay neg ctrl avg +/- 2 sd as black dashed line
            if neg_ctrl and list_ctrlstats is not None: 
                tup_comp_stdev = [tup for tup in list_ctrlstats if tup[0] == comp][0][2]
                ax.axhline(y=2*tup_comp_stdev, **axhline_kws) # top baseline
                ax.axhline(y=-2*tup_comp_stdev, **axhline_kws) # bottom baseline

            # Adjust x and y axis limits
            plt.ylim(np.floor(df_data[comp].min()), np.ceil(df_data[comp].max()))
            plt.title(comp) ; plt.ylabel(ylab) ; plt.xlabel(xlab)
            plt.xticks(rotation=45, horizontalalignment='right')

        # Adjust dimensions
        plt.tight_layout()
        # Save file
        outpath = Path(out_dir)
        if savefig: 
            out = f'{out_name}.{out_type}'
            plt.savefig(outpath / out, format=out_type, dpi=300)
        if show: plt.show()
        plt.close()

# boxplot(
#     df_filepath="tests/test_data/plot/NZL10196_v9_comparisons.csv", 
#     comparisons=["d3-pos", "d3-neg", "d6-pos"], #, "d6-neg", "d9-pos", "d9-neg"], 
#     plot_conditions = ["PWWP", "ADD", "MTase", "Nterm"], 
#     plot_column="Domain", 
#     neg_ctrl=True, neg_ctrl_col="Gene", neg_ctrl_conditions=["NON-GENE"], 
#     interactive=False, 
# )
# boxplot(
#     df_filepath="tests/test_data/plot/NZL10196_v9_comparisons.csv", 
#     comparisons=["d3-pos", "d3-neg", "d6-pos"], #, "d6-neg", "d9-pos", "d9-neg"], 
#     plot_conditions = ["PWWP", "ADD", "MTase", "Nterm"], 
#     plot_column="Domain", 
#     neg_ctrl=True, neg_ctrl_col="Gene", neg_ctrl_conditions=["NON-GENE"], 
#     interactive=True, 
# )
