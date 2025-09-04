import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import polars as pl
import gsw
from tqdm import tqdm

# Mapping colour palettes
import cmocean.cm as cm
palette_map = {
    'PRES': cm.deep,
    'CONS_TEMP': cm.thermal,
    'ABS_SALINITY': cm.haline,
    'OXY': cm.oxy,
    'DENSITY': cm.dense,
    'POT_DENSITY': cm.dense,
    'CHLA': cm.algae,
    'BBP': cm.matter,
    'BBP1': cm.matter,
    'BBP2': cm.matter,
}


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

def plot_processing(df, time_range=(np.datetime64('2025-04-15'), np.datetime64('2025-08-21'))):
    """
    Processes a DataFrame by filling missing values, dropping nulls, and adding a 'depth' column
    calculated from pressure and latitude. Also adds an elapsed time column.

    args:
        df (polars.DataFrame): The input DataFrame to process.

    return:
        polars.DataFrame: The processed DataFrame with a 'depth' column.
    """

    # Convert to OG1
    column_name_map = {
        'datetime': 'TIME',
        'm_lat': 'LATITUDE',
        'm_lon': 'LONGITUDE',
        'sci_water_pressure': 'PRES',
        'sci_water_temp': 'TEMP',
        'sci_water_cond': 'CNDC',
        'sci_flbbbbv1_fl_scaled': 'CHLA',
        'sci_flbbcd_chlor_units': 'CHLA',
        'sci_oxy4_oxygen': 'OXY',
        'sci_flbbbbv1_bb1_scaled': 'BBP1',
        'sci_flbbbbv1_bb2_scaled': 'BBP2',
        'sci_flbbcd_bb_units': 'BBP'
    }

    ignore_cols = []
    for col_name in column_name_map.keys():
        if col_name not in df.columns:
            ignore_cols.append(col_name)
    for col_name in ignore_cols:
        column_name_map.pop(col_name)
    df = df.rename(column_name_map)

    # truncate to time_range
    df = df.filter(
        pl.col('TIME') > time_range[0],
        pl.col('TIME') < time_range[1]
    )

    # Forward fill missing values and drop any remaining nulls
    df = df.select(pl.all().forward_fill())

    # Correct units
    df = df.with_columns(
        pl.col('PRES') * 10,
        pl.col('CNDC') * 10
    )

    # Derive CTD variables
    gsw_function_calls = (
        ("DEPTH", gsw.z_from_p, ["PRES", "LATITUDE"]),
        ("PRAC_SALINITY", gsw.SP_from_C, ["CNDC", "TEMP", "PRES"]),
        ("ABS_SALINITY", gsw.SA_from_SP, ["PRAC_SALINITY", "PRES", "LONGITUDE", "LATITUDE"]),
        ("CONS_TEMP", gsw.CT_from_t, ["ABS_SALINITY", "TEMP", "PRES"]),
        ("DENSITY", gsw.rho, ["ABS_SALINITY", "CONS_TEMP", "PRES"]),
        ('POT_DENSITY', gsw.sigma0, ["ABS_SALINITY", "CONS_TEMP"])
    )

    # Process each GSW function call to derive new variables
    for var_name, func, args in gsw_function_calls:
        print(f"Deriving {var_name}...")
        df = df.with_columns(
            pl.struct(args).map_batches(
                lambda x: func(*(x.struct.field(arg) for arg in args))
            ).alias(var_name)
        )

    # Add a new column 'elapsed_time' as time from deployment start in days
    df = df.select(
        pl.col(['TIME']),
        ((pl.col('TIME') - pl.col('TIME').first()).dt.total_nanoseconds() * 1e-9)
        .alias('ELAPSED_TIME[s]'),
        pl.all().exclude(['TIME'])
    )

    return df

