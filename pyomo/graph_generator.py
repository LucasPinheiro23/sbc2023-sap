from matplotlib.ticker import (AutoMinorLocator)
import matplotlib.pyplot as plt
import scipy.interpolate as sp
import numpy as np
import logging
import sys
import os

os.chdir("./pyomo")

#Input data
L = 15 #10,15,20,25
d = 5 #1-9
instance_filename = (
            "SAP-inst_" + str(L) + "x" + str(L) + "_d0." + str(d) + ".dat"
        )
sol_I = [-1.835346,-1.835346,-2.285346,-2.285346,2.5912365063432072,-2.735346,-2.735346,-3.185346,-3.185346,-3.635346,-3.941237,-4.391237,-4.8412370000000005,-5.453019]
sol_C = [21.0,30.0,54.0,64.0,75.99999399029315,90.0,105.0,138.0,135.0,151.0,167.0,182.0,195.0,210.0]
sol_eps = [15,30,45,60,75,90,105,120,135,150,165,180,195,210]
sol_gap = [0.0,0.0,0.0,0.0,11.49,0.0,0.0,0.0,0.0,0.0,0.08,0.0,0.0,0.0]

sys.stdout = open("./output/logs/" + str(L) + "x" + str(L) + "/d0." + str(d) + "/" + instance_filename[:-4] + "_objfunccomp.txt","w")

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
    ax.plot(sol_C_feas, sol_I_feas, "r*", alpha=0.5)

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