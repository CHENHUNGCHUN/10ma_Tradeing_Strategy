
'''
簡單均線策略單純價格突破或跌破均線做動作,差別在於一個是用均線當出場依據,一個是用盈虧比率當出場依據
交易設定為准許加碼(同時間可能會有1張以上的持股)

由於是從yfinance 上下載 所以"只有沒有調整"的價格 也就是說股價分割或配股配息會干擾最後結果
實際交易會有穿價 不到價 賣不掉 買不到問題

先安裝 yfinance 、matplotlib、 padas

參數:
stock_no 股票代碼 "0050.TW"
start 起始日期 "2018-01-01"
end 結束日期 "2022-8-7"
win 停利 0.09(9%)
loss 停損 0.03(3%)
ma  幾日均線  5,10,20日均線
'''
