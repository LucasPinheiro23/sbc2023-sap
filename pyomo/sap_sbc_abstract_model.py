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
    return (max(2,ceil(0.05*model.n)),sum( sum( model.s[t,i] for t in model.S) for i in model.V),model.n)

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
    model.smallest_X = Param(within=Integers, initialize = 0) #INICIALIZAR
    model.smallest_Y = Param(within=Integers, initialize = 0) #INICIALIZAR
    # Maiores coordenadas (X,Y)
    model.biggest_X = Param(within=Integers, initialize = model.n) #INICIALIZAR
    model.biggest_Y = Param(within=Integers, initialize = model.n) #INICIALIZAR
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
    #Estado das posicoes de alocacao (1 = alocado, 0 = nao alocado)
    model.s = Var(model.S, model.V, within=Binary)
    #Variaveis de controle das restricoes com min(x,y). (1 => x < y, 0 => x > y)
    model.d1 = Var(model.S, model.V, within=Binary)
    # model.d2 = Var(within=Binary)
    #Variaveis componentes de restricao
    model.Neig = Var(model.S, model.V, within=NonNegativeIntegers)
    #model.OR = Var(within=Binary)

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
    model.Neig1 = Constraint(model.S, model.V, rule=const_Neig1)
    model.Neig2 = Constraint(model.S, model.V, rule=const_Neig2)
    model.Neig3 = Constraint(model.S, model.V, rule=const_Neig3)
    model.Neig4 = Constraint(model.S, model.V, rule=const_Neig4)
    model.Neig5 = Constraint(model.S, model.V, rule=const_Neig5)
    model.Neig6 = Constraint(model.S, model.V, rule=const_Neig6)
    
    model.OR = Constraint(model.S, model.V, rule=const_OR)

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