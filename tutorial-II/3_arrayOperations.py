import numpy as np
import matplotlib.pyplot as plt
#loading only first three columns
ts,left_x,left_y,right_x,right_y=np.loadtxt('exampleEyetrackerData.csv',usecols=[0,1,2,4,5],delimiter=',',unpack=True,skiprows=1)

tstart=ts[0]
ts=(ts-tstart)/1e6   #convert to seconds and do time relative to first time index

x_pos=(left_x+right_x)/2.0  #average of left and right eye position
y_pos=(left_y+right_y)/2.0  #average of left and right eye positions

#TODO in class: show mean position and standard deviation of position.

plt.plot(ts,x_pos)
plt.plot(ts,y_pos)
plt.show()

# TODO: convert units to DVA for screen distance of 100cm and width of 54cm
 