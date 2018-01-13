import argparse, requests, os, datetime, gspread
import good_morning as gm
import pandas as pd
import numpy as np
import bs4 as bs
from df2gspread import df2gspread as d2g
from oauth2client.service_account import ServiceAccountCredentials

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
    print('Fetching key ratios...')
    for index, isin in enumerate(isin_list):
        if index % 10 == 0:
            print('{:.0f}/{:.0f} remaining, {:.0f} failed.'.format(nr_of_stocks-index,nr_of_stocks,nr_failed))
        kr_list = []
        try:
            kr_list = kr.download(isin)
        except ValueError:
            nr_failed += 1
            continue
        for kr_index, frame in enumerate(kr_list):
            if kr_index not in [0,2,8,9,10]:
                continue
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
        try:
            output_frame = pd.concat([output_frame, isin_frame])
        except AssertionError:
            nr_failed += 1
            continue
    print('Done!')
    return output_frame

def piotroski_score(df):
    output_frame = df.copy()
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
    output_frame['rank_piotroski'] = output_frame['p_score'].rank(method='dense', ascending=False).replace(np.nan,df.shape[0]+1).values
    return output_frame

def magic_formula(df):
    output_frame = df.copy()
    output_frame['magic_formula_score'] = ((1/output_frame['ev_ebitda_ratio']).clip(0,None)*output_frame['return_on_invested_capital_%'].clip(0,None)).replace(np.inf,0)
    output_frame['rank_magic_formula'] = output_frame[['magic_formula_score']].rank(method='dense', ascending=False).replace(np.nan,df.shape[0]+1).values
    return output_frame

def oshaugnessy_value_composite(df):
    output_frame = df.copy()
    output_frame['price_to_sales'] = output_frame['marketcap'] / output_frame['revenue_mil']
    output_frame['price_to_cash_flow'] = output_frame['marketcap'] / output_frame['operating_cash_flow_mil']
    output_frame['shareholder_yield'] = (((output_frame.groupby('isin')['shares_mil'].shift(1)-output_frame.groupby('isin')['shares_mil'].shift(0))/output_frame.groupby('isin')['shares_mil'].shift(1)) + (output_frame['dividends'] / output_frame['currentprice'])).fillna(0)
    output_frame['oshaugnessy_score'] = (output_frame['ev_ebitda_ratio'].rank(method='dense', ascending=True) + output_frame['pricetobook'].rank(method='dense', ascending=True) + output_frame['trailingpe'].rank(method='dense', ascending=True) + output_frame['price_to_sales'].rank(method='dense', ascending=True) + output_frame['price_to_cash_flow'].rank(method='dense', ascending=True) + output_frame['shareholder_yield'].rank(method='dense', ascending=False))
    output_frame['rank_oshaugnessy'] = output_frame[['oshaugnessy_score']].rank(method='dense', ascending=True).replace(np.nan,df.shape[0]+1).values
    return output_frame    

def croic(df):
    # Cash return on invested capital
    output_frame = df.copy()
    output_frame['croic'] = output_frame['free_cash_flow_mil'] / (output_frame['net_income_mil'] / (output_frame['return_on_invested_capital_%']/100)) 
    output_frame['croic_1yr'] = output_frame.groupby('isin')['croic'].shift(1).fillna(0)
    output_frame['croic_2yr'] = output_frame.groupby('isin')['croic'].shift(2).fillna(0)
    output_frame['croic_3yr'] = np.where((output_frame['croic'].values > output_frame['croic_1yr'].values) * (output_frame['croic_1yr'].values > output_frame['croic_2yr'].values),1.,0)
    output_frame['rank_croic'] = output_frame['croic_3yr'].rank(method='dense', ascending=False).replace(np.nan,df.shape[0]+1).values
    return output_frame

def ncav_nnwc(df):
    # Net Current Asset Value and Net Net Working Capital Screens
    output_frame = df.copy()
    output_frame['rank_ncav'] = output_frame['ncav'].rank(method='dense', ascending=False).replace(np.nan,df.shape[0]+1).values
    output_frame['rank_nnwc'] = output_frame['nnwc'].rank(method='dense', ascending=False).replace(np.nan,df.shape[0]+1).values
    return output_frame

