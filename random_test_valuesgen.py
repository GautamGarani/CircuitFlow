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

generate_random_test_values(100)



