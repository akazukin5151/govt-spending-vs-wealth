import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import geopandas as gpd
from mpl_toolkits.axes_grid1 import make_axes_locatable

TOTAL_WEALTH = 'NW.TOW.TO'
HUMAN_CAPITAL = 'NW.HCA.TO'
NATURAL_CAPITAL = 'NW.NCA.TO'
PRODUCED_WEALTH = 'NW.PCA.TO'
NET_FOREIGN_ASSETS = 'NW.NFA.TO'

def main():
    (world, gs, wealth) = load_data()
    #merge_wealth(wealth, wealth_alt)
    df = merge_dfs(gs, wealth)

    total_wealth_df = df[df['wealth_type'] == TOTAL_WEALTH].dropna()
    sorted_df = total_wealth_df.sort_values('percent', ascending=False)
    merged = merge_data(sorted_df, world)

    plot_hist(total_wealth_df)
    plot_bar(sorted_df)
    plot_map(merged)
    plot_year(merged)

def load_data():
    world = gpd.read_file('data/gadm_410-levels.gpkg', layer='ADM_0')

    gs = pd.read_csv(
        'data/govt spending/API_NE.CON.GOVT.KD_DS2_en_csv_v2_4524749.csv',
        skiprows=4
    )
    gs.drop(columns=['Indicator Code', 'Indicator Name'], inplace=True)
    melted = gs.melt(
        id_vars=['Country Name', 'Country Code'],
        value_vars=gs.columns[2:],
        var_name='year',
        value_name='spending'
    )
    melted.dropna(subset=['spending'], inplace=True)
    melted.sort_values('year', ascending=False, inplace=True)
    gs = melted.groupby('Country Name').first().reset_index()
    print(gs['year'].min())

    # use uchardet to detect encoding, as utf-8 doesn't work
    wealth = pd.read_csv(
        'data/wealth/e2d71af5-452c-4b25-b60a-c5d396ec9cc6_Data.csv',
        encoding='ISO-8859-1'
    )
    wealth = wealth[
        ['Country Name', 'Country Code', 'Series Code', '2018 [YR2018]']
    ]

#    wealth_alt = pd.read_csv('data/global-wealth-2017-2018-2023.csv', skiprows=1)
#    wealth_alt = wealth_alt[['Country', '2018']]
#    wealth_alt['2018'] = wealth_alt['2018'].apply(parse_wealth_alt)

    return (world, gs, wealth)

def parse_wealth_alt(s: str) -> float:
    no_comma = s.replace(',', '')
    billions = int(no_comma)
    return billions * 1e9

#def merge_wealth(wealth, wealth_alt):
#    merged = wealth.merge(
#        wealth_alt, left_on='Country Name', right_on='Country',
#        how='outer', indicator=True
#    )
#    print(merged[merged['_merge'] == 'right_only'].dropna())

def merge_dfs(gs, wealth):
    df = gs.merge(wealth, on='Country Code', how='outer', indicator=True)

    print('missing wealth data')
    with pd.option_context('display.max_rows', None):
        print(df[df._merge == 'left_only']['Country Name_x'])

    print('missing govt spending data')
    with pd.option_context('display.max_rows', None):
        print(df[df._merge == 'right_only']['Country Name_y'].drop_duplicates())

    df = df[df._merge == 'both'].drop(columns='_merge')
    df.drop(columns=['Country Name_y'], inplace=True)
    df.columns = [
        'country_name',
        'country_code',
        'year_of_spending',
        'govt_spending',
        'wealth_type',
        'wealth_value',
    ]
    df['percent'] = df['govt_spending'] / df['wealth_value'] * 100
    return df

def plot_hist(total_wealth_df):
    sns.histplot(data=total_wealth_df, x='percent')
    plt.xlabel('Government spending as a percentage of total national wealth')
    plt.ylabel('Frequency')

    plt.tight_layout()
    plt.savefig('out/histogram.png')
    plt.close()

def plot_bar(sorted_df):
    _, ax = plt.subplots(figsize=(10, 40))

    sns.barplot(data=sorted_df, x='percent', y='country_name')

    plt.xlabel('Government spending as a percentage of total national wealth')
    plt.title('Government spending as a percentage of total national wealth')
    plt.tight_layout()
    plt.savefig('out/bar.png')
    plt.close()
    return sorted_df

def merge_data(sorted_df, world):
    cleaned = sorted_df[['country_code', 'percent', 'year_of_spending']]
    return world.merge(
        cleaned, left_on='GID_0', right_on='country_code',
        how='outer', indicator=True
    )

def plot_map(merged):
    _, ax = plt.subplots(figsize=(20, 10))
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="2%", pad=0.1)
    merged.plot(
        ax=ax,
        column='percent',
        legend=True,
        cmap='Greens',
        cax=cax,
        edgecolor='black',
        missing_kwds={
            "color": "lightgrey",
            "hatch": "///",
            "label": "No data",
        }
    )
    sns.despine(ax=ax, left=True, bottom=True)
    plt.tight_layout()
    plt.savefig('out/map.png')
    plt.close()

def plot_year(merged):
    _, ax = plt.subplots(figsize=(20, 10))
    merged.plot(
        ax=ax,
        column='year_of_spending',
        legend=True,
        edgecolor='black',
        missing_kwds={
            "color": "lightgrey",
            "hatch": "///",
            "label": "No data",
        }
    )
    sns.despine(ax=ax, left=True, bottom=True)
    plt.tight_layout()
    plt.savefig('out/year.png')
    plt.close()


main()
