import numpy as np
import matplotlib.pyplot as plt
#loading only first three columns
ts,left_x,left_y=np.loadtxt('exampleEyetrackerData.csv',usecols=[0,1,2],unpack=True,skiprows=1,delimiter=',')

plt.plot(left_x)
plt.show()


#TODO in class: show selection with index over an interesting range in data

#TODO in class: plot the data after selecting a range

#TODO in class: show how to skip samples

#TODO in class. Find total time on centre of the screen. use loop.

#TODO in class: above without loop, array masking examples(enough time?)

