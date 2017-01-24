from pandas.core.common import array_equivalent
import pandas as pd
import time as t
import re
import pickle
import datetime
import numpy as np
import pandas_datareader.data as web

import stock_screener.good_morning as gm
from stock_screener.helperfunctions import *

def keyratiodata(tickerlist):

    kr = gm.KeyRatiosDownloader()

    df=pd.DataFrame()
    i = 0
    for each_stock in tickerlist:
        t.sleep(0.5)
        try:
            kr_frames = kr.download(each_stock)
        except:
            pass
        for k in range(0,len(kr_frames)):
            if k==0:
                temp_df=kr_frames[k].transpose()
                temp_df.insert(0,'Ticker',each_stock)
                temp_df.insert(1,'Year',temp_df.index.to_timestamp().year)
                temp_df.insert(2,'Month',12)
                temp_df.insert(3,'Day',31)
    #            test=pd.merge(temp_df,temp_df,on=['Year','Month','Day','Ticker'],how='left')
                temp_df.columns=temp_df.columns.str.replace(" ","")            
                result=temp_df
                
            else:
                temp_df=kr_frames[k].transpose()
                temp_df.insert(0,'Ticker',each_stock)
                temp_df.insert(1,'Year',temp_df.index.to_timestamp().year)
                temp_df.insert(2,'Month',12)
                temp_df.insert(3,'Day',31)
                temp_df.columns=temp_df.columns.str.replace(" ","")
                result=pd.merge(result,temp_df,on=['Year','Month','Day','Ticker'],how='left')
                
        result.set_index(['Year','Month','Day','Ticker'],inplace=True)

        try:

            if i!=0:
                
                df.columns=result.columns
                df=df.append(result,ignore_index=False)
            else:
                df=df.append(result,ignore_index=False)
            print(each_stock)
            i+=1
        except Exception as e:
            print(str(e),'<-- problem')
            i+=1
    df1=df.drop(duplicate_columns(df),axis=1).reset_index()
    return df1           

def financialdata(tickerlist):

    fd=gm.FinancialsDownloader()
    finData=pd.DataFrame()
    k = 0
    for each_stock in tickerlist:
        t.sleep(0.5)
        
        try:
            fd_dict=fd.download(each_stock)
    #        
    #        test=fd_dict.get('balance_sheet')
    #        test=test.append(fd_dict.get('cash_flow'),ignore_index=False)
    #        test=test.append(fd_dict.get('income_statement'),ignore_index=False)
    #        test.insert(1,'Ticker',each_stock)
    #        test=test.transpose()
    #        test.reset_index(inplace=True)
            StockCurrency=fd_dict.get('currency')
            
            isdf_1=fd_dict.get('income_statement')   
            isdf_2=rename_IS(isdf_1,'Basic')
            isdf_3=rename_IS(isdf_2,'Diluted')
            
            bsdf=restructure_df(fd_dict.get('balance_sheet'),StockCurrency,each_stock)
            cfdf=restructure_df(fd_dict.get('cash_flow'),StockCurrency,each_stock)
            isdf=restructure_df(isdf_3,StockCurrency,each_stock)
            
            res=pd.merge(bsdf,cfdf,how='left',on=['Year','Month','Day','Ticker','Currency'])
            res=pd.merge(res,isdf,how='left',on=['Year','Month','Day','Ticker','Currency'])

    #        res.set_index(['Year','Month','Day','Ticker'],inplace=True)
            
            
        except Exception as e:
            print(str(e),'stock combination failed')        
            pass
            
        try:
            if k!=0:
    #            finData.columns=res.columns
                rmvdups=res.T.drop_duplicates().T
                dupslist=duplicate_columns(rmvdups)
                res_final=rmvdups.drop(dupslist, axis=1)
                
                finData=pd.concat([finData,res_final],axis=0,ignore_index=True)
    #            finData=pd.merge(finData,res.T.drop_duplicates().T,how='outer')
    #            finData=finData.append(res,ignore_index=False)
            else:
                rmvdups=res.T.drop_duplicates().T
                dupslist=duplicate_columns(rmvdups)
                res_final=rmvdups.drop(dupslist, axis=1)
                finData=finData.append(res_final,ignore_index=True)

            print(each_stock)
            k+=1
        except Exception as e:
            print(str(e),'<-- problem')
            k+=1
            
        fd_dict.clear

    finData['Year2']=0
    for x in range(len(finData)):
        if finData['Year'].dtypes!=np.int64:
            finData['Year2'][x]=finData['Year'][x].to_timestamp().year
    finData.rename(columns={'Year' : 'PeriodYear','Year2' : 'Year'},inplace=True)

    return finData      

