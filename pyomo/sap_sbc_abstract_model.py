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
            if(model.D[i,j] <= model.RMAX[t] and model.D[i,j] >= 0.8*model.RMAX[t]):
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
    return (max(2,ceil(0.50*model.n)),sum( sum( model.s[t,i] for t in model.S) for i in model.V),model.n)

##Componente de restricao de vizinhanca. Neig == 1 se existe pelo menos um vizinho para dado no. Neig == 0 caso nenhum vizinho.
def const_Neig1(model, t, i):
    return sum( sum( model.s[u,j] for u in model.S) for j in model.N[t,i]) - 1 <= model.n * model.d1[t,i]

def const_Neig2(model, t, i):
    return 1 - sum( sum( model.s[u,j] for u in model.S) for j in model.N[t,i]) <= model.n * (1 - model.d1[t,i])

def const_Neig3(model, t, i):
    return model.Neig[t,i] <= 1

def const_Neig4(model, t, i):
    return model.Neig[t,i] <= sum( sum( model.s[u,j] for u in model.S) for j in model.N[t,i])

def const_Neig5(model, t, i):
    return model.Neig[t,i] >= 1 - (model.n * (1 - model.d1[t,i]))

def const_Neig6(model, t, i):
    return model.Neig[t,i] >= sum( sum( model.s[u,j] for u in model.S) for j in model.N[t,i]) - model.n * model.d1[t,i]

# def const_Pair1(model, t, u, i ,j):
#     return model.Pair[t,u,i,j] == (3*model.s[t,i] + 2*model.s[u,j])/5

def const_Pair1(model, t, u, i, j):
    if j in model.N[t,i]:
            return model.Pair[t,i,j] == ((3*model.s[t,i] + 2*model.s[u,j])/5)
    else:
        return Constraint.Skip

def const_Pair2(model, t, i, j):
    if j in model.N[t,i]:
            return model.Pair_floor[t,i,j] <= model.Pair[t,i,j]
    else:
        return Constraint.Skip
    
def const_Pair3(model, t, i, j):
    if j in model.N[t,i]:
        return model.Pair[t,i,j] + 0.5 <= model.Pair_floor[t,i,j] + 1
    else:
        return Constraint.Skip

def const_Pair4(model):
    return sum( sum( sum( model.Pair_floor[t,i,j] for j in model.N[t,i]) for t in model.S) for i in model.V) >= 1


#Define que o no fonte deve estar ativo
def const_source_act(model):
    return sum( model.s[t,value(model.V0)] for t in model.S) == 1

#--------

#Define fluxo de saida do no fonte v0, individualmente para cada vizinho j
def const_source_fout1(model, j, t):
    if j in model.N[t,value(model.V0)]:
        return model.f[value(model.V0),j] <= model.n * model.Pair_floor[t,value(model.V0),j]
    else:
        return Constraint.Skip

def const_source_fout2(model, j, t):
    if j in model.N[t,value(model.V0)]:
        return model.f[value(model.V0),j] >= sum( model.Pair_floor[t,u,value(model.V0),j] for u in model.S)

def const_source_fout3(model):
    return sum( sum( model.f[value(model.V0),j] for j in model.N[t,value(model.V0)]) for t in model.S) >= sum( model.Pair_floor[t,u,value(model.V0),j] for u in model.S)

#Define fluxo de saida do no fonte, especificando que J deve ser vizinho ativo
def const_source_fout2(model):
    return sum( sum( sum(model.f[value(model.V0),j] for j in model.N[t,value(model.V0)]) for t in model.S) for u in model.S) >= model.n * sum(sum(sum( model.Pair_floor[t,u,value(model.V0),j] for j in model.N[t,value(model.V0)]) for t in model.S) for u in model.S)


#Define fluxo de entrada do no fonte (ESPECIFICAR QUE K DEVE SER VIZINHO ATIVO!!!!)
def const_source_fin(model):
    return sum( sum( model.f[k,value(model.V0)] for k in model.N[t,value(model.V0)]) for t in model.S) == 1

