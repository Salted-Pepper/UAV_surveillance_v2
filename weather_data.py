import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns


def fetch_weather_markov_chain(make_plots=True) -> dict:
    import xarray as xr
    df = xr.open_dataset("wave_data.nc", engine="netcdf4").to_dataframe()
    """
    mwd = mean wave direction
    swh = Significant Wave Height
    shww = Significant Height Wind Waves
    """

    df = df.dropna()

    df.unstack(level=-1)
    df = df.reset_index()

    if make_plots:
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.set_title("Distribution of Sea States")
        ax.set_ylabel("Frequency")
        ax.set_xlabel("Significant Wave Height")
        plt.hist(df["swh"], bins=np.arange(int(np.floor(min(df["swh"]))),
                                           int(np.ceil(max(df["swh"]))),
                                           0.25))
        plt.show()

    df["swh_rounded"] = np.round(df["swh"])
    df["swh_rounded_lag"] = df["swh_rounded"].shift(1)

    data = df[["swh_rounded", "swh_rounded_lag"]].dropna()
    data = data.groupby(["swh_rounded", "swh_rounded_lag"]).size().reset_index()
    data = data.rename(columns={0: "count"})

    states = data["swh_rounded"].unique()
    for state in states:
        total_value = sum(data[data["swh_rounded"] == state]["count"])
        data.loc[data["swh_rounded"] == state, 'freq'] = data[data["swh_rounded"] == state]["count"] / total_value

    if make_plots:
        fig = plt.figure()
        pivot = data.pivot(index="swh_rounded", columns="swh_rounded_lag", values='freq')
        sns.set(font_scale=0.7)
        ax = sns.heatmap(pivot, annot=True, fmt='0.3f')
        ax.set_facecolor('white')
        ax.set_title("Sea State Transitions")
        ax.set_xlabel("Next Sea State")
        ax.set_ylabel("Current Sea State")
        fig.show()

    # Creating the DTMC matrix as dictionary:
    matrix = dict()

    for state_0 in states:
        matrix[int(state_0)] = {}
        for state_1 in states:
            state_data = data[(data["swh_rounded"] == state_0) & (data["swh_rounded_lag"] == state_1)]

            if len(state_data) == 0:
                transition_probability = 0
            else:
                transition_probability = state_data['freq']
            matrix[int(state_0)][int(state_1)] = transition_probability

    return matrix
