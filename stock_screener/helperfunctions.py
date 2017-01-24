from pandas.core.common import array_equivalent
import pandas as pd
import pickle
import os
import bs4 as bs
import requests

import pkg_resources

def duplicate_columns(frame):
    groups = frame.columns.to_series().groupby(frame.dtypes).groups
    dups = []

    for u, v in groups.items():

        cs = frame[v].columns
        vs = frame[v]
        lcs = len(cs)

        for i in range(lcs):
            ia = vs.iloc[:,i].values
            for j in range(i+1, lcs):
                ja = vs.iloc[:,j].values
                if array_equivalent(ia, ja):
                    dups.append(cs[i])
                    break

    return dups

def rename_IS(df,name):
    
    df_not_in=df[~df['title'].isin([name])]
    df_in=df[df['title'].isin([name])]

    
    for k in df_in.index:
        if k==df_in.index[0]:
            df_in.set_value(k,'title',name+'_eps')
        else:
            df_in.set_value(k,'title',name+'_nos')
    
    return df_not_in.append(df_in,ignore_index=False)
    

def restructure_df(df,curris,stock):
    temp=df
    try:
        del temp['parent_index']   
    except:
        pass
    test2=temp.transpose()
    test3=test2.iloc[0].to_frame()
    listtest2=test3['title'].tolist()
    
    test2.columns=listtest2
    test2.reset_index(inplace=True)
    test2.drop(test2.index[[0]],inplace=True)
    test2['Year']=test2['index']
    test2['Month']=12
    test2['Day']=31
    del test2['index']
    test2.reset_index(inplace=True)
    del test2['index']
    test2.columns=test2.columns.str.replace(" ","") 
    test2['Ticker']=stock
    test2['Currency']=curris
    return test2

def saveobject(inputobject,path):
    pickle_out=open(path,'wb')
    pickle.dump(inputobject, pickle_out)
    pickle_out.close()

def openobject(path):
    filehandler = open(path,'rb')
    outputobject = pickle.load(filehandler)
    filehandler.close()
    return outputobject

def get_listed_companyinfo(urllist):
    outputdict = {}
    for url in urllist:    
        resp = requests.get(url)
        soup = bs.BeautifulSoup(resp.text, 'lxml')
        table = soup.find('table',{'id' : 'listedCompanies'})
        tickerrows = []
        for row in table.findAll('tr')[1:]:
            tickerrows.append([cell.string for cell in row.findChildren('td')[:-1]])
        outputdict[url] = tickerrows
    return outputdict 

def getresources():
    resfiles = pkg_resources.resource_listdir('stock_screener','resources')
    textfiles = [x for x in resfiles if x[-4:]=='.txt']
    return textfiles

def parsetxtfiles(reslist=None, input_dict = None):
    if reslist:
        rawtext = {}
        for resource in reslist:
            tmp1 =   pkg_resources.resource_string('stock_screener','/'.join(('resources',resource))).decode('utf-8','ignore')
            tmp2 = [list(filter(None,x.split('\t'))) for x in tmp1.split('\n')]
            tmp3 = [x for x in tmp2 if x!=[]]
            rawtext[resource]=tmp3
    parseddict = {}
    if input_dict:
        rawtext=input_dict
    for filename in rawtext:
        if 'oslo' in filename: 
            gm_input = [x[1].replace('OSE: ','XOSL:') for x in rawtext[filename]]
            yahoo_input = [x[1].replace('OSE: ','')+'.OL' for x in rawtext[filename]]
        else:
            gm_input = [x[3] for x in rawtext[filename]]
            if 'stockholm' in filename:
                yahoo_input = [(x[1]+'.ST').replace(' ','-') for x in rawtext[filename]]
            if 'helsinki' in filename:
                yahoo_input = [(x[1]+'.HE').replace(' ','-') for x in rawtext[filename]]
            if 'copenhagen' in filename:
                yahoo_input = [(x[1]+'.CO').replace(' ','-') for x in rawtext[filename]]
            else:
                yahoo_input = [
                (x[1]+'.ST').replace(' ','-') if x[2]=='SEK' else 
                (x[1]+'.HE').replace(' ','-') if x[2]=='EUR' else
                (x[1].replace('o','')+'.OL').replace(' ','-') if x[2]=='NOK' else
                (x[1]+'.CO').replace(' ','-') if x[2]=='DKK' else
                (x[1]+'.ST').replace(' ','-')  for x in rawtext[filename]]
        yahoo_input.append('^GDAXI')
        parseddict[filename]= [gm_input,yahoo_input]
    return parseddict
