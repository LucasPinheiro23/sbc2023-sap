from efficient_sap_sbc_abstract_model import *
# from sap_sbc_abstract_model import *
from pyomo.environ import *
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import logging
import os

#Muda diretorio (BUG DO VSCODE)
os.chdir('./pyomo')

# Script principal para resolver instancias do SAP

#Suprime logs de warning do Pyomo (necessario pois gera muitas warnings durante alteracoes do modelo para calcular min-max)
logging.getLogger('pyomo.core').setLevel(logging.ERROR)

#Nome do arquivo da instancia a ser resolvida
#instance_filename = '../instances_DAT/512/T1.dat'
instance_filename = 'sap-10.dat'
# instance_filename = 'sap-20.dat'
# instance_filename = 'sap-100.dat'
#Solver a ser utilizado
solver = 'cplex'
#Executavel do solver
solver_exec = 'cplex'

## CONSTRUCAO DO MODELO E INSTANCIA

## Seleciona FOs que serao ponderadas (dicionario binario)
fo = {'E': 0, 'C': 1, 'M': 0}

## Seleciona valores de alpha para cada FO (ponderacao)
alpha = {'E': 0.5, 'C': 0.5, 'M': 0}

#Se apenas 1 FO estiver ativa, zera os outros alphas e define o alpha respectivo como 1
if sum(list(fo.values())) == 1:
    index = list(fo.keys())[list(fo.values()).index(1)]
    alpha=alpha.fromkeys(alpha,0)
    alpha[index] = 1
# Valores de alpha devem somar exatamente 1.0 = 100%
elif sum(list(alpha.values())) != 1:
    print("Erro. Valores de alpha somam diferente de 100%!")
    exit(-1)

## Gera modelo abstrato
model = generate_model()

if(fo['E'] == 1 and fo['C'] == 0 and fo['M'] == 0):
    model.E.activate()
elif(fo['E'] == 0 and fo['C'] == 1 and fo['M'] == 0):
    model.C.activate()
elif(fo['E'] == 0 and fo['C'] == 0 and fo['M'] == 1):
    model.M.activate()
else:
    print("ERRO SELECAO INCORRETA")
    exit(0)

## Imprime modelo abstrato
#model.pprint()

# ##Normalizacao min-max - Etapa 1

# #Coleta os valores minimos e maximos de cada FO
# print("Calculando min-max:")
# max_fo = get_fo_max(model, fo, instance_filename, solver, solver_exec)
# min_fo = get_fo_min(model, fo, instance_filename, solver, solver_exec)
# print("Maximos: "+str(max_fo))
# print("Minimos: "+str(min_fo))

# # #Cria novos objetivos normalizados
# if(fo['E'] == 1):
#     model.exp_norm_E = (model.E - min_fo['E'])/(max_fo['E']-min_fo['E'])
# else:
#     model.exp_norm_E = 0

# if(fo['C'] == 1):
#     model.exp_norm_C = (model.C - min_fo['C'])/(max_fo['C']-min_fo['C'])
# else:
#     model.exp_norm_C = 0

# if(fo['M'] == 1):
#     model.exp_norm_M = (model.M - min_fo['M'])/(max_fo['M']-min_fo['M'])
# else:
#     model.exp_norm_M = 0

# model.norm_E = Objective(rule=obj_norm_E,sense=minimize)
# model.norm_C = Objective(rule=obj_norm_C,sense=maximize)
# model.norm_M = Objective(rule=obj_norm_M,sense=minimize)

# #Ativa FOs de acordo
# model.norm_E.deactivate()
# model.norm_C.deactivate()
# model.norm_M.deactivate()
# if fo['E'] == 1 and fo['C'] == 0 and fo['M'] == 0:
#     model.norm_E.activate()
# elif fo['E'] == 0 and fo['C'] == 1 and fo['M'] == 0:
#     model.norm_C.activate()
# elif fo['E'] == 0 and fo['C'] == 0 and fo['M'] == 1:
#     model.norm_M.activate()
#Se nao, significa que o problema eh multiobjetivo (ponderado por alphas)
# else:
#     model.weig = alpha['E'] * fo['E'] * model.norm_E - alpha['C'] * fo['C'] * model.norm_C + alpha['M'] * fo['M'] * model.norm_M
#     model.WEIGHTED = Objective(rule=obj_WEIGHTED,sense=minimize)
#     model.WEIGHTED.activate()

