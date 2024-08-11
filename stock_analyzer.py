from quickfs import QuickFS
import os
import pandas as pd
from matplotlib import pyplot as plt
import statistics

def get_data(ticker, country, exchange):
    # load the key from the enviroment variables
    api_key = 'fa5a33285245cf6b0ba079906295fd6bd89fce2d'

    client = QuickFS(api_key)

    # Request reference data for the supported companies
    client.get_api_metadata()
    if country == "CA":
        client.get_supported_companies(country=country, exchange='TORONTO')
    else:
        print(country, exchange, ticker)
        client.get_supported_companies(country=country, exchange=exchange)


    resp = client.get_data_full(symbol=ticker + ":" + country)

    df_annual = pd.DataFrame(resp['financials']['annual'])
    df_ttm = pd.DataFrame({k: [v] for k, v in resp['financials']['ttm'].items()})

    return df_annual, df_ttm

def print_intrinsic_value(cagr, df_ttm):
    intrinsic_value = intrinsic_value_formula(cagr, 0.15, df_ttm['fcf'][0])
    print(f"intrinsic value: {intrinsic_value} based on {cagr}%")
    print(f"market cap (ttm): {df_ttm['market_cap'][0]}")
    print (f"50% cost: {intrinsic_value/df_ttm['shares_eop'][0]*0.5}")
    print (f"75% cost: {intrinsic_value/df_ttm['shares_eop'][0]*0.75}")
    print (f"100% cost: {intrinsic_value/df_ttm['shares_eop'][0]*1}")
    print (f"125% cost: {intrinsic_value/df_ttm['shares_eop'][0]*1.25}")

def NA_to_0(v):
    if v == 'NA':
        print(v)
        v.value = 0
    return v

def graph_data(df_annual, df_ttm):
    # Assuming cagr_stats returns a list of lists with CAGR values
    cagr = cagr_stats(df_annual)
    # Combine the dataframes
    df = pd.concat([df_annual, df_ttm])
    
    # Extract data
    year = df['period_end_date']
    revenue = df['revenue']
    fcf = df['fcf_per_share']
    eps = df['eps_diluted']
    dps = df['dividends']
    roce = df['roce']

    # Create subplots
    fig, axs = plt.subplots(3, 3, figsize=(20, 11))
    
    # Define titles
    title1 = f'Revenue: CAGR 10y, 5y, 3y, 1y: {cagr[0][0]}% {cagr[0][1]}% {cagr[0][2]}% {cagr[0][3]}%'
    title2 = f'Free Cash Flow per Share: CAGR 10y, 5y, 3y, 1y: {cagr[1][0]}% {cagr[1][1]}% {cagr[1][2]}% {cagr[1][3]}%'
    title3 = f'Diluted EPS: CAGR 10y, 5y, 3y, 1y: {cagr[2][0]}% {cagr[2][1]}% {cagr[2][2]}% {cagr[2][3]}%'
    title4 = f'Dividends per Share: CAGR 10y, 5y, 3y, 1y: {cagr[3][0]}% {cagr[3][1]}% {cagr[3][2]}% {cagr[3][3]}%'
    title5 = f'operating margin: CAGR 10y, 5y, 3y, 1y: {cagr[4][0]}% {cagr[4][1]}% {cagr[4][2]}% {cagr[4][3]}%'
    title6 = f'ROCE: CAGR 10y, 5y, 3y, 1y: {cagr[5][0]}% {cagr[5][1]}% {cagr[5][2]}% {cagr[5][3]}%'
    

    # Plot on each subplot
    make_graph(axs[0, 0], year.astype(str), revenue, title1)
    make_graph(axs[0, 1], year.astype(str), fcf, title2)
    make_graph(axs[1, 0], year.astype(str), eps, title3)
    make_graph(axs[1, 1], year.astype(str), dps, title4)
    make_graph(axs[1, 2], year.astype(str), roce, title6)
    if 'operating_margin' in df:
        op_margin = df['operating_margin']
        make_graph(axs[0, 2], year.astype(str), op_margin, title5)
    if 'price_to_book' in df:
        pb = df['price_to_book']
        title7 = f'Historical P/B (r=10y, m=5y, y=3y): {round(statistics.mean(pb[-10:]), 2)} {round(statistics.mean(pb[-5:]), 2)} {round(statistics.mean(pb[-3:]), 2)} TTM: {round(pb[-1:][0], 2)}' 
        make_line_graph(axs[2, 0], year.astype(str), pb, title7)
    if 'price_to_earnings' in df:
        pe = df['price_to_earnings']
        title8 = f'Historical P/E (r=10y, m=5y, y=3y): {round(statistics.mean(pe[-10:]), 2)} {round(statistics.mean(pe[-5:]), 2)} {round(statistics.mean(pe[-3:]), 2)} TTM: {round(pe[-1:][0], 2)}'
        make_line_graph(axs[2, 1], year.astype(str), pe, title8)
    if 'payout_ratio' in df:
        payout_ratio = df['payout_ratio']
        title9 = f'Historical Payout ratio: 10y, 5y, 3y, TTM; {round(statistics.mean(payout_ratio[-10:]*100), 2)}% {round(statistics.mean(payout_ratio[-5:]*100), 2)}% {round(statistics.mean(payout_ratio[-3:]*100), 2)}% {round(payout_ratio[-1:][0]*100, 2)}%'
        make_graph(axs[2, 2], year.astype(str), payout_ratio, title9)
    
    # Adjust layout
    fig.tight_layout()
    
    print_intrinsic_value(20, df_ttm)
    print_intrinsic_value(15, df_ttm)
    print_intrinsic_value(10, df_ttm)
    print("---------------------------------------------------------")
    print_intrinsic_value(cagr[1][0], df_ttm)
    print_intrinsic_value(cagr[1][1], df_ttm)
    print("---------------------------------------------------------")
    stats = ""
    if 'operating_margin' in df:
        stats = f"operating_margin: {df_ttm['operating_margin'][0]}     "
    stats += f"roce: {df_ttm['roce'][0]}   fcf yield (fcf/ev): {round(df_ttm['fcf'][0] / df_ttm['enterprise_value'][0] * 100, 2)}"
    print(stats)

    # Show plot
    plt.show()

