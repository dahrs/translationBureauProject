import sys, math, mimetypes
sys.path.append(u'../utils')
sys.path.append(u'./utils')
from tqdm import tqdm

import utilsOs, utilsString, b000path, b003heuristics
import re, os, sys
from scipy.stats import pearsonr

# import pandas as pd
# import numpy as np

# count the time the algorithm takes to run
startTime = utilsOs.countTime()

l = [1]
print([0] + l[:2])


# print the time the algorithm took to run
print(u'\nTIME IN SECONDS ::', utilsOs.countTime(startTime))