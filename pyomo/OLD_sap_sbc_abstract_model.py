from pyomo.environ import *
from itertools import chain, combinations
from collections import defaultdict
import math

#Constantes
# BIG = -100000
# SMALL = 100000

### MODELAGEM ABSTRATA
#--------------------#

#Variavel global: subconjuntos de V
# subsets = []
subsets = {}

#Funcoes de inicializacao do modelo

#Subconjuntos do conjunto de nos (V), exceto vazio e conjuntos com um único elemento.
def init_V2(model, i):
    global subsets
    subs = []

    if i == 1:
        for j in model.V-{1}:
            for subset in combinations(model.V,j):
                subs.append(list(subset))
        subsets = dict(enumerate(subs, start=1))

    # print(subsets)

    for j in subsets[i]:
        yield j

# def init_V2(model, i):
#     global subsets

#     if i == 1:
#         for j in model.V-{1}:
#             for subset in combinations(model.V,j):
#                 # subsets[j] = []
#                 subsets[j] += list(subset)

#     print(subsets)

#     for k in subsets[i]:
#         yield k

# Distancia entre pares de posicoes fixas (D)
def init_D(model, i, j):
    return math.sqrt(pow((model.X[i]-model.X[j])*model.scale,2)+pow((model.Y[i]-model.Y[j])*model.scale,2))

# Vizinhanca dos nos (somente considerado vizinho se entre 80% e 100% do alcance maximo, de forma a garantir afastamento minimo)
def init_N(model, t, i):
    for j in model.V:
        if i != j:
            if(model.D[i,j] <= model.RMAX[t]):# and model.D[i,j] >= 0.8*model.RMAX[t]):
                yield j
    yield model.n + 1

# Anti-vizinhanca dos nos (nos cujo vizinho eh i)
def init_N2(model, j):
    for t in model.S:
        for i in model.V:
            if i != j:
                for k in model.N[t,i]:
                    if j == k:
                        yield i
    yield 0

# FO - Consumo de Energia
def obj_Energy_rule(model):
    return sum(sum(model.I[t]*model.s[t,i] for t in model.S) for i in model.V)

# FO - Area de Cobertura
def obj_Coverage_rule(model):
    return sum(sum(math.pi*pow(model.RMAX[t],2)*model.s[t,i] for t in model.S) for i in model.V)

    #Melhor resultado ate o momento
    # return sum(sum(sum( model.s[t,i] * model.D[i,j] for j in model.N[t,i]-{(model.n+1)}) for t in model.S) for i in model.V)
    # return sum(sum(sum(sum( model.P[t,u,i,j] * model.D[i,j] for j in model.V) for t in model.S) for u in model.S) for i in model.V)
    # return sum(sum(sum(sum( model.P[t,u,i,j] * model.D[i,j] * model.RMAX[t] * model.RMAX[u] for j in model.N[t,i]-{(model.n+1)}) for t in model.S) for u in model.S) for i in model.V)
    # return sum(sum(sum(sum( model.P[t,u,i,j] * model.D[i,j] for j in model.V) for t in model.S) for u in model.S) for i in model.V)

# FO - Custo Monetario
def obj_Monetary_rule(model):
    return sum(sum(model.MC[t]*model.s[t,i] for t in model.S) for i in model.V)

# FO E normalizada por min-max
def obj_norm_E(model):
    return model.exp_norm_E

# FO C normalizada por min-max
def obj_norm_C(model):
    return model.exp_norm_C

# FO M normalizada por min-max
def obj_norm_M(model):
    return model.exp_norm_M

# FO - Metodo das ponderacoes
def obj_WEIGHTED(model):
    return model.weig

# Restricao de tipo (apenas um t por posicao)
def const_typenum(model, i):
    return (0,sum( model.s[t,i] for t in model.S),1)

# Restricao de quantidade minima (LB) e maxima (UB) de alocacao
def const_numalloc(model):
    return (max(2,ceil(0.05*model.n)),sum( sum( model.s[t,i] for t in model.S) for i in model.V),model.n)

####

def const_Pair1(model, t, u, i, j):
    return model.P[t,u,i,j] <= model.s[t,i]