def cagr_stats(df_a):
    result = []
    gr10 = 0
    gr5 = 0
    gr3 = 0
    gr1 = 0

    for key in ['revenue', 'fcf_per_share', 'eps_diluted', 'dividends', 'operating_margin', 'roce']:
        if len(df_a) >= 10:
            if key in df_a:
                gr10 = cagr_formula(10, df_a[key])
                gr5 = cagr_formula(5, df_a[key])
                gr3 = cagr_formula(3, df_a[key])
                gr1 = cagr_formula(1, df_a[key])
            
        result.append([round(gr10*100, 2),round(gr5*100, 2),round(gr3*100, 2),round(gr1*100, 2)])

    return result

def cagr_formula(years, col):
    if col.iloc[-(1 + years)] <= 0 or col.iloc[-1] <= 0:
        return 0
    return (col.iloc[-1] / col.iloc[-(1 + years)]) ** (1 / years) - 1

def intrinsic_value_formula(fcf_growth, discount_rate, initial_value):
    projected_values = []
    for year in range(1,11):
        compounded_value = initial_value * (1 + (fcf_growth/100)) ** year / (1 + discount_rate) ** year
        projected_values.append(int(compounded_value))

    intrinsic_value = (sum(projected_values) + projected_values[len(projected_values) - 1] * 10)
    return intrinsic_value

def make_graph(ax, x, y, title):
    ax.bar(x, y.astype(float))
    ax.set_xticks(range(len(x)))
    ax.set_xticklabels(x, rotation=45, ha='right')
    ax.set_title(title)

def make_line_graph(ax, x, y, title):
    ax.plot(x, y)
    ax.set_xticks(range(len(x)))
    ax.set_xticklabels(x, rotation=45, ha='right')
    ax.set_title(title)
    ax.axhline(y = statistics.mean(y[-10:]), color = 'r', linestyle = '-')
    ax.axhline(y = statistics.mean(y[-5:]), color = 'm', linestyle = '-')
    ax.axhline(y = statistics.mean(y[-3:]), color = 'y', linestyle = '-')

def main():
    stop = False
    exchange = ''
    country = input('enter country (ca/us): ').upper()
    if country == 'US':
        exchange = input('enter exchange (nyse/nasdaq): ').upper()

    #main loop
    while(not stop):
        ticker = input('enter ticker symbol: ').upper()
        print(f"fetching {ticker}:{country}")
        #try:
        df_a, df_t = get_data(f'{ticker}', country, exchange)
        graph_data(df_a, df_t)
        '''        except:
            print(f"Error fetching {ticker}")'''
    
        yorn = input("would you like to enter a new ticker symbol? (y/n): ")
        if yorn == 'n':
            stop = True
        
if __name__ == main():
    main()