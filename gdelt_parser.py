LAT_MIN = -3.0000
LAT_MAX = 37.0000
LONG_MIN = 27.0000
LONG_MAX = 64.0000

actors = ['israel', 'palestine']

import gdelt
import csv
import os
from datetime import datetime

try:
    os.remove('gdeltdb.csv')
    os.remove('cleanevents.csv')
except:
    pass

#Modifica questo ciclo per creare una lista adatta all'intervallo temporale di interesse. In questo caso, vogliamo il mese di Gennaio 2024
datelist = []
for j in range(30, 31):
    if j < 10:
        d = f"2024 01 0{j}"
    else:
        d = f"2024 01 {j}"
    datelist.append(d)

gd = gdelt.gdelt(version=2)
for i in datelist:
    results = gd.Search(i, table='events', coverage=True, output='csv')
    print("Retrieving data for:", i)
    with open('gdeltdb.csv', 'a', encoding='utf-8') as f:
        f.write(results)

data_list = []
with open('gdeltdb.csv', 'r', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)

    for row in reader:
        data = {'Actor1Name':row['Actor1Name'], 'Actor2Name':row['Actor2Name'], 'EventCode':row['EventCode'], 'Actor1Geo_Lat':row['Actor1Geo_Lat'], 'Actor1Geo_Long':row['Actor1Geo_Long'], 'Actor2Geo_Lat':row['Actor2Geo_Lat'], 'Actor2Geo_Long':row['Actor2Geo_Long'], 'ActionGeo_Lat':row['ActionGeo_Lat'], 'ActionGeo_Long':row['ActionGeo_Long']}
        #Filtraggio in base agli attori e corrispondenza tra nomi di attori simili per evitare doppie entrate inutili (come ISRAEL e ISRAELI)
        for a in actors:
            if (a in data['Actor1Name'].lower()):
                data['Actor1Name'] = a.upper()
                data_list.append(data)
                print(data)
                break
            elif (a in data['Actor2Name'].lower()):
                data['Actor2Name'] = a.upper()
                data_list.append(data)
                print(data)
            elif (data['Actor1Name'].lower()=='palestinian'):
                data['Actor1Name']='PALESTINE'
                data_list.append(data)
                print(data)
            elif (data['Actor2Name'].lower()=='palestinian'):
                data['Actor2Name']='PALESTINE'
                data_list.append(data)
                print(data)

fields = ['Actor1Name', 'Actor2Name', 'EventCode', 'Actor1Geo_Lat', 'Actor1Geo_Long', 'Actor2Geo_Lat', 'Actor2Geo_Long', 'ActionGeo_Lat', 'ActionGeo_Long'] #Possiamo anche pensare di selezionare una zona per LAT e LONG

#Filtraggio per posizione in latitudine e longitudine
lat_min = LAT_MIN
lat_max = LAT_MAX
long_min = LONG_MIN
long_max = LONG_MAX

#Dobbiamo filtrare meglio

with open('cleanevents.csv', 'w', encoding='utf-8') as f:
    f.write("Source;Target;Label\n")
for i in data_list:
    cleandict = {key: i[key] for key in fields}
    try:
        #Filtraggio per posizione
        if ((((float(cleandict['Actor1Geo_Lat']) > lat_min) and (float(cleandict['Actor1Geo_Lat']) < lat_max)) or ((float(cleandict['Actor2Geo_Lat']) > lat_min) and (float(cleandict['Actor2Geo_Lat']) < lat_max)) or ((float(cleandict['ActionGeo_Lat']) > lat_min) and (float(cleandict['ActionGeo_Lat']) < lat_max))) and (((float(cleandict['Actor1Geo_Long']) > long_min) and (float(cleandict['Actor1Geo_Long']) < long_max)) or ((float(cleandict['Actor2Geo_Long']) > long_min) and (float(cleandict['Actor2Geo_Long']) < long_max)) or ((float(cleandict['ActionGeo_Long']) > long_min) and (float(cleandict['ActionGeo_Long']) < long_max)))):
            with open('cleanevents.csv', 'a', encoding='utf-8') as f:
                f.write(f"{str(cleandict['Actor1Name'])};{str(cleandict['Actor2Name'])};{str(cleandict['EventCode'])}\n")      
        else:
            pass
    except:
        pass