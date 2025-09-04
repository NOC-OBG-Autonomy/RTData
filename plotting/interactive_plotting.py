from plots import explode_variable_output, plot_processing
from matplotlib.gridspec import GridSpec
import numpy as np
import polars as pl
from scipy.interpolate import griddata
import matplotlib.pyplot as plt
import matplotlib.widgets as widgets
import matplotlib as mpl
import cmocean.cm as cm
mpl.use('tkagg')

def interactive(df):

    # Set figure layout
    gs = GridSpec(ncols=4, nrows=3, height_ratios=[1, 1, 0.1])
    fig = plt.figure(figsize=(18, 9))
    ax_map = fig.add_subplot(gs[0:2, 0:2])
    ax0, ax1 = fig.add_subplot(gs[0, 2]), fig.add_subplot(gs[0, 3])
    ax2, ax3 = fig.add_subplot(gs[1, 2]), fig.add_subplot(gs[1, 3])
    widget_ax = fig.add_subplot(gs[2, :])


    glider_path, = ax_map.plot(df['LONGITUDE'], df['LATITUDE'], c='blue', linestyle='-')
    temp, = ax0.plot(df['CONS_TEMP'], df['DEPTH'], c='blue', linestyle='', marker='o')
    salinity, = ax1.plot(df['ABS_SALINITY'], df['DEPTH'], c='blue', linestyle='', marker='o')
    density, = ax2.plot(df['POT_DENSITY'], df['DEPTH'], c='blue', linestyle='', marker='o')
    ts_space, = ax3.plot(df['ABS_SALINITY'], df['CONS_TEMP'], c='blue', linestyle='', marker='o')

    # Define UX params
    # TODO: adjust min/max values
    slider = widgets.RangeSlider(widget_ax, "Time Range", df['timestamp'].min(), df['timestamp'].max())

    # Define an update function for the plot
    def update(val):
        # Data to plot
        data = df.filter(
            pl.col('timestamp') > val[0],
            pl.col('timestamp') < val[1],
        )

        glider_path.set_data(data['LONGITUDE'], data['LATITUDE'])
        for line, var in zip([temp, salinity, density], ['CONS_TEMP', 'ABS_SALINITY', 'POT_DENSITY']):
            line.set_data(data[var], data['DEPTH'])
        ts_space.set_data(data['ABS_SALINITY'], data['CONS_TEMP'])

        fig.canvas.draw_idle()


    slider.on_changed(update)
    plt.show(block=True)


if __name__ == '__main__':
    test_data = r'C:\Users\ddab1n24\Desktop\Repos\Autonomy_Repos\RTData\outputs\unit_306_2025-08-17.csv'
    df = explode_variable_output(test_data)
    df = plot_processing(df, time_range=(np.datetime64('2025-07-18'), np.datetime64('2025-08-18')))


    df = df.select(
        pl.col('TIME'),
        ((pl.col('timestamp') - pl.col('timestamp').min())/(1000*60*60)).alias('ELAPSED_TIME'),
        pl.col(['DEPTH', 'POT_DENSITY'])
    ).drop_nans()

    Nx, Ny = 7000, 800
    t_min, t_max = df['ELAPSED_TIME'].min(), df['ELAPSED_TIME'].max()
    z_min, z_max = int(df['DEPTH'].min()), int(df['DEPTH'].max())
    grid_t, grid_z = np.mgrid[t_min:t_max:Nx*1j, z_min:z_max:Ny*1j]

    points = df[['ELAPSED_TIME', 'DEPTH']].to_numpy()
    values = df['POT_DENSITY'].to_numpy()

    grid_data = griddata(points, values, (grid_t, grid_z), method='linear')

    fig, ax = plt.subplots()
    ax.contourf(grid_t, grid_z, grid_data, cmap=cm.dense)

    t_ticks = [(df['TIME'][0] + np.timedelta64(int(t_val), 'h')).strftime("%Y-%m-%d") for t_val in grid_t[::700, 0]]
    ax.set_xticks(ticks = grid_t[::700, 0], labels=t_ticks)
    plt.show(block=True)

    

