from pyomo.environ import *
import math

### MODELAGEM ABSTRATA
#--------------------#

## Cria modelo abstrato do pyomo
model = AbstractModel()

## Parametros (Params)
## ---

# Numero de nos
model.n = Param(within=NonNegativeIntegers) #INICIALIZAR
# Escala
model.scale = Param(within=NonNegativeIntegers) #INICIALIZAR

## Conjuntos (Sets)
## ---

# Conjunto de nos
model.V = RangeSet(1,model.n)
# Conjunto de arestas
model.A = Set(model.V,model.V,dimen=2,doc="Arestas")
# Conjunto de modelos/tipos de transceptor
model.S = Set(initialize=["S2C","S2CPro","S3"],doc="Modelos")

## Constantes do problema (demais parametros)

# Coordenadas x dos nos
model.X = Param(model.V) #INICIALIZAR
# Coordenadas y dos nos
model.Y = Param(model.V) #INICIALIZAR
# Conjunto de corrente consumida media (I)
model.I = Param(model.S) #INICIALIZAR
# Conjunto de custo medio em dolar (M)
model.MC = Param(model.S) #INICIALIZAR
# Conjunto de raio maximo de alcance (Rmax)
model.RMAX = Param(model.S) #INICIALIZAR
# Distancia entre pares de posicoes fixas (D)
def init_D(model, i, j):
    return math.sqrt(pow((model.X[i]-model.X[j])*model.scale,2)+pow((model.Y[i]-model.Y[j])*model.scale,2))

model.D = Param(model.V,model.V,initialize=init_D,domain=NonNegativeReals) ##DECLARACAO TALVEZ ESTEJA ERRADA

# # Vizinhanca dos nos
def init_N(model, t, i):
    for j in model.V:
        if(i != j):
            if(model.D[i,j] > model.RMAX[t]):
                yield j

model.N = Set(model.S,model.V,initialize=init_N) ##DECLARACAO TALVEZ ESTEJA ERRADA

# Parametros de iteracao (i,j,t)
# ---
# model.i = Param(model.V,default=1)
# model.j = Param(model.V,default=1)
# model.t = Param(model.S,default="S2C",doc="Modelo")
# model.u = Param(model.S,default="S2C",doc="Modelo")

# # Parametro de iteracao na vizinhanca (k)
# model.k = Param(model.i,model.t,model.N) ##DECLARACAO TALVEZ ESTEJA ERRADA


# Variaveis de decisao
# ---
# model.s = Var(model.t, model.i, within=Binary)

# # Funcoes objetivo
# # ---
# # Consumo de Energia
# def obj_Energy_rule(model):
#     return sum( sum(model.I*model.s[t][i] for t in model.S) for i in model.V)

# model.E = Objective(rule=obj_Energy_rule,sense=minimize)

# # Area de Cobertura
# def obj_Coverage_rule(model):
#     return sum( sum(math.pi*pow(RMAX[t],2)*model.s[t][i] for t in model.S) for i in model.V)

# model.C = Objective(rule=obj_Coverage_rule,,sense=maximize)

# # Custo financeiro
# def obj_Monetary_rule(model):
#     return sum( sum(model.MC*model.s[t][i] for t in model.S) for i in model.V)

# model.M = Objective(rule=obj_Monetary_rule,sense=minimize)

# Expressoes
# ---

#Nor = min(1,summation(model.s))

# Restricoes
# ---





#-----------------------------------------------------------#

## OUTPUT
## ------

## IMPRIME MODELO
# model.pprint()

## CARREGA DADOS DE INSTANCIA NO MODELO ABSTRATO
data = DataPortal()
data.load(filename='sap.dat', model=model)
instance = model.create_instance(data)

print(instance.D[1,2])
instance.pprint()

# ## IMPRIME INSTANCIA (FUNCIONA? TESTAR)
# instance.pprint()

# ## RESOLVE INSTANCIA
# optimizer = SolverFactory('glpk', executable='glpsol')
# optimizer.solve(instance)
# instance.display

# SolverFactory('cplex', executable='cplex').solve(model).write()

#ADICIONAR AO FINAL UM POS PROCESSAMENTO PARA VISUALIZAR A SOLUCAO EM 2D. Usar inicialmente texto, mas depois fazer com matplot.