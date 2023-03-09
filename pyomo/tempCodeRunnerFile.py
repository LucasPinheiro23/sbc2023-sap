print("Calculando min-max:")
# max_fo = get_fo_max(model, instance_filename, solver, solver_exec)
# min_fo = get_fo_min(model, instance_filename, solver, solver_exec)
# print("Maximos: "+str(max_fo))
# print("Minimos: "+str(min_fo))

# #Cria novos objetivos normalizados
# model.exp_norm_E = (model.E - min_fo['E'])/(max_fo['E']-min_fo['E'])
# model.exp_norm_C = (model.C - min_fo['C'])/(max_fo['C']-min_fo['C'])
# model.exp_norm_M = (model.M - min_fo['M'])/(max_fo['M']-min_fo['M'])
# model.norm_E = Objective(rule=obj_norm_E,sense=minimize)
# model.norm_C = Objective(rule=obj_norm_C,sense=maximize)
# model.norm_M = Objective(rule=obj_norm_M,sense=minimize)