def const_Pair2(model, t, u, i, j):
    # if j in model.N[t,i]:
        return model.P[t,u,i,j] <= model.s[u,j]
    # else:
        # return Constraint.Skip

def const_Pair3(model, t, u, i, j):
    # if j in model.N[t,i]:
        return model.P[t,u,i,j] >= model.s[t,i] + model.s[u,j] - 1
    # else:
        # return Constraint.Skip

#Se nenhum tiver vizinho, da erro aqui. Restricao força que exista ao menos 1 par ativo na rede
def const_Pair4(model):
    return sum( sum( sum( sum( model.P[t,u,i,j] for j in model.N[t,i]-{(model.n+1)}) for t in model.S) for u in model.S) for i in model.V) >= 1

#Restrição exige que todo no so seja ativo se tiver vizinho ativo
# def const_Pair5(model, t, i):
    # return sum( sum( model.P[t,u,i,j] for j in model.N[t,i]-{(model.n+1)}) for u in model.S) >= model.s[t,i]

###

#Restricoes A0

def const_A0_1(model, j):
    return model.A0[j] <= model.a[0,j]

def const_A0_2(model, j):
    return model.A0[j] <= sum( model.s[t,j] for t in model.S)

def const_A0_3(model, j):
    return model.A0[j] >= model.a[0,j] + sum( model.s[t,j] for t in model.S) - 1

def const_A0_4(model):
    return sum( model.A0[j] for j in model.V) == 1

#Restricoes A_(n+1)

def const_An1_1(model, k):
    return model.An1[k] <= model.a[k,(model.n+1)]

def const_An1_2(model, k):
    return model.An1[k] <= sum( model.s[t,k] for t in model.S)

def const_An1_3(model, k):
    return model.An1[k] >= model.a[k,(model.n+1)] + sum( model.s[t,k] for t in model.S) - 1

def const_An1_4(model):
    return sum( model.An1[k] for k in model.V) == 1

### Restricoes 0-n1, repeat e back

def const_a0n1(model):
    return model.a[0,(model.n+1)] == 0

def const_no_repeat(model, i):
    return 2*model.A0[i] + model.An1[i] <= 2

def const_no_back(model, i, j):
    return sum ( sum ( 2*model.AP[t,u,i,j] + model.AP[u,t,j,i] for u in model.S) for t in model.S) <= 2

def const_AP0(model, j):
    return sum( sum( model.AP[t,u,0,j] for t in model.S) for u in model.S) == model.A0[j]

def const_APn1(model, k):
    return sum( sum( model.AP[t,u,k,(model.n+1)] for t in model.S) for u in model.S) == model.An1[k]

def const_AP0n1(model):
    return sum( sum( model.AP[t,u,0,(model.n+1)] for t in model.S) for u in model.S) == model.a[0,(model.n+1)]

###

def const_aij(model, i, j):
    for t in model.S:
        vart = 0
        if j not in model.N[t,i]:
            vart+=1
    if vart == len(model.S):
        return model.a[i,j] == 0
    else:
        return Constraint.Skip

def const_AP1(model, t, u, i, j):
    return model.AP[t,u,i,j] <= model.a[i,j]

def const_AP2(model, t, u, i, j):
    return model.AP[t,u,i,j] <= model.P[t,u,i,j]

def const_AP3(model, t, u, i, j):
    return model.AP[t,u,i,j] >= model.a[i,j] + model.P[t,u,i,j] - 1

#Se tiver algum no sem vizinho, da erro aqui:
def const_AP4(model, t, i):
    return sum( sum( model.AP[t,u,i,j] for j in model.N[t,i]) for u in model.S) - sum( sum( model.AP[v,t,k,i] for k in model.N2[i]) for v in model.S) == 0

def const_AP5(model):
    return sum( sum( sum( sum( model.AP[t,u,i,j] for j in model.N[t,i]-{(model.n+1)}) for t in model.S) for u in model.S) for i in model.V) == sum( sum( model.s[t,i] for t in model.S) for i in model.V) - 1
    # return sum( sum( sum( model.a[i,j] for j in model.N[t,i]-{(model.n+1)}) for t in model.S) for i in model.V) == sum( sum( model.s[t,i] for t in model.S) for i in model.V) - 1

