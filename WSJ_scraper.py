#Scraper per WSJ. Prendiamo solamente data, titolo e riassunto, altrimenti andiamo di molto fuori dal limite di contesto
#Importiamo le librerie necessarie

#VALORI DA MODIFICARE IN BASE ALLE ESIGENZE
TIMEPERIOD = -1 #Quanto voglio andare indietro in mesi dal momento attuale. Quindi 204 da ora e' Gennaio 2007
TICKER = "NVDA"
SAVEFILE = "data_nvda.txt"

import yfinance as yf
import pandas as pd

ticker = yf.Ticker(TICKER)
stock_summary =  ticker.info["longBusinessSummary"]

#Fornisci le info sulla compagnia come system per dare migliore contesto. Ricorda anche di inserire sigla TICKER manualmente
import openai
from openai import ChatCompletion, Completion

system_message = f"Generate 10 to 20 single words related to the company associated to the stock ticker that you will be given. They will be used to select news articles that contain those keywords, in order to then feed those articles to a language model for financial forecasting; thus, words must be as unambiguous as possible, and technical. You are also given a short summary of the company, in order to chose better related words. Use the format: word 1,word 2,word 3,... without any additional output other than the words. Include the company name and the word {TICKER}. For each word, include it as capitalized and as all lower caps."
openai.api_key="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" #RICORDA DI COPRIRLO NELLA TESI

chat = ChatCompletion.create(
    model="gpt-4-1106-preview",
    messages = [{"role": "system", "content": system_message},
              {"role": "user", "content":f"Ticker: {TICKER}, Company description: {stock_summary}"}])
KEYWORDS = str(chat['choices'][0]['message']['content']).split(",")
print(KEYWORDS)

import requests
from bs4 import BeautifulSoup
from pprint import pprint
import re
import os
from bs4 import BeautifulSoup
from urllib.request import Request, urlopen

def crawler(site, hdr):
    req = Request(site,headers=hdr)
    page = urlopen(req)
    soup = BeautifulSoup(page)
    return soup

def link_scraper(soup):
    links = []
    for a_tag in soup.find_all('a', href=True):
        links.append(a_tag['href'])
    return links

#Prima fase dello scraping: caricare la pagina principale con i link degli anni e dei mesi

site= "https://www.wsj.com/news/archive/years"
hdr = {'User-Agent': 'Mozilla/5.0'}

soup = crawler(site, hdr)

#Identifichiamo tutti i link della pagina e selezioniamo solo quelli di interesse

links = link_scraper(soup)

#Selezioniamo solo i link contenenti anno/mese, ignorando il noise di tutto il resto
cleanlinks = []
cleanlinks.clear()
for i in links:
    if "/news/archive/1" in i or "/news/archive/2" in i:
        cleanlinks.append(i)

#La lista cleanlinks contiene tutti i link anno/mese

#Recuperiamo ora i link, per ogni anno/mese, di ogni giorno. Dovremo quindi iterare per ogni oggetto di cleanlinks

scrapedstring = ""

#Siamo arrivati a 2021/03/14

base_url = "https://www.wsj.com"

