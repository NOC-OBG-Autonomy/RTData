import seaborn as sns
import polars as pl
# TODO: update requirements

def explode_variable_output(fname):
    df = pl.read_csv(fname)
    df = df.pivot('variable', index='timestamp', values='value', aggregate_function='last')
    df = df.select((pl.datetime(1970,1,1) + pl.duration(milliseconds=pl.col('timestamp'))).alias('TIME'),
                   pl.all().exclude('timestamp'))
    return df

if __name__ == '__main__':
    test = r'C:\Users\ddab1n24\Desktop\Repos\Autonomy_Repos\RTData\outputs\unit_306_ts.csv'
    df = explode_variable_output(test)

# 1742648929335