def const_MST(model, k):
    return sum( sum( sum( sum( model.AP[t,u,i,j] for j in model.V2[k]) for t in model.S) for u in model.S) for i in model.V2[k]) <= model.MAX_0_V2[k]

def const_MST_max1(model, k):
    return (sum( sum( model.s[t,i] for t in model.S) for i in model.V2[k]) - 1) <= len(model.V) * model.d[k]

def const_MST_max2(model, k):
    return -(sum( sum( model.s[t,i] for t in model.S) for i in model.V2[k]) - 1) <= len(model.V) * (1-model.d[k])

def const_MST_max3(model, k):
    return model.MAX_0_V2[k] >= 0

def const_MST_max4(model, k):
    return model.MAX_0_V2[k] >= (sum( sum( model.s[t,i] for t in model.S) for i in model.V2[k]) - 1)

def const_MST_max5(model, k):
    return model.MAX_0_V2[k] <= (sum( sum( model.s[t,i] for t in model.S) for i in model.V2[k]) - 1) + len(model.V) * (1-model.d[k])

def const_MST_max6(model, k):
    return model.MAX_0_V2[k] <= len(model.V) * model.d[k]

# Funcao principal para gerar instancia do modelo
def generate_model():

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
    # Subconjuntos de nos
    model.V2_s = RangeSet(1,(pow(2,model.n))-model.n-1)
    model.V2 = Set(model.V2_s, initialize=init_V2)
    # Conjunto de nos incluindo nos ficticios 0 e n+1
    model.Va = RangeSet(0,(model.n+1))
    model.VaX0 = RangeSet(1,(model.n+1))
    model.VaXn1 = RangeSet(0,model.n)
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

    # Vizinhanca dos nos (i.e. os nos que sao vizinhos de i)
    model.N = Set(model.S,model.V,initialize=init_N)
    # "Anti-vizinhanca" dos nos (i.e. os nos que tem i como vizinho)
    model.N2 = Set(model.V,initialize=init_N2)

    # Variaveis de decisao
    # ---
    #Estado das posicoes de alocacao (1 = alocado, 0 = nao alocado)
    model.s = Var(model.S, model.V, within=Binary)
    
    #Variavel de linearizacao que indica se em um par de nos (vizinhos?), ambos sao ativos
    model.P = Var(model.S, model.S, model.V, model.V, within=Binary)

    #Indica se aresta esta presente no caminho entre nos ficticios 0 e n+1
    model.a = Var(model.VaXn1, model.VaX0, within=Binary)

    #Variavel de controle (para max na restricao MST)
    model.d = Var(model.V2_s, within=Binary)

    #Variavel de max (para restricao MST)
    model.MAX_0_V2 = Var(model.V2_s, within=NonNegativeIntegers)

    model.A0 = Var(model.V, within=Binary)
    model.An1 = Var(model.V, within=Binary)

    #Variavel de linearizacao que indica se aresta esta no caminho entre 0 e n+1 e ao mesmo tempo passa por um par de nos ativos/alocados
    model.AP = Var(model.S, model.S, model.VaXn1, model.VaX0, within=Binary)

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

    # Restricoes
    # ---

    #Restricao de tipo (apenas um t por posicao)
    model.typenum = Constraint(model.V, rule=const_typenum)

    # #Restricao de quantidade minima (LB) e maxima (UB) de alocacao
    model.numalloc = Constraint(rule=const_numalloc)

    model.P1 = Constraint(model.S, model.S, model.V, model.V, rule=const_Pair1)
    model.P2 = Constraint(model.S, model.S, model.V, model.V, rule=const_Pair2)
    model.P3 = Constraint(model.S, model.S, model.V, model.V, rule=const_Pair3)
    model.P4 = Constraint(rule=const_Pair4)
    # model.P5 = Constraint(model.S, model.V, rule=const_Pair5)

    #Restricoes de excecao
    model.a0n1 = Constraint(rule=const_a0n1) #Garante que a variavel a[0,(n+1)] seja igual a 0
    model.no_rpt = Constraint(model.V, rule=const_no_repeat)
    model.no_bck = Constraint(model.V, model.V, rule=const_no_back)
    
    model.AP0 = Constraint(model.V, rule=const_AP0)
    model.APn1 = Constraint(model.V, rule=const_APn1)
    model.AP0n1 = Constraint(rule=const_AP0n1)

    model.aij = Constraint(model.V,model.V, rule=const_aij)
    
    model.A0_1 = Constraint(model.V,rule=const_A0_1)
    model.A0_2 = Constraint(model.V,rule=const_A0_2)
    model.A0_3 = Constraint(model.V,rule=const_A0_3)
    model.A0_4 = Constraint(rule=const_A0_4)

    model.An1_1 = Constraint(model.V,rule=const_An1_1)
    model.An1_2 = Constraint(model.V,rule=const_An1_2)
    model.An1_3 = Constraint(model.V,rule=const_An1_3)
    model.An1_4 = Constraint(rule=const_An1_4)

    model.AP1 = Constraint(model.S, model.S, model.V, model.V, rule=const_AP1)
    model.AP2 = Constraint(model.S, model.S, model.V, model.V, rule=const_AP2)
    model.AP3 = Constraint(model.S, model.S, model.V, model.V, rule=const_AP3)
    model.AP4 = Constraint(model.S, model.V, rule=const_AP4)
    model.AP5 = Constraint(rule=const_AP5)

    model.MST = Constraint(model.V2_s,rule=const_MST)

    model.max_MST1 = Constraint(model.V2_s,rule=const_MST_max1)
    model.max_MST2 = Constraint(model.V2_s,rule=const_MST_max2)
    model.max_MST3 = Constraint(model.V2_s,rule=const_MST_max3)
    model.max_MST4 = Constraint(model.V2_s,rule=const_MST_max4)
    model.max_MST5 = Constraint(model.V2_s,rule=const_MST_max5)
    model.max_MST6 = Constraint(model.V2_s,rule=const_MST_max6)

    return model

