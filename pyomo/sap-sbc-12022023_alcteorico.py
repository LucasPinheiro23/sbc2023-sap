import pyomo.environ as pyo
import math

#Define modelo abstrato do pyomo
model = pyo.AbstractModel()

#Numero de nos
model.n = pyo.Param(within=pyo.NonNegativeIntegers)

#Conjunto de nos
model.V = pyo.RangeSet(1,model.n)
#Conjunto de modelos/tipos de transceptor
model.S = pyo.Set(initialize=["S2C","S2CPro","S3"],doc="Modelos")

#Parametros de iteracao (i,j,t)
#---
model.i = pyo.Param(model.V,default=1)
model.j = pyo.Param(model.V,default=1)
model.t = pyo.Param(model.S,default="S2C",doc="Modelo")
model.u = pyo.Param(model.S,default="S2C",doc="Modelo")

#Conjunto de arestas
model.A = pyo.Set(model.i,model.j,dimen=2) #DECLARACAO TALVEZ ESTEJA ERRADA

#Constantes do problema
#---
#Coordenadas x dos nos
model.x = pyo.Set(model.i) #INICIALIZAR
#Coordenadas y dos nos
model.y = pyo.Set(model.i) #INICIALIZAR
#Conjunto de corrente consumida media (I)
model.I = pyo.Set(model.S) #INICIALIZAR
#Conjunto de custo medio em dolar (M)
model.Mc = pyo.Set(model.S) #INICIALIZAR
#Conjunto de raio maximo de alcance (Rmax)
model.Rmax = pyo.Set(model.S) #INICIALIZAR
#Distancia entre pares de posicoes fixas (D)
def init_D():
    for i in model.V:
        for j in model.V:
            if(i != j):
                yield math.sqrt(pow(model.x[i]-model.x[j],2)+pow(model.y[i]-model.y[j],2))

model.D = pyo.Set(initialize=init_D) ##DECLARACAO TALVEZ ESTEJA ERRADA
#Vizinhanca dos nos
def init_N():
    for t in model.S:
        for i in model.V:
            for j in model.V:
                if(i != j):
                    if(model.D[i][j] > Rmax[t])
                        yield j

model.N = pyo.Set(initialize=init_N) ##DECLARACAO TALVEZ ESTEJA ERRADA
#Parametro de iteracao na vizinhanca (k)
model.k = pyo.Param(model.i,model.t,model.N) ##DECLARACAO TALVEZ ESTEJA ERRADA


#Variaveis de decisao
#---
model.s = pyo.Var(model.i, model.t, domain=pyo.Binary)

#Funcoes objetivo
#---
#Consumo de Energia
def obj_Energy():
    return pyo.summation(model.I,model.s)

model.E = pyo.Objective(rule=obj_Energy)
#Area de Cobertura
def obj_Coverage():
    return pyo.summation(math.pi,model.Rmax,model.s)

model.C = pyo.Objective(rule=obj_Coverage)
#Custo financeiro
def obj_Monetary():
    return pyo.summation(model.M,model.s)

model.M = pyo.Objective(rule=obj_Monetary)

#Expressoes
#---

#Nor = min(1,pyo.summation(model.s))

#Restricoes
#---





model.s = pyo.Var()

#Imprime modelo
# model.pprint()

#Resolve o modelo com solver escolhido
# #SolverFactory('glpk', executable='glpsol').solve(model).write()
# SolverFactory('cplex', executable='cplex').solve(model).write()

#Apresenta solucao
#print('\nProfit = ', model.profit())

#print('\nDecision Variables')
#print('x = ', model.x())
#print('y = ', model.y())

#print('\nConstraints')
#print('Demand  = ', model.demand())
#print('Labor A = ', model.laborA())
#print('Labor B = ', model.laborB())

#ADICIONAR AO FINAL UM POS PROCESSAMENTO PARA VISUALIZAR A SOLUCAO EM 2D. Usar inicialmente texto, mas depois fazer com matplot.