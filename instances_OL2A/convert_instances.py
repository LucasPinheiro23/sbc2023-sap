#Converte instancias da OL2A (OPL) em instancias do pyomo

import pyperclip

data = input("Entre com os CSV: ")

res = list(map(str.strip, data.split(",")))

count = 1

clip = ""

for i in res:
    clip = clip + str(count) + " " + str(i) + "\n"
    count +=1

pyperclip.copy(clip)