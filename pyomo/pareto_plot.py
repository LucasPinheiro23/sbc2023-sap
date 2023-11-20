from matplotlib.ticker import AutoMinorLocator
import matplotlib.pyplot as plt
import scipy.interpolate as sp
import numpy as np
import logging
import os
import time
import sys

# Muda diretorio (BUG DO VSCODE)
os.chdir("./pyomo")

sol_E = [-0.611782,1.817673,-1.061782,-1.061782,-1.061782,2.735346,-1.511782,2.267673]
sol_C = [12.0,62.0,36.0,36.0,49.0,62.0,68.0,78.0]
sol_eps = [9,18,27,36,45,54,63,72]
sol_gap = [0.0,61.2,0.0,0.0,0.0,61.2,0.0,27.0]

L = 10

d = 1

if(len(sol_E) > 0 and len(sol_C) > 0 and len(sol_eps) > 0):
    try:

        sol_E_opt = []
        sol_C_opt = []

        sol_E_feas = []
        sol_C_feas = []

        for i in range(0,len(sol_E)):
            if sol_E[i] < 0:
                sol_E_opt.append(sol_E[i])
                sol_E[i] = sol_E[i] * (-1)
                sol_C_opt.append(sol_C[i])
            else:
                sol_E_feas.append(sol_E[i])
                sol_C_feas.append(sol_C[i])

        sol_E_opt = [i * (-1) for i in sol_E_opt]

        # Plotando a fronteira de pareto
        print("Started plotting Objective Function Comparison Graph...\n")

        fig = plt.figure("Obj Function Comparison")
        ax = fig.add_subplot(1, 1, 1)
        ax.grid(linestyle="--", linewidth=0.5, alpha=0.5)
        ax.grid(which = "minor")
        ax.minorticks_on()

        ### Resultados (valores subotimos)

        # f = sp.interp1d(sol_C,sol_E)#kind='cubic')

        # xnew = np.arange(new_sol_E[0],new_sol_E[-1],0.1)
        # xnew = np.arange(sol_C[0],sol_C[-1],0.1)
        # ynew = f(xnew)
        # ax.plot(sol_E, sol_C, "y*", xnew, ynew, "b--")
        
        ax.plot(sol_C, sol_E, "b*", alpha=0.5)
        # ax.plot(xnew, ynew, "b--", alpha = 0.2)

        ### Resultados (valores otimos)

        # f = sp.interp1d(sol_C_opt,sol_E_opt)#kind='cubic')

        # xnew = np.arange(new_sol_E[0],new_sol_E[-1],0.1)
        # xnew = np.arange(sol_C_opt[0],sol_C_opt[-1],0.1)
        # ynew = f(xnew)
        # ax.plot(sol_E, sol_C, "y*", xnew, ynew, "b--")
        
        ax.plot(sol_C_opt, sol_E_opt, "r*", alpha=0.5)
        # ax.plot(xnew, ynew, "r--", alpha = 0.2)


        plt.xlabel("C (points)")
        
        plt.ylabel("E (mA)")

        ax.xaxis.set_minor_locator(AutoMinorLocator())
        ax.yaxis.set_minor_locator(AutoMinorLocator())


        plt.savefig("./output/objfunccomp_single.svg")
        print("Objective Function Comparison plot successful!")
        plt.close()
        sys.stdout.close()

    except:
        logging.exception("AN ERROR OCCURRED WHILE PLOTTING OBJ FUNC COMP GRAPH!")
        sys.stdout.close()
else:
    print("ERROR: NO SOLUTION VECTOR FOR THIS INSTANCE, CAN'T PLOT OBJ FUNC COMP GRAPH!")
    sys.stdout.close()