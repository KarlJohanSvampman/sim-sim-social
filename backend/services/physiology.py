def update_needs(c):
    rates={"hunger":0.5,"thirst":0.7,"fatigue":0.5,"bladder":0.6}
    for k, rate in rates.items():
        c["needs"][k]=min(100, c["needs"][k]+rate)