#Fluxo que passa por um no diferente da fonte eh sempre consumido em uma unidade
#DEFINIR QUE AMBOS OS PARES DEVEM ESTAR ATIVOS!!!
def const_flow_consume(model):
    return sum( sum( sum( sum( (model.f[i,j] - model.f[k,i]) for k in model.N[t,i]) for j in model.N[t,i]) for i in (model.V-{value(model.V0)})) for t in model.S) + 1 == 0

#DEFINIR QUE AMBOS OS PARES DEVEM ESTAR ATIVOS!!!
#Fluxo de saida deve ser maior que 1 e menor que (n-1) para todo no intermediario
def const_fout_bounds(model):
    return (1, sum( sum( sum( model.f[i,j] for j in model.N[t,i]) for i in model.V-{value(model.V0)}) for t in model.S), (model.n-1))

#DEFINIR QUE AMBOS OS PARES DEVEM ESTAR ATIVOS!!!
#Fluxo de entrada deve ser maior que 2 para todo no intermediario
def const_fin_bounds(model):
    return sum( sum( sum( model.f[k,i] for k in model.N[t,i]) for i in model.V-{value(model.V0)}) for t in model.S) >= 2


# def const_Dist(model):
#     return sum( sum( sum( sum( (model.D[i,j] * model.Pair_floor[t,u,i,j]) for t in model.S) for u in model.S) for i in model.V) for j in model.V)/((model.n-1) * model.n) <= model.DMED
    
# Restricao de vizinhanca (nao deve haver nenhum no sem vizinhos)
def const_OR(model, t, i):
    return (2*model.s[t,i] + (1 - model.Neig[t,i])) <= 2


# def const_OR(model):
    # return (0,sum( sum( (1 - model.s[t,i]) * (1 - min(1,model.Neig[t,i])) for t in model.S) for i in model.V),0)
    # return (0, sum( sum( (1 - sum( sum( minl(1,model.s[u,j]) for u in model.S) for j in model.N[t,i])) for t in model.S) for i in model.V),0)
    # return (0, sum( sum( minl(model.s[t,i], (1 - model.Neig[t,i])) for t in model.S) for i in model.V),0)

