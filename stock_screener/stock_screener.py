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
            columns = [header.string for header in table.findAll('th')[:-1]]
        for row in table.findAll('tr')[1:]:
            stock_info.append([cell.string for cell in row.findChildren('td')[:-1]])

    return pd.DataFrame(data=stock_info, columns=columns).drop_duplicates().fillna('Unknown') 

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





def main():


if __name__=='__main__':
    main()