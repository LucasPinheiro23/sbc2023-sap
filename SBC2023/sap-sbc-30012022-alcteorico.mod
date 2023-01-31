/*********************************************
 * OPL 22.1.0.0 Model
 * Author: Lucas Pinheiro
 * Creation Date: 17 de jan de 2023 at 20:23:00
 
 MODELO DE OTIMIZAÇÃO DE TOPOLOGIA DE REDE DE SENSORES SEM FIO
 
 CONSIDERANDO ALCANCE TEÓRICO
 
 *********************************************/

//-----------------
//Dados do problema
//-----------------

//Dados de entrada (importar do DAT depois) - DADOS DE TESTE REFERENTES AOS XBEES [S2C, S2C Pro, S3 Pro]

//Tipos de sensores [S2C=1,S2CPro=2,S3=3]

{string} Tipos = ...;

//range S = 1..n_t;

int Rmax[Tipos] = ...; //Alcance maximo teorico
float It[Tipos] = ...; //Corrente consumida (DC=1%,payload=16B)
float Mt[Tipos] = ...; //Custo medio em dolar

//Pesos das funções objetivo
//float alfas[1..5] = [0,0.25,0.5,0.75,1];

float a = 0.333;

//Número total de posicoes de alocacao (n)
int n = ...;
range V = 1..n;


////Tamanho total da área do problema (lx * ly)
float lx = ...;
float ly = ...;

range LX = 1..ftoi(round(lx));
range LY = 1..ftoi(round(ly));


//Coordenadas (em unidades) de cada nó da malha LxL, i.e., (L^2xL^2)
//escala*1 metros para a unidade de distancia das coordenadas
//int escala = 6250; 
int escala = ...;
int x[V] = ...;
int y[V] = ...;

//Matriz de distâncias entre cada par de pontos da rede
float D[V][V];

execute COORDS{
  
  for(i in V){
    x[i] = escala*x[i];
  }
  
  for(i in V){
    y[i] = escala*y[i];
  }
   
   //Calcula distancias entre duas possiveis posicoes de alocacao
   
   for(var i in V){
     for(var j in V){
       
       D[i][j] = Math.sqrt(Math.pow((x[j]-x[i]),2)+Math.pow((y[j]-y[i]),2));
       
     }
   }
}

{int} N[Tipos][V];

execute VIZINHANCA {
  
  var Pr;
  //A vizinhanca eh preenchida de acordo com Rmax, mediante distancia entre dois nos.
  for(var t in Tipos){
	  for(var i in V){
	    for(var j in V){
	      	if(i != j){
		      	  
		      	  if(D[i][j] > Rmax[t]){
		      	    N[t][i].add(j);
		      	  }
		      	  
		      	}
     		}		    	
	    }
	  }
}  

//-----------------
//Variváveis de decisão
//---------------------
dvar boolean s[Tipos][V];

//----------
//Expressões
//----------

//Nor (verifica se nó i alocado está isolado. Se igual a 0, o nó tem pelo menos 1 vizinho ou não está alocado na posição i (inativo). Se igual a 1, não possui nenhum vizinho.)
dexpr int Nor = sum(i in V, t in Tipos) minl(s[t][i],(1 - minl(1,(sum(u in Tipos, j in N[t][u][i]) s[u][j]))));

////Funções Objetivo

//Minimizar consumo de energia
dexpr float E = sum(i in V) sum(t in Tipos) It[t] * s[t][i];
//Maximizar cobertura da rede
dexpr float C = (sum(i in V) sum(t in Tipos) s[t][i])/n;
dexpr float C_alt = sum(i in V, t in Tipos, u in Tipos, j in N[t][u][i]) s[u][j];
//Minimizar custo monetario da rede
dexpr float M = sum(i in V) sum(t in Tipos) Mt[t] * s[t][i];

////FO

////Minimizar energia e custo monetário, ao passo que maximiza cobertura da rede
minimize E;
//minimize M;
//maximize C;
//maximize C_alt;

subject to{
	
  //Garante a alocação de apenas 1 tipo por posição  
  forall(i in V){
    sum(t in Tipos) s[t][i] <= 1;
  };
  
  //Exije a alocação de ao menos 1 ou 5% das n posições, o que for maior.
  maxl(1,ftoi(round(0.05*n))) <= sum(i in V, t in Tipos) s[t][i] <= n;
  
  //Exije que não haja nós isolados, i.e., que não consigam se comunicar com nenhum outro.
  Nor == 0;
  

}

//Plotar a matriz geográfica mostrando em quais pontos o modelo aplicou cada tipo de sensor
execute Pos_processamento{
	  writeln("------------------------------------");
	  writeln("A alocação ótima para os sensores no espaço "+Opl.ftoi(Opl.round(lx))+"x"+Opl.ftoi(Opl.round(ly))+" é:");
	  var k = 1;
	  for(var i in LX){
	    write("[ ");
	    for(var j in LY){
	      
	      if(k == n+1){
	        write("- ");
	      }
	      
	      else if(x[k] == i*escala && y[k] == j*escala){
	        
	        if(s["S2C"][k] == 1){
	        	write("1 ");
	        	k = k+1;
       		}
       		else if(s["S2CPro"][k] == 1){
		        write("2 ");
		        k = k+1;
        	}
        	else if(s["S3"][k] == 1){
	        	write("3 ");
	        	k = k+1;
       		}
       		else{
       		  write("- ");
       		  k = k+1;
       		}
               	
	      }
	              	
	      else{
	        write("- ");
	      }
	  }
	  writeln("]");
	}
}