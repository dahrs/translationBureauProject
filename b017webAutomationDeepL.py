#!/usr/bin/python
# -*- coding:utf-8 -*-

import sys
sys.path.append(u"../utils")
sys.path.append(u"./utils")
import time, random, b000path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, InvalidSessionIdException, MoveTargetOutOfBoundsException

# info
deepLUrl = u"https://www.deepl.com/translator"
mUser, mPass, sUser, sPass = b000path.getDeepLProfileInfo()

# open the driver
driver = webdriver.Firefox()
driver.get(deepLUrl)
time.sleep(random.uniform(1.3, 3.1))
# log to deepL

# shiv = 2k words/day, michel=2k words/day, free = 5000 char