#Funcao para coletar valor maximo da FO de uma instancia
def get_fo_max(model, fo, instance_filename,solver,solver_exec):

    #Inicializa resultados maximos
    max_fo = {'E':0,'C':0,'M':0}
    #Inicializa DataPortal
    data = DataPortal()
    #Inicializa solver
    opt = SolverFactory(solver, executable=solver_exec)


    #Maximiza todas as FOs
    model.E = Objective(rule=obj_Energy_rule,sense=maximize)
    model.C = Objective(rule=obj_Coverage_rule,sense=maximize)
    model.M = Objective(rule=obj_Monetary_rule,sense=maximize)

    #Desativa todas as FOs
    model.E.deactivate()
    model.C.deactivate()
    model.M.deactivate()

    if(fo['E'] == 1):
        ##Ativa apenas FO E
        model.E.activate()

        print("Criando instancia max-E...")
        ## Carrega dados de instancia no modelo
        data = DataPortal()
        data.load(filename=instance_filename, model=model)
        instance = model.create_instance(data)
        print("Instancia criada.")
        print("Resolvendo instancia...")
        ## Resolve para encontrar max

        #Resolve a instancia e pega resultado da FO
        results = opt.solve(instance)
        instance.solutions.store_to(results)

        if(results.solver.termination_condition == TerminationCondition.infeasible):
            print("ERRO: Nenhuma solucao encontrada para Max E.")
            exit(-1)

        max_fo['E'] = value(instance.E)

        #Desativa FO E
        model.E.deactivate()

    if(fo['C'] == 1):

        ##Ativa apenas FO C
        model.C.activate()

        print("Criando instancia max-C...")
        ## Carrega dados de instancia no modelo
        
        data.load(filename=instance_filename, model=model)
        instance = model.create_instance(data)

        print("Instancia criada.")
        print("Resolvendo instancia...")

        ## Resolve para encontrar max

        #Resolve a instancia e pega resultado da FO
        results = opt.solve(instance)
        instance.solutions.store_to(results)

        if(results.solver.termination_condition == TerminationCondition.infeasible):
            print("ERRO: Nenhuma solucao encontrada para Max C.")
            exit(-1)

        max_fo['C'] = value(instance.C)

        #Desativa FO C
        model.C.deactivate()

    if(fo['M'] == 1):
        ##Ativa apenas FO M
        model.M.activate()

        print("Criando instancia max-M...")
        ## Carrega dados de instancia no modelo
        data = DataPortal()
        data.load(filename=instance_filename, model=model)
        instance = model.create_instance(data)

        print("Instancia criada.")
        print("Resolvendo instancia...")

        ## Resolve para encontrar max

        #Resolve a instancia e pega resultado da FO
        results = opt.solve(instance)
        instance.solutions.store_to(results)

        if(results.solver.termination_condition == TerminationCondition.infeasible):
            print("ERRO: Nenhuma solucao encontrada para Max M.")
            exit(-1)

        max_fo['M'] = value(instance.M)

        #Desativa FO M
        model.M.deactivate()

    return max_fo

