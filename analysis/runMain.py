from analyzeBlankDuration import plotDistribution,performAnova
from plotSaccadeParams import plotCombined

sub_all=[1,2,3,4,5,6,8,9,12,13,14,15,16,17,18,20,22,23,24]

plotDistribution(sub_all) #generate main result plot
plotCombined(sub_all)       #generate saccade parameter plot

#performAnova(sub_all)       #get annova results (run only if you have the pingouin package installed)
