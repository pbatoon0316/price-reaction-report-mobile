import pandas as pd 
import yfinance as yf
import datetime as dt
import streamlit as st
import plotly.graph_objects as go

###### Initialize Page ######
st.set_page_config(page_title='Earnings Announcements Price Reaction Report', page_icon='📈')
st.set_option('deprecation.showPyplotGlobalUse', False)
hide_streamlit_style = """
            <style>
              footer {visibility: hidden;}
              div.block-container{padding-top:2rem;padding-bottom:2rem;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True) 

###### Initialize Function ######
@st.cache_data(ttl=dt.timedelta(hours=12))
def get_earnings_data(stock_ticker_input, years):

  stock = yf.Ticker(stock_ticker_input)
  today_date = dt.datetime.today()
  start_date = today_date - dt.timedelta(weeks=52*years)


  data = stock.history(start=start_date, end=today_date)
  data = data.reset_index()
  data['Date'] = data['Date'].dt.date


  earnings_dates = stock.get_earnings_dates(limit=years*4)
  earnings_dates = earnings_dates.dropna()
  earnings_dates = earnings_dates[::-1].reset_index()
  earnings_dates['Date'] = earnings_dates['Earnings Date'].dt.date


  earnings = pd.DataFrame()
  for date in earnings_dates['Date']:

    df = data.loc[data['Date'] == date].copy()
    idx = data.loc[data['Date'] == date].index

    df['Close Before Earnings'] = data['Close'].iloc[idx-1].values
    df['Close After Earnings'] = data['Close'].iloc[idx+1].values
    df['+1D %Change'] = 100 * (df['Close After Earnings'] - df['Close Before Earnings']) / df['Close Before Earnings']

    try:
      df['Close 7D After Earnings'] = data['Close'].iloc[idx+7].values
      df['+7D %Change'] = 100 * (df['Close 7D After Earnings'] - df['Close Before Earnings']) / df['Close Before Earnings']
    except:
      df['Close 7D After Earnings'] = None

    earnings = pd.concat([earnings,df])

  earnings = earnings[['Date','Close Before Earnings', 'Close After Earnings', '+1D %Change', 'Close 7D After Earnings', '+7D %Change']].copy()
  earnings = earnings[::-1].set_index('Date')
  return data, earnings 

### Input Region Sidebar
with st.expander(f'The following data has been generated on {dt.datetime.now().date()}'):
    with st.form(key='ticker_input'):
        stock_ticker_input = st.text_input(label='Input Stock Ticker', value='None')
        years = st.number_input(label='Number of Years', value=4)
        submit_button = st.form_submit_button(label='Submit')
    include_7d = st.checkbox('Include +7D', value=True)
    include_optionsImplied = st.checkbox('Include Implied Move')

### Download and acquire data
raw_data = get_earnings_data(stock_ticker_input,years)
stock_data = raw_data[0].set_index('Date')
stock_data.index = pd.to_datetime(stock_data.index)
earnings_data = raw_data[1]
company_name = yf.Ticker(stock_ticker_input).info['shortName']

### Report Heater and Intro Text
st.divider()
st.markdown(f'''
### ${stock_ticker_input.upper()} Expected Move (+1D)
''')


### Immediately Before and After Earnings
avg_1d_move = round(earnings_data['+1D %Change'].mean(),2)
std_1d_move = round(earnings_data['+1D %Change'].std(),2)
low = stock_data['Close'].iloc[-1] * (1 - earnings_data['+1D %Change'].std()/100)
high = stock_data['Close'].iloc[-1] * (1 + earnings_data['+1D %Change'].std()/100)
range_1d = (high-low)/2

st.markdown(f'''
##### σ<sub>+1D After Earnings</sub> = ±{std_1d_move}%
\\${round(low,2)} through \\${round(high,2)}''',unsafe_allow_html=True)

candle_fig_1d = go.Figure(data=go.Candlestick(x=stock_data[-50:].index,
                    open=stock_data[-50:]['Open'],
                    high=stock_data[-50:]['High'],
                    low=stock_data[-50:]['Low'],
                    close=stock_data[-50:]['Close']))
candle_fig_1d.add_hline(y=low, line_dash='dash', line_color='red', opacity=0.7, annotation_text=round(low,2), annotation_position='bottom right')
candle_fig_1d.add_hline(y=high, line_dash='dash', line_color='teal', opacity=0.7, annotation_text=round(high,2), annotation_position='top right')
candle_fig_1d.update_layout(height=225, margin=dict(l=1, r=1, t=1, b=1), xaxis_rangeslider_visible=False)
candle_fig_1d.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])])
#candle_fig_1d.update_yaxes(title_text='Price')
st.plotly_chart(candle_fig_1d, use_container_width=True)

### 7-Days After Earnings
if include_7d:
  st.divider() ## DIVIDER ##
  avg_7d_move = round(earnings_data['+7D %Change'].mean(), 2)
  std_7d_move = round(earnings_data['+7D %Change'].std(), 2)
  low_7D = stock_data['Close'].iloc[-1] * (1 - earnings_data['+7D %Change'].std()/100)
  high_7D = stock_data['Close'].iloc[-1] * (1 + earnings_data['+7D %Change'].std()/100)
  range_7d = (high_7D-low_7D)/2
  st.markdown(f'### ${stock_ticker_input.upper()} Expected Move (+7D)')
  st.markdown(f'''
  ##### σ<sub>+7D After Earnings</sub> = ±{std_7d_move}%
  \\${round(low_7D,2)} through {round(high_7D,2)}''',unsafe_allow_html=True)

  candle_fig_7d = go.Figure(data=go.Candlestick(x=stock_data[-50:].index,
                      open=stock_data[-50:]['Open'],
                      high=stock_data[-50:]['High'],
                      low=stock_data[-50:]['Low'],
                      close=stock_data[-50:]['Close']))
  candle_fig_7d.add_hline(y=low_7D, line_dash='dash', line_color='red', opacity=0.7, annotation_text=round(low_7D,2), annotation_position='bottom right')
  candle_fig_7d.add_hline(y=high_7D, line_dash='dash', line_color='teal', opacity=0.7, annotation_text=round(high_7D,2), annotation_position='top right')
  candle_fig_7d.update_layout(height=225, margin=dict(l=1, r=1, t=1, b=1), xaxis_rangeslider_visible=False)
  candle_fig_7d.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])])
  #candle_fig_7d.update_yaxes(title_text='Price')
  st.plotly_chart(candle_fig_7d, use_container_width=True)

### Data Table Summary
st.divider() ## DIVIDER ##
if include_7d:
  earnings_data_short = earnings_data[['+1D %Change','+7D %Change']][:5]
  st.table(data=earnings_data_short.round(2).style.format('{:7,.2f}'))
else:
  earnings_data_short = earnings_data[['+1D %Change']][:5]
  st.table(data=earnings_data_short.round(2).style.format('{:7,.2f}'))

### Disclaimer
st.markdown('''
<sub>Check the link in profile for more historical earnings price reaction data.👆</sub>
''',unsafe_allow_html=True)

st.divider() ## DIVIDER ##
