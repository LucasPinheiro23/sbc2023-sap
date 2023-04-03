from sap_sbc_abstract_model import *
from pyomo.environ import *
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import logging
import os

#Muda diretorio (BUG DO VSCODE)
os.chdir('./pyomo')

all_subset_gen(3)

for s in subsets:
    print(len(s))
    print("\n")