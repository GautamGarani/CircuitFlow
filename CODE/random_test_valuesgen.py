import random
import csv


def generate_random_test_values(numrows):
    with open("random_values.csv", 'a', newline='') as f:
        filewriter=csv.writer(f)
        header=["volume of water flown (mL)", "time of flow(s)"]
        filewriter.writerow(header)
        for _ in range(numrows):
            col_volume=random.randint(100,500)
            col_time=random.randint(2,10)
            row=[col_volume, col_time]
            filewriter.writerow(row)
    Vol_flow=[]
    Time_flow=[]
    with open("random_values.csv", 'r', newline="") as f:
        filereader=csv.DictReader(f)
        for row in filereader: 
            Vol_flow.append(row["volume of water flown (mL)"])
            Time_flow.append(row["time of flow(s)"])
    
    return Vol_flow, Time_flow

generate_random_test_values(100)