def stockpricedata(yahoo_tickerlist, isin_tickerlist):
    end_date_list=[]
    start_date_list=[]
    for year in range(11):
        end_date_list.append(datetime.date(datetime.date.today().year-1-year,12,31))
        start_date_list.append(datetime.date(datetime.date.today().year-1-year,12,31-6))
    dates_list = [start_date_list,end_date_list]
    for dt in range(len(dates_list[0])):
        haloj=web.DataReader(yahoo_tickerlist,'yahoo',dates_list[0][dt],dates_list[1][dt])['Adj Close']        
        if dt==0: 
            adjCloseMeanDF = pd.DataFrame(index=dates_list[1],columns=haloj.columns)    
        for k in haloj.columns:
            adjCloseMeanDF.set_value(dates_list[1][dt],k,np.mean(haloj[k]))
    adjCloseMeanDF.sort_index(inplace=True)
    adjCloseChange=adjCloseMeanDF.pct_change()
    adjCloseChange2=pd.DataFrame(index=adjCloseChange.index,columns=adjCloseChange.columns)
    for k in adjCloseChange.columns:
                adjCloseChange2[k]=np.where(adjCloseChange[k]>adjCloseChange['^GDAXI']+0.05,1,0)
    testdf=adjCloseChange2.stack().to_frame()
    testdf2=adjCloseMeanDF.stack().to_frame()
    testdf2.rename(columns={0:'eoy_price'},inplace=True)
    testdf.rename(columns={0:'12mWinner'},inplace=True)
    testdf3=testdf.join(testdf2)
    testdf3.reset_index(inplace=True)
    testdf3['Year']=testdf3['level_0'].apply(lambda x: x.year)
    testdf3['Month']=testdf3['level_0'].apply(lambda x: x.month)
    testdf3['Day']=testdf3['level_0'].apply(lambda x: x.day)
    testdf3['Ticker']=testdf3['level_1']
    testdf3.set_index(['Year','Month','Day','Ticker'],inplace=True)
    del testdf3['level_1'],testdf3['level_0']
    testdf3.reset_index(inplace=True)
    asddf=pd.DataFrame(isin_tickerlist,columns=['isin'])
    asddf['Ticker']=yahoo_tickerlist[:-1]
    testdf4=pd.merge(testdf3,asddf,how='left',on=['Ticker'])
    testdf4.rename(columns={'Ticker':'yahooticker','isin':'Ticker'},inplace=True)
    testdf4=testdf4[['Year','Month','Day','Ticker','12mWinner','eoy_price']]
    testdf4=testdf4[pd.notnull(testdf4['Ticker'])]
    return testdf4

def combinedata(keystatsframe,financialsframe,pricedataframe):
    
    keyframe = keystatsframe.copy()
    finframe = financialsframe.copy()
    priceframe = pricedataframe.copy()
    
    keycols=keyframe.columns.values
    fincols=finframe.columns.values
    pricecols=priceframe.columns.values
    
    keycols = [x+'1' for x in keycols]
    fincols = [x+'2' for x in fincols]
    pricecols = [x+'3' for x in pricecols]
    
    keycols = [x[:-1] if x=='Ticker1' or x=='Year1' or x=='Month1' or x=='Day1' else x for x in keycols]
    fincols = [x[:-1] if x=='Ticker2' or x=='Year2' or x=='Month2' or x=='Day2' else x for x in fincols]
    pricecols = [x[:-1] if x=='Ticker3' or x=='Year3' or x=='Month3' or x=='Day3' else x for x in pricecols]
    
    keyframe.columns = keycols
    finframe.columns = fincols
    priceframe.columns = pricecols
    
    currData = finframe[['Ticker','Currency2']].drop_duplicates()
    exch_final=pd.DataFrame()
    exch_final=exch_final.append(keyframe)

    exch_final=pd.merge(exch_final,priceframe,on=['Year','Month','Day','Ticker'],how='left')
    exch_final=pd.merge(exch_final,finframe,on=['Year','Month','Day','Ticker'],how='left')
    exch_final.drop('Currency2',axis=1,inplace=True)
    exch_final=pd.merge(exch_final,currData,on=['Ticker'],how='left')

    exch_final.columns=exch_final.columns.str.replace("SEK","")
    exch_final.columns=exch_final.columns.str.replace("EUR","")
    exch_final.columns=exch_final.columns.str.replace("NOK","")
    exch_final.columns=exch_final.columns.str.replace("USD","")
    exch_final.columns=exch_final.columns.str.replace("DKK","")
    exch_final.columns=exch_final.columns.str.replace("GBP","")

    exch_final.fillna(value=0,inplace=True)
    exch_final.columns = [x.upper() for x in exch_final.columns.values]

    return exch_final