## Carrega dados de instancia no modelo
data = DataPortal()
data.load(filename=instance_filename, model=model)
instance = model.create_instance(data)

## Imprime instancia
#instance.pprint()

#TESTE DE REMOCAO DE ITEM DO SET, FUNCIONA!
# instance.N['S2C',1] = instance.N['S2C',1] - {3}
instance.N.pprint()
# instance.AP4.pprint()

# exit(0)

#-----------------------------------------------------------#

## SOLVER
## ------

#Cria um solver
opt = SolverFactory(solver, executable=solver_exec)
#opt = SolverFactory('glpk', executable='glpsol')

#Resolve a instancia e armazena os resultados em um arquivo JSON
results = opt.solve(instance, tee=True)
instance.solutions.store_to(results)
results.problem.name = instance_filename
results.write(filename='results.json',format='json')

#Normalizacao min-max - Etapa 2 (normaliza os resultados de acordo com os valores calculados previamente)
# if fo['E'] == 1:
#     norm_E = (value(instance.E) - min_fo['E'])/(max_fo['E']-min_fo['E'])
# else:
#     norm_E = 0

# if fo['C'] == 1:
#     norm_C = (value(instance.C) - min_fo['C'])/(max_fo['C']-min_fo['C'])
# else:
#     norm_C = 0

# if fo['M'] == 1:
#     norm_M = (value(instance.M) - min_fo['M'])/(max_fo['M']-min_fo['M'])
# else:
#     norm_M = 0

# norm_WEIGHTED = alpha['E'] * fo['E'] * norm_E - alpha['C'] * fo['C'] * norm_C + alpha['M'] * fo['M'] * norm_M

#Pega resultados diretamente
# print("\nResultados:\n")

# #Funcoes objetivo (valores otimos)
# if(fo['C'] == 1):
#     print("C: "+str(value(instance.norm_C))+" -- "+ str(min_fo['C']+(max_fo['C']-min_fo['C'])*value(instance.norm_C)) +" m^2")

# if(fo['E'] == 1):
#     print("E: "+str(value(instance.norm_E))+" -- "+ str(min_fo['E']+(max_fo['E']-min_fo['E'])*value(instance.norm_E)) +" mA")

# if(fo['M'] == 1):
#     print("M: "+str(value(instance.norm_M))+" -- $"+ str(min_fo['M']+(max_fo['M']-min_fo['M'])*value(instance.norm_M)))

# #Funcao multiobjetivo (valor otimo)
# if(sum(list(fo.values())) > 1):
#     print("WEIGHTED: "+str(value(instance.WEIGHTED)))

#Variavel de decisao (exemplo)
#print(value(instance.s['S2C',1]))

#Tempo de execucao do solver
print("Solving time: "+str(results.solver.user_time)+" s")

#Tempo de execucao total (incluido tempo de traducao do modelo do pyomo para o solver)
print("Total time: "+str(results.solver.time)+" s")

#Imprime resultados
#print(results)

#-----------------------------------------------------------#

## POS-PROCESSAMENTO
## -----------------

# Plota todos os espacos disponiveis para alocacao como circulos nao-preenchidos pretos
# Se estiver alocado, preenche o circulo e colore de acordo com modelo de transceptor ativo

fig = plt.figure('Resultado Ótimo do PAS')
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
    
    plt.text(instance.X[i], instance.Y[i], str(i), color="red", fontsize=12)

ax.grid(linestyle='--',linewidth=0.5,alpha=0.5)
# ax.set_xticks(np.arange(int(instance.smallest_X),int(instance.biggest_X)+1,1))
# ax.set_yticks(np.arange(int(instance.smallest_Y),int(instance.biggest_Y)+1,1))

red_patch = mpatches.Patch(color='red', label='S3')
blue_patch = mpatches.Patch(color='blue', label='S2CPro')
green_patch = mpatches.Patch(color='green', label='S2C')

ax.legend(handles=[red_patch,blue_patch,green_patch], loc='upper right')

plt.xlabel('Eixo X (m)')
plt.ylabel('Eixo Y (m)')
plt.title('Instancia: '+str(instance_filename)+'\nEscala: '+str(int(instance.scale))+' : 1 m\nAlphas: '+str(alpha['E'])+'E, '+str(alpha['C'])+'C, '+str(alpha['M'])+'M')
plt.show()