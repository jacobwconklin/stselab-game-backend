# initial conversion of Athul's code to a python script so the front-end can call it eventually. To run this you need the following libraries, 
# numpy
# pandas
# scipy
# matplotlib
# add them to requirements.txt if this will be included.


# import numpy as np
# import pandas as pd
# import random
# from random import choices
# from scipy.stats import beta
# import sys
# import matplotlib.pyplot as plt
# from statistics import fmean


# df = pd.read_csv('input_test.csv')
# df
# df['Embodiment'].unique()
# df = df[df['Embodiment']!= np.nan]
# df
# import numpy as np

# common_values = np.intersect1d(df['Principle'], df['Embodiment'])
# common_values


# # Classes

# class embodiment:
#   def __init__(self, alpha = 2, beta = 5):
#     self.alpha = alpha
#     self.beta = beta

#     self.alpha_am = 5
#     self.beta_am = 2

#     self.con = 0.8
#   # Diff ways to generate quality
#   # beta
#   def beta_q(self):
#     q = np.random.beta(self.alpha, self.beta)
#     return q

#   # Constant
#   def const_q(self):
#     con = 0.1
#     if self.alpha == 5: ## change to something more logical
#       con = 0.75
#     return con
#   # Gaussian
#   def gauss_q(self):
#     q = np.random.normal(0.4, 0.25)
#     return q

#   def gauss_q(self):
#     q = np.random.normal(0.4, 0.25)
#     return q

#   # rectangular
#   def rec_q(self):
#     q = 0.7 + 0.1*random.uniform(0, 1)
#     return q
# # ARM.rec_q()


# # Class
# # Hard coded to uses uniform or biased scores at the moment will change to read from csv
# class pathp2:
#   def __init__(self, emb):
#     self.emb = emb

#     self.propro = []
#     self.proam = []
#     for idj, j in enumerate(emb):
#       if idj == 0:
#         if len(emb) < 2:
#           # self.propro.append(0.8)
#           self.propro.append(1)
#         else:
#           self.propro.append(0.5)
#         self.proam.append(1/len(emb))
#       else:
#         self.propro.append(0.5/(len(emb)-1))
#         # self.propro.append(0)
#         self.proam.append(1/len(emb))
# # Class

# # Stores the function and expertise required to solve.
# class pathp:
#   def __init__(self, princ):
#     self.princ = princ
#     self.propro = []
#     self.proam = []
#     # self.exp = exp
#     # 0 - Mech, 1 - Elec, 2 - Comp
#     for idj, j in enumerate(princ):
#       if idj == 0:
#         self.propro.append(0.6)
#         # self.propro.append(1)
#         self.proam.append(1/len(princ))
#       else:
#         self.propro.append(0.4/(len(princ)-1))
#         # self.propro.append(0)
#         self.proam.append(1/(len(princ)))


# # Generating classes from csv file input
# # Working on the assumption that first entry of csv is the professional solution

# # Can be changed to read the probabilities directly from the csv input


# # Identify functions
# func_values = df['Functionality'].unique()
# princ_values= [[]]*(len(func_values))

# # read principles from input and map to corresponding function
# for i in range(len(func_values)):
#   princ_values[i] = df[df['Functionality'] == func_values[i]]['Principle'].unique()
# for i in range(len(func_values)):
#   emb_values= [[]]*(len(princ_values[i]))
#   # temp array to store all embodiments corresponding to each principle
#   for j in range(len(princ_values[i])):
#     emb_values[j] = df[df['Principle'] == princ_values[i][j]]['Embodiment'].unique()
#     globals()[princ_values[i][j]] = pathp2(emb_values[j])
#     for k in range(len(emb_values[j])):
#       if j == 0 and k == 0:
#         globals()[emb_values[j][k]] = embodiment(2, 5)
#         # Hard code - alpha and beta values for pro solution (for testing), will be modified soon
#       else:
#         globals()[emb_values[j][k]] = embodiment()
#   # exp = df[df['Functionality'] == func_values[i]]['Expertise'].tolist()
#   globals()[func_values[i]] = pathp(princ_values[i])
# emb_values
# X