def screencolumns(exch_final):
    exch_final.fillna(0.0,inplace=True)
#     exch_final['COMPBOOKVALUE']=exch_final['ASSETS']-exch_final['LIABILITIES']-exch_final['INTANGIBLEASSETS']-exch_final['GOODWILL']
    exch_final['BV']=exch_final['BASIC_NOS2']*exch_final['BOOKVALUEPERSHARE*1']
    exch_final['EV']=exch_final['BASIC_NOS2']*exch_final['EOY_PRICE3']+exch_final['SHORT-TERMDEBT1']+exch_final['LONG-TERMDEBT1']-exch_final['CASHANDCASHEQUIVALENTS2']
    exch_final['EV']=np.where((exch_final['BASIC_NOS2']==0) | (exch_final['EOY_PRICE3']==0),0,exch_final['EV'])
    exch_final['BOOKTOMARKET']=exch_final['BV']/exch_final['EV']
    exch_final['EARNINGSYIELD']=exch_final['EBITDA2']/exch_final['EV']
    exch_final['EARNINGSYIELD']=np.where(exch_final['EARNINGSYIELD']==np.inf,0,exch_final['EARNINGSYIELD'])

    exch_final['EBIT']=exch_final['REVENUE2']-exch_final['OPERATINGEXPENSES2']
    exch_final['EARNINGSYIELD2']=exch_final['EBIT']/exch_final['EV']
    exch_final['EARNINGSYIELD3']=exch_final['EARNINGSPERSHARE1']/exch_final['EOY_PRICE3']

    exch_final['ROCE']=exch_final['EBITDA2']/(exch_final['ASSETS2']-exch_final['TOTALCURRENTLIABILITIES1'])

    exch_final['P-SCORE_1']=np.where(exch_final['RETURNONASSETS%1']>0,1,0)
    exch_final['P-SCORE_2']=np.where(exch_final['OPERATINGCASHFLOWMIL1']>0,1,0)

    exch_final['P-SCORE_3']=np.where(exch_final['RETURNONASSETS%1']>exch_final.groupby('TICKER')['RETURNONASSETS%1'].shift(1),1,0)

    exch_final['P-SCORE_4']=np.where(exch_final['OPERATINGCASHFLOWMIL1']>exch_final['NETINCOMEMIL1'],1,0)

    exch_final['P-SCORE_5']=np.where(exch_final['LONG-TERMDEBT1']<exch_final.groupby('TICKER')['LONG-TERMDEBT1'].shift(1),1,0)
    exch_final['P-SCORE_6']=np.where(exch_final['CURRENTRATIO1']>exch_final.groupby('TICKER')['CURRENTRATIO1'].shift(1),1,0)
    exch_final['P-SCORE_7']=np.where(exch_final['SHARESMIL1']<=exch_final.groupby('TICKER')['SHARESMIL1'].shift(1),1,0)

    exch_final['P-SCORE_8']=np.where(exch_final['GROSSMARGIN%1']>exch_final.groupby('TICKER')['GROSSMARGIN%1'].shift(1),1,0)
    exch_final['P-SCORE_9']=np.where(exch_final['ASSETTURNOVER1']>exch_final.groupby('TICKER')['ASSETTURNOVER1'].shift(1),1,0)

    exch_final['P-SCORE']=exch_final['P-SCORE_1']+exch_final['P-SCORE_2']+exch_final['P-SCORE_3']+exch_final['P-SCORE_4']+exch_final['P-SCORE_5']+exch_final['P-SCORE_6']+exch_final['P-SCORE_7']+exch_final['P-SCORE_8']+exch_final['P-SCORE_9']

    exch_final['SORTINGPARAMETER']=exch_final['P-SCORE']*exch_final['RETURNONINVESTEDCAPITAL%1']
    exch_final['SORTINGPARAMETERMF-P']=exch_final['EARNINGSYIELD']*exch_final['RETURNONINVESTEDCAPITAL%1']*exch_final['P-SCORE']
    return exch_final