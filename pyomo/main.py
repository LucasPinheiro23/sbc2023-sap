# from sap_sbc_abstract_model import *
from efficient_sap_sbc_abstract_model import *
from pyomo.environ import *
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import scipy.interpolate as sp
import numpy as np
import logging
import os
import time
import sys

#Constante que determina variacao toleravel no valor da FO durante a variacao dos epsilon. Determina o encerramento da execucao
# T = 5

# Zera o tempo decorrido total
tt0 = time.time()

# Lista de solucoes da FO E
sol_E = []
# Lista de solucoes da FO C
sol_C = []
# Lista de epsilons
sol_eps = []
# Lista de tempo de solucao
sol_time = []

# Muda diretorio (BUG DO VSCODE)
os.chdir("./pyomo")

# Script principal para resolver instancias do SAP

# Suprime logs de warning do Pyomo (necessario pois gera muitas warnings durante alteracoes do modelo para calcular min-max)
logging.getLogger("pyomo.core").setLevel(logging.ERROR)

# Solver a ser utilizado
# solver = 'cplex'
solver = "glpk"
# Executavel do solver
# solver_exec = 'cplex'
solver_exec = "glpsol"
# Caminho das instancias

for L in range(10, 15, 5):
    for d in range(1, 2):
        instance_path = "./instances_OL2A_updated/" + str(L) + "x" + str(L) + "/"
        instance_filename = (
            "SAP-inst_" + str(L) + "x" + str(L) + "_d0." + str(d) + ".dat"
        )

        ## Gera modelo abstrato inicial com qualquer epsilon (indiferente)
        model = generate_model(0)

        ## Carrega dados de instancia no modelo
        data = DataPortal()
        data.load(filename=instance_path + instance_filename, model=model)
        instance1 = model.create_instance(data)

        #Calcula o epsilon maximo para a respectiva FO
        eps_MAX = preproc_C_max(instance1)

        eps_MIN = 0

        eps_step = floor(eps_MAX/10)

        #Inicializa variavel de execucao adicional para o ultimo epsilon
        ad_run = False

        #Executa o solver para variados epsilon, comecando do maximo. Quando encontra muita variacao na FO, para a execucao.
        for eps in range(eps_MIN, eps_MAX, eps_step):
            
            #Se o proximo passo ultrapassar o maximo, precisa de uma nova execucao para eps_MAX
            if(eps + eps_step > eps_MAX):
                ad_run = True

            # Zera o tempo decorrido no epsilon
            t0 = time.time()

            # Nome do arquivo da instancia a ser resolvida

            instance_eps = "_eps" + str(eps)

            # Define nome da figura a salvar
            figname = instance_filename[:-3] + instance_eps

            # Nome do arquivo de log
            sys.stdout = open("./output/logs/" + str(L) + "x" + str(L) + "/d0." + str(d) + "/" + figname + ".txt","w")

            ## CONSTRUCAO DO MODELO E INSTANCIA

            ## Gera modelo abstrato com epsilon correspondente
            model = generate_model(eps)

            ## Carrega dados de instancia no modelo
            data = DataPortal()
            data.load(filename=instance_path + instance_filename, model=model)
            instance = model.create_instance(data)

            # instance.epsC.pprint()
            # instance.objC.pprint()
            # continue
            # -----------------------------------------------------------#

            ## SOLVER
            ## ------

            # Cria um solver
            opt = SolverFactory(solver, executable=solver_exec)
            # opt.options["tmlim"] = 1200
            opt.options["mipgap"] = 0.0001

            print("Translating instance to solver...\n")
            # Resolve a instancia e armazena os resultados em um arquivo JSON
            results = opt.solve(instance)  # , tee=True)
            instance.solutions.store_to(results)
            results.problem.name = instance_filename
            results.write(filename="results.json", format="json")

            if results.solver.termination_condition == "maxTimeLimit":
                print("\n\nSOLVER TIME LIMIT EXCEEDED\n\n")
                if math.isinf(results.problem.lower_bound) or math.isinf(
                    results.problem.upper_bound
                ):
                    print("\n\nNO SOLUTION FOUND FOR THIS INSTANCE!\n\n")
                    continue

            # Pega resultados diretamente
            print("\nResults:\n")

            # PEGAR RESULTADOS:
            # VALOR DA FO DE ENERGIA
            # VALOR DA RESTRICAO DE COBERTURA (FO DE COBERTURA)
            # TEMPO DE EXECUCAO (DO SOLVER)
            # GAP DE OTIMALIDADE
            #
            # Funcao objetivo de Energia (valor otimo)
            E_now = value(instance.E)
            sol_E.append(E_now)
            print("E = " + str(E_now) + "mA")

            # Variavel de decisao da Cobertura (valor otimo)
            C_now = value(instance.objC)
            sol_C.append(C_now)
            print("C = " + str(C_now) + "points")
            print("C ~= " + str((C_now/4)*1.6) + "km^2")

            # Valor de epsilon utilizado nessa execucao
            sol_eps.append(eps)
            print("Minimum Epsilon for this instance = " + str(eps_MIN))
            print("Maximum Epsilon for this instance = " + str(eps_MAX))
            print("Current Epsilon = " + str(eps))

            sol_time.append(results.solver.time)
            # Tempo de execucao total (incluido tempo de traducao do modelo do pyomo para o solver)
            print("Time in solver (for this epsilon): " + str(results.solver.time) + " s")
            
            t = time.time() - t0
            print("Elapsed time (for this epsilon): " + str(t))

            tt = time.time() - tt0
            print("\n\nTotal elapsed time since execution of first epsilon: " + str(tt))

            # -----------------------------------------------------------#

            ## POS-PROCESSAMENTO
            ## -----------------

            # Plota todos os espacos disponiveis para alocacao como circulos nao-preenchidos pretos
            # Se estiver alocado, preenche o circulo e colore de acordo com modelo de transceptor ativo

            fig = plt.figure("SAP Optimal Result")
            ax = fig.add_subplot(1, 1, 1)
            ax.axis("equal")

            for i in instance.V:

                plt.text(
                    (instance.X[i]-1 + 0.1)*instance.scale,
                    (instance.Y[i]-1 + 0.1)*instance.scale,
                    str(i),
                    color="k",
                    fontsize=10,
                )

                if value(instance.s["S2C", i]) == 1:
                    ax.plot((instance.X[i]-1)*instance.scale, (instance.Y[i]-1)*instance.scale, "go")
                    ax.add_patch(
                        plt.Circle(
                            ((instance.X[i]-1)*instance.scale, (instance.Y[i]-1)*instance.scale),
                            (instance.RMAX["S2C"]),
                            color="g",
                            alpha=0.1,
                        )
                    )
                elif value(instance.s["S2CPro", i]) == 1:
                    ax.plot((instance.X[i]-1)*instance.scale, (instance.Y[i]-1)*instance.scale, "bo")
                    ax.add_patch(
                        plt.Circle(
                            ((instance.X[i]-1)*instance.scale, (instance.Y[i]-1)*instance.scale),
                            (instance.RMAX["S2CPro"]),
                            color="b",
                            alpha=0.1,
                        )
                    )
                elif value(instance.s["S3", i]) == 1:
                    ax.plot((instance.X[i]-1)*instance.scale, (instance.Y[i]-1)*instance.scale, "ro")
                    ax.add_patch(
                        plt.Circle(
                            ((instance.X[i]-1)*instance.scale, (instance.Y[i]-1)*instance.scale),
                            (instance.RMAX["S3"]),
                            color="r",
                            alpha=0.1,
                        )
                    )
                else:
                    ax.plot((instance.X[i]-1)*instance.scale, (instance.Y[i]-1)*instance.scale, "ko", fillstyle="none")

            ax.grid(linestyle="--", linewidth=0.5, alpha=0.5)

            ax.set_xticks(np.arange(0,instance.W[value(instance.dimW)]*value(instance.scale)+value(instance.scale),step=value(instance.scale)))
            ax.set_yticks(np.arange(0,instance.H[value(instance.dimH)]*value(instance.scale)+value(instance.scale),step=value(instance.scale)))

            red_patch = mpatches.Patch(color="red", label="S3Pro")
            blue_patch = mpatches.Patch(color="blue", label="S2CPro")
            green_patch = mpatches.Patch(color="green", label="S2C")

            ax.legend(handles=[red_patch, blue_patch, green_patch], loc="upper right")

            plt.plot(
                [instance.W[1]*value(instance.scale), instance.W[value(instance.dimW)]*value(instance.scale)],
                [instance.H[1]*value(instance.scale), instance.H[1]*value(instance.scale)],
                color="k",
            )
            plt.plot(
                [instance.W[value(instance.dimW)]*value(instance.scale), instance.W[value(instance.dimW)]*value(instance.scale)],
                [instance.H[1]*value(instance.scale), instance.H[value(instance.dimH)]*value(instance.scale)],
                color="k",
            )
            plt.plot(
                [instance.W[1]*value(instance.scale), instance.W[1]*value(instance.scale)],
                [instance.H[1]*value(instance.scale), instance.H[value(instance.dimH)]*value(instance.scale)],
                color="k",
            )
            plt.plot(
                [instance.W[1]*value(instance.scale), instance.W[value(instance.dimW)]*value(instance.scale)],
                [instance.H[value(instance.dimH)]*value(instance.scale), instance.H[value(instance.dimH)]*value(instance.scale)],
                color="k",
            )

            for i in instance.KW:
                for j in instance.KH:
                    if value(instance.cc[i, j]):
                        plt.plot(
                            instance.W[i]*value(instance.scale),
                            instance.H[j]*value(instance.scale),
                            marker="x",
                            color="r",
                            alpha=0.3,
                        )
                    else:
                        plt.plot(
                            instance.W[i]*value(instance.scale),
                            instance.H[j]*value(instance.scale),
                            marker="x",
                            color="k",
                            alpha=0.3,
                        )

            plt.xlabel("X Coordinates (km)")
            plt.ylabel("Y Coordinates (km)")
            # plt.title('Instance: '+str(instance_filename)+'\nScale: 1:'+str(int(instance.scale))+'m\nAlphas: '+str(alpha['E'])+'E, '+str(alpha['C'])+'C, '+str(alpha['M'])+'M  -  Time: '+str(results.solver.user_time)+' s')
            # plt.show()
            plt.savefig("./output/" + str(L) + "x" + str(L) + "/d0." + str(d) + "/" + figname +".svg")
            plt.close()

            ###Condicao de parada!
            # if(eps != eps_MIN):
                
            #     #Se o valor atual de E eh maior ou igual a um percentual T determinado do E original (minimo), entao encerra a execucao
            #     if(E_now >= T*E0):
                    
            #         print("HALTED BY EPSILON")
            #         exit(1)
            # else:
            #     E0 = E_now

            sys.stdout.close()
    
    #Executa rodada adicional apenas para o ultimo epsilon, caso ja nao tenha sido considerado
    if(ad_run):

        eps = eps_MAX

        # Zera o tempo decorrido no epsilon
        t0 = time.time()

        # Nome do arquivo da instancia a ser resolvida

        instance_eps = "_eps" + str(eps)

        # Define nome da figura a salvar
        figname = instance_filename[:-4] + instance_eps

        # Nome do arquivo de log
        sys.stdout = open("./output/logs/" + str(L) + "x" + str(L) + "/d0." + str(d) + "/" + figname + ".txt","w")

        ## CONSTRUCAO DO MODELO E INSTANCIA

        ## Gera modelo abstrato com epsilon correspondente
        model = generate_model(eps)

        ## Carrega dados de instancia no modelo
        data = DataPortal()
        data.load(filename=instance_path + instance_filename, model=model)
        instance = model.create_instance(data)

        # instance.epsC.pprint()
        # instance.objC.pprint()
        # continue
        # -----------------------------------------------------------#

        ## SOLVER
        ## ------

        # Cria um solver
        opt = SolverFactory(solver, executable=solver_exec)
        # opt.options["tmlim"] = 1200
        opt.options["mipgap"] = 0.0001

        print("Translating instance to solver...\n")
        # Resolve a instancia e armazena os resultados em um arquivo JSON
        results = opt.solve(instance)  # , tee=True)
        instance.solutions.store_to(results)
        results.problem.name = instance_filename
        results.write(filename="results.json", format="json")

        if results.solver.termination_condition == "maxTimeLimit":
            print("\n\nSOLVER TIME LIMIT EXCEEDED\n\n")
            if math.isinf(results.problem.lower_bound) or math.isinf(
                results.problem.upper_bound
            ):
                print("\n\nNO SOLUTION FOUND FOR THIS INSTANCE!\n\n")
                continue

        # Pega resultados diretamente
        print("\nResults:\n")

        # PEGAR RESULTADOS:
        # VALOR DA FO DE ENERGIA
        # VALOR DA RESTRICAO DE COBERTURA (FO DE COBERTURA)
        # TEMPO DE EXECUCAO (DO SOLVER)
        # GAP DE OTIMALIDADE
        #
        # Funcao objetivo de Energia (valor otimo)
        E_now = value(instance.E)
        sol_E.append(E_now)
        print("E = " + str(E_now) + "mA")

        # Variavel de decisao da Cobertura (valor otimo)
        C_now = value(instance.objC)
        sol_C.append(C_now)
        print("C = " + str(C_now) + "points")
        print("C ~= " + str((C_now/4)*1.6) + "km^2")

        # Valor de epsilon utilizado nessa execucao
        sol_eps.append(eps)
        print("Minimum Epsilon for this instance = " + str(eps_MIN))
        print("Maximum Epsilon for this instance = " + str(eps_MAX))
        print("Current Epsilon = " + str(eps))

        sol_time.append(results.solver.time)
        # Tempo de execucao total (incluido tempo de traducao do modelo do pyomo para o solver)
        print("Time in solver (for this epsilon): " + str(results.solver.time) + " s")
        
        t = time.time() - t0
        print("Elapsed time (for this epsilon): " + str(t))

        tt = time.time() - tt0
        print("\n\nTotal elapsed time since execution of first epsilon: " + str(tt))

        # -----------------------------------------------------------#

        ## POS-PROCESSAMENTO
        ## -----------------

        # Plota todos os espacos disponiveis para alocacao como circulos nao-preenchidos pretos
        # Se estiver alocado, preenche o circulo e colore de acordo com modelo de transceptor ativo

        fig = plt.figure("SAP Optimal Result")
        ax = fig.add_subplot(1, 1, 1)
        ax.axis("equal")

        for i in instance.V:
            plt.text(
                (instance.X[i]-1 + 0.1)*instance.scale,
                (instance.Y[i]-1 + 0.1)*instance.scale,
                str(i),
                color="k",
                fontsize=10,
            )

            if value(instance.s["S2C", i]) == 1:
                ax.plot((instance.X[i]-1)*instance.scale, (instance.Y[i]-1)*instance.scale, "go")
                ax.add_patch(
                    plt.Circle(
                        ((instance.X[i]-1)*instance.scale, (instance.Y[i]-1)*instance.scale),
                        (instance.RMAX["S2C"]),
                        color="g",
                        alpha=0.1,
                    )
                )
            elif value(instance.s["S2CPro", i]) == 1:
                ax.plot((instance.X[i]-1)*instance.scale, (instance.Y[i]-1)*instance.scale, "bo")
                ax.add_patch(
                    plt.Circle(
                        ((instance.X[i]-1)*instance.scale, (instance.Y[i]-1)*instance.scale),
                        (instance.RMAX["S2CPro"]),
                        color="b",
                        alpha=0.1,
                    )
                )
            elif value(instance.s["S3", i]) == 1:
                ax.plot((instance.X[i]-1)*instance.scale, (instance.Y[i]-1)*instance.scale, "ro")
                ax.add_patch(
                    plt.Circle(
                        ((instance.X[i]-1)*instance.scale, (instance.Y[i]-1)*instance.scale),
                        (instance.RMAX["S3"]),
                        color="r",
                        alpha=0.1,
                    )
                )
            else:
                ax.plot((instance.X[i]-1)*instance.scale, (instance.Y[i]-1)*instance.scale, "ko", fillstyle="none")

        ax.grid(linestyle="--", linewidth=0.5, alpha=0.5)
        ax.set_xticks(np.arange(instance.W[1]*instance.scale,instance.W[instance.dimW]*instance.scale))
        ax.set_yticks(np.arange(instance.H[1]*instance.scale,instance.H[instance.dimH]*instance.scale))

        red_patch = mpatches.Patch(color="red", label="S3Pro")
        blue_patch = mpatches.Patch(color="blue", label="S2CPro")
        green_patch = mpatches.Patch(color="green", label="S2C")

        ax.legend(handles=[red_patch, blue_patch, green_patch], loc="upper right")

        plt.plot(
            [instance.W[1]*instance.scale, instance.W[instance.dimW]*instance.scale],
            [instance.H[1]*instance.scale, instance.H[1]*instance.scale],
            color="k",
        )
        plt.plot(
            [instance.W[instance.dimW]*instance.scale, instance.W[instance.dimW]*instance.scale],
            [instance.H[1]*instance.scale, instance.H[instance.dimH]*instance.scale],
            color="k",
        )
        plt.plot(
            [instance.W[1]*instance.scale, instance.W[1]*instance.scale],
            [instance.H[1]*instance.scale, instance.H[instance.dimH]*instance.scale],
            color="k",
        )
        plt.plot(
            [instance.W[1]*instance.scale, instance.W[instance.dimW]*instance.scale],
            [instance.H[instance.dimH]*instance.scale, instance.H[instance.dimH]*instance.scale],
            color="k",
        )

        # for i in instance.KW:
        #     for j in instance.KH:
        #         if value(instance.cc[i, j]):
        #             plt.plot(
        #                 instance.W[i],
        #                 instance.H[j],
        #                 marker="x",
        #                 color="r",
        #                 alpha=0.3,
        #             )
        #         else:
        #             plt.plot(
        #                 instance.W[i],
        #                 instance.H[j],
        #                 marker="x",
        #                 color="k",
        #                 alpha=0.3,
        #             )

        plt.xlabel("X Coordinates (km)")
        plt.ylabel("Y Coordinates (km)")
        # plt.title('Instance: '+str(instance_filename)+'\nScale: 1:'+str(int(instance.scale))+'m\nAlphas: '+str(alpha['E'])+'E, '+str(alpha['C'])+'C, '+str(alpha['M'])+'M  -  Time: '+str(results.solver.user_time)+' s')
        # plt.show()
        plt.savefig("./output/" + str(L) + "x" + str(L) + "/d0." + str(d) + "/" + figname +".svg")
        plt.close()

        ###Condicao de parada!
        # if(eps != eps_MIN):
            
        #     #Se o valor atual de E eh maior ou igual a um percentual T determinado do E original (minimo), entao encerra a execucao
        #     if(E_now >= T*E0):
                
        #         print("HALTED BY EPSILON")
        #         exit(1)
        # else:
        #     E0 = E_now

        sys.stdout.close()

    sys.stdout = open("./output/logs/" + str(L) + "x" + str(L) + "/d0." + str(d) + "/" + instance_filename[:-4] + "_pareto.txt","w")
    # sys.stdout = sys.__stdout__
    
    try:
        # Plotando a fronteira de pareto
        # print("Checking if x is strictly increasing sequence...")

        # print("\nBefore (E): " + str(sol_E))
        # print("\nBefore (C): " + str(sol_C))

        # x1 = 0
        # x2 = 1

        # new_sol_E = sol_E
        # new_sol_C = sol_C

        # print("\n")

        # for x in range(0,len(sol_E)-3):
            
        #     # print("\nX1: "+ str(sol_E[x1]))
        #     # print("\nX2: "+ str(sol_E[x2]))

        #     if sol_E[x1] == sol_E[x2]:
        #         del new_sol_E[x1]
        #         del new_sol_C[x1]
            
        #     x1 += 1
        #     x2 += 1
            
        # print("\nAfter (E): " + str(new_sol_E))
        # print("\nAfter (C): " + str(new_sol_C))

        print("Started to plot Pareto Frontier...\n")

        fig = plt.figure("Pareto Frontier")
        ax = fig.add_subplot(1, 1, 1)
        ax.grid(linestyle="--", linewidth=0.5, alpha=0.5)
        # ax.set_xticks(np.arange(int(instance.smallest_X),int(instance.biggest_X)+1,1))
        # ax.set_yticks(np.arange(int(instance.smallest_Y),int(instance.biggest_Y)+1,1))

        # f = sp.interp1d(new_sol_E,new_sol_C,kind='cubic')
        f = sp.interp1d(sol_C,sol_E)#kind='cubic')

        # xnew = np.arange(new_sol_E[0],new_sol_E[-1],0.1)
        xnew = np.arange(sol_C[0],sol_C[-1],0.1)
        ynew = f(xnew)
        # ax.plot(sol_E, sol_C, "y*", xnew, ynew, "b--")
        ax.plot(sol_C, sol_E, "y*", xnew, ynew, "b--")

        # plt.xlabel("E (mA)")
        plt.xlabel("C (points)")
        # plt.ylabel("C (points)")
        plt.ylabel("E (mA)")
        
        plt.savefig("./output/" + str(L) + "x" + str(L) + "/d0." + str(d) + "/" + instance_filename[:-4] +"_pareto.svg")
        print("Pareto plot successful!")
        plt.close()
    except:
        logging.exception("AN ERROR OCCURRED WHILE PLOTTING PARETO!")
        sys.stdout.close()
