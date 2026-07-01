from saccadeDetectionCore import detectAndSaveSaccades

infodict={
    'rootdir':'./',
    'experiment':'CLP',
    'subjectNamePrefix':'Sub_',
    'outdirname':'derived',
    'figuredirectory':'./figures/',
    'subjects':[1,2,3,4,5,6,7,8,9,12,13,14,15,16,17,18,19,20,22,23,24]
}

#looping over all subjects and saving out saccades
for subID in infodict['subjects']:
    #preprocess(infodict,subID)
    detectAndSaveSaccades(infodict,subID,thresholdVel=5,minDurationInSamples=3)

