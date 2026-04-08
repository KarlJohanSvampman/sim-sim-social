def tick_addiction(c):
    c["cravings"]["alcohol"]=min(100,c["cravings"]["alcohol"]+c["addiction"]["alcohol"]*0.01)
    c["cravings"]["tobacco"]=min(100,c["cravings"]["tobacco"]+c["addiction"]["tobacco"]*0.015)
    c["withdrawal"]["alcohol"]=max(0,c["cravings"]["alcohol"]-50)*0.5
    c["withdrawal"]["tobacco"]=max(0,c["cravings"]["tobacco"]-40)*0.6
    penalty=c["withdrawal"]["alcohol"]*0.02+c["withdrawal"]["tobacco"]*0.015
    c["needs"]["fatigue"]=min(100,c["needs"]["fatigue"]+penalty)
