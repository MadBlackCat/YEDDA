from Tkinter import *
from ttk import *#Frame, Button, Label, Style, Scrollbar
import tkFileDialog
import tkFont
import re
from collections import deque
import pickle
import os.path
import matplotlib.pyplot as plt
import platform
from utils.recommend import *
import tkMessageBox

configFile = "configs/default.config"

if os.path.isfile(configFile):
    with open(configFile, 'r') as fp:
        # print(fp.read())
        pressCommand = pickle.load(fp)

        fp.close()
