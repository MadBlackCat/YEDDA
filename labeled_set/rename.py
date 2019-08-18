import os

list = os.listdir("./")
for i in list:
    if i[-3:] != ".py":
        newname = i.replace("grj.", "")
        os.rename(i, newname)