#for i in cleanlinks[:TIMEPERIOD]
for i in cleanlinks:
    site = base_url + str(i)
    monthsoup = crawler(site, hdr)
    
    #Abbiamo aperto il mese. Iteriamo sui giorni

    daylinks = []
    daylinks.clear()

    daylinks = link_scraper(monthsoup)
    cleandaylinks = []
    cleandaylinks.clear()
    for k in daylinks:
        if "/news/archive" in k:
            cleandaylinks.append(k)
    cleandaylinks.pop(0)
    cleandaylinks.pop(-1)
    cleandaylinks.pop(-1)
    
    #Abbiamo lista dei giorni. Iteriamo su ogni giorno
   
    for j in cleandaylinks: #cleandaylinks
        print("Scraping " + str(j))
        site = base_url + str(j) 
        daysoup = crawler(site, hdr)
       
        #Recuperiamo i link delle news dal giorno
        
        articles = []
        articles.clear()
        articles = link_scraper(daysoup)
        
        cleanarticles = []
        cleanarticles.clear()
        for j in articles:
            if "articles" in j:
                if j not in cleanarticles:
                    cleanarticles.append(j)
        tickerarticles = []
        tickerarticles.clear()
        for i in cleanarticles:
            for k in KEYWORDS:
                if k in i:
                    if i not in tickerarticles:
                        tickerarticles.append(i)
        
        #Selezioniamo solo gli articoli che contengono le keyword di interesse (possibilmente da rivedere le keyword)
        for f in tickerarticles:
            print("Scraping " + str(f))
            artsoup = crawler(f, hdr)
            
            #Aggiorniamo mega stringa strutturata come segue: "Date: ..., Title: ..., Description: ...;"
            date = str(artsoup.find_all("script", id="articleschema")).split("\"dateCreated\":\"")[1][:10]
            descr = str(artsoup.find_all("script", id="articleschema")).split("\"description\":\"")[1].split("\",\"")[0]
            scrapedstring = scrapedstring + "Date: " + date + ", Title: " + artsoup.title.string +", Description: " + descr +"; \n"
            print(scrapedstring)
                    
        for z in articles:
            if "page=2" in z:
                print("Scraping " + str(z) + " - Page 2")
                #C'e' pagina 2. Andiamo a scraparla
                site = base_url + str(z)
                daysoup = crawler(site, hdr)

                #Recuperiamo i link delle news dal giorno

                articles = []
                articles.clear()
                for a_tag in daysoup.find_all('a', href=True):
                    articles.append(a_tag['href'])

                cleanarticles.clear()
                for j in articles:
                    if "articles" in j:
                        if j not in cleanarticles:
                            cleanarticles.append(j)
                tickerarticles.clear()
                for i in cleanarticles:
                    for k in KEYWORDS:
                        if k in i:
                            if i not in tickerarticles:
                                tickerarticles.append(i)

                for f in tickerarticles: #tickerarticles
                    artsoup = crawler(f, hdr)

                    #Aggiorniamo mega stringa strutturata come segue: "Date: ..., Title: ..., Description: ...;"
                    date = str(artsoup.find_all("script", id="articleschema")).split("\"dateCreated\":\"")[1][:10]
                    descr = str(artsoup.find_all("script", id="articleschema")).split("\"description\":\"")[1].split("\",\"")[0]
                    scrapedstring = scrapedstring + "Date: " + date + ", Title: " + artsoup.title.string +", Description: " + descr +"; \n"
                    print(scrapedstring)
                    
                for n in articles:
                    if "page=3" in n:
                        print("Scraping " + str(n) + " - Page 3")
                        #C'e' pagina 3. Andiamo a scraparla
                        site = base_url + str(n)
                        daysoup = crawler(site, hdr)

                        #Recuperiamo i link delle news dal giorno

                        articles = []
                        articles.clear()
                        for a_tag in daysoup.find_all('a', href=True):
                            articles.append(a_tag['href'])

                        cleanarticles.clear()
                        for j in articles:
                            if "articles" in j:
                                if j not in cleanarticles:
                                    cleanarticles.append(j)
                        tickerarticles.clear()
                        for i in cleanarticles:
                            for k in KEYWORDS:
                                if k in i:
                                    if i not in tickerarticles:
                                        tickerarticles.append(i)

                        for f in tickerarticles: #tickerarticles
                            artsoup = crawler(f, hdr)

                            #Aggiorniamo mega stringa strutturata come segue: "Date: ..., Title: ..., Description: ...;"
                            date = str(artsoup.find_all("script", id="articleschema")).split("\"dateCreated\":\"")[1][:10]
                            descr = str(artsoup.find_all("script", id="articleschema")).split("\"description\":\"")[1].split("\",\"")[0]
                            scrapedstring = scrapedstring + "Date: " + date + ", Title: " + artsoup.title.string +", Description: " + descr +"; \n"
                            print(scrapedstring)

with open(SAVEFILE, "w") as f:
    f.write(scrapedstring)