from pyomo.environ import *
from itertools import chain, combinations
from collections import defaultdict
import math

### MODELAGEM ABSTRATA
# --------------------#

# Constante para linerizacao da funcao min()
M = 100000

# Funcoes de inicializacao do modelo


# Distancia entre pares de posicoes fixas (D)
def init_D(model, i, j):
    return model.scale * math.sqrt(
        pow((model.X[i] - model.X[j]), 2)
        + pow((model.Y[i] - model.Y[j]), 2)
    )


# Distancia entre posicoes de nos sensores e pontos parametrizados na regiao de monitoramento (DK)
def init_DK(model, i, j, k):
    return model.scale * math.sqrt(
        pow((model.X[i]-1 - model.W[j]), 2)
        + pow((model.Y[i]-1 - model.H[k]), 2)
    )


# Vizinhanca dos nos (somente considerado vizinho se entre 80% e 100% do alcance maximo, de forma a garantir afastamento minimo)
def init_N(model, t, i):
    for j in model.V:
        if i != j:
            if (
                model.D[i, j] <= model.RMAX[t]
            ):  # and model.D[i,j] >= 0.8*model.RMAX[t]):
                yield j
    yield 0


# FO - Consumo de Energia
def obj_Energy_rule(model):
    return sum(sum(model.I[t] * model.s[t, i] for t in model.S) for i in model.V)


# Restricao de tipo (apenas um t por posicao)
def const_typenum(model, i):
    return sum(model.s[t, i] for t in model.S) <= 1


# Restricao de quantidade minima (LB) e maxima (UB) de alocacao
def const_numalloc(model):
    return (
        max(2, ceil(0.05 * model.n)),
        sum(sum(model.s[t, i] for t in model.S) for i in model.V),
        model.n,
    )


####


def const_Pair1(model, t, u, i, j):
    return model.P[t, u, i, j] <= model.s[t, i]


def const_Pair2(model, t, u, i, j):
    return model.P[t, u, i, j] <= model.s[u, j]


def const_Pair3(model, t, u, i, j):
    return model.P[t, u, i, j] >= model.s[t, i] + model.s[u, j] - 1


###


# Determina que nao pode existir aresta de caminho saindo e voltando para mesmo no, ou quando j nao for vizinho de i
def const_aij(model, t, u, i, j):
    if i == j:
        return model.a[t, u, i, j] == 0
    else:
        if j not in model.N[t, i]:
            return model.a[t, u, i, j] == 0
        else:
            return Constraint.Skip


# Determina que somente existe possibilidade de aresta entre pares de nos ativos
def const_aP(model, t, u, i, j):
    return model.a[t, u, i, j] <= model.P[t, u, i, j]


# Determina que o numero total de arestas que saem de cada no i ativo eh 1
def const_a1(model, i):
    return sum(
        sum(sum(model.a[t, u, i, j] for j in model.N[t, i]) for u in model.S)
        for t in model.S
    ) == sum(model.s[t, i] for t in model.S)


# Determina que somente existe possibilidade de aresta entre um no i e o no 0 se o no i for ativo
def const_a0(model, t, u, i):
    return model.a[t, u, i, 0] <= model.s[t, i]


# Determina que o total de arestas que alcanca o no 0 eh sempre 1
def const_a00(model):
    return (
        sum(
            sum(sum(model.a[t, u, i, 0] for t in model.S) for u in model.S)
            for i in model.V
        )
        == 1
    )


# Define que se houver apenas o 0 como vizinho, i deve estar inativo
def const_sN(model, t, i):
    return model.s[t, i] <= len(model.N[t, i]) - 1


# Determina que o nivel do no i deve ser sempre maior que o nivel do no j quando i tem aresta ligando a j
def const_L1(model, t, u, i, j):
    if j in model.N[t, i]:
        return model.L[i] >= model.L[j] + model.a[t, u, i, j] - model.n * (
            1 - model.a[t, u, i, j]
        )
    else:
        return Constraint.Skip


def const_L2(model, i):
    return model.L[i] <= sum(model.s[t, i] for t in model.S) * model.n - (
        1 - sum(model.s[t, i] for t in model.S)
    )


