from sap_sbc_abstract_model import generate_model
from pyomo.environ import *
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np

# Script principal para resolver instancias do SAP

## CONSTRUCAO DO MODELO E INSTANCIA

## Seleciona FOs que serao ponderadas (dicionario binario)
fo = {'E': 0, 'C': 0, 'M': 1}

## Seleciona valores de alpha para cada FO (ponderacao)
alpha = {'E': 0.5, 'C': 0.5, 'M': 0}

#Se apenas 1 FO estiver ativa, zera os outros alphas e define o alpha respectivo como 1
if sum(list(fo.values())) == 1:
    index = list(fo.keys())[list(fo.values()).index(1)]
    alpha=alpha.fromkeys(alpha,0)
    alpha[index] = 1
# Valores de alpha nao podem somar mais que 1.0 = 100%
elif sum(list(alpha.values())) != 1:
    print("Erro. Valores de alpha somam diferente de 100%!")
    exit(-1)

## Gera modelo abstrato
model = generate_model(fo, alpha)

## Imprime modelo abstrato
#model.pprint()

## Carrega dados de instancia no modelo
data = DataPortal()
data.load(filename='sap.dat', model=model)
instance = model.create_instance(data)

## Imprime instancia
instance.pprint()

#-----------------------------------------------------------#

## SOLVER
## ------

#Cria um solver
opt = SolverFactory('cplex', executable='cplex')
#Resolve a instancia e armazena os resultados em um arquivo JSON
results = opt.solve(instance, tee=True)
instance.solutions.store_to(results)
results.write(filename='results.json',format='json')

#Pega resultados diretamente
print("\n\n")

#Funcao objetivo (valor otimo)
print("C: "+str(value(instance.C))+" m²")

#Funcao objetivo (valor otimo)
print("E: "+str(value(instance.E))+" mA")

#Funcao objetivo (valor otimo)
print("M: $"+str(value(instance.M)))

#Variavel de decisao (exemplo)
#print(value(instance.s['S2C',1]))

#Tempo de execucao do solver
print("Solving time: "+str(results.solver.user_time))

#Tempo de execucao total (incluido tempo de traducao do modelo do pyomo para o solver)
print("Total time: "+str(results.solver.time))

#Imprime resultados
#print(results)

#-----------------------------------------------------------#

## POS-PROCESSAMENTO
## -----------------

# Plota todos os espacos disponiveis para alocacao como circulos nao-preenchidos pretos
# Se estiver alocado, preenche o circulo e colore de acordo com modelo de transceptor ativo

fig = plt.figure('Resultado ótimo do SAP')
ax = fig.add_subplot(1,1,1)
ax.axis("equal")

for i in instance.V:
    if value(instance.s['S2C',i]) == 1:
        ax.plot(instance.X[i],instance.Y[i],'go')
        ax.add_patch(plt.Circle((instance.X[i],instance.Y[i]), (instance.RMAX['S2C']/instance.scale), color='g', alpha=0.1))
    elif value(instance.s['S2CPro',i]) == 1:
        ax.plot(instance.X[i],instance.Y[i],'bo')
        ax.add_patch(plt.Circle((instance.X[i],instance.Y[i]), (instance.RMAX['S2CPro']/instance.scale), color='b', alpha=0.1))
    elif value(instance.s['S3',i]) == 1:
        ax.plot(instance.X[i],instance.Y[i],'ro')
        ax.add_patch(plt.Circle((instance.X[i],instance.Y[i]), (instance.RMAX['S3']/instance.scale), color='r', alpha=0.1))
    else:
        ax.plot(instance.X[i],instance.Y[i],'ko',fillstyle='none')

ax.grid(linestyle='--',linewidth=0.5,alpha=0.5)
ax.set_xticks(np.arange(int(instance.smallest_X),int(instance.biggest_X)+1,1))
ax.set_yticks(np.arange(int(instance.smallest_Y),int(instance.biggest_Y)+1,1))

red_patch = mpatches.Patch(color='red', label='S3')
blue_patch = mpatches.Patch(color='blue', label='S2CPro')
green_patch = mpatches.Patch(color='green', label='S2C')

ax.legend(handles=[red_patch,blue_patch,green_patch], loc='upper right')

plt.xlabel('Coordenadas X')
plt.ylabel('Coordenadas Y')
plt.title('Escala: '+str(int(instance.scale))+' : 1 m\nAlphas: '+str(alpha['E'])+'E, '+str(alpha['C'])+'C, '+str(alpha['M'])+'M')
plt.show()