#Funcao para coletar valor minimo da FO de uma instancia
def get_fo_min(model, fo, instance_filename,solver,solver_exec):

    #Inicializa resultados maximos
    min_fo = {'E':0,'C':0,'M':0}
    #Inicializa DataPortal
    data = DataPortal()
    #Inicializa solver
    opt = SolverFactory(solver, executable=solver_exec)

    #Maximiza todas as FOs
    model.E = Objective(rule=obj_Energy_rule,sense=minimize)
    model.C = Objective(rule=obj_Coverage_rule,sense=minimize)
    model.M = Objective(rule=obj_Monetary_rule,sense=minimize)

    #Desativa todas as FOs
    model.E.deactivate()
    model.C.deactivate()
    model.M.deactivate()

    if(fo['E'] == 1):
        ##Ativa apenas FO E
        model.E.activate()

        print("Criando instancia min-E...")
        ## Carrega dados de instancia no modelo
        data = DataPortal()
        data.load(filename=instance_filename, model=model)
        instance = model.create_instance(data)

        print("Instancia criada.")
        print("Resolvendo instancia...")

        ## Resolve para encontrar max

        #Resolve a instancia e pega resultado da FO
        results = opt.solve(instance)
        instance.solutions.store_to(results)

        if(results.solver.termination_condition == TerminationCondition.infeasible):
            print("ERRO: Nenhuma solucao encontrada para Min E.")
            exit(-1)

        min_fo['E'] = value(instance.E)

        #Desativa FO E
        model.E.deactivate()

    if(fo['C'] == 1):
        ##Ativa apenas FO C
        model.C.activate()

        print("Criando instancia min-C...")
        ## Carrega dados de instancia no modelo
        
        data.load(filename=instance_filename, model=model)
        instance = model.create_instance(data)

        print("Instancia criada.")
        print("Resolvendo instancia...")

        ## Resolve para encontrar max

        #Resolve a instancia e pega resultado da FO
        results = opt.solve(instance)
        instance.solutions.store_to(results)

        if(results.solver.termination_condition == TerminationCondition.infeasible):
            print("ERRO: Nenhuma solucao encontrada para Min C.")
            exit(-1)

        min_fo['C'] = value(instance.C)

        #Desativa FO C
        model.C.deactivate()

    if(fo['M'] == 1):
        ##Ativa apenas FO M
        model.M.activate()

        print("Criando instancia min-M...")
        ## Carrega dados de instancia no modelo
        data = DataPortal()
        data.load(filename=instance_filename, model=model)
        instance = model.create_instance(data)

        print("Instancia criada.")
        print("Resolvendo instancia...")

        ## Resolve para encontrar max

        #Resolve a instancia e pega resultado da FO
        results = opt.solve(instance)
        instance.solutions.store_to(results)

        if(results.solver.termination_condition == TerminationCondition.infeasible):
            print("ERRO: Nenhuma solucao encontrada para Min M.")
            exit(-1)

        min_fo['M'] = value(instance.M)

        #Desativa FO M
        model.M.deactivate()

    return min_fo