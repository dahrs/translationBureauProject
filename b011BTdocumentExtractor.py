#!/usr/bin/python
# -*- coding:utf-8 -*-


from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import sys, time
sys.path.append(u'../utils')
sys.path.append(u'./utils')
import utilsOs, utilsString


outputPath = u'/data/rali5/Tmp/alfonsda/workRali/004tradBureau/008originalDocumentsBt/'
tempPath = u'{0}tmp/'.format(outputPath)
dejaVu = set([])

# count the time the algorithm takes to run
startTime = utilsOs.countTime()


# get url, user and password
with open(u'./b011pathUserPassword') as pup:
    url = pup.readline().replace(u'\n', u'')
    user = pup.readline().replace(u'\n', u'')
    passw = pup.readline().replace(u'\n', u'')

# open the driver go to the page
profile = webdriver.FirefoxProfile()
profile.set_preference("webdriver_assume_untrusted_issuer",  False)
profile.set_preference("webdriver_accept_untrusted_certs",  True)

# To prevent download dialog
profile.set_preference('browser.download.folderList', 2) # custom location
profile.set_preference("browser.download.manager.showWhenStarting", False)
profile.set_preference('browser.download.dir', tempPath)
mimeFormats = 'text/plain,text/csv,application/csv,application/download,application/octet-stream,application/msword' # docx == application/vnd.openxmlformats-officedocument.wordprocessingml.document
profile.set_preference('browser.helperApps.neverAsk.saveToDisk', mimeFormats)
profile.set_preference("browser.download.manager.alertOnEXEOpen", False)
profile.set_preference("browser.download.manager.closeWhenDone", False)
profile.set_preference("browser.download.manager.focusWhenStarting", False)


# open the browser
driver = webdriver.Firefox(profile)
# driver = webdriver.Chrome(u'/usr/bin/chromium')
driver.refresh()
driver.get(url)

# write the username and password
usernameCase = driver.find_element_by_name(u"LoginForm[username]")
passwordCase = driver.find_element_by_name(u"LoginForm[password]")
usernameCase.send_keys(user)
passwordCase.send_keys(passw)
# click on the button
logInButton = driver.find_element_by_name(u"yt0")
logInButton.click()

# select a client
clientCaseXpath = u'/html/body/div[1]/div/div[6]/div/div/form[1]/div[1]/fieldset/div/div[4]/fieldset/div[1]/div/ul/li/input'
clientCase = driver.find_elements_by_xpath(clientCaseXpath)
clientCase[0].click()

clntSlctXpath = u'/html/body/div[1]/div/div[6]/div/div/form[1]/div[1]/fieldset/div/div[4]/fieldset/div[1]/div/div/ul'
clientSelection = driver.find_elements_by_xpath(clntSlctXpath)[0]
clientNames = clientSelection.text.split(u'\n')

# send a client as query
quitXpath = '/html/body/div[1]/div/div[6]/div/div/form[1]/div[1]/fieldset/div/div[4]/fieldset/div[1]/div/ul/li[1]/a'
for indexClient, clntName in enumerate(clientNames):
    if indexClient == 2:
        break
    clientCase[0].send_keys(u'{0}{1}'.format(clientNames[0], Keys.RETURN))
    time.sleep(1)
    while True:
        # get the documents ids from the dynamic table
        dynTable = driver.find_elements_by_xpath(u'/html/body/div[1]/div/div[6]/div/div/div[4]/div[5]/table/tbody')[0]
        # '/html/body/div[1]/div/div[6]/div/div/div[4]/div[3]/div/table'
        rows = dynTable.find_elements(By.TAG_NAME, "tr")
        # look at each row
        for row in rows:
            # look at the id column
            columns = row.find_elements(By.TAG_NAME, "td")
            idCol = columns[4]
            id = idCol.text
            # look of the id is in the deja vu list, otherwise download the document
            if id not in dejaVu:
                # click on the looking glass button to download the doc
                lookingGlassButton = columns[6].find_elements(By.TAG_NAME, "span")[0]
                lookingGlassButton.click()
                # response = driver.execute_script("arguments[0].click();", lookingGlassButton)
                time.sleep(1)
                # get the download links
                englishDownloadLink = driver.find_element_by_id('context-document-en')
                frenchDownloadLink = driver.find_element_by_id('context-document-fr')

                englishDownloadLink.click()
                frenchDownloadLink.click()

                # close the window in the browser
                exitButton = driver.find_elements_by_xpath(
                    '/html/body/div[1]/div/div[6]/div/div/form[1]/div[2]/div/div/div/div/button')[0]
                exitButton.click()

                # add to deja vu
                dejaVu.add(id)
                print(88888, dejaVu)
        # scroll to the bottom of the page
        driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
        # if it was not the last page of the client
        actualPage = driver.find_elements_by_xpath(
            '/html/body/div[1]/div/div[6]/div/div/div[4]/div[6]/div[1]/div[5]/span/input')[0]
        lastPage = driver.find_elements_by_xpath(
            '/html/body/div[1]/div/div[6]/div/div/div[4]/div[6]/div[1]/div[5]/span/span')[0]
        print(111111111111111, actualPage.text, lastPage.text, actualPage.text == lastPage.text)
        # if it's the last, break the loop
        if actualPage.text == lastPage.text:
            break
        # go to next page
        nextPage = driver.find_elements_by_xpath(
            u'/html/body/div[1]/div/div[6]/div/div/div[4]/div[6]/div[1]/div[7]/div[1]/span')[0]
        nextPage.click()
        time.sleep(2.5)



    # close current query before sending the next one
    ###choiceQuitButton = driver.find_elements_by_xpath(quitXpath)[0]
    ###choiceQuitButton.click()








# print the time the algorithm took to run
print(u'\nTIME IN SECONDS ::', utilsOs.countTime(startTime))

#/u/alfonsda/anaconda3/bin/geckodriver