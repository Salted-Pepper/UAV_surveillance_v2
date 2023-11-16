# python -m pip install "xarray[complete]"
import xarray as xr
import pandas as pd

ds = xr.open_dataset("C:/Users/Gebruiker/PycharmProjects/UAVsurveillance_v2/wave_data.nc", engine='netcdf4')
df = ds.to_dataframe()
df = df.dropna()
df = df.reset_index()

df.hist(column="swh")
