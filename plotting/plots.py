import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import polars as pl
import gsw
# TODO: update requirements

def explode_variable_output(fname):
    df = pl.read_csv(fname)
    df = df.pivot('variable', index='timestamp', values='value', aggregate_function='last')
    df = df.select((pl.datetime(1970,1,1) + pl.duration(milliseconds=pl.col('timestamp'))).alias('datetime'),
                   pl.all())
    return df

def plot_processing(df, pres_col='sci_water_pressure', lat_col='m_lat'):
    df = df.select(pl.all().forward_fill()).drop_nulls()
    df = df.with_columns(
        pl.struct(pres_col, lat_col).map_batches(
            lambda x: gsw.z_from_p(x.struct.field(pres_col), x.struct.field(lat_col))
        ).alias('depth')
    )
    return df

def plot_transect(df, depth_col='depth', time_col='datetime', exclude=[], hue_norm_percentiles=(1,99)):
    vars_to_plot = df.columns
    for var in exclude + [depth_col, time_col]:
        vars_to_plot.remove(var)

    sns.set_theme()
    fig, axs = plt.subplots(nrows=len(vars_to_plot), figsize=(15, 5*len(vars_to_plot)))
    for ax, var in zip(axs, vars_to_plot):
        vmin, vmax = np.percentile(df[var].to_numpy(), hue_norm_percentiles)
        sns.scatterplot(
            data=df, x=time_col, y=depth_col, hue=var, edgecolor=None,
            palette='summer', hue_norm=(vmin, vmax), ax=ax
        )
        ax.set(
            title=var,
        )
        ax.legend(loc='upper right')
    fig.tight_layout()
    return fig

if __name__ == '__main__':
    test_data = r'C:\Users\ddab1n24\Desktop\Repos\Autonomy_Repos\RTData\outputs\unit_306_ts.csv'
    df = explode_variable_output(test_data)
    plot_df = plot_processing(df)
    transect_fig = plot_transect(plot_df, exclude=['m_lat', 'm_lon', 'timestamp', 'sci_water_pressure'])
    transect_fig.savefig('../outputs/transect.png')

