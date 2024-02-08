#Installazione delle librerie nell'environment di Google Colab
!pip install transformers
!pip install accelerate
!pip install auto-gptq --extra-index-url https://huggingface.github.io/autogptq-index/whl/cu118/
!pip install optimum
!pip install langchain
!pip install beautifulsoup4
!pip install requests
!pip install unstructured[pdf]
!pip install sentence-transformers
!pip install chromadb

#Importazione delle librerie di interesse.
from transformers import AutoModelForCausalLM, AutoTokenizer
from sentence_transformers import SentenceTransformer
import torch
from langchain.vectorstores import Chroma #ChromaDB integrato con LangChain
from langchain.document_loaders import DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import SentenceTransformerEmbeddings
import requests
from bs4 import BeautifulSoup
from pprint import pprint
import re
import os

#Sezione di scraping del sito web delle Nazioni Unite per recuperare i documenti di interesse. In questo caso, si tratta di 50 documenti del Consiglio di Sicurezza dell'ONU in lingua inglese, aventi come argomento il conflitto Israelo-Palestinese
url = "https://digitallibrary.un.org/search?ln=en&rm=&sf=&so=d&rg=50&c=Resource%20Type&c=UN%20Bodies&c=&of=hb&fti=0&fct__1=Meeting%20Records&fct__2=Security%20Council&fct__3=2023&fti=0&p="
data = requests.get(url)
soup = BeautifulSoup(data.content)
articles = soup.select('a.moreinfo')
cleanlinks = []
#Creazione di una lista composta da tutti gli URL presenti nella pagina iniziale
links = []
for a_tag in soup.find_all('a', class_="moreinfo", href=True):
    links.append(a_tag['href'])
#Creazione di una lista composta da tutti gli URL che puntano ad un PDF
for i in links:
    if "record" in i:
        cleanlinks.append(i)      
#Apertura di ogni singolo URL ottenuto e recupero dei file PDF di interesse, salvandoli in una cartella locale.
documentspage = []
base_url = "https://digitallibrary.un.org"
for i in cleanlinks:
    request_href = base_url + str(i)
    minidata = requests.get(request_href)
    minisoup = BeautifulSoup(minidata.content)
    for j in minisoup.find_all('meta', content=True):
        if "EN" in str(j):
            substring = str(j).split("content=\"")[1]
            substring = substring.split("\" name")[0]
            os.system('wget %s' % substring)
            print("Done")
#Percorso in cui sono contenuti i file PDF scaricati.
directory = "/content/PDF"
#Creazione di una funzione che carichi i documenti dalla cartella locale.
def docloader(directory):
    loader = DirectoryLoader(directory)
    documents = loader.load()
    return documents
#Creazione di una funzione che splitti i documenti per non superare i limiti di embedding.
def docsplitter(documents, chunk_size=1000, chunk_overlap=20):
    textsplitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    splitteddocs = textsplitter.split_documents(documents)
    return splitteddocs
#Caricamento della cartella precedentemente specificata e vettorizzazione dei documenti utilizzando SentenceTransformer
documents = docloader(directory)
splitteddocs = docsplitter(documents)
embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2") #V. https://docs.trychroma.com/embeddings

#Creazione del database vettoriale
db = Chroma.from_documents(splitteddocs, embeddings)

#Inizializzazione del modello StableBeluga a 7B ottimizzato tramite GPTQ
model = AutoModelForCausalLM.from_pretrained("TheBloke/StableBeluga-7B-GPTQ", device_map="auto", torch_dtype=torch.float16)
#Inizializzazione del tokenizer
tokenizer = AutoTokenizer.from_pretrained("TheBloke/StableBeluga-7B-GPTQ")
#Creazione di una funzione che formatti l'input in modo da inserire la domanda posta e il relativo contesto da fornire al modello
def ask(syst, context, question):
    return f"""### System:\n{syst}\n\n### User:\n\n## Context\n\n{context}\n\n## Question\n\n {question}\n\n### Assistant:\n"""

#Creazione di una funzione che interroghi il modello e restituisca la risposta
def invoke(p, maxlen, sample=True):
  tokens = tokenizer(p, return_tensors="pt")
  answer = model.generate(**tokens.to("cuda"), max_new_tokens=maxlen, do_sample=sample).to("cpu")
  answer = str(tokenizer.batch_decode(answer))
  return answer.split("### Assistant:\\n ",1)[1]

#Definizione della funzione di ricerca semantica
def search(question, k):
    simsearch = db.similarity_search_with_relevance_scores(question, k)
    return simsearch

#Formato di interrogazione del modello.
%%time
#Definizione delle custom instructions. In questo caso, viene imposto al modello di rispondere alla domanda posta solamente utilizzo le informazioni fornite come contesto; nel caso in cui trovi nulla di attinente, non deve cercare di rispondere comunque, ma dire chiaramente di non essere in grado di rispondere. In questo modo, si cerca di evitare il problema delle allucinazioni.
syst = "You are Stable Beluga, an AI that follows instructions and helps the user as much as it can. Please answer the question with information from the context given. If there isn't enough information in the context, don't try to answer and just say it."
question = "How is the European Unione contributing the resolution of the Palestinian conflict?"
#Contesto fornito al modello per la generazione della risposta, ottenuto tramite la funzione di ricerca semantica
context = search(question, 15)
invoke(ask(syst, context, question), 1000)