def get_valuation_ratios(yahoo_tickers):
    params = {"formatted": "false",
                "lang": "en-US",
                "region": "US",
                "modules": "summaryDetail,financialData,price,defaultKeyStatistics,balanceSheetHistory",
                "corsDomain": "finance.yahoo.com"}
    columns = ['']
    nr_of_stocks = len(yahoo_tickers)
    nr_failed = 0
    out_cols = ['targetmedianprice','numberofanalystopinions','ebitda','currentprice','pricetobook','marketcap','trailingpe','forwardpe','recommendationkey']
    balsheet_cols = ['cash','totalCurrentAssets','totalLiab','inventory','netReceivables']
    out_frame = pd.DataFrame(columns=[col.lower() for col in out_cols+balsheet_cols])
    print('Fetching valuation ratios...')
    for index, ticker in enumerate(yahoo_tickers):
        if index % 10 == 0:
            print('{:.0f}/{:.0f} remaining, {:.0f} failed.'.format(nr_of_stocks-index,nr_of_stocks,nr_failed))
        r = requests.get("https://query1.finance.yahoo.com/v10/finance/quoteSummary/{}".format(ticker), params=params)
        data = r.json()
        try:
            flattened_resp = {key.lower():val for d in list(data['quoteSummary']['result'][0].values()) for key,val in d.items()}
        except (KeyError, TypeError):
            nr_failed += 1
            continue
        if flattened_resp['symbol'].lower()==ticker.lower():
            ticker_dict = {}
            ticker_dict['yahoo_ticker'] = ticker.upper()
            for element in out_cols + balsheet_cols:
                element_dict = element.lower()
                try:
                    if element in balsheet_cols:
                            ticker_dict[element_dict] = flattened_resp['balancesheetstatements'][0][element]['raw']
                    else:   
                        if isinstance(flattened_resp[element], dict):
                            ticker_dict[element_dict] = np.nan
                        else:
                            ticker_dict[element_dict] = flattened_resp[element]
                except (KeyError, IndexError):
                    ticker_dict[element_dict] = np.nan
        else:
            nr_failed += 1
            continue
        out_frame = out_frame.append(pd.Series(ticker_dict), ignore_index=True)
    print('Done!')
    print(ticker_dict)
    out_frame['ev'] = out_frame['marketcap']+out_frame['totalliab']-out_frame['cash']
    out_frame['ev_ebitda_ratio'] = out_frame['ev'].div(out_frame['ebitda'])
    out_frame['ncav'] = out_frame['totalcurrentassets'] - out_frame['totalliab'] - out_frame['marketcap']
    out_frame['nnwc'] = out_frame['cash'] + 0.75*out_frame['netreceivables'] + 0.5*out_frame['inventory'] - out_frame['marketcap']
    out_frame['marketcap_sci'] = out_frame['marketcap'].apply(lambda x: '{:.2E}'.format(x))
    return out_frame

def upload_df(df, spreadsheet_name, sheet_name, sac_file=''):
    google_spreadsheet = spreadsheet_name
    wks_name = sheet_name
    scope = ['https://spreadsheets.google.com/feeds']
    credentials = ServiceAccountCredentials.from_json_keyfile_name(sac_file, scope)
    gc = gspread.authorize(credentials)
    workbook = gc.open(google_spreadsheet)
    print('Uploading to workbook={}, worksheet={}...'.format(google_spreadsheet,wks_name))
    if wks_name in [sheet.title for sheet in workbook.worksheets()]:
        workbook.del_worksheet(workbook.worksheet(wks_name))
    worksheet = workbook.add_worksheet(title=wks_name, rows=df.shape[0]+10, cols=df.shape[1]+1)
    worksheet.insert_row(['processyear']+list(df.columns.values),index=1)
    start_col = 1
    end_col = df.shape[1]+1
    start_row = 2
    end_row = df.shape[0]+1
    cell_range = '{col_i}{row_i}:{col_f}{row_f}'.format(
        col_i=chr((start_col-1) + ord('A')),    
        col_f=chr((end_col-1) + ord('A')),      
        row_i=start_row,
        row_f=end_row)
    cells = np.array(worksheet.range(cell_range)).reshape(end_row-start_row+1,end_col-start_col+1)
    for cell_index in np.ndindex(cells.shape):
        if cell_index[1] == 0:
            cells[cell_index].value = df.index[cell_index[0]]
        else:
            cells[cell_index].value = df.iloc[cell_index[0], cell_index[1]-1]
    worksheet.update_cells(cells.reshape(-1,1).flatten().tolist())

