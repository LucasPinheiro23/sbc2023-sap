# from sap_sbc_abstract_model import *
from efficient_sap_sbc_abstract_model import *
from pyomo.environ import *
from pyomo.common import timing
from matplotlib.ticker import AutoMinorLocator
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import scipy.interpolate as sp
import numpy as np
import logging
import os
import time
import sys

#Constante que determina o percentual minimo da cobertura maxima a ser alcancado. Condicao de parada.
stop_perc = 0.9

# Zera o tempo decorrido total
tt0 = time.time()

# Lista de solucoes da FO E
sol_E_opt = []
# Lista de solucoes da FO C
sol_C_opt = []
# Lista de epsilons
sol_eps_opt = []

# Lista de solucoes da FO E
sol_E_feas = []
# Lista de solucoes da FO C
sol_C_feas = []
# Lista de epsilons
sol_eps_feas = []

# Muda diretorio (BUG DO VSCODE)
# os.chdir("./pyomo")

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

for L in range(10, 30, 5):
    for d in range(1, 10):
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
        ttt0 = time.time()
        eps_MAX = preproc_C_max(instance1)
        ttt = time.time() - ttt0

        #Reduz o epsilon maximo a 90% da cobertura maxima
        eps_MAX = floor(stop_perc * eps_MAX)

        eps_step = floor(eps_MAX/10)

        eps_MIN = eps_step

        #Inicializa variavel de execucao adicional para o ultimo epsilon
        # ad_run = False

        #Executa o solver para variados epsilon, comecando do maximo. Quando encontra muita variacao na FO, para a execucao.
        eps = eps_MIN
        
        while eps <= eps_MAX:
        # for eps in range(eps_MIN, eps_MAX, eps_step):
            
            #Se esta na run adicional, epsilon atual deve ser o epsilon maximo. Programa encerramento atualizando o valor de epsilon maximo original.
            # if(ad_run):
            #     eps_MAX = eps_bkp
            #     eps = eps_MAX

            # #Se o proximo passo ultrapassar o maximo, precisa de uma nova execucao para eps_MAX
            # if((eps + eps_step > eps_MAX) and eps != eps_MAX):
            #     eps_bkp = eps_MAX
            #     eps_MAX = eps_MAX*1000
            #     ad_run = True

            # Zera o tempo decorrido no epsilon
            t0 = time.time()

            # Nome do arquivo da instancia a ser resolvida

            instance_eps = "_eps" + str(eps)

            # Define nome da figura a salvar
            figname = instance_filename[9:-4] + instance_eps

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
            opt.options["tmlim"] = 36000
            # opt.options["tmlim"] = 120
            opt.options["mipgap"] = 0.01

            print("Translating instance to solver...\n")
            # Resolve a instancia e armazena os resultados em um arquivo JSON
            results = opt.solve(instance, tee=True)

            instance.solutions.store_to(results)
            results.problem.name = instance_filename
            results.write(filename="./output/logs/" + str(L) + "x" + str(L) + "/d0." + str(d) + "/" + figname + "-results.json", format="json")

            if (results.solver.termination_condition == TerminationCondition.noSolution or results.solver.termination_condition == TerminationCondition.infeasibleOrUnbounded):
                print("\n\nNO SOLUTION FOUND FOR THIS EPSILON!\n\n")
                continue

            # Pega resultados diretamente
            print("\nResults:\n")

            # Resultado da funcao objetivo de Energia
            E_now = value(instance.E)
            print("E = " + str(E_now) + " mA")

            # Resultado da variavel de decisao da Cobertura
            C_now = value(instance.objC)
            print("C = " + str(C_now) + " points")
            print("C ~= " + str((C_now/4)*1.6) + " km^2")

            #Dados do epsilon
            print("\nMinimum Epsilon for this instance = " + str(eps_MIN))
            print("Maximum Epsilon for this instance = " + str(eps_MAX))
            print("Current Epsilon = " + str(eps))
            print("\nInstance Maximum Epsilon Preprocessing Time: " + str(ttt) + " s")

            # Tempo de execucao total (incluido tempo de traducao do modelo do pyomo para o solver)
            print("\nTime in solver (for this epsilon): " + str(results.solver.time) + " s")
            
            t = time.time() - t0
            print("Elapsed time (for this epsilon): " + str(t) + " s")

            tt = time.time() - tt0
            print("\n\nTotal elapsed time since execution of first epsilon: " + str(tt) + " s")

            #Se acabou o tempo limite, verifica se obteve solucao. Se sim, armazena.
            if((results.solver.status == TerminationCondition.maxTimeLimit)):
                if((results.solver.status == SolverStatus.ok) and (results.solver.termination_condition == TerminationCondition.feasible)):
                    sol_E_feas.append(E_now)
                    sol_C_feas.append(C_now)
                    sol_eps_feas.append(eps)
            #Verifica se encontrou solucao com gap limite definido.
            elif((results.solver.status == SolverStatus.ok) and (results.solver.termination_condition == TerminationCondition.feasible)):
                sol_E_opt.append(E_now)
                sol_C_opt.append(C_now)
                sol_eps_opt.append(eps)
            elif((results.solver.status == SolverStatus.ok) and (results.solver.termination_condition == TerminationCondition.optimal)):
                sol_E_opt.append(E_now)
                sol_C_opt.append(C_now)
                sol_eps_opt.append(eps)
            

            sys.stdout.close()

            # -----------------------------------------------------------#

            ## POS-PROCESSAMENTO
            ## -----------------

            # Plota todos os espacos disponiveis para alocacao como circulos nao-preenchidos pretos
            # Se estiver alocado, preenche o circulo e colore de acordo com modelo de transceptor ativo

            fig = plt.figure("SAP Result")
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

            ax.legend(handles=[red_patch, blue_patch, green_patch], loc="upper right", prop={'size':6})

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

            eps_END = eps

            eps = eps + eps_step

        sys.stdout = open("./output/logs/" + str(L) + "x" + str(L) + "/d0." + str(d) + "/" + instance_filename[:-4] + "_pareto.txt","w")
        # sys.stdout = sys.__stdout__
        
        try:
            # Plotando a fronteira de pareto
            print("Started to plot Pareto Frontier...\n")

            fig = plt.figure("Pareto Frontier")
            ax = fig.add_subplot(1, 1, 1)
            ax.grid(linestyle="--", linewidth=0.5, alpha=0.5)
            ax.grid(which = "minor")
            ax.minorticks_on()

            ###Fronteira de Pareto

            f = sp.interp1d(sol_C_opt,sol_E_opt)#kind='cubic')

            # xnew = np.arange(new_sol_E[0],new_sol_E[-1],0.1)
            xnew = np.arange(sol_C_opt[0],sol_C_opt[-1],0.1)
            ynew = f(xnew)
            # ax.plot(sol_E, sol_C, "y*", xnew, ynew, "b--")
            
            ax.plot(sol_C_opt, sol_E_opt, "r*")
            ax.plot(xnew, ynew, "r--", alpha = 0.2)

            ###Solucoes dominadas

            # f = sp.interp1d(sol_C_feas,sol_E_feas)#kind='cubic')

            # xnew = np.arange(new_sol_E[0],new_sol_E[-1],0.1)
            # xnew = np.arange(sol_C_feas[0],sol_C_feas[-1],0.1)
            # ynew = f(xnew)

            ax.plot(sol_C_feas, sol_E_feas, "b*")
            # ax.plot(xnew, ynew, "b--", alpha = 0.2)

            # eps_range = np.arange(eps_MIN,eps_END+eps_step,eps_step)
                
            # ax.set_xticks(sol_C)
            # ax.set_yticks(sol_E)

            # plt.xlabel("E (mA)")
            plt.xlabel("C (points)")
            # plt.ylabel("C (points)")
            plt.ylabel("E (mA)")

            red_patch = mpatches.Patch(color="red", label="Non-dominated Solution")
            blue_patch = mpatches.Patch(color="blue", label="Dominated Solution")

            ax.legend(handles=[red_patch, blue_patch], loc="upper left", prop={'size':6})

            ax.xaxis.set_minor_locator(AutoMinorLocator())
            ax.yaxis.set_minor_locator(AutoMinorLocator())

            #Clona eixo y
            # ax2 = ax.twinx()

            #Configura eixo secundario
            # ax2.plot(sol_C,np.arange(eps_MIN,eps_END+eps_step,eps_step), alpha=0)
            # ax2.set_yticks(np.arange(eps_MIN,eps_END+eps_step,eps_step))
            # ax2.get_xaxis().set_visible(False)
            # ax2.set_ylabel("$\\epsilon$ (points)")
            # ax2.yaxis.label.set_color('blue')
            # ax2.tick_params(axis='y', colors='blue')

            # ax2.yaxis.set_minor_locator(AutoMinorLocator())
            
            plt.savefig("./output/" + str(L) + "x" + str(L) + "/d0." + str(d) + "/" + instance_filename[:-4] +"_pareto.svg")
            print("Pareto plot successful!")
            plt.clf()
            plt.close()

        except:
            logging.exception("AN ERROR OCCURRED WHILE PLOTTING PARETO!")
            sys.stdout.close()