# Determina que o nivel do no 0 (sorvedouro) eh sempre igual a 0
def const_L0(model):
    return model.L[0] == 1


# Determina que um ponto da parametrizacao esta coberto apenas se existe sensor alocado cujo raio de alcance cobre o ponto
def const_C1(model, j, k, t, i):
    if model.DK[i, j, k] <= model.RMAX[t]:
        return model.c[j, k, i, t] == model.s[t, i]
    else:
        return model.c[j, k, i, t] == 0


# Restringe sobreposição
def const_C2(model, k, l):
    return model.cc[k, l] <= 1


def const_C3(model, k, l):
    return model.cc[k, l] <= sum(
        sum(model.c[k, l, i, t] for i in model.V) for t in model.S
    )


def const_C4(model, k, l):
    return model.cc[k, l] >= 1 - M * model.ccY[k, l, 1]


def const_C5(model, k, l):
    return (
        model.cc[k, l]
        >= sum(sum(model.c[k, l, i, t] for i in model.V) for t in model.S)
        - M * model.ccY[k, l, 2]
    )


def const_C6(model, k, l):
    return model.ccY[k, l, 1] + model.ccY[k, l, 2] <= 1


### OUTRAS FOs NA FORMA DE RESTRICAO

def const_obj_C1(model):
    return model.FO_C == sum(sum(model.cc[k, l] for k in model.KW) for l in model.KH)

def const_obj_C(model):
    return model.FO_C >= model.epsC

def const_obj_M(model, epsM):
    return (
        sum(sum(model.MC[t] * model.s[t, i] for t in model.S) for i in model.V) <= epsM
    )