def stock_screener():
    parser = argparse.ArgumentParser(description='Screen Nordic stocks for winners. Using data on disk, if exists.')
    parser.add_argument('--keystats', help='Forces keystats scrape (takes a long time)', action='store_true')
    parser.add_argument('--pyear', type=int, help='Process year, default last year.', default=datetime.date.today().year-1)
    parser.add_argument('--sac_file', help='Path to Google Service Account Credential json file.')
    parser.add_argument('--gspreadsheet', help='Name or ID of spreadsheet in your google drive')
    args = parser.parse_args()
    if os.path.exists(os.path.join(os.getcwd(),'stock_data','stock_data.csv')):
        if args.keystats:
            old_df = pd.read_csv(os.path.join(os.getcwd(),'stock_data','stock_data.csv'), index_col=0, low_memory=False)
            screened = list(old_df[old_df.index==args.pyear]['isin'].unique())
            not_screened = list(old_df[~old_df['isin'].isin(screened)]['isin'].unique() )
            screened_df = old_df[old_df['isin'].isin(screened)]
            keystats_df_ns = get_keyratios(not_screened)
            keystats_df_ns = keystats_df_ns[keystats_df_ns.index<=args.pyear]
            keystats_df = pd.concat([screened_df, keystats_df_ns])
        else:
            keystats_df = pd.read_csv(os.path.join(os.getcwd(),'stock_data','stock_data.csv'), index_col=0, low_memory=False)
    else:
        listed_companies_df = get_listed_company_info(url_list)
        keystats_df = get_keyratios(list(listed_companies_df['isin'].unique()))
        keystats_df = keystats_df[keystats_df.index<=args.pyear]
        if not os.path.exists(os.path.join(os.getcwd(),'stock_data')):
            os.makedirs(os.path.join(os.getcwd(),'stock_data'))
        keystats_df = pd.merge(keystats_df.reset_index(), listed_companies_df, on='isin', how='left').set_index('index')
        keystats_df.to_csv(os.path.join(os.getcwd(),'stock_data','stock_data.csv'), encoding='utf-8')
    p_score_df = piotroski_score(keystats_df)
    p_score_df = p_score_df[(p_score_df['p_score']>=6)]
    valuation_path = os.path.join(os.getcwd(),'stock_data','valuation_ratios_{}.csv'.format(datetime.datetime.strftime(datetime.date.today(),'%Y%m%d')))
    if os.path.exists(valuation_path):
        valuation_ratios = pd.read_csv(valuation_path, low_memory=False)
    else:
        valuation_ratios = get_valuation_ratios(list(p_score_df['yahoo_ticker'].unique()))
        valuation_ratios.to_csv(valuation_path, encoding='utf-8')    
        valuation_ratios = pd.read_csv(valuation_path, low_memory=False)
    screened_stocks = pd.merge(p_score_df.reset_index(), valuation_ratios, on='yahoo_ticker', how='left').set_index('index')
    screened_stocks = screened_stocks[((screened_stocks['trailingpe'].isnull()) | (screened_stocks['trailingpe']>=0)) & ((screened_stocks['return_on_invested_capital_%'].isnull()) | (screened_stocks['return_on_invested_capital_%']>=0))]
    screened_stocks = magic_formula(screened_stocks)
    screened_stocks = oshaugnessy_value_composite(screened_stocks)
    screened_stocks = croic(screened_stocks)
    screened_stocks = ncav_nnwc(screened_stocks)
    screened_stocks = screened_stocks[screened_stocks.index==args.pyear]
    screened_stocks_output = screened_stocks.copy()[['name','isin','yahoo_ticker','sector','currency','marketcap_sci','recommendationkey','currentprice','targetmedianprice','numberofanalystopinions','forwardpe','trailingpe','ev_ebitda_ratio','pricetobook','p_score','return_on_invested_capital_%','croic','croic_1yr','croic_2yr','ncav','nnwc','rank_piotroski','rank_magic_formula','rank_oshaugnessy','rank_croic','rank_ncav','rank_nnwc']]
    screened_stocks_output.loc[:,'combined_rank'] = (screened_stocks_output['rank_ncav'] + screened_stocks_output['rank_nnwc'] + screened_stocks_output['rank_croic']+screened_stocks_output['rank_piotroski']+screened_stocks_output['rank_magic_formula']+screened_stocks_output['rank_oshaugnessy']).rank(method='dense', ascending=True).replace(np.nan,screened_stocks_output.shape[0]+1).values
    screened_stocks_output.to_csv(os.path.join(os.getcwd(),'stock_data','stock_screener_results.csv'), encoding='utf-8')
    google_spreadsheet = args.gspreadsheet
    wks_name = datetime.datetime.strftime(datetime.date.today(),'%Y-%m-%d')
    upload_df(screened_stocks_output, google_spreadsheet, wks_name, sac_file=args.sac_file)
    
if __name__=='__main__':
    stock_screener()
