# from sap_sbc_abstract_model import *
from efficient_sap_sbc_abstract_model import *
from pyomo.environ import *
from pyomo.common import timing
from matplotlib.ticker import (MultipleLocator, AutoMinorLocator)
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import scipy.interpolate as sp
import numpy as np
import logging
import os
import time
import sys
import re

#Constante que determina o percentual minimo de cobertura a ser alcancado. Condicao de parada.
# stop_perc = 0.98
stop_perc = 1

# Zera o tempo decorrido total
tt0 = time.time()

# Muda diretorio (BUG DO VSCODE)
# os.chdir("./pyomo")

# Script principal para resolver instancias do SAP

# Suprime logs de warning do Pyomo (necessario pois gera muitas warnings durante alteracoes do modelo para calcular min-max)
logging.getLogger("pyomo.core").setLevel(logging.ERROR)

# Solver a ser utilizado
# solver = 'cplex'
# solver = "glpk"
solver = "gurobi_direct"

# Executavel do solver
# solver_exec = 'cplex'
# solver_exec = "glpsol"

# Caminho das instancias

for L in range(20, 30, 5):
    for d in range(1, 6):

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

        eps_step = floor(eps_MAX/L)

        eps_MIN = eps_step

        #Inicializa variavel de execucao adicional para o ultimo epsilon
        # ad_run = False

        #Executa o solver para variados epsilon, comecando do minimo.
        eps = eps_MIN

        # Lista de solucoes da FO E
        sol_I = []
        # Lista de solucoes da FO C
        sol_C = []
        # Lista de epsilons
        sol_eps = []
        # Lista de gaps
        sol_gap = []

        while eps <= eps_MAX:

            # Checa se foi encontrada solucao
            no_sol = 0

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
            opt = SolverFactory(solver, manage_env=True) #, executable=solver_exec)
            opt.options["TimeLimit"] = 43200 #12h
            opt.options["mipgap"] = 0.001

            print("Translating instance to solver...\n")
            # Resolve a instancia e armazena os resultados em um arquivo JSON
            results = opt.solve(instance, tee=True)
            
            t = time.time() - t0
            tt = time.time() - tt0

            #instance.solutions.store_to(results)
            results.problem.name = instance_filename
            results.write(filename="./output/logs/" + str(L) + "x" + str(L) + "/d0." + str(d) + "/" + figname + "-results.json", format="json")

            #Se achou solucao, armazena.
            #if((results.solver.status == SolverStatus.ok) and ((results.solver.termination_condition == TerminationCondition.feasible) or (results.solver.termination_condition == TerminationCondition.optimal))):
            if(results.problem.number_of_solutions > 0):
                
                instance.solutions.store_to(results)
                with open("./output/logs/" + str(L) + "x" + str(L) + "/d0." + str(d) + "/" + figname + ".txt", 'rb') as fb:
                    try:  # catch OSError in case of a one line file 
                        fb.seek(-2, os.SEEK_END)
                        while fb.read(1) != b'\n':
                            fb.seek(-2, os.SEEK_CUR)
                    except OSError:
                        fb.seek(0)
                    line = fb.readline().decode()

                gap_split = line.find("%")
                #gap = line[gap_split-7:gap_split].replace(" ","")
                gap = float(re.sub("[<>=:$%!@ ()\/;,]","",line[gap_split-7:gap_split]))

                # Tempo de execucao total (incluido tempo de traducao do modelo do pyomo para o solver)
                print("----------\nSolver wallclock time (for this epsilon): " + str(results.solver.wallclock_time) + " s")
                print("Python wallclock time (for this epsilon): " + str(t) + " s")
                print("\nTotal elapsed Time (since program call): " + str(tt) + " s")

                # Pega resultados diretamente
                print("--------\nResults:\n")

                # Resultado da funcao objetivo de Energia
                if(results.solver.termination_condition == TerminationCondition.optimal):
                    E_now = (-1)*value(instance.E)
                    print("I = " + str((-1)*E_now) + " mA")
                else:
                    E_now = value(instance.E)
                    print("I = " + str(E_now) + " mA")

                # Resultado da variavel de decisao da Cobertura
                C_now = value(instance.objC)
                print("C = " + str(C_now) + " pts")
                # print("C ~= " + str((C_now/4)*1.6) + " km^2")

                #Dados do epsilon
                print("\nMinimum Epsilon for this instance = " + str(eps_MIN))
                print("Maximum Epsilon for this instance = " + str(eps_MAX))
                print("Current Epsilon = " + str(eps))
                # print("\n\nPreprocessing Time (for this epsilon): " + str(ttt) + " s")

                sol_I.append(E_now)
                sol_C.append(C_now)
                sol_eps.append(eps)
                sol_gap.append(round(gap,2))

                print("\nUpdated solution vectors (negative I is just optimal indicative):\nsol_I = [", end="")
                print(",".join(map(str, sol_I)), end="")
                print("]\nsol_C = [", end="")
                print(",".join(map(str, sol_C)), end="")
                print("]\nsol_eps = [", end="")
                print(",".join(map(str, sol_eps)), end="")
                print("]\nsol_gap = [", end="")
                print(",".join(map(str, sol_gap)), end="")
                print("]")
                
            else:
                # Tempo de execucao total (incluido tempo de traducao do modelo do pyomo para o solver)
                print("\nSolver Wallclock Time (for this epsilon): " + str(results.solver.wallclock_time) + " s")
                print("Python wallclock Time (for this epsilon): " + str(t) + " s")
                print("\n\nTotal Elapsed Time (since program call): " + str(tt) + " s")
                print("\n\nNO SOLUTION FOUND FOR THIS INSTANCE!")
                no_sol = 1

            sys.stdout.close()

            # -----------------------------------------------------------#

            ## POS-PROCESSAMENTO
            ## -----------------

            # Plota todos os espacos disponiveis para alocacao como circulos nao-preenchidos pretos
            # Se estiver alocado, preenche o circulo e colore de acordo com modelo de transceptor ativo

            if(no_sol == 0):
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
                    # elif value(instance.s["S3", i]) == 1:
                    #     ax.plot((instance.X[i]-1)*instance.scale, (instance.Y[i]-1)*instance.scale, "ro")
                    #     ax.add_patch(
                    #         plt.Circle(
                    #             ((instance.X[i]-1)*instance.scale, (instance.Y[i]-1)*instance.scale),
                    #             (instance.RMAX["S3"]),
                    #             color="r",
                    #             alpha=0.1,
                    #         )
                    #     )
                    else:
                        ax.plot((instance.X[i]-1)*instance.scale, (instance.Y[i]-1)*instance.scale, "ko", fillstyle="none")

                ax.grid(linestyle="--", which="minor", linewidth=0.5, alpha=0.5)
                ax.grid(linestyle="-", which="major", linewidth=0.5, alpha=0.5)
                ax.minorticks_on()
                ax.xaxis.set_minor_locator(MultipleLocator(value(instance.scale)))
                ax.yaxis.set_minor_locator(MultipleLocator(value(instance.scale)))

                ax.set_xticks(np.arange(0,instance.W[value(instance.dimW)]*value(instance.scale)+value(instance.scale),step=value(instance.scale*2)))
                ax.set_yticks(np.arange(0,instance.H[value(instance.dimH)]*value(instance.scale)+value(instance.scale),step=value(instance.scale*2)))


                # red_patch = mpatches.Patch(color="red", label="S3Pro")
                blue_patch = mpatches.Patch(color="blue", label="S2CPro")
                green_patch = mpatches.Patch(color="green", label="S2C")

                ax.legend(handles=[blue_patch, green_patch], loc="upper right", prop={'size':6})

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

                plt.xlabel("X (km)")
                plt.ylabel("Y (km)")
                # plt.title('Instance: '+str(instance_filename)+'\nScale: 1:'+str(int(instance.scale))+'m\nAlphas: '+str(alpha['E'])+'E, '+str(alpha['C'])+'C, '+str(alpha['M'])+'M  -  Time: '+str(results.solver.user_time)+' s')
                # plt.show()
                plt.savefig("./output/" + str(L) + "x" + str(L) + "/d0." + str(d) + "/" + figname +".svg")
                plt.close()
            
            eps_END = eps

            eps = eps + eps_step

        sys.stdout = open("./output/logs/" + str(L) + "x" + str(L) + "/d0." + str(d) + "/" + instance_filename[:-4] + "_objfunccomp.txt","w")
        # sys.stdout = sys.__stdout__
        
        if(len(sol_I) > 0 and len(sol_C) > 0 and len(sol_eps) > 0):
            try:

                sol_I_opt = []
                sol_C_opt = []
                eps_opt = []
                gap_opt = []

                sol_I_feas = []
                sol_C_feas = []
                eps_feas = []
                gap_feas = []

                for i in range(0,len(sol_I)):
                    if sol_I[i] < 0:
                        sol_I[i] = sol_I[i] * (-1)
                        sol_I_opt.append(sol_I[i])
                        sol_C_opt.append(sol_C[i])
                        eps_opt.append(sol_eps[i])
                        gap_opt.append(sol_gap[i])
                    else:
                        sol_I_feas.append(sol_I[i])
                        sol_C_feas.append(sol_C[i])
                        eps_feas.append(sol_eps[i])
                        gap_feas.append(sol_gap[i])

                # Plotando a fronteira de pareto
                print("Started plotting Objective Function Comparison Graph...\n")

                fig = plt.figure("Obj Function Comparison")
                ax = fig.add_subplot(1, 1, 1)
                ax.grid(linestyle="--", which="minor", linewidth=0.5, alpha=0.5)
                ax.grid(linestyle="-", which="major", linewidth=0.5, alpha=0.5)
                ax.minorticks_on()

                ### Resultados (valores subotimos)

                # f = sp.interp1d(sol_C,sol_E)#kind='cubic')

                # xnew = np.arange(new_sol_E[0],new_sol_E[-1],0.1)
                # xnew = np.arange(sol_C[0],sol_C[-1],0.1)
                # ynew = f(xnew)
                # ax.plot(sol_E, sol_C, "y*", xnew, ynew, "b--")
                
                ax.plot(sol_C_feas, sol_I_feas, "r*", alpha=0.5)
                # ax.plot(xnew, ynew, "b--", alpha = 0.2)

                ### Resultados (valores otimos)

                f = sp.interp1d(sol_C,sol_I)#kind='cubic')

                # xnew = np.arange(sol_I[0],sol_I[-1],0.1)
                xnew = np.arange(sol_C[0],sol_C[-1],0.1)
                ynew = f(xnew)
                ax.plot(xnew, ynew, "k:", alpha=0.3)
                
                ax.plot(sol_C_opt, sol_I_opt, "b*", alpha=0.5)
                # ax.plot(xnew, ynew, "r--", alpha = 0.2)

                ax.spines['top'].set_alpha(0.25)
                ax.spines['right'].set_alpha(0.25)
                ax.spines['bottom'].set_alpha(0.25)
                ax.spines['left'].set_alpha(0.25)

                # ax.spines['top'].set_visible(False)
                # ax.spines['right'].set_visible(False)
                # ax.spines['bottom'].set_visible(False)
                # ax.spines['left'].set_visible(False)

                offset = 0.10
                for i in range(0,len(sol_I_feas)):
                    if i == 0:
                        repeat = (-1)*offset
                    elif ((sol_C_feas[i] == sol_C_feas[i-1]) or (sol_C_feas[i] - sol_C_feas[i-1] <= 12)) and sol_I_feas[i] == sol_I_feas[i-1]:
                        repeat = repeat + offset
                    else:
                        repeat = 0
                    
                    plt.text(
                        sol_C_feas[i],
                        offset+sol_I_feas[i]+repeat,
                        # "$\epsilon$ |Gap(%)\n"+str(eps_feas[i])+"|"+str(gap_feas[i]),
                        str(eps_feas[i])+"|"+str(gap_feas[i])+"%",
                        color="k",
                        fontsize=6,
                        # weight="bold",
                        style="italic"
                    )

                for i in range(0,len(sol_I_opt)):
                    if i == 0:
                        repeat = 0
                    elif ((sol_C_opt[i] == sol_C_opt[i-1]) or (sol_C_opt[i] - sol_C_opt[i-1] <= 12)) and sol_I_opt[i] == sol_I_opt[i-1]:
                        repeat = repeat + offset
                    else:
                        repeat = 0
                    plt.text(
                        sol_C_opt[i],
                        offset+sol_I_opt[i]+repeat,
                        # "$\epsilon$  |Gap(%)\n"+str(eps_opt[i])+"|"+str(gap_opt[i]),
                        str(eps_opt[i]),
                        color="k",
                        fontsize=6,
                        # weight="bold",
                        style="italic"
                    )
                

                plt.xlabel("C (pts)")
                
                plt.ylabel("I (mA)")

                ax.xaxis.set_minor_locator(AutoMinorLocator())
                ax.yaxis.set_minor_locator(AutoMinorLocator())


                plt.savefig("./output/" + str(L) + "x" + str(L) + "/d0." + str(d) + "/" + instance_filename[:-4] +"_objfunccomp.svg")
                print("Objective Function Comparison plot successful!")
                plt.close()
                sys.stdout.close()

            except:
                logging.exception("AN ERROR OCCURRED WHILE PLOTTING OBJ FUNC COMP GRAPH!")
                sys.stdout.close()
        else:
            print("ERROR: NO SOLUTION VECTOR FOR THIS INSTANCE, CAN'T PLOT OBJ FUNC COMP GRAPH!")
            sys.stdout.close()
