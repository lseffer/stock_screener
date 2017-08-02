import argparse, requests, os
import good_morning as gm
import pandas as pd
import numpy as np
import bs4 as bs

url_list = [
    'http://www.nasdaqomxnordic.com/aktier/listed-companies/copenhagen',
    'http://www.nasdaqomxnordic.com/aktier/listed-companies/helsinki',
    'http://www.nasdaqomxnordic.com/aktier/listed-companies/stockholm',
    'http://www.nasdaqomxnordic.com/aktier/listed-companies/first-north',
    'http://www.nasdaqomxnordic.com/aktier/listed-companies/norwegian-listed-shares'
]

currencies = set([
'AED', 'AFN', 'ALL', 'AMD', 'ANG', 'AOA', 'ARS', 'AUD', 'AWG', 'AZN', 
'BAM', 'BBD', 'BDT', 'BGN', 'BHD', 'BIF', 'BMD', 'BND', 'BOB', 'BRL', 
'BSD', 'BTN', 'BWP', 'BYN', 'BZD', 'CAD', 'CDF', 'CHF', 'CLP', 'CNY', 
'COP', 'CRC', 'CUC', 'CUP', 'CVE', 'CZK', 'DJF', 'DKK', 'DOP', 'DZD', 
'EGP', 'ERN', 'ETB', 'EUR', 'FJD', 'FKP', 'GBP', 'GEL', 'GGP', 'GHS', 
'GIP', 'GMD', 'GNF', 'GTQ', 'GYD', 'HKD', 'HNL', 'HRK', 'HTG', 'HUF', 
'IDR', 'ILS', 'IMP', 'INR', 'IQD', 'IRR', 'ISK', 'JEP', 'JMD', 'JOD', 
'JPY', 'KES', 'KGS', 'KHR', 'KMF', 'KPW', 'KRW', 'KWD', 'KYD', 'KZT', 
'LAK', 'LBP', 'LKR', 'LRD', 'LSL', 'LYD', 'MAD', 'MDL', 'MGA', 'MKD', 
'MMK', 'MNT', 'MOP', 'MRO', 'MUR', 'MVR', 'MWK', 'MXN', 'MYR', 'MZN', 
'NAD', 'NGN', 'NIO', 'NOK', 'NPR', 'NZD', 'OMR', 'PAB', 'PEN', 'PGK', 
'PHP', 'PKR', 'PLN', 'PYG', 'QAR', 'RON', 'RSD', 'RUB', 'RWF', 'SAR', 
'SBD', 'SCR', 'SDG', 'SEK', 'SGD', 'SHP', 'SLL', 'SOS', 'SPL', 'SRD', 
'STD', 'SVC', 'SYP', 'SZL', 'THB', 'TJS', 'TMT', 'TND', 'TOP', 'TRY', 
'TTD', 'TVD', 'TWD', 'TZS', 'UAH', 'UGX', 'USD', 'UYU', 'UZS', 'VEF', 
'VND', 'VUV', 'WST', 'XAF', 'XCD', 'XDR', 'XOF', 'XPF', 'YER', 'ZAR', 
'ZMW', 'ZWD'     
])

def get_listed_company_info(url_list):
    stock_info = []
    for index, url in enumerate(url_list):    
        resp = requests.get(url)
        soup = bs.BeautifulSoup(resp.text, 'lxml')
        table = soup.find('table',{'id' : 'listedCompanies'})
        if index==0:
            columns = ['_'.join(header.string.lower().split(' ')) for header in table.findAll('th')[:-1]]
        for row in table.findAll('tr')[1:]:
            stock_info.append([cell.string for cell in row.findChildren('td')[:-1]])
    output_frame = pd.DataFrame(data=stock_info, columns=columns).drop_duplicates().fillna('Unknown')
    output_frame['yahoo_ticker'] = output_frame.apply(lambda x: x['symbol'].replace(' ','-')+'.CO' if x['isin'][:2]=='DK' 
                else x['symbol'].replace(' ','-')+'.ST' if x['isin'][:2]=='SE' 
                else x['symbol'].replace(' ','-')+'.HE' if x['isin'][:2]=='FI' 
                else x['symbol'].replace(' ','-').replace('o','')+'.OL' if x['isin'][:2]=='NO' 
                else x['symbol'].replace(' ','-')+'.CO' if x['currency']=='DKK' 
                else x['symbol'].replace(' ','-')+'.CO' if x['currency']=='ISK'
                else x['symbol'].replace(' ','-')+'.ST' if x['currency']=='SEK'
                else x['symbol'].replace(' ','-')+'.HE' if x['currency']=='EUR'
                else x['symbol'].replace(' ','-').replace('o','')+'.OL' if x['currency']=='NOK'
                else ''
                , axis=1)
    return output_frame[output_frame['symbol'].apply(lambda x: x.split(' ')[-1]!='A')]

