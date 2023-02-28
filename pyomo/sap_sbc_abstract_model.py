from pyomo.environ import *
import math

#Constantes
BIG = -100000
SMALL = 100000

### MODELAGEM ABSTRATA
#--------------------#

#Funcoes de inicializacao do modelo

# Distancia entre pares de posicoes fixas (D)
def init_D(model, i, j):
    return math.sqrt(pow((model.X[i]-model.X[j])*model.scale,2)+pow((model.Y[i]-model.Y[j])*model.scale,2))

# Vizinhanca dos nos (somente considerado vizinho se entre 80% e 100% do alcance maximo, de forma a garantir afastamento minimo)
def init_N(model, t, i):
    for j in model.V:
        if(i != j):
            if(model.D[i,j] < model.RMAX[t] and model.D[i,j] > 0.8*model.RMAX[t]):
                yield j

# FO - Consumo de Energia
def obj_Energy_rule(model):
    return sum(sum(model.I[t]*model.s[t,i] for t in model.S) for i in model.V)

# FO - Area de Cobertura
def obj_Coverage_rule(model):
    return sum(sum(math.pi*pow(model.RMAX[t],2)*model.s[t,i] for t in model.S) for i in model.V)

# FO - Custo Monetario
def obj_Monetary_rule(model):
    return sum(sum(model.MC[t]*model.s[t,i] for t in model.S) for i in model.V)

# FO - Metodo das ponderacoes
def obj_WEIGHTED(model):
    return model.weig

# Computa a quantidade de vizinhos para cada no i de tipo t
def init_Neig(model, t, i):
    for u in model.S:
        neig = 0
        for j in model.N[t,i]:
            if j not in model.V:
                return 0
            else:
                neig = neig + 1
    return neig

# Restricao de tipo (apenas um t por posicao)
def const_typenum(model, i):
    return (0,sum( model.s[t,i] for t in model.S),1)

# Restricao de quantidade minima (LB) e maxima (UB) de alocacao
def const_numalloc(model):
    return (max(2,ceil(0.05*model.n)),sum( sum( model.s[t,i] for t in model.S) for i in model.V),model.n)

# Restricao de vizinhanca (nao deve haver nenhum no sem vizinhos)
def const_OR(model):
    return sum( sum( model.s[t,i] * (1 - min(1,model.Neig[t,i])) for t in model.S) for i in model.V) == 0

# Funcao principal para gerar instancia do modelo
def generate_model(fo, alpha):

    ## Cria modelo abstrato do pyomo
    model = AbstractModel()

    ## Parametros (Params)
    ## ---
    # Numero de nos
    model.n = Param(within=NonNegativeIntegers) #INICIALIZAR
    # Largura do terreno
    model.W = Param(within=NonNegativeIntegers) #INICIALIZAR
    # Altura do terreno
    model.H = Param(within=NonNegativeIntegers) #INICIALIZAR
    # Menores coordenadas (X,Y)
    model.smallest_X = Param(within=NonNegativeIntegers, initialize = 0) #INICIALIZAR
    model.smallest_Y = Param(within=NonNegativeIntegers, initialize = 0) #INICIALIZAR
    # Maiores coordenadas (X,Y)
    model.biggest_X = Param(within=NonNegativeIntegers, initialize = model.n) #INICIALIZAR
    model.biggest_Y = Param(within=NonNegativeIntegers, initialize = model.n) #INICIALIZAR
    # Altura do terreno
    model.H = Param(within=NonNegativeIntegers) #INICIALIZAR
    # Escala
    model.scale = Param(within=NonNegativeIntegers) #INICIALIZAR

    ## Conjuntos (Sets)
    ## ---
    # Conjunto de nos
    model.V = RangeSet(1,model.n)
    # Conjunto de arestas
    model.A = Set(model.V,model.V,doc="Arestas",within=Binary)
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
    model.D = Param(model.V,model.V,initialize=init_D,domain=NonNegativeReals)

    # Vizinhanca dos nos
    model.N = Set(model.S,model.V,initialize=init_N)

    # Variaveis de decisao
    # ---
    model.s = Var(model.S, model.V, within=Binary)

    ## Funcoes objetivo
    ## ---

    # FO - Consumo de Energia
    model.E = Objective(rule=obj_Energy_rule,sense=minimize)
    # FO - Area de Cobertura
    model.C = Objective(rule=obj_Coverage_rule,sense=maximize)
    # FO - Custo Monetario
    model.M = Objective(rule=obj_Monetary_rule,sense=minimize)

    model.E.deactivate()
    model.C.deactivate()
    model.M.deactivate()

    #Significa que temos apenas 1 FO
    if sum(list(alpha.values())) == 1:
        if fo['E'] == 1:
            model.E.activate()
        elif fo['C'] == 1:
            model.C.activate()
        elif fo['M'] == 1:
            model.M.activate()
    #Significa que o problema eh multiobjetivo (ponderado por alphas)
    else:
        model.weig = alpha['E'] * fo['E'] * model.E - alpha['C'] * fo['C'] * model.C + alpha['M'] * fo['M'] * model.M
        model.WEIGHTED = Objective(rule=obj_WEIGHTED,sense=minimize)
        model.WEIGHTED.activate()

    ## Expressoes
    ## ---

    # Computa a quantidade de vizinhos para cada no i de tipo t
    model.Neig = Param(model.S, model.V, initialize=init_Neig)

    # Restricoes
    # ---

    #Restricao de tipo (apenas um t por posicao)
    model.typenum = Constraint(model.V, rule=const_typenum)

    # #Restricao de quantidade minima (LB) e maxima (UB) de alocacao
    model.numalloc = Constraint(rule=const_numalloc)

    # Restricao de vizinhanca (nao deve haver nenhum no sem vizinhos)
    model.OR = Constraint(rule=const_OR)

    return model