def transects(df, vars_to_plot: list, depth_col='DEPTH', time_col='TIME', force_norm={}, ylims=None):
    """
    Creates scatter plots of various variables against depth and time, excluding specified columns.

    args:
        df (polars.DataFrame): The input DataFrame to plot.
        depth_col (str, optional): The column name for depth data. Default is 'depth'.
        time_col (str, optional): The column name for time data. Default is 'datetime'.
        hue_norm_percentiles (tuple, optional): Percentiles for normalizing the hue values. Default is (1, 99).

    return:
        matplotlib.figure.Figure: The figure containing the plots.
    """

    # Set the Seaborn theme
    sns.set_theme()

    # Create subplots for each variable to plot
    fig, axs = plt.subplots(nrows=len(vars_to_plot), figsize=(15, 5 * len(vars_to_plot)))

    # Plot each variable against depth and time
    for ax, var in tqdm(zip(axs, vars_to_plot), total=len(vars_to_plot)):
        # Check if vmin and vmax have been specified
        if var in force_norm.keys():
            vmin = force_norm[var][0]
            vmax = force_norm[var][1]
        else:
            # find the 1st and 99th percentiles for the variable
            hue_lims = df.select(
                pl.col(var).quantile(0.01).name.suffix('_vmin'),
                pl.col(var).quantile(0.99).name.suffix('_vmax')
            )
            vmin, vmax = hue_lims[f'{var}_vmin'][0], hue_lims[f'{var}_vmax'][0]

        # Check if the vmin, vmax are OK. If not then skip this plot
        if (vmin is not None) & (vmax is not None):
            # Assign a colour palette:
            palette = palette_map[var]
            norm = plt.Normalize(vmin=vmin, vmax=vmax)
            cbar_map = mpl.cm.ScalarMappable(norm=norm, cmap=palette)

            # Create a scatter plot
            sns.scatterplot(
                data=df, x=time_col, y=depth_col, hue=var,
                edgecolor=None,
                palette=palette,
                legend=False,
                hue_norm=norm,
                rasterized=True,
                ax=ax
            )
            ax.figure.colorbar(cbar_map, ax=ax, pad=0.01, label=f'{var} [units not available]')

            # Set the title and legend for the plot
            ax.set(
                title=var,
                ylim=ylims
            )

    # Adjust the layout of the figure
    fig.tight_layout()

    return fig

def profiles(df, vars_to_plot: list, depth_col='DEPTH', time_col='timestamp'):

    plot_lims = df.select(
        pl.all().quantile(0.01).name.suffix('_low'),
        pl.all().quantile(0.99).name.suffix('_high')
    )

    recent_data = df.filter(
        ((pl.col('timestamp').last()-pl.col('timestamp'))*1e-3/3600) < 2
    )

    sns.set_theme()

    ncols = 3
    nrows = np.ceil(len(vars_to_plot)/ncols).astype(int)
    fig, axs = plt.subplots(nrows=nrows, ncols=ncols, figsize=(15, 5*nrows))
    for ax, var in tqdm(zip(axs.flatten(), vars_to_plot), total=len(vars_to_plot)):
        sns.scatterplot(
            data=df,
            x=var, y=depth_col, hue=time_col,
            alpha=0.5,
            edgecolor=None,
            size=0.05,
            palette='Blues',
            ax=ax,
            legend=False
        )
        sns.scatterplot(
            data=recent_data,
            x=var, y=depth_col,
            color='r',
            edgecolor=None,
            size= 0.1,
            ax=ax,
            legend=False
        )
        xmin, xmax = plot_lims[f'{var}_low'][0], plot_lims[f'{var}_high'][0]
        if (xmin is not None) & (xmax is not None):
            pad = 0.2*(xmax-xmin)
            ax.set(
                xlim=[xmin-pad, xmax+pad]
            )

    # Adding time colourbar
    fig.subplots_adjust(top=0.95, bottom=0.4/nrows, left=0.075, right=0.975, wspace=0.3, hspace=0.2)
    last_row = axs.flatten()[-3:]
    l, r = (last_row[0].get_position().get_points()[0, 0],
            last_row[-1].get_position().get_points()[1, 0])
    plot_dims = last_row[0].get_position().get_points()  # [[x0, y0], [x1, y1]]
    h = (plot_dims[1, 1] - plot_dims[0, 1]) * 0.1
    b = plot_dims[0, 1]-h*3
    cbar_ax = fig.add_axes((l, b, r-l, h))

    time = df['timestamp'].to_numpy()*1e-3/(3600*24)
    time = time-time[0]
    vmin, vmax = time.min(), time.max()
    norm = plt.Normalize(vmin=vmin, vmax=vmax)
    cbar_map = mpl.cm.ScalarMappable(norm=norm, cmap=mpl.cm.Blues)
    fig.colorbar(cbar_map, cax=cbar_ax, orientation='horizontal', label='Time [D]')

    # annotation for red dot
    pos = (l+0.03, b-0.03)
    circle = mpl.patches.Circle(pos, radius=0.005,
                                transform=fig.transFigure,
                                facecolor='#C44E52')
    fig.patches.append(circle)
    fig.text(pos[0]+0.01, pos[1], 'Last 2h',
             transform=fig.transFigure,
             verticalalignment='center')

    return fig

