import numpy as np
import matplotlib.pyplot as plt
#loading only first three columns
ts,left_x,left_y=np.loadtxt('exampleEyetrackerData.csv',usecols=[0,1,2],unpack=True,skiprows=1,delimiter=',')
startTime=ts[0]

#for indx in range(len(ts)):
#    ts[indx]=ts[indx]-startTime
'''
ts=ts-startTime
plt.plot(ts,left_x,label='x pos')
plt.plot(ts,left_y,label='y pos')
plt.xlabel("Time (second)")
plt.legend()
#plt.ylabel("Left eye x-position (in pixels)")
plt.show()
'''

plt.scatter(left_x,left_y)
plt.xlim((0,1920))
plt.ylim((0,1080))
plt.show()

#TODO in class: plot each variable one at a time

#TODO in class: understand "gaps" in data; understand data quality from plot

#TODO in class: plot each variable as a function of time

#TODO in class: plot a "meaningful" time axes; first intro to array operations