# Funcao principal para gerar instancia do modelo
def generate_model(epsC):
    ## Cria modelo abstrato do pyomo
    model = AbstractModel()

    ## Parametros (Params)
    ## ---
    # Dimensoes da regiao de monitoramento
    model.dimW = Param(within=NonNegativeIntegers)
    model.dimH = Param(within=NonNegativeIntegers)
    # Numero de nos
    model.n = Param(within=NonNegativeIntegers)  # INICIALIZAR
    # Escala
    model.scale = Param(within=NonNegativeReals)  # INICIALIZAR

    ## Conjuntos (Sets)
    ## ---
    # Conjunto de pontos parametrizados na regiao de monitoramento
    model.KW = RangeSet(1, model.dimW)
    model.KH = RangeSet(1, model.dimH)
    # Conjunto de nos
    model.V = RangeSet(1, model.n)
    # Conjunto de nos incluindo 0
    model.V0 = RangeSet(0, model.n)
    # Conjunto de modelos/tipos de transceptor
    model.S = Set(initialize=["S2C", "S2CPro"], doc="Modelos")
    # Conjunto unitario (constante)
    model.UNIT = RangeSet(0, 0)

    ## Constantes do problema (demais parametros)

    # Coordenadas x dos nos
    model.X = Param(model.V)  # INICIALIZAR
    # Coordenadas y dos nos
    model.Y = Param(model.V)  # INICIALIZAR
    # Conjuntos de pontos parametrizados na superficie
    model.W = Param(model.KW, domain=NonNegativeReals)  # INICIALIZAR
    model.H = Param(model.KH, domain=NonNegativeReals)  # INICIALIZAR
    # Conjunto de corrente consumida media (I)
    model.I = Param(model.S)  # INICIALIZAR
    # Conjunto de custo medio em dolar (M)
    model.MC = Param(model.S)  # INICIALIZAR
    # Conjunto de raio maximo de alcance (Rmax)
    model.RMAX = Param(model.S)  # INICIALIZAR
    # Distancia entre pares de posicoes fixas (D)
    model.D = Param(model.V, model.V, initialize=init_D, domain=NonNegativeReals)
    # Distancia entre posicoes de nos sensores e pontos parametrizados na regiao de monitoramento (DK)
    model.DK = Param(
        model.V, model.KW, model.KH, initialize=init_DK, domain=NonNegativeReals
    )

    # Vizinhanca dos nos (i.e. os nos que sao vizinhos de i)
    model.N = Set(model.S, model.V, initialize=init_N)

    # Variaveis de decisao
    # ---
    # Estado das posicoes de alocacao (1 = alocado, 0 = nao alocado)
    model.s = Var(model.S, model.V, within=Binary)

    # Variavel de linearizacao que indica se para um par de nos, ambos sao ativos
    model.P = Var(model.S, model.S, model.V, model.V, within=Binary)

    # Indica se aresta esta presente no caminho entre nos ficticios 0 e n+1
    model.a = Var(model.S, model.S, model.V, model.V0, within=Binary)

    # Nivel do no sensor
    model.L = Var(model.V0, within=Integers)

    # Ponto da regiao de monitoramento coberto por ao menos um no sensor
    model.c = Var(model.KW, model.KH, model.V, model.S, within=Binary)

    # Pontos da região de monitoramento (se coberto ou nao, independente do no sensor)
    model.cc = Var(model.KW, model.KH, within=Binary)

    # Variavel que equivale a FO de cobertura, na forma de restricao
    model.FO_C = Var(within=NonNegativeIntegers)

    # Variaveis auxiliares de min
    model.ccY = Var(model.KW, model.KH, RangeSet(1, 2), within=Binary)

    # Epsilons para restricoes de objetivo
    model.epsC = Param(initialize=epsC, within=NonNegativeReals)
    # model.epsM = Param(domain=NonNegativeReals)

    ## Funcoes objetivo
    ## ---

    # FO Principal - Consumo de Energia
    model.E = Objective(rule=obj_Energy_rule, sense=minimize)
    model.E.activate()

    # Restricoes
    # ---

    # Restricao de tipo (apenas um t por posicao)
    model.typenum = Constraint(model.V, rule=const_typenum)

    # Restricao de quantidade minima (LB) e maxima (UB) de alocacao
    model.numalloc = Constraint(rule=const_numalloc)

    # Restricao que limita as solucoes. Posicoes de alocacao mais afastadas sempre receberao nos com maior alcance, o que torna a execucao mais rapida.
    # model.sN = Constraint(model.S, model.V, rule=const_sN)

    model.P1 = Constraint(model.S, model.S, model.V, model.V, rule=const_Pair1)
    model.P2 = Constraint(model.S, model.S, model.V, model.V, rule=const_Pair2)
    model.P3 = Constraint(model.S, model.S, model.V, model.V, rule=const_Pair3)

    model.aij = Constraint(model.S, model.S, model.V, model.V, rule=const_aij)

    model.aP = Constraint(model.S, model.S, model.V, model.V, rule=const_aP)
    model.a1 = Constraint(model.V, rule=const_a1)
    model.a0 = Constraint(model.S, model.S, model.V, rule=const_a0)
    model.a00 = Constraint(rule=const_a00)

    model.L1 = Constraint(model.S, model.S, model.V, model.V0, rule=const_L1)
    model.L2 = Constraint(model.V, rule=const_L2)
    model.L0 = Constraint(rule=const_L0)

    model.C1 = Constraint(model.KW, model.KH, model.S, model.V, rule=const_C1)
    model.C2 = Constraint(model.KW, model.KH, rule=const_C2)
    model.C3 = Constraint(model.KW, model.KH, rule=const_C3)
    model.C4 = Constraint(model.KW, model.KH, rule=const_C4)
    model.C5 = Constraint(model.KW, model.KH, rule=const_C5)
    model.C6 = Constraint(model.KW, model.KH, rule=const_C6)

    model.objC = Constraint(rule=const_obj_C)
    model.objC1 = Constraint(rule=const_obj_C1)
    # model.objM = Constraint(model.epsM, rule=const_obj_M)

    return model


# Preprocessamento do C_max para encontrar maximo epsilon
def preproc_C_max(model):
    x = [[0 for _ in model.KW] for _ in model.KH]

    for i in model.V:
        for j in model.KW:
            for k in model.KH:
                if value(model.DK[i, j, k]) <= value(model.RMAX["S2CPro"]):
                    x[j - 1][k - 1] = 1

    sum_x = 0

    for j in model.KW:
        for k in model.KH:
            sum_x += x[j - 1][k - 1]

    return sum_x
