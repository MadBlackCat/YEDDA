import os

list = os.listdir("./")
for i in list:
    if i[-3:] != ".py":
        newname = "grj."+i
        os.rename(i, newname)
