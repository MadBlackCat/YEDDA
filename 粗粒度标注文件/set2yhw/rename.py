import os

list = os.listdir("./")
for i in list:
    if i[-3:] != ".py":
        newname = "yhw."+i
        os.rename(i, newname)