# Funcao principal para gerar instancia do modelo
def generate_model():

    ## Cria modelo abstrato do pyomo
    model = AbstractModel()

    ## Parametros (Params)
    ## ---
    # Numero de nos
    model.n = Param(within=NonNegativeIntegers) #INICIALIZAR
    # Largura do terreno
    #model.W = Param(within=NonNegativeIntegers) #INICIALIZAR
    # Altura do terreno
    #model.H = Param(within=NonNegativeIntegers) #INICIALIZAR
    # Menores coordenadas (X,Y)
    # model.smallest_X = Param(within=Integers, initialize = 0) #INICIALIZAR
    # model.smallest_Y = Param(within=Integers, initialize = 0) #INICIALIZAR
    # Maiores coordenadas (X,Y)
    # model.biggest_X = Param(within=Integers, initialize = model.n) #INICIALIZAR
    # model.biggest_Y = Param(within=Integers, initialize = model.n) #INICIALIZAR
    # Escala
    model.scale = Param(within=NonNegativeIntegers) #INICIALIZAR

    ## Conjuntos (Sets)
    ## ---
    # Conjunto de nos
    model.V = RangeSet(1,model.n)
    # Conjunto de arestas
    #model.A = Set(model.V,model.V,doc="Arestas",within=Binary)
    # Conjunto de modelos/tipos de transceptor
    model.S = Set(initialize=["S2C","S2CPro","S3"],doc="Modelos")

    ## Constantes do problema (demais parametros)

    # Coordenadas x dos nos
    model.X = Param(model.V) #INICIALIZAR
    # Coordenadas y dos nos
    model.Y = Param(model.V) #INICIALIZAR
    # Indice do no v0 (fonte da rede)
    model.V0 = Param() #INICIALIZAR
    # Conjunto de corrente consumida media (I)
    model.I = Param(model.S) #INICIALIZAR
    # Conjunto de custo medio em dolar (M)
    model.MC = Param(model.S) #INICIALIZAR
    # Conjunto de raio maximo de alcance (Rmax)
    model.RMAX = Param(model.S) #INICIALIZAR
    # Distancia entre pares de posicoes fixas (D)
    model.D = Param(model.V,model.V,initialize=init_D,domain=NonNegativeReals)
    # model.DMED = Param()

    # Vizinhanca dos nos
    model.N = Set(model.S,model.V,initialize=init_N)

    # Variaveis de decisao
    # ---
    #Estado das posicoes de alocacao (1 = alocado, 0 = nao alocado)
    model.s = Var(model.S, model.V, within=Binary)
    #Variaveis de controle das restricoes com min(x,y). (1 => x < y, 0 => x > y)
    model.d1 = Var(model.S, model.V, within=Binary)
    # model.d2 = Var(within=Binary)
    #Variaveis componentes de restricao
    model.Neig = Var(model.S, model.V, within=NonNegativeIntegers)
    #model.OR = Var(within=Binary)
    
    #Variavel que indica se em um par de nos vizinhos, ambos sao ativos
    model.Pair = Var(model.S, model.V, model.V, within=NonNegativeReals)
    model.Pair_floor = Var(model.S, model.V, model.V, within=NonNegativeIntegers)

    #Variavel que representa o indice do no fonte da rede
    # model.v0 = Var(bounds = (0,model.n), within=model.V)
    #Fluxo de cada no (origem,destino)
    model.f = Var(model.V, model.V, within=NonNegativeIntegers)



    ## Funcoes objetivo
    ## ---

    # # FO - Maximizar Neig
    # model.max_Neig = Objective(rule=obj_max_Neig,sense=maximize)
    # # FO - Maximizar OR
    # model.max_OR = Objective(rule=obj_max_OR,sense=maximize)

    # FO - Consumo de Energia
    model.E = Objective(rule=obj_Energy_rule,sense=minimize)
    # FO - Area de Cobertura
    model.C = Objective(rule=obj_Coverage_rule,sense=maximize)
    # FO - Custo Monetario
    model.M = Objective(rule=obj_Monetary_rule,sense=minimize)

    model.E.deactivate()
    model.C.deactivate()
    model.M.deactivate()

    ## Expressoes
    ## ---

    # Computa a quantidade de vizinhos para cada no i de tipo t
    # model.Neig = Param(model.S, model.V, initialize=init_Neig)

    # Restricoes
    # ---

    #Restricao de tipo (apenas um t por posicao)
    model.typenum = Constraint(model.V, rule=const_typenum)

    # #Restricao de quantidade minima (LB) e maxima (UB) de alocacao
    model.numalloc = Constraint(rule=const_numalloc)

    # Restricoes de vizinhanca (nao deve haver nenhum no sem vizinhos)
    # model.Neig1 = Constraint(model.S, model.V, rule=const_Neig1)
    # model.Neig2 = Constraint(model.S, model.V, rule=const_Neig2)
    # model.Neig3 = Constraint(model.S, model.V, rule=const_Neig3)
    # model.Neig4 = Constraint(model.S, model.V, rule=const_Neig4)
    # model.Neig5 = Constraint(model.S, model.V, rule=const_Neig5)
    # model.Neig6 = Constraint(model.S, model.V, rule=const_Neig6)
    
    # model.OR = Constraint(model.S, model.V, rule=const_OR)

    model.Pair1 = Constraint(model.S, model.S, model.V, model.V, rule=const_Pair1)
    model.Pair2 = Constraint(model.S, model.V, model.V, rule=const_Pair2)
    model.Pair3 = Constraint(model.S, model.V, model.V, rule=const_Pair3)
    model.Pair4 = Constraint(rule=const_Pair4)

    model.Flow1 = Constraint(rule=const_source_act)
    model.Flow2_1 = Constraint(rule=const_source_fout1)
    model.Flow2_2 = Constraint(rule=const_source_fout2)
    model.Flow3 = Constraint(rule=const_source_fin)
    model.Flow4 = Constraint(rule=const_flow_consume)
    model.Flow5 = Constraint(rule=const_fout_bounds)
    model.Flow6 = Constraint(rule=const_fin_bounds)

    # model.Dist = Constraint(rule=const_Dist)

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