def get_keyratios(isin_list):
    kr = gm.KeyRatiosDownloader()
    nr_of_stocks = len(isin_list)
    nr_failed = 0
    for index, isin in enumerate(isin_list):
        kr_list = []
        if index == 0:
            print('Fetching key ratios...')
        try:
            kr_list = kr.download(isin)
        except ValueError:
            nr_failed += 1
            continue
        for kr_index, frame in enumerate(kr_list):
            cols = frame.transpose().columns.values
            new_cols = [(lambda x: '_'.join([word.lower() for word in x.split(' ') if word not in currencies]))(col) for col in cols]
            temporary_frame = frame.copy().transpose()
            temporary_frame.columns = new_cols
            temporary_frame.index = temporary_frame.index.year
            if kr_index == 0:
                isin_frame = pd.DataFrame(index=temporary_frame.index)
            isin_frame = pd.merge(isin_frame, temporary_frame, left_index=True, right_index=True, how='outer')
        isin_frame.insert(0,'isin',isin)
        if index == 0:
            output_frame = pd.DataFrame(columns=isin_frame.columns)
        output_frame = pd.concat([output_frame, isin_frame])
        if index % 10 == 0:
            print('{:.0f}/{:.0f} remaining, {:.0f} failed.'.format(nr_of_stocks-index,nr_of_stocks,nr_failed))
    print('Done!')
    return output_frame

def piotroski_score(dataframe):
    output_frame = dataframe.copy()
    output_frame['p_score_1'] = np.where(output_frame['return_on_assets_%']>0,1,0)
    output_frame['p_score_2'] = np.where(output_frame['operating_cash_flow_mil']>0,1,0)
    output_frame['p_score_3'] = np.where(output_frame.groupby('isin')['return_on_assets_%'].shift(0)>output_frame.groupby('isin')['return_on_assets_%'].shift(1),1,0)
    output_frame['p_score_4'] = np.where(output_frame['operating_cash_flow_mil']>output_frame['net_income_mil'],1,0)
    output_frame['p_score_5'] = np.where(output_frame.groupby('isin')['long-term_debt'].shift(0)<output_frame.groupby('isin')['long-term_debt'].shift(1),1,0)
    output_frame['p_score_6'] = np.where(output_frame.groupby('isin')['current_ratio'].shift(0)>output_frame.groupby('isin')['current_ratio'].shift(1),1,0)
    output_frame['p_score_7'] = np.where(output_frame.groupby('isin')['shares_mil'].shift(0)<=output_frame.groupby('isin')['shares_mil'].shift(1),1,0)
    output_frame['p_score_8'] = np.where(output_frame.groupby('isin')['gross_margin_%'].shift(0)>output_frame.groupby('isin')['gross_margin_%'].shift(1),1,0)
    output_frame['p_score_9'] = np.where(output_frame.groupby('isin')['asset_turnover'].shift(0)>output_frame.groupby('isin')['asset_turnover'].shift(1),1,0)
    output_frame['p_score'] = np.sum(output_frame[['p_score_1', 'p_score_2', 'p_score_3', 'p_score_4', 'p_score_5', 'p_score_6', 'p_score_7', 'p_score_8', 'p_score_9']], axis=1)
    return output_frame

def get_valuation_ratios(yahoo_tickers):
    params = {"formatted": "false",
                "lang": "en-US",
                "region": "US",
                "modules": "summaryDetail,financialData,price",
                "corsDomain": "finance.yahoo.com"}
    columns = ['']
    nr_of_stocks = len(yahoo_tickers)
    nr_failed = 0
    out_cols = ['ebitda','totalcash','totaldebt','marketcap','trailingpe','forwardpe','recommendationkey']
    out_frame = pd.DataFrame(columns=out_cols)
    print('Fetching valuation ratios...')
    for index, ticker in enumerate(yahoo_tickers):
        r = requests.get("https://query1.finance.yahoo.com/v10/finance/quoteSummary/{}".format(ticker), params=params)
        data = r.json()
        try:
            flattened_resp = {key.lower():val for d in list(data['quoteSummary']['result'][0].values()) for key,val in d.items()}
        except (KeyError):
            nr_failed += 1
            continue
        if flattened_resp['symbol'].lower()==ticker.lower():
            ticker_dict = {}
            ticker_dict['yahoo_ticker'] = ticker.upper()
            for element in out_cols:
                try:
                    ticker_dict[element] = flattened_resp[element]
                except (KeyError, IndexError):
                    ticker_dict[element] = np.nan
        else:
            nr_failed += 1
            continue
        out_frame = out_frame.append(pd.Series(ticker_dict), ignore_index=True)
        if index % 10 == 0:
            print('{:.0f}/{:.0f} remaining, {:.0f} failed.'.format(nr_of_stocks-index,nr_of_stocks,nr_failed))
    print('Done!')
    out_frame['ev'] = out_frame['marketcap']+out_frame['totaldebt']-out_frame['totalcash']
    out_frame['ev_ebitda_ratio'] = out_frame['ev'].div(out_frame['ebitda'])
    return out_frame

def stock_screener():
    parser = argparse.ArgumentParser()


if __name__=='__main__':
    stock_screener()