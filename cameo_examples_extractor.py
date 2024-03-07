#Creiamo un set di esempi presi dal documento CAMEO (http://data.gdeltproject.org/documentation/CAMEO.Manual.1.1b3.pdf)
from langchain.document_loaders import DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import SentenceTransformerEmbeddings
from unstructured.partition.pdf import partition_pdf
import tabula

#Le tabelle del PDF sono state convertite in formato CSV utilizzando il tool Tabula (https://tabula.technology/)
with open("C:\\Users\\umbyf\\OneDrive\\Desktop\\Christopher\\finalproject\\tabula-examples_pdf.csv", encoding="utf-8") as f:
    text = f.read()

#Filtraggio e pulizia dei dati
    
cltext = text.replace("Name,", "Name: ")
cltext = cltext.replace("Description,", "Description: ")
cltext = cltext.replace("Usage Notes,", "Usage Notes: ")
cltext = cltext.replace("\n", " ")
cltext = cltext.replace("Example,", "Example: ")
cltext = cltext.replace("Example Note,", "NOTE: ")
cltext = cltext.replace("\",", "")
cltext = cltext.replace("\"", "")
cltext = cltext.replace("- \"\",", "")
cltext = cltext.replace("- ", "")
cltext = cltext.replace(",,", "")
cltext = cltext.replace(".,", ".")
with open("C:\\Users\\umbyf\\OneDrive\\Desktop\\Christopher\\finalproject\\cameoarchive\\cameo_examples.txt", "w") as f:
    f.write(cltext)
alist = cltext.split("CAMEO,")
blist = []
blist.clear()
for i in alist:
    if (",") in i[:5]:
        j = i[:5].replace(",", "")
        j = j + i[5:]
        blist.append(j)
    else:
        blist.append(i)
blist.pop(0)
clist = []
clist.clear()
examples_list = []
training_dict = {}
training_dict.clear()
training_list = []
training_list.clear()
for j in blist:
    examples_list.clear()
    code, ee = j.split(" Name: ")
    name, ee = ee.split(" Description: ")
    #Alcuni non hanno le Usage Notes
    try:
        usage_notes_index = ee.index(" Usage Notes: ")
        description = ee[:usage_notes_index]
        try: #Vediamo se c'è un esempio o meno
            first_example_index = ee.index(" Example: ")
            usage_notes = ee[usage_notes_index+14:first_example_index]
        except:
            usage_notes = ee[usage_notes_index+14:]    
    except:
        #Troviamo il primo Esempio nel caso in cui ce ne siano multipli, ora vogliamo solo salvare la Description
        try:
            first_example_index = ee.index(" Example: ")
            description = ee[:first_example_index]
            usage_notes = "N/A"
        except:
            description = ee
            usage_notes = "N/A"    
    #Contiamo il numero di esempi
    num_ex = ee.count(" Example: ")
    if num_ex > 1:
        print(f"Multiple Indexes ({num_ex})")
        for i in range(num_ex):
            #Last Example
            if i+1 == num_ex:
                examples_list.append(ee[10:])
            else:
                index = ee.find(" Example: ")
                index2 = ee[index+10:].find(" Example: ")
                ex_string = ee[index+10:index+10+index2]
                ee = ee[index+10+index2:]
                examples_list.append(ex_string)
    elif num_ex == 1:
        example_index = ee.find(" Example: ")
        example = ee[example_index+10:]
        examples_list.append(example)
    else:
        examples_list.append("N/A")
 
    print(f"Code: {code}\nName: {name}\nDescription: {description}\nUsage Notes: {usage_notes}\nExample(s): {examples_list}")
    
#Creiamo il format per il training
system_message = "You are an artificial intelligence used to make predictions of geopolitical events. You understand the meaning of CAMEO coding, and you are able to correlate the occurrence of certain events with geopolitical consequences."
format_string = ""
with open("C:\\Users\\umbyf\\OneDrive\\Desktop\\Christopher\\finalproject\\finetuning_examples.txt", "a+") as f:
    format_string = f"{{\"messages\": [{{\"role\": \"system\", \"content\":\"{system_message}\"}}, {{\"role\": \"user\", \"content\": \"Describe the name of the CAMEO Code provided, its description, its usage notes and give a real-world example. Code: {code}\"}}, {{\"role\": \"assistant\", \"content\": \"Name: {name} - Description: {description} - Usage Notes: {usage_notes} - Example(s):"
    m = 0
    for k in examples_list:
        m = m+1
        format_string = format_string + f" {m}." + k
    format_string = format_string + "\"}]}"
    f.write(f"{format_string}\n")
    if examples_list[0] != "N/A":
        format_string = f"{{\"messages\": [{{\"role\": \"system\", \"content\":\"{system_message}\"}}, {{\"role\": \"user\", \"content\": \"Given the following real-world event, to which CAMEO code would you associate it?"
        for l in examples_list:
            if l != "N/A":
                format_string_v2 = format_string + " Example: " + l + f"\"}}, {{\"role\": \"assistant\", \"content\": \"Code: {code} - Name: {name} - Description: {description} - Usage Notes: {usage_notes}" + "\"}]}"
                f.write(f"{format_string_v2}\n")
        
