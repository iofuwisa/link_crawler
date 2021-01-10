import math
import random
import csv
import os


def pick():
    rootList = []
    if os.path.isfile("sitelist.csv"):
        with open ("sitelist.csv", mode="r") as f :
            reader = csv.reader(f)
            for row in reader:
                rootList.append(row[0])
            return rootList[math.floor(random.random()*len(rootList))]

def analyze():
    rootList = []
    if os.path.isfile("sitelist.csv"):
        with open ("sitelist.csv", mode="r") as f :
            reader = csv.reader(f)
            for row in reader:
                rootList.append(row[0])

    count = 0
    for r in rootList:
        if "tumblr.com" in r:
            count += 1
    print("%s/%s : %s" % (str(count), str(len(rootList)), str(count/len(rootList)*100)))


def main():
    print(pick())
    analyze()

if __name__ == "__main__":
    main()