# # Model Parameters
# # - Tournament size/contract mechanism for each solver type
# # - Total number of runs


# N_run = 100
# N_Am = 10
# N_Pro = 10
# N_Spec = 1


# ## Inputs
# # - List of Architectures
# # - List of subsystems under it
# # - List of functions under it


# # Read Input
# Architecture = ["D1", "D2" ,"D3","D4"]

# D1 = ['SRA']
# D1w = [1]
# SRA = ['Pack_Unpack', '2-Reaching ', '3-Grasping', '4-Orient',
#        'Contingency Loading', 'Control Free Space',
#        'Control onto Handrail', 'Control Orient',
#        'Electronics']

# SRAw = [1, 1, 1, 1, 1 , 1, 1, 1, 1]

# D2 = ['SFA', 'SAM']
# D2w = [1.0, 1.0]
# SFA = ['Pack_Unpack', '2-Reaching ', '4-Orient',
#        'Contingency Loading', 'Control onto Handrail',
#        'Electronics']
# SFAw = [0.85, 0.78, 1, 0.48, 0.54, 0.71]

# SAM = ['Pack_Unpack', '3-Grasping',
#        'Contingency Loading', 'Control Free Space',
#        'Control onto Handrail', 'Control Orient', 'Control Other',
#        'Electronics']
# SAMw = [0.87, 1, 0.94, 0.81, 0.61, 1, 1, 0.79]

# D3 = ['SCA','SPAM']
# D3w = [1.0, 1.0]

# SCA = ['Pack_Unpack', '2-Reaching ', '4-Orient',
#        'Contingency Loading', 'Control Orient', 'Control Other',
#        'Electronics']
# SCAw = [0.73, 0.43, 1, 0.48, 1, 1, 0.56]

# SPAM = ['Pack_Unpack', '2-Reaching ', '3-Grasping',
#        'Contingency Loading',
#        'Control onto Handrail',
#        'Electronics']
# SPAMw =  [0.5, 0.78, 1, 0.7, 1, 0.46]


# # Test Inputs
# # Mechanical.propro
# # Mechanical.proam
# # Numerical Verification Inputs


# # Test Input 1
# Architecture = ["D2"]
# D2 = ['SFA', 'SAM']
# D2w = [1.0, 1.0]

# SAM = ['Pack_Unpack', '3-Grasping',
#        'Contingency Loading', 'Control Free Space',
#        'Control onto Handrail', 'Control Orient', 'Control Other',
#        'Electronics']

# SAMw = [0.67, 0.94, 0.94, 0.81, 0.61, 0.07, 0.71, 0.79]


# SFA = ['Pack_Unpack', '2-Reaching ', '4-Orient',
#        'Contingency Loading', 'Control onto Handrail',
#        'Electronics']

# SFAw = [0.45, 0.78, 0.12, 0.28, 0.54, 0.31]
# # Test Input 2
# Architecture = ["D2"]
# D2 = ['SAM']
# SAM = ['Pack_Unpack']
# SAMw = [0.1]
# globals()[D2[0] + 'w']
# # Test Input 3
# Architecture = ["D2"]
# D2 = ['SAM']
# SAM = ['Pack_Unpack', '2-Reaching ', '4-Orient']

# # Test Input 4
# Architecture = ["D2"]
# D2 = ['SAM']
# SAM = ['Electronics']
# # Tournament Run Functions
# def run_tour_am(n, subs, amp = 0):
#   q = []
#   out = []

#   for am in range(n):
#     qf = []
#     # if random.uniform(0, 1) < amp:
#     #   continue
#       # using 0 or 1.1 etc is dependent on aggregation, just skipping instead
#     for j in globals()[subs]:
#       # print(globals()[j].princ)
#       # print(globals()[j].proam)
#       out.append(j)
#       k0 = choices(globals()[j].princ, globals()[j].proam)
#       # print(k0)

#       out.append(k0[0])

#       d = globals()[k0[0]]
#       # print("\n")

#       # print(d.emb)
#       # print(d.proam)
#       k1 = choices(d.emb, d.proam)