def ts_space(df, hue_var='DEPTH', hue_norm_percentiles=(1, 99)):

    xlims = (np.percentile(df['ABS_SALINITY'].drop_nulls().to_numpy(), (1, 99)))
    ylims = (np.percentile(df['CONS_TEMP'].drop_nulls().to_numpy(), (1, 99)))
    df = df.filter(
        pl.col('ABS_SALINITY') > xlims[0],
        pl.col('ABS_SALINITY') < xlims[1],
        pl.col('CONS_TEMP') > ylims[0],
        pl.col('CONS_TEMP') < ylims[1]
    )

    vmin, vmax = np.percentile(df[hue_var].to_numpy(), hue_norm_percentiles)
    norm = plt.Normalize(vmin=vmin, vmax=vmax)
    fig, ax = plt.subplots(figsize=(10, 10))
    sns.scatterplot(data=df, x='ABS_SALINITY', y='CONS_TEMP',
                    hue=hue_var, size=hue_var, palette='managua', edgecolor=None,
                    hue_norm=norm, rasterized=True, legend=False, ax=ax)

    # Colourbar creation
    cbar_map = mpl.cm.ScalarMappable(norm=norm, cmap=mpl.cm.managua)
    ax.figure.colorbar(cbar_map, ax=ax, pad=0.01, label=f'{hue_var}')

    # axes formatting
    ax.set(
        title='TS Space',
        ylabel='CONS_TEMP',
        xlabel='ABS_SALINITY',
    )

    return fig

def currents(df, n_plots=4, lims=[(-55.5, -55), (58.85, 59.3)]):

    subset_size = len(df)/n_plots
    df = df.with_row_index().with_columns(
        (pl.col("index") // subset_size).alias("subset")
    )
    fig, axs = plt.subplots(nrows=n_plots, figsize=(6, 6*n_plots))

    # Plot arrows
    for i in range(n_plots):
        data=df.filter(pl.col('subset') == i)
        axs[i].quiver(data['LONGITUDE'], data['LATITUDE'], data['m_final_water_vx'], data['m_final_water_vy'],
                      angles='xy', scale_units='xy', scale=20,
                      color='red', alpha=0.7, width=0.003)

        axs[i].plot(
            df['LONGITUDE'], df['LATITUDE'],
            c='gray', linestyle='-',
            alpha=0.9
        )

        axs[i].plot(
            data['LONGITUDE'], data['LATITUDE'],
            c='blue', marker='o', linestyle='--',
            alpha=0.6
        )


        # Formatting
        axs[i].set(
            xlabel='Longitude',
            ylabel='Latitude',
            title=f'{data['TIME'].min()}',
            xlim=lims[0],
            ylim=lims[1]
        )
        axs[i].grid(True, alpha=0.3)
        axs[i].set_aspect('equal')

    plt.tight_layout()
    return fig


if __name__ == '__main__':
    test_data = r'C:\Users\ddab1n24\Desktop\Repos\Autonomy_Repos\RTData\outputs\unit_408_2025-08-26.csv'
    df = explode_variable_output(test_data)
    plot_df = plot_processing(df)  # .gather_every(100)

    # variables to plot:
    vars_to_plot = [
        'CONS_TEMP',
        'ABS_SALINITY',
        'DENSITY',
        'POT_DENSITY',
        'OXY',
        'CHLA',
        # 'BBP1',
        # 'BBP2',
        # 'BBP'
    ]

    # print('\nPlotting variable profiles...')
    # depth_var_fig = profiles(plot_df, vars_to_plot)
    # print('Saving... \n')
    # depth_var_fig.savefig(f'../outputs/{test_data.split('\\')[-1][:-4]}_profiles.png')
    #
    # print('Plotting variable transects...')
    # transect_fig = transects(plot_df, vars_to_plot, force_norm={}, ylims=(-100, 0))
    # print('Saving... \n')
    # transect_fig.savefig(f'../outputs/{test_data.split('\\')[-1][:-4]}_transects.png')
    # 
    # print('Plotting TS space...')
    # ts_fig = ts_space(plot_df, hue_var='DEPTH')
    # print('Saving... \n')
    # ts_fig.savefig(f'../outputs/{test_data.split('\\')[-1][:-4]}_ts_space.png')
    #
    # print('Plotting currents...')
    # currents_fig = currents(plot_df.gather_every(100))
    # print('Saving... \n')
    # currents_fig.savefig(f'../outputs/{test_data.split('\\')[-1][:-4]}_currents.png')
    # print('Done :)')
