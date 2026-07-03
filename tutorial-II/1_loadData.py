import numpy as np

#loading only first three columns
ts,left_x,left_y=np.loadtxt('exampleEyetrackerData.csv',usecols=[0,1,2],unpack=True,skiprows=1,delimiter=',')
#TODO in class. Show how to look at the size of the array and how to retrieve elements in the array (contraints on what indexes can be)
#x=[1,2,3,4]
lengthOfData=len(ts)
print(lengthOfData)
