# from sap_sbc_abstract_model import *
# from efficient_sap_sbc_abstract_model import *
# from pyomo.environ import *
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import scipy.interpolate as sp
import numpy as np
# import logging
import os
# import time
import sys

#sys.stdout = open("./output/logs/" + str(L) + "x" + str(L) + "/d0." + str(d) + "/" + instance_filename[:-3] + "-pareto.txt","w")
#sys.stdout = sys.__stdout__
    
# Plotando a fronteira de pareto
print("Checking if x is strictly increasing sequence...")

sol_E = [1,2,2,3,4,5,5,6]
sol_C = [10,20,30,40,50,60,70,80]

print("\nBefore (E): " + str(sol_E))
print("\nBefore (C): " + str(sol_C))

x1 = 0
x2 = 1

new_sol_E = sol_E
new_sol_C = sol_C

print("\n")

for x in range(0,len(sol_E)-3):
    
    print("\nX1: "+ str(sol_E[x1]))
    print("\nX2: "+ str(sol_E[x2]))

    if sol_E[x1] == sol_E[x2]:
        del new_sol_E[x1]
        del new_sol_C[x1]
    
    x1 += 1
    x2 += 1
        
print("\nAfter (E): " + str(new_sol_E))
print("\nAfter (C): " + str(new_sol_C))

print("Started to plot Pareton Frontier...\n")

fig = plt.figure("Pareto Frontier")
ax = fig.add_subplot(1, 1, 1)
ax.grid(linestyle="--", linewidth=0.5, alpha=0.5)
# ax.set_xticks(np.arange(int(instance.smallest_X),int(instance.biggest_X)+1,1))
# ax.set_yticks(np.arange(int(instance.smallest_Y),int(instance.biggest_Y)+1,1))

# f = sp.interp1d(sol_E,sol_C,kind='cubic')
f = sp.CubicSpline(sol_E, sol_C, bc_type='natural')
xnew = np.arange(sol_E[0],sol_E[-1],0.1)
ynew = f(xnew)
ax.plot(sol_E, sol_C, "y*", xnew, ynew, "b--")

plt.xlabel("E (mA)")
plt.ylabel("C (points)")
plt.savefig("./output/" + str(L) + "x" + str(L) + "/d0." + str(d) + "/" + instance_filename[:-3] +"_pareto.svg")
print("Pareto plot successful!")
plt.close()
sys.stdout.close()