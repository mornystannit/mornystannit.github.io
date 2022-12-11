# Rank largest changes in the binary prediction data. 



# from collections import Counter
from datetime import datetime
# from itertools import chain
# from pprint import pprint
# from tqdm import tqdm
# tqdm.pandas()

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from statsmodels.nonparametric.smoothers_lowess import lowess
from scipy.signal import find_peaks_cwt
# import seaborn as sns
# pd.options.mode.chained_assignment = None



def log_odd(p, base=np.e):
    return np.log(p/(1-p)) / np.log(base)

def add_logs(df, base):
    """Add logs to the cp and mp"""
    df['logcp'] = log_odd(df['cp'], base)
    # df['logmp'] = log_odd(df['mp'], base)
    return df

def add_deltas(df, timestep):
    """Add time-related deltas and differentials
    NOTE: `df` must either be grouped, or be for a single question only
    NOTE: `df` must have already been passed through `add_logs()` to get log cols
    """
    df = df.sort_index(sort_remaining=False)
    df['dt'] = df['t'].diff()

    df['dcp'] = df['cp'].diff(timestep)
    # df['dmp'] = df['mp'].diff(timestep)

    df['dlogcp'] = df['logcp'].diff(timestep)
    # df['dlogmp'] = df['logmp'].diff(timestep)

    df['dcp_dt'] = df['dcp'] / df['dt']
    # df['dmp_dt'] = df['dmp'] / df['dt']

    df['dlogcp_dt'] = df['dlogcp'] / df['dt']
    # df['dlogmp_dt'] = df['dlogmp'] / df['dt']
    return df

def add_df_deltas_and_logs(df, timestep, base):
    """Wrapper function to get deltas and logs
    NOTE: input `df` must be for a single question only
    """
    df = add_logs(df, base)
    df = add_deltas(df, timestep)
    return df



def get_smoothed_df(df, frac=0.01, rsmpl='6h'):

    '''
    Smooth using statsmodels LOWESS and interpolates points at specified intervals 

    frac: The fraction of the data used when estimating each y-value

    '''
    title = df.title.values[0]

    df_smoothed = pd.DataFrame(lowess(df.cp, np.arange(len(df.cp)), frac=frac)[:, 1], 
                               index=df.index, columns=['cp'])
    # df_smoothed['mp'] = lowess(df.mp, np.arange(len(df.mp)), frac=frac)[:, 1]
    df_smoothed['t'] = df.t

    df_smoothed = df_smoothed[['cp', 't']].resample(rsmpl).mean().interpolate() 
    # df_smoothed = df_smoothed[['cp', 'mp', 't']].resample(rsmpl).mean().interpolate() 

    df_smoothed['title'] = title

    return df_smoothed




def get_peak(gdf, question_id, frac=0.05, plot=False):

    '''
    gdf is a grouped dataframe of predictions by question number, 
        for which we extract groupings. 

    1. Smoothes the community/metaculus predictions time series with frac proportion, 
        and interpolates at 3 hour intervals.
    2. Performs derivatives (and fills values for NaN). 
    3. Performs smoothing for the cp derivative: with frac=0.01
    4. Finds peaks and takes the largest peak. 
    5. Returns the time of the largest peak slice. 

    '''


    df= gdf.get_group(question_id)

    df = get_smoothed_df(df, frac=frac, rsmpl='1h')
    q_df = add_df_deltas_and_logs(df, timestep=1, base=np.e)
    q_df = q_df.bfill(limit=1) # get rid of NaN

    q_df['abs_dcp_dt'] = abs(q_df['dcp_dt'])

    # q_df['r_av_abs_dcp_dt'] = q_df.abs_dcp_dt.rolling(2, center=True, closed='both').mean()
    q_df['lowess_abs_dcp_dt'] = pd.Series(lowess(q_df.abs_dcp_dt, np.arange(len(q_df.abs_dcp_dt)), 
                                            frac=0.01)[:, 1], index=q_df.index)

    peaks_found = find_peaks_cwt(q_df.lowess_abs_dcp_dt.values, widths=5)
    # peaks = peaks_found[0]
    # metadata = peaks_found[1]
    peaks=peaks_found
    peak_scatter = q_df.iloc[peaks]
    
    peak_val = peak_scatter.sort_values(by='lowess_abs_dcp_dt', ascending=False).iloc[0]

    # if plot:
        
    #     fig = make_subplots(specs=[[{"secondary_y": True}]])

    #     fig.add_trace(go.Scatter(x=q_df.index.astype(dtype=str), 
    #                             y=q_df['lowess_abs_dcp_dt'],
    #                             text="abs dcp/dt smoothed", 
    #                             name="abs dcp/dt smoothed"))

    #     fig.add_trace(go.Scatter(x=peak_scatter.index,  
    #                             y=peak_scatter.lowess_abs_dcp_dt,
    #                             mode='markers', marker_color='blue', 
    #                             name='found peaks'))

    #     fig.add_trace(go.Scatter(x=[peak_val.name],  
    #                     y=[peak_val.lowess_abs_dcp_dt],
    #                     mode='markers', marker_color='red', 
    #                     name='Highest Peak'))


    #     fig.add_trace(go.Scatter(x=q_df.index.astype(dtype=str), 
    #                             y=q_df['cp'],
    #                             text="cp", name="cp"), secondary_y=True)

    #     fig.update_layout({"title": f'{q_df.title.values[0]}',
    #                     "xaxis": {"title":"time"},
    #                     "showlegend": True})

    #     fig.update_yaxes(title_text="dcp/dt", secondary_y=False)
    #     fig.update_yaxes(title_text="cp", secondary_y=True)
    #     # fig.write_image("by-month.png",format="png", width=1000, height=600, scale=3)
    #     fig.show()
    return peak_val




def find_significant_changes(questions):
    """
    Loop over all questions and find each questions' highest peak. 

    Rank peaks and output the top 10. 

    """
    binary = questions.copy(True)
    qids = binary.question_id.unique() 
    gdf = binary.groupby('question_id') 

    all_peak_values = []
    for i in qids: 
        peak_val = get_peak(gdf, i, frac=0.05)
        peak_val['question_id'] = i
        all_peak_values.append(peak_val)

    all_peak_values = pd.DataFrame(all_peak_values).sort_values(by='lowess_abs_dcp_dt', 
                                    ascending=False)[['question_id']] # peaks' qids

    all_peak_values.index.names = ['peak_time']
    changes = all_peak_values.reset_index()
    changes = changes.set_index('question_id')
    # print(all_peak_values)

    return changes


if __name__ == '__main__':
    print('Hello')