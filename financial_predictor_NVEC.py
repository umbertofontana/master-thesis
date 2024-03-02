#VALORI DA MODIFICARE IN BASE ALLE ESIGENZE
TICKER = "NVEC" #TICKER DELLA STOCK DA ANALIZZARE
INTERVAL = "1wk" #INTERVALLO DI ANALISI E PREVISIONE
PERIOD = "max" #QUANTO VOGLIAMO ANDARE INDIETRO NELL'ANALISI
HISTORICAL = "data_nvec.txt" #NOME/PERCORSO DEL FILE CON LO SCRAPE DI DATI STORICI WSJ

#STEP 1: INFORMAZIONI SULL'ANDAMENTO DEL PREZZO DELLA STOCK

import yfinance as yf
import pandas as pd

ticker = yf.Ticker(TICKER)
hist = ticker.history(period=PERIOD, interval=INTERVAL, actions="False")
#Creiamo stringa da feedare come prompt all'assistant, strutturata come data1: prezzochiusura1, data2: prezzochiusura2, ...
stock_string = ""
for k in range(len(hist)): #Mettiamo 20 come test, poi sarà len(hist)
    stock_string = stock_string + str(hist.iloc[k]).split("Name: ")[1][:10] + ": " + str(hist.iloc[k]["Close"]) + ", "
stock_string = stock_string[:-2]

# STEP 2: RIASSUNTO DELLE INFORMAZIONI SULLA COMPAGNIA

stock_summary =  ticker.info["longBusinessSummary"]

#STEP 3: SCRAPE DELLE NEWS PIU RECENTI SUL TICKER DA YAHOOFINANCE

import requests
from bs4 import BeautifulSoup
from pprint import pprint
import re
import os
from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
from datetime import datetime, timedelta

newslist = []
blacklist = ['[document]', 'noscript', 'header', 'html', 'meta', 'head', 'input', 'script']

for i in ticker.news:
    #Grab the title
    title = i["title"]
    #Grab the link
    link = i["link"]
    #Grab the date and format it
    date = timedelta(seconds = i["providerPublishTime"])
    reftime = datetime(year = 1970, month = 1, day = 1)
    date = (reftime + date).strftime("%Y-%m-%d %H:%M")
    #Apriamo il link e scrapiamo l'articolo
    site= str(link)
    hdr = {'User-Agent': 'Mozilla/5.0'}
    req = Request(site,headers=hdr)
    page = urlopen(req)
    soup = BeautifulSoup(page, "html.parser")
    text = soup.find_all(string=True)
    output = ""
    for t in text:
        if t.parent.name not in blacklist:
            output += '{} '.format(t)
    newslist.append(f"DATE: {date}, TITLE: {title}\n{output[-10000:]}")
    
#Ora dovremo feedare ogni item della lista a GPT per fargli fare un riassunto
import openai
from openai import ChatCompletion, Completion
openai.api_key="***REDACTED***" #RICORDA DI COPRIRLO NELLA TESI

news_string = ""
system_message = f"You are an artificial intelligence that helps as much as it can. Please summarize the following noisy but possible news data extracted from web page HTML, and extract keywords of the news. The news text can be very noisy due to its HTML extraction. Give formatted answer such as Date: ...(use Year-Month-Day as format, such as 2023-12-13), Title: ..., Summary: ..., Keywords: ... The news is supposed to be for {TICKER} stock. You may put ’N/A’ if the noisy text does not have relevant information to extract."

for k in newslist:
    chat = ChatCompletion.create(
        model="gpt-4-1106-preview",
        messages = [{"role": "system", "content": system_message},
                  {"role": "user", "content": str(k)}])
    news_string = f"{news_string}{(chat['choices'][0]['message']['content'])}\n\n"
    
#CALL FINALE A GPT-4 PER EFFETTUARE LA PREVISIONE

with open(HISTORICAL, "r") as f:
    historical_news = f.read()

chatinput = f"## WEEKLY STOCK PRICE\n{stock_string}\n\n## COMPANY PROFILE\n{stock_summary}\n\n## HISTORICAL NEWS\n{historical_news}\n\n## LATEST NEWS\n{news_string}\n\nNow predict what could be the next week's Summary, Keywords and forecast the Stock Return. The predicted Summary/Keywords should explain the stock return forecasting. You should predict what could happen next week. Do not just summarize the history. The next week stock return need not to be the same as the previous week. Use format Summary: ..., Keywords: ..., Stock Return. It is very important that you reason step by step before the finalized output, and explain the steps you have taken during your reasoning process."
PROMPT = f"Forecast next week stock return (price change) for {TICKER}, given the company profile, historical news from 2007 until now, keywords, and stock returns.\n\nYou are given the following data to elaborate a forecast:\n\n## WEEKLY STOCK PRICE\nWeekly stock returns, formatted as DATE1: PRICE1, DATE2: PRICE2, DATE3: PRICE3... \n\n## COMPANY PROFILE\nA short description of the company.\n\n## HISTORICAL NEWS\nA dataset of historical news scraped from The Wall Street Journal website that are related to {TICKER}. They are formatted as Date: ..., Title: ..., Summary: ...; Date2: ..., Title2: ..., Summary2: ...; Correlate the historical news of a certain date or time period to the stock price of that same period during your reasoning.\n\n## LATEST NEWS\nA dataset of the latest news related to {TICKER}, scraped from Yahoo Finance and summarized using GPT 3.5."
      
chat = ChatCompletion.create(
        model="gpt-4-1106-preview",
        messages = [{"role": "system", "content": PROMPT},
                  {"role": "user", "content": chatinput}])

output = f"{(chat['choices'][0]['message']['content'])}"
print(output)