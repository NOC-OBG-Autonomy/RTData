import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import polars as pl
import gsw
# TODO: update requirements


def explode_variable_output(fname):
    """
    Reads a CSV file and transforms the data by pivoting it based on the 'variable' column
    and converting timestamps to datetime objects.

    args:
        fname (str): The filename of the CSV file to read.

    return:
        polars.DataFrame: The transformed DataFrame with datetime objects.
    """
    df = pl.read_csv(fname)

    # Basically makes the var names in 'variables' into the columns of a new DataFrame.
    df = df.pivot('variable', index='timestamp', values='value', aggregate_function='last')

    # Convert 'timestamp' to datetime and add it as a new column 'datetime'
    df = df.select(
        (pl.datetime(1970, 1, 1) + pl.duration(milliseconds=pl.col('timestamp'))).alias('datetime'),
        pl.all()
    )

    return df


def plot_processing(df, pres_col='sci_water_pressure', lat_col='m_lat'):
    """
    Processes a DataFrame by filling missing values, dropping nulls, and adding a 'depth' column
    calculated from pressure and latitude. Also adds an elapsed time column.

    args:
        df (polars.DataFrame): The input DataFrame to process.
        pres_col (str, optional): The column name for pressure data. Default is 'sci_water_pressure'.
        lat_col (str, optional): The column name for latitude data. Default is 'm_lat'.

    return:
        polars.DataFrame: The processed DataFrame with a 'depth' column.
    """
    # Forward fill missing values and drop any remaining nulls
    df = df.select(pl.all().forward_fill()).drop_nulls()

    # Add a new column 'depth' calculated from pressure and latitude
    df = df.with_columns(
        pl.struct(pres_col, lat_col).map_batches(
            lambda x: gsw.z_from_p(x.struct.field(pres_col)*10, x.struct.field(lat_col))
        ).alias('depth')
    )

    # Add a new column 'elapsed_time' as time from deployment start in days
    df = df.with_columns(
        ((pl.col('timestamp') - pl.col('timestamp').first())*1e-3/(3600*24))
        .alias('elapsed_time[d]')
    )

    return df


def plot_transect(df, depth_col='depth', time_col='datetime', exclude=[], hue_norm_percentiles=(1, 99)):
    """
    Creates scatter plots of various variables against depth and time, excluding specified columns.

    args:
        df (polars.DataFrame): The input DataFrame to plot.
        depth_col (str, optional): The column name for depth data. Default is 'depth'.
        time_col (str, optional): The column name for time data. Default is 'datetime'.
        exclude (list, optional): List of column names to exclude from plotting. Default is [].
        hue_norm_percentiles (tuple, optional): Percentiles for normalizing the hue values. Default is (1, 99).

    return:
        matplotlib.figure.Figure: The figure containing the plots.
    """
    # Get the list of variables to plot, excluding specified columns
    vars_to_plot = df.columns
    for var in exclude + [depth_col, time_col]:
        vars_to_plot.remove(var)

    # Set the Seaborn theme
    sns.set_theme()

    # Create subplots for each variable to plot
    fig, axs = plt.subplots(nrows=len(vars_to_plot), figsize=(15, 5 * len(vars_to_plot)))

    # Plot each variable against depth and time
    for ax, var in zip(axs, vars_to_plot):
        # Calculate the percentiles for hue normalization
        vmin, vmax = np.percentile(df[var].to_numpy(), hue_norm_percentiles)

        # Create a scatter plot
        sns.scatterplot(
            data=df, x=time_col, y=depth_col, hue=var, edgecolor=None,
            palette='summer', hue_norm=(vmin, vmax), ax=ax
        )

        # Set the title and legend for the plot
        ax.set(title=var)
        ax.legend(loc='upper right')

    # Adjust the layout of the figure
    fig.tight_layout()

    return fig

def plot_vars_against_depth(df, depth_col='depth', time_col='timestamp', exclude=[]):

    plot_lims = df.select(
        pl.all().quantile(0.01).name.suffix('_low'),
        pl.all().quantile(0.99).name.suffix('_high')
    )

    recent_data = df.filter(
        ((pl.col('timestamp').last()-pl.col('timestamp'))*1e-3/3600) < 2
    )

    vars_to_plot = df.columns
    for var in exclude + [depth_col, time_col]:
        vars_to_plot.remove(var)

    sns.set_theme()

    ncols = 3
    nrows = np.ceil(len(vars_to_plot)/ncols).astype(int)
    fig, axs = plt.subplots(nrows=nrows, ncols=ncols, figsize=(15, 5*nrows))
    for ax, var in zip(axs.flatten(), vars_to_plot):
        sns.scatterplot(data=df, x=var, y=depth_col, hue=time_col,
                        alpha=0.5,
                        edgecolor=None,
                        size=0.05,
                        palette='Blues',
                        ax=ax,
                        legend=False)
        sns.scatterplot(data=recent_data, x=var, y=depth_col,
                        color='r',
                        edgecolor=None,
                        size= 0.1,
                        ax=ax,
                        legend=False)
        xmin, xmax = plot_lims[f'{var}_low'][0], plot_lims[f'{var}_high'][0]
        pad = 0.2*(xmax-xmin)
        ax.set(
            xlim=[xmin-pad, xmax+pad]
        )

    fig.tight_layout()

    return fig

if __name__ == '__main__':
    test_data = r'C:\Users\ddab1n24\Desktop\Repos\Autonomy_Repos\RTData\outputs\unit_306_ts.csv'
    df = explode_variable_output(test_data)
    plot_df = plot_processing(df)
    transect_fig = plot_vars_against_depth(plot_df, time_col='elapsed_time[d]',
                                           exclude=['datetime', 'timestamp', 'm_lat', 'm_lon'])
    plt.show(block=True)
    # transect_fig.savefig('../outputs/transect.png')

