def trade_with_ma(stock_no='0050.TW',start="2018-01-01",end= "2022-8-7",win=0.09,loss=0.03,ma=10):

    stock = yf.Ticker(stock_no)
    stock_data = stock.history(start=start,end=end)
    df = stock_data['Close'].to_frame().rename(columns={'Close':'price'}).reset_index()

    stock_return = [0]
    for i in range(1,len(df['price'])):
        _ = (df['price'][i]-df['price'][i-1]) / df['price'][i-1]
        stock_return.append(_)
    df['stock_return'] = stock_return

    #計算10日均線
    df['ma'] = df['price'].rolling(window=ma).mean()
    df = df.dropna()
    df.reset_index(inplace=True,drop=True)

    #寫入買賣訊號
    buy_singnal = [0]
    for i in range(1,len(df['price'])):
        if (df['price'][i-1] <= df['ma'][i-1]) and (df['price'][i] > df['ma'][i]):
            buy_singnal.append(df['price'][i])
        elif (df['price'][i-1] >= df['ma'][i-1]) and (df['price'][i] < df['ma'][i]):
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
    #調整第一筆不是buy
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
    #如果倒數第二筆是sell 刪除最後一筆的sell
    _=[]
    loc=[]
    for i in range(len(df.iloc[:,5])):
        x = df.iloc[-i,5]
        if (x == 'sell') or (x == 'buy'):
            _.append(x)
            loc.append(i)
    if _[1] != 'buy':
        df.drop(df.shape[0]-1,axis=0,inplace=True)
    #盈虧比出場的return
    win_loss_ratio = [] #直接是用盈虧比出場的全部return
    total_long = len(df['buy_sell_hold'])  # 0~2332(包含2332)
    for i in range(total_long):
        if df['buy_sell_hold'][i] == 'buy':
            for j in range(1,total_long):
                if i+j < total_long-1:
                    Return = (df['price'][i+j]-df['price'][i])/df['price'][i]
                    if Return >= win:
                        win_loss_ratio.append(win)
                        break
                    elif Return <= -loss:
                        win_loss_ratio.append(-loss)
                        break
                elif i+j == total_long-1: #期末強平
                    win_loss_ratio.append(Return)
    #用MA出場的return                
    ma_return = []
    for i in range(total_long-1): #最後一筆不用check   1~2331(包含2331)
        if df['buy_sell_hold'][i] == 'buy':
            for j in range(1,total_long):  #1~2332(包含2332)  i+j (0~)
                if df['buy_sell_hold'][i+j] == 'sell':
                    Return = (df['price'][i+j]-df['price'][i])/df['price'][i]
                    ma_return.append(Return)
                    break
    #資金狀態

    #MA出場
    money1 = 100
    money1_list = []
    money1_count=0
    for i in ma_return:
        money1 *= (1+i)
        money1_list.append(money1)
        if i > 0:
            money1_count+=1
    money1_win=money1_count/len(ma_return)
    plt.figure(figsize=(12,8))
    plt.plot(money1_list)
    plt.title(f'Close_with_{ma}MA',fontsize=20)
    plt.xlabel("trading_times",fontsize=20)
    plt.ylabel("account",fontsize=20)
    plt.show()
    #盈虧比出場
    money2 = 100
    money2_list = []
    money2_count=0
    for i in win_loss_ratio:
        money2 *= (1+i)
        money2_list.append(money2)
        if i > 0:
            money2_count+=1
    money2_win=money2_count/len(win_loss_ratio)
    
    plt.figure(figsize=(12,8))
    plt.plot(money2_list)
    plt.title(f'Close_with_win/loss_ratio:{win/loss}',fontsize=20)
    plt.xlabel("trading_times",fontsize=20)
    plt.ylabel("account",fontsize=20)
    plt.show()

    return f"\n原始資金為100,進場用{ma}日均線\n用{ma}日均線出場,最後資金為{money1:.2f},總交易次數為{len(ma_return)},勝率為{money1_win*100:.2f}%,最低報酬率{min(ma_return):.2f}%,最高報酬率{max(ma_return):.2f}% \
        \n用盈虧比出場,最後資金為{money2:.2f},總交易次數為{len(win_loss_ratio)},勝率為{money2_win*100:.2f}%,最低報酬率{min(win_loss_ratio):.2f}%,最高報酬率{max(win_loss_ratio):.2f}%"
#######################################################################################
import pandas as pd
import yfinance as yf
import warnings
warnings.filterwarnings("ignore")
import matplotlib.pyplot as plt

'''
簡單均線策略單純價格突破或跌破均線做動作,差別在於一個是用均線當初場依據,一個是用盈虧比率當出場依據
交易設定為准許加碼(同時間可能會有1張以上的持股)
實際交易會有穿價 不到價 賣不掉 買不到問題
先安裝 yfinance 、matplotlib、 padas

參數:
stock_no 股票代碼 "0050.TW" "2330.TW"
start 起始日期 "2018-01-01"
end 結束日期 "2022-8-7"
win 停利 0.09(9%)
loss 停損 0.03(3%)
ma 用多少日的平均線
'''

a=trade_with_ma("0050.TW","2013-01-01","2022-8-1",0.09,0.03,10)
print(a)
