n = 288                        # Define number of timesteps in a day
m = n                          # Define number of SOC_Calculations (pseudo)
s = 366                        # Number of sample intervals
                    
set_N = range(1, n+1)
set_M = range(1, m+1)
set_T = range(1, s+1) 

import numpy as np

# SOC Related matrix
A1  = np.eye(n)
A2  = np.concatenate((np.eye(n-1),np.zeros((n-1, 1))), axis=1)
A3  = np.vstack((np.zeros((1, n)), A2))
A_Mat = A1 - A3

# Charging and discharging efficieny of storage and time step
ch_eff = 0.94
dch_eff = 0.94
Tstp    = 5/60
# Storage Rated power in MW and capacity in MWh
P_rated = 10000   # Made it a large number

# Charge discharge related matrix done with respect to 1MWh storage
Ach_Mat  = Tstp*ch_eff*np.eye(n)
Adch_Mat = Tstp*(1/dch_eff)*np.eye(n)

SOC_Ini = 0.98
SOC_Min = 0.00
SOC_Max = 1.00

# SOC initial input
b_Mat = np.vstack(([SOC_Ini], np.zeros((n-1,1))))

A    = {(j+1, i+1): A_Mat[j, i]    for j in range(0, m) for i in range(0, n)}
Ach  = {(j+1, i+1): Ach_Mat[j, i]  for j in range(0, m) for i in range(0, n)}
Adch = {(j+1, i+1): Adch_Mat[j, i] for j in range(0, m) for i in range(0, n)}
b    = {(j+1, t+1): b_Mat[j] for j in range(0, m) for t in range(0, s)}

import gurobipy as grb
model = grb.Model(name="MIP Model")

# P is Continuous P = x_1_vars - x_2_vars; x_1_vars >= 0 and x_2_vars >= 0
# Power injected into the grid = -P
x_1_vars  ={(i,t):model.addVar(vtype=grb.GRB.CONTINUOUS, 
                        lb=0, 
                        ub= P_rated,
                        name="x+_{0}".format(i,t)) for i in set_N for t in set_T}
x_2_vars  ={(i,t):model.addVar(vtype=grb.GRB.CONTINUOUS, 
                        lb=0, 
                        ub= P_rated,
                        name="x-_{0}".format(i,t)) for i in set_N for t in set_T}
Capacity_vars  ={(i,t):model.addVar(vtype=grb.GRB.CONTINUOUS, 
                        lb=0,
                        name="Cap_{0}".format(i,t)) for i in set_N for t in set_T}
z_vars  ={(i,t):model.addVar(vtype=grb.GRB.BINARY, 
                        name="z_{0}".format(i,t)) for i in set_N for t in set_T}

Pin_vars  ={(i,t):model.addVar(vtype=grb.GRB.CONTINUOUS, 
                        lb= -float('inf'), 
                        ub= float('inf'),
                        name="x+_{0}".format(i,t)) for i in set_N for t in set_T}

Capacity_Req   = {t:model.addVar(vtype=grb.GRB.CONTINUOUS,
                  lb= 0, 
                  ub= float('inf')) for t in set_T}

# == constraints
constraints = {(i,t) : 
model.addLConstr(
        lhs= Capacity_vars[i,t],
        sense=grb.GRB.GREATER_EQUAL,
        rhs= SOC_Min*Capacity_Req[t])
    for i in set_M for t in set_T}

constraints = {(i,t) : 
model.addLConstr(
        lhs= Capacity_vars[i,t],
        sense=grb.GRB.LESS_EQUAL,
        rhs= SOC_Max*Capacity_Req[t])
    for i in set_M for t in set_T}

constraints = {(j,t) : 
model.addLConstr(
        lhs=grb.quicksum((A[j,i]*Capacity_vars[i,t] - Ach[j,i]*x_1_vars[i,t] + Adch[j,i]*x_2_vars[i,t] - SOC_Ini*Capacity_Req[t]) for i in set_N) ,
        sense=grb.GRB.EQUAL,
        rhs=0)
    for j in range(1, 1) for t in set_T }

constraints = {(j,t) : 
model.addLConstr(
        lhs=grb.quicksum((A[j,i]*Capacity_vars[i,t] - Ach[j,i]*x_1_vars[i,t] + Adch[j,i]*x_2_vars[i,t]) for i in set_N) ,
        sense=grb.GRB.EQUAL,
        rhs=0)
    for j in range(2, m+1) for t in set_T }

constraints = {(i,t) : 
model.addLConstr(
        lhs= x_1_vars[i,t],
        sense=grb.GRB.LESS_EQUAL,
        rhs= P_rated*z_vars[i,t], 
        name="Pch_{0}".format(i,t))
    for i in set_M for t in set_T}

constraints = {(i,t) : 
model.addLConstr(
        lhs= x_2_vars[i,t],
        sense=grb.GRB.LESS_EQUAL,
        rhs= P_rated*(1-z_vars[i,t]), 
        name="Pdch_{0}".format(i,t))
    for i in set_M for t in set_T}

constraints = {(i,t) : 
model.addLConstr(
        lhs= Pin_vars[i,t],
        sense=grb.GRB.EQUAL,
        rhs= x_2_vars[i,t] - x_1_vars[i,t], 
        name="Pin_{0}".format(i,t))
    for i in set_M for t in set_T}

constraints = {t : 
model.addLConstr(
        lhs=Capacity_vars[n,t] ,
        sense=grb.GRB.EQUAL,
        rhs=SOC_Ini*Capacity_Req[t])
    for t in set_T }

