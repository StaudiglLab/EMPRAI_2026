import numpy as np
import matplotlib.pyplot as plt
#loading only first three columns
ts,left_x,left_y=np.loadtxt('exampleEyetrackerData.csv',usecols=[0,1,2],unpack=True,skiprows=1,delimiter=',')

plt.plot(left_x)
plt.show()

#TODO in class: plot each variable one at a time

#TODO in class: understand "gaps" in data; understand data quality from plot

#TODO in class: plot each variable as a function of time

#TODO in class: plot a "meaningful" time axes; first intro to array operations
