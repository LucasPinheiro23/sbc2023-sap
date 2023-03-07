#Separa dados raw da instancia do CDP e cria instancia do SAP no formato designado

orig_path = "./instances_CDP_raw"
instances = {512: ["T1","T2","T3","T11","T12"], 1024: ["T13","T14","T15","T21","T22"]}

scale = 1

big_X = -100000
big_Y = -100000
smal_X = 100000
smal_Y = 100000

for size in instances:
    for inst in instances[size]:
        
        x = []
        y = []

        orig = orig_path+"/"+str(size)+"/"+inst+".txt"

        dest = "./instances_DAT/"+str(size)+"/"+inst+".dat"

        with open(dest,"w") as dat:
            
            dat.write("param scale := "+str(scale)+";\n")

            with open(orig,"r") as txt:

                firstline = 1
                for line in txt:
                    #Pega n da primeira linha
                    if(firstline):
                        dat.write("param n := "+line.split('\n')[0]+";\n\n")
                        firstline = 0
                        continue
                    currentline = line.split(",")
                    x.append(currentline[0])
                    y.append(currentline[1])

            dat.write("param X :=")

            for i in range(0,len(x)):
                dat.write("\n"+str(i+1)+" "+x[i])
                if(int(x[i]) > big_X):
                    big_X = int(x[i])
                if(int(x[i]) < smal_X):
                    smal_X = int(x[i])
            
            dat.write(";\n\n")

            dat.write("param Y :=")

            for i in range(0,len(y)):
                dat.write("\n"+str(i+1)+" "+y[i])
                if(int(y[i]) > big_Y):
                    big_Y = int(y[i])
                if(int(y[i]) < smal_Y):
                    smal_Y = int(y[i])
            
            dat.write(";\n\n")

            dat.write("param smallest_X := "+str(smal_X)+";\n")
            dat.write("param smallest_Y := "+str(smal_Y)+";\n")
            dat.write("param biggest_X := "+str(big_X)+";\n")
            dat.write("param biggest_Y := "+str(big_Y)+";\n\n")

            sensor_data = open("sensor_data.txt","r")

            dat.write(sensor_data.read())

        sensor_data.close()
        txt.close()
        dat.close()

        print("SUCESSO")