P_calc  = model.addVar(vtype=grb.GRB.CONTINUOUS, lb=0, ub=float('inf'))
Capacity_Calc  = model.addVar(vtype=grb.GRB.CONTINUOUS, lb=0, ub=float('inf'))

kappa = 0.98

## CC Variables Power
sigma1CC_vars  = model.addVar(vtype=grb.GRB.CONTINUOUS, lb=-float('inf'), ub=float('inf'))
beta1CC_vars   = {(i,t):model.addVar(vtype=grb.GRB.CONTINUOUS,
                  lb= 0, 
                  ub= float('inf')) for i in set_N for t in set_T}

sigma2CC_vars  = model.addVar(vtype=grb.GRB.CONTINUOUS, lb=-float('inf'), ub=float('inf'))
beta2CC_vars   = {(i,t):model.addVar(vtype=grb.GRB.CONTINUOUS,
                  lb= 0, 
                  ub= float('inf')) for i in set_N for t in set_T}


constraints = {model.addLConstr(
        lhs= sigma1CC_vars + 2/(1-kappa)*1/s*grb.quicksum(beta1CC_vars[i,t] for i in set_N for t in set_T),
        sense=grb.GRB.LESS_EQUAL,
        rhs= P_calc)}

constraints = {(i,t) : 
model.addLConstr(
        lhs= x_1_vars[i,t] - sigma1CC_vars - beta1CC_vars[i,t],
        sense=grb.GRB.LESS_EQUAL,
        rhs= 0, 
        name="Pin_{0}".format(i,t))
    for i in set_M for t in set_T}

constraints = {model.addLConstr(
        lhs= sigma2CC_vars + 2/(1-kappa)*1/s*grb.quicksum(beta2CC_vars[i,t] for i in set_N for t in set_T),
        sense=grb.GRB.LESS_EQUAL,
        rhs= P_calc)}

constraints = {(i,t) : 
model.addLConstr(
        lhs= x_2_vars[i,t] - sigma2CC_vars - beta2CC_vars[i,t],
        sense=grb.GRB.LESS_EQUAL,
        rhs= 0, 
        name="Pin_{0}".format(i,t))
    for i in set_M for t in set_T}

## CC Variables Energy
sigma1CCCapacity_vars  = model.addVar(vtype=grb.GRB.CONTINUOUS, lb=-float('inf'), ub=float('inf'))
beta1CCCapacity_vars   = {t:model.addVar(vtype=grb.GRB.CONTINUOUS,
                  lb= 0, 
                  ub= float('inf')) for t in set_T}


constraints = {model.addLConstr(
        lhs= sigma1CCCapacity_vars + 1/(1-kappa)*1/s*grb.quicksum(beta1CCCapacity_vars[t] for t in set_T),
        sense=grb.GRB.LESS_EQUAL,
        rhs= Capacity_Calc)}

constraints = {t : 
model.addLConstr(
        lhs= Capacity_Req[t] - sigma1CCCapacity_vars - beta1CCCapacity_vars[t],
        sense=grb.GRB.LESS_EQUAL,
        rhs= 0)
    for i in set_M for t in set_T}

# Import LMP data
import pandas as pd

df_Site = pd.read_csv('WRSBES_BESS1_2020_1.csv')
df_Site = df_Site.drop(columns=['Time'])
df_Site.fillna(0, inplace=True)

# Check if the number of columns is less than the threshold
avl_col = df_Site.shape[1]
if df_Site.shape[1] < s:
    num_columns_to_add = s - df_Site.shape[1]
    additional_columns = pd.DataFrame(np.zeros((df_Site.shape[0], num_columns_to_add)))
    df_Site = pd.concat([df_Site, additional_columns], axis=1)
    
c_matrix = df_Site.values

c = {(i+1,t+1): c_matrix[i,t] for i in range(0, n) for t in range(0, s)}

PManu = 1.9
CManu = 3.9
CostManu = 1655225

C_Num  =model.addVar(vtype=grb.GRB.INTEGER, lb=0, ub= 10)

constraints = {model.addLConstr(
        lhs= P_calc,
        sense=grb.GRB.LESS_EQUAL,
        rhs= PManu*C_Num)}

constraints = {model.addLConstr(
        lhs= Capacity_Calc,
        sense=grb.GRB.LESS_EQUAL,
        rhs= CManu*C_Num)}

PManu = 1.9
CManu = 3.9
CostManu = 1655225

C_Num  =model.addVar(vtype=grb.GRB.INTEGER, lb=0, ub= 10)

constraints = {model.addLConstr(
        lhs= P_calc,
        sense=grb.GRB.LESS_EQUAL,
        rhs= PManu*C_Num)}

constraints = {model.addLConstr(
        lhs= Capacity_Calc,
        sense=grb.GRB.LESS_EQUAL,
        rhs= CManu*C_Num)}

objective = grb.quicksum(s*(1/avl_col)*(x_2_vars[i,t]-x_1_vars[i,t])*c[i,t]   for i in set_N for t in set_T)  - 1/10*CostManu*C_Num

# for maximization
model.ModelSense = grb.GRB.MAXIMIZE
model.setObjective(objective)

model.optimize()

all_vars    = model.getVars()
values_Xch  = model.getAttr('X', x_1_vars)
values_Xdch = model.getAttr('X', x_2_vars)
values_SOC  = model.getAttr('X', Capacity_vars)
values_z_vars  = model.getAttr('X', z_vars)
values_Pin_vars  = model.getAttr('X', Pin_vars)



# Extract values and store in dataframe
df = pd.DataFrame(list(values_Pin_vars.values()), index=pd.MultiIndex.from_tuples(values_Pin_vars.keys()))
df = df.unstack().fillna(0)