#       out.append(k1[0])
#       # print(k1)
#       # print("\n")

#       al = globals()[k1[0]].alpha_am
#       be = globals()[k1[0]].beta_am
#       # aggregate dist first

#       ## different ways to generate quality
#       qf.append(np.random.beta(al, be))

#       # qf.append(globals()[k1[0]].rec_q())

#       # qf.append(globals()[k1[0]].gauss_q())

#       # qf.append(globals()[k1[0]].const_q())
#     q.append(dot_product(qf,globals()[subs + 'w'] ))
#   if not q:
#     return 0, []
#   return min(q), out
# def run_tour_pro(n, subs):
#   q = []
#   out = []
#   for am in range(n):
#     qf = []
#     for j in globals()[subs]:
#       # print(globals()[j].princ)
#       # print(globals()[j].propro)
#       out.append(j)
#       k0 = choices(globals()[j].princ, globals()[j].propro)
#       # print(k0)

#       out.append(k0[0])

#       d = globals()[k0[0]]
#       # print("\n")

#       # print(d.emb)
#       # print(d.propro)
#       k1 = choices(d.emb, d.propro)

#       out.append(k1[0])
#       # print(k1)
#       # print("\n")

#       al = globals()[k1[0]].alpha
#       be = globals()[k1[0]].beta
#       ## different ways to generate quality
#       qf.append(np.random.beta(al, be))

#       # qf.append(globals()[k1[0]].rec_q())

#       # qf.append(globals()[k1[0]].gauss_q())

#       # qf.append(globals()[k1[0]].const_q())
#     q.append(dot_product(qf,globals()[subs + 'w'] ))
#   return min(q), out
# def run_am(j):
#   out = []
#   # print(globals()[j].princ)
#   # print(globals()[j].proam)
#   out.append(j)
#   k0 = choices(globals()[j].princ, globals()[j].proam)
#   print(k0)

#   out.append(k0[0])

#   d = globals()[k0[0]]
#   # print("\n")

#   # print(d.emb)
#   # print(d.proam)
#   k1 = choices(d.emb, d.proam)

#   out.append(k1[0])
#   # print(k1)
#   # print("\n")

#   al = globals()[k1[0]].alpha
#   be = globals()[k1[0]].beta
#   # print('alpha ', al)
#   # print('beta ', be)
#   return np.random.beta(al, be), out
# def run_pro(j):
#   out = []
#   # print(globals()[j].princ)
#   # print(globals()[j].propro)
#   out.append(j)
#   k0 = choices(globals()[j].princ, globals()[j].propro)
#   out.append(k0[0])
#   # print(k0)
#   d = globals()[k0[0]]
#   # print("\n")

#   # print(d.emb)
#   # print(d.propro)
#   k1 = choices(d.emb, d.propro)
#   out.append(k1[0])
#   # print(k1)
#   # print("\n")

#   al = globals()[k1[0]].alpha
#   be = globals()[k1[0]].beta

#   return np.random.beta(al, be), out
# def run_tour_spec(n, subs, exp):
#   q = []
#   out = []
#   for spec in range(n):
#     qf = []
#     for j in globals()[subs]:
#       if (globals()[j].exp == exp):
#         # print("Pro ", j)
#         q1, out = run_pro(j)
#         qf.append(q1)
#       else:
#         print("AM ", j)
#         q1, out = run_am(j)
#         qf.append(q1)
#     q.append(quality_score(qf))
#   return max(q), out
# # Quality Score Gereneration Function
# # Quality Score Gereneration Function
# def quality_score(a):
#   # return min(a)
#   # return max(a)
#   return fmean(a)
# def dot_product(list1, list2):
#     return sum(x*y for x,y in zip(list1, list2))



# ## attempt to run:

# print("Running amateur tournament now")
# print(run_tour_am(1, 'SAM'))
# print("Running professional tournament now")
# print(run_tour_pro(1, 'SAM'))
# # print("Running specialist tournament now Mech specialist")
# # print(run_tour_spec(1, 'SPAM', 0))
# # print("Running specialist tournament now EE specialist")
# # print(run_tour_spec(1, 'SPAM', 1))