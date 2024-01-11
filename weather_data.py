import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
from perlin_noise import PerlinNoise

import constants


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
    df["swh_rounded_lag_2"] = df["swh_rounded"].shift(2)

    steps = 9
    df["swh_rounded_lag_steps"] = df["swh_rounded"].shift(steps)

    data = df[["swh_rounded", "swh_rounded_lag", "swh_rounded_lag_2", "swh_rounded_lag_steps"]].dropna()
    data_1 = (data[["swh_rounded", "swh_rounded_lag"]].groupby(["swh_rounded", "swh_rounded_lag"])
              .size().reset_index())
    data_2 = (data[["swh_rounded", "swh_rounded_lag_2"]].groupby(["swh_rounded", "swh_rounded_lag_2"])
              .size().reset_index())
    data_steps = (data[["swh_rounded", "swh_rounded_lag_steps"]].groupby(["swh_rounded", "swh_rounded_lag_steps"])
                  .size().reset_index())
    data_1 = data_1.rename(columns={0: "count"})
    data_2 = data_2.rename(columns={0: "count"})
    data_steps = data_steps.rename(columns={0: "count"})

    states = data_1["swh_rounded"].unique()
    for state in states:
        total_value_1 = sum(data_1[data_1["swh_rounded"] == state]["count"])
        total_value_2 = sum(data_2[data_2["swh_rounded"] == state]["count"])
        total_value_steps = sum(data_steps[data_steps["swh_rounded"] == state]["count"])
        data_1.loc[data_1["swh_rounded"] == state, 'count'] = (
                data_1[data_1["swh_rounded"] == state]["count"] / total_value_1)
        data_2.loc[data_2["swh_rounded"] == state, 'count'] = (
                data_2[data_2["swh_rounded"] == state]["count"] / total_value_2)
        data_steps.loc[data_steps["swh_rounded"] == state, 'count'] = (
                data_steps[data_steps["swh_rounded"] == state]["count"] / total_value_steps)

    if make_plots:
        fig = plt.figure()
        pivot = data_1.pivot(index="swh_rounded", columns="swh_rounded_lag", values='count')
        sns.set(font_scale=0.7)
        ax = sns.heatmap(pivot, annot=True, fmt='0.3f')
        ax.set_facecolor('white')
        ax.set_title("Sea State Transitions")
        ax.set_xlabel("Next Sea State")
        ax.set_ylabel("Current Sea State")
        fig.show()

        fig_2 = plt.figure()
        pivot = data_steps.pivot(index="swh_rounded", columns="swh_rounded_lag_steps", values='count')
        sns.set(font_scale=0.7)
        ax_2 = sns.heatmap(pivot, annot=True, fmt='0.3f')
        ax_2.set_facecolor('white')
        ax_2.set_title(f"Sea State Transitions - {steps} steps")
        ax_2.set_xlabel(f"Next Sea State - {steps} steps")
        ax_2.set_ylabel("Current Sea State")
        fig_2.show()

    # Creating the DTMC matrix as dictionary:
    matrix = dict()

    for state_0 in states:
        matrix[int(state_0)] = {}
        for state_1 in states:

            state_data = data_1[(data_1["swh_rounded"] == state_0) & (data_1["swh_rounded_lag"] == state_1)]

            if len(state_data) == 0:
                transition_probability = 0
            else:
                transition_probability = state_data['count'].item()
            matrix[int(state_0)][int(state_1)] = transition_probability

    if make_plots:
        fig_location = px.scatter(df, x="longitude", y="latitude", animation_frame="time", color="swh")
        fig_location.show()

    return matrix


weather_transition_matrix = fetch_weather_markov_chain(False)


def update_sea_states(world):
    global weather_transition_matrix
    grid = world.receptor_grid
    update_u_values(grid)

    # OLD FORCED AREA-CORRELATION MODEL
    # for receptor in grid.receptors:
    #     surrounding_receptors = grid.select_receptors_in_radius(receptor.location,
    #                                                             radius=9 * max(constants.GRID_WIDTH,
    #                                                                             constants.GRID_HEIGHT))
    #     u_value = (0.2 * receptor.last_uniform_value +
    #                0.8 * (0.1 * receptor.new_uniform_value + sum([0.9 / len(surrounding_receptors)
    #                * r.new_uniform_value
    #                                                               for r in surrounding_receptors])))
    #     transition_probabilities = weather_transition_matrix[receptor.sea_state]
    #     prob = 0
    #     for key in transition_probabilities.keys():
    #         prob += transition_probabilities[key]
    #         if prob > u_value:
    #             receptor.sea_state = key
    #             break

    # PERLIN NOISE MODEL
    for receptor in grid.receptors:
        transition_probabilities = weather_transition_matrix[receptor.sea_state]
        prob = 0
        for key in transition_probabilities.keys():
            prob += transition_probabilities[key]
            if prob > receptor.new_uniform_value:
                receptor.sea_state = key
                break


def update_u_values(grid):
    cols = grid.max_cols
    rows = grid.max_rows

    # TODO: Base octave on weather conditions (lower octave = more stable) -
    #  other option is to scale the distribution dependent on weather conditions

    noise = PerlinNoise(octaves=8)
    noise_data = [[noise([j/rows, i/cols]) for i in range(cols)] for j in range(rows)]
    # normalize noise
    min_value = min(x if isinstance(x, int) else min(x) for x in noise_data)
    noise_data = [[n + abs(min_value) for n in rows] for rows in noise_data]
    max_value = max(x if isinstance(x, int) else max(x) for x in noise_data)
    noise_data = [[n / max_value for n in rows] for rows in noise_data]
    min(x if isinstance(x, int) else min(x) for x in noise_data)
    max(x if isinstance(x, int) else max(x) for x in noise_data)
    new_u_matrix = noise_data

    # new_u_matrix = np.random.uniform(low=0, high=1, size=(rows, cols))
    for index, receptor in enumerate(grid.receptors):

        receptor.last_uniform_value = receptor.new_uniform_value
        receptor.new_uniform_value = new_u_matrix[index // cols][index % cols]
