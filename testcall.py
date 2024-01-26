# import os
# os.environ["R_HOME"] = r"./\R\R-4.3.2"
# os.environ["PATH"]   = r"C:\Program files\R\R-4.3.2\bin\x64\R.dll" + ";" + os.environ["PATH"]
# import rpy2
# # import rpy2.robjects as robjects
# # from rpy2.robjects.packages import importr
# from rpy2.robjects.packages import STAP

# def testr():``
#     #Read the file with the R code snippet with 
#     print("In tester")
#     # with open('test.r', 'r') as f:
#     #     fileString = f.read()
#     # #Parse using STAP
#     # print("Read this file string: " + fileString)
#     # msgmanFunction = STAP(fileString, "Forecast_r_function")
#     # print("Called stap")
#     # outputMessage = msgmanFunction.msgman("Hello from Python")
#     # print(outputMessage)

# testr()

import subprocess

res = subprocess.call("Rscript Main.R", shell=True)
res