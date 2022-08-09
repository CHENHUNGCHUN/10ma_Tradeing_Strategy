
def trade_with_ma(stock_no='0050.TW',start="2018-01-01",end= "2022-8-7",win=0.09,loss=0.03,ma=10):
    if ma < 5:
        return f"不支援ma 5以下"
    else:    
        # stock_no = '0050.TW'
        # start="2018-01-01"
        # end= "2022-8-7"
        # win = 0.09
        # loss = 0.03
        stock = yf.Ticker(stock_no)
        stock_data = stock.history(start=start,end=end)
        df = stock_data['Close'].to_frame().rename(columns={'Close':'price'}).reset_index()
        stock_return = [0]
        for i in range(1,len(df['price'])):
            _ = (df['price'][i]-df['price'][i-1]) / df['price'][i-1]
            stock_return.append(_)
        df['stock_return'] = stock_return

        #計算10日均線
        df['10ma'] = df['price'].rolling(window=ma).mean()
        df = df.dropna()
        df.reset_index(inplace=True,drop=True)

        #寫入買賣訊號
        buy_singnal = [0]
        for i in range(1,len(df['price'])):
            if (df['price'][i-1] <= df['10ma'][i-1]) and (df['price'][i] > df['10ma'][i]):
                buy_singnal.append(df['price'][i])
            elif (df['price'][i-1] >= df['10ma'][i-1]) and (df['price'][i] < df['10ma'][i]):
                buy_singnal.append(df['price'][i]*-1)
            else:
                buy_singnal.append(0)
        df['buy_singnal'] = buy_singnal
        df['buy_singnal'] =df['buy_singnal'].astype(float)

        #買賣持有
        buy_sell_hold = []
        for i in df['buy_singnal']:
            if i > 0:
                buy_sell_hold.append('buy')
            elif i < 0:
                buy_sell_hold.append('sell')
            else:
                buy_sell_hold.append(0)
        df['buy_sell_hold'] = buy_sell_hold

        #一律將最後一筆設定為賣出
        df.iloc[-1,-1] = 'sell'
        _=[]
        loc=[]
        for i in range(len(df['price'])):
            x = df.iloc[i,5]
            if (x == 'sell') or (x == 'buy'):
                _.append(x)
                loc.append(i)
        if _[0] == 'sell':
            index = loc[0]
            df.iloc[index,5] = 0
            df.iloc[index,4] = 0
        #增加持有標記
        for i in range(len(df['buy_sell_hold'])):
            if df['buy_sell_hold'][i] == 'buy':
                for j in range(1,len(df['buy_sell_hold'])):
                    if df['buy_sell_hold'][i+j] == 'sell':
                        break
                    else:
                        df['buy_sell_hold'][i+j] = 'holding'
            elif (df['buy_sell_hold'][i] == 'sell') | (df['buy_sell_hold'][i] == 'holding') | (df['buy_sell_hold'][i] == 0):
                pass
        _=[]
        loc=[]
        for i in range(len(df.iloc[:,5])):
            x = df.iloc[-i,5]
            if (x == 'sell') or (x == 'buy'):
                _.append(x)
                loc.append(i)
        if _[1] != 'buy':
            df.drop(df.shape[0]-1,axis=0,inplace=True)
        #計算持有期間報酬率
        r = []
        for i in range(len(df['buy_sell_hold'])):
            if df['buy_sell_hold'][i] == 'buy':
                r.append(0)
                for j in range(1,len(df['buy_sell_hold'])):
                    if df['buy_sell_hold'][i+j] == 'sell':
                        return_ = (df['price'][i+j]-df['price'][i]) / df['price'][i]
                        r.append(return_)
                        break
                    else:
                        return_ = (df['price'][i+j]-df['price'][i]) / df['price'][i]
                        r.append(return_)
            elif (df['buy_sell_hold'][i] == 'holding') | (df['buy_sell_hold'][i] == 'sell'):
                continue
            elif df['buy_sell_hold'][i] == 0:
                r.append('no_position')
        df['return'] = r
        #計算最後報酬率
        total_sell=[]
        for i in range(len(df['buy_sell_hold'])):
            if df.iloc[i,-2] == 'sell':
                total_sell.append(df.iloc[i,-1])
        money=100
        for i in total_sell:
            money *= (1+i)
        #return f'單純用10日均線出場,最後資金為{money:.2f}'

        #將交易測略改為一樣用10日均線進場 但改成盈虧比出場
        df['trading_with_win/loss_ratio']=0
        for i in range(len(df['buy_singnal'])):
            if df.iloc[i,-3] == 'buy':
                df.iloc[i,-1] = 'buy' 
        df['return_win/loss'] = 0
        df2=df.copy()

        #加入盈虧比
        df2.loc[:,'sell_profit']=0
        for i in range(len(df2['trading_with_win/loss_ratio'])):
            if df2.iloc[i,-3] == 'buy':
                for j in range(1,len(df2['trading_with_win/loss_ratio'])):
                    if i+j < len(df2['trading_with_win/loss_ratio'])-1:   #一個是試算"個數",一個是算index,所以個數要-1
                        Return = (df2.iloc[i+j,1] - df2.iloc[i,1]) / df2.iloc[i,1]
                        if Return > win:
                            if df2.iloc[i+j,-1] != 0:
                                df2.iloc[i+j,-1] += win
                            elif df2.iloc[i+j,-1] == 0:
                                df2.iloc[i+j,-1] = win
                            df2.iloc[i+j,-2] = 'sell'
                            break
                        elif Return < -loss:
                            if df2.iloc[i+j,-1] != 0:
                                df2.iloc[i+j,-1] += -loss
                            elif df2.iloc[i+j,-1] == 0:
                                df2.iloc[i+j,-1] = -loss
                            df2.iloc[i+j,-2] = 'sell'
                            break
                        #強制於期末平倉
                        elif i+j == len(df2['trading_with_win/loss_ratio'])-1:
                            df2.iloc[i+j,-2] = 'sell'
                            df2.iloc[i+j,-1] = Return
                            break     
            else:
                pass
        #計算用盈虧比當出場;原始資金100 最後金額
        sell_return_2 = []
        for i in range(len(df2['return_win/loss'])):
            if df2['return_win/loss'][i] == 'sell':
                sell_return_2.append(df2['sell_profit'][i])
        money2=100
        money_for_plot=[]
        for i in sell_return_2:
            money2 *= (1+i)
            money_for_plot.append(money2)
        trad_time = df2['trading_with_win/loss_ratio'].value_counts()['buy']
        count=0
        index = df2['sell_profit'].value_counts().index
        value = df2['sell_profit'].value_counts().values
        for i in range(len(index)):
            if (type(index[i]) != str) and (index[i]>0):
                nums=index[i] * value[i]
                count += nums
        win_rate = count/win
        win_rate = win_rate/trad_time
        
        plt.figure(figsize=(12,8))
        plt.plot(money_for_plot)
        plt.title(f'Straegy_with_{ma}MA',fontsize=20)
        plt.xlabel("trading_times",fontsize=20)
        plt.ylabel("account",fontsize=20)
        plt.show()
        return f"\n原始資金為100\n單純用{ma}日均線進出場,最後資金為{money:.2f},總交易次數為{len(total_sell)} \n用{ma}日均線進場,出場用盈虧比,最後資金為{money2:.2f},總交易次數為{trad_time},勝率為{win_rate*100:.2f}%"
#######################################################################################
import pandas as pd
import yfinance as yf
import warnings
warnings.filterwarnings("ignore")
import matplotlib.pyplot as plt

'''
單純價格突破或跌破均線做動作
交易設定為准許加碼(同時間可能會有1張以上的持股)
先安裝 yfinance 跟 padas

參數:
stock_no 股票代碼 "0050.TW" "2330.TW"
start 起始日期 "2018-01-01"
end 結束日期 "2022-8-7"
win 停利 0.09(9%)
loss 停損 0.03(3%)
ma 用多少日的平均線(目前不支援5日以下會出問題)
'''

a=trade_with_ma("2330.TW","2019-01-01","2022-8-8",0.09,0.03,5)
print(a)
