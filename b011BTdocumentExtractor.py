#!/usr/bin/python
# -*- coding:utf-8 -*-


from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import sys, time, os, shutil
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
mimeTypes = ['text/plain', 'text/csv', 'application/csv', 'application/download', 'application/octet-stream',
             'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
             'application/pdf', 'application/vnd.wordperfect', 'application/rtf', 'application/vnd.ms-powerpoint',
             'application/vnd.openxmlformats-officedocument.presentationml.presentation', 'application/vnd.ms-excel',
             'application/vnd.oasis.opendocument.text', 'application/vnd.oasis.opendocument.spreadsheet',
             'application/vnd.oasis.opendocument.presentation', 'application/xml', 'text/xml', 'text/html',
             'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'application/x-pdf',
             'application/x-download', 'application/download']
mimeFormats = u','.join(mimeTypes)
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
    # make a list of deja vus documents
    dejavuDocs = set([])
    # click on the query case
    clientCase[0].click()
    clientCase[0].send_keys(u'{0}{1}'.format(clntName, Keys.RETURN))
    time.sleep(1)
    while True:
        # get the documents ids from the dynamic table
        try:
            dynTable = driver.find_elements_by_xpath(u'/html/body/div[1]/div/div[6]/div/div/div[4]/div[5]/table/tbody')[0]
        except IndexError:
            print('getout')
            break
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
                time.sleep(2)
                # click on the looking glass button to download the doc
                lookingGlassButton = columns[6].find_elements(By.TAG_NAME, "span")[0]
                lookingGlassButton.click()
                ### response = driver.execute_script("arguments[0].click();", lookingGlassButton)
                time.sleep(2)
                # get the en-fr or fr-en info in order to make the folder
                contextDirection = driver.find_elements_by_xpath(u'//*[@id="context-direction"]')[0]
                contextDirection = u'en-fr' if contextDirection.text == u'eng ► fra' else u'fr-en'
                # open the documents tab
                docsTab = driver.find_elements_by_xpath(u'//*[@id="documents-view-tab"]')[0]
                docsTab.click()
                # get the list of the docs names
                archivedDocs = driver.find_elements_by_xpath(u'//*[@id="documents-view"]')[0]
                listOfNames = archivedDocs.find_elements(By.TAG_NAME, u'h5')
                #prepare the list of names so we can change the name of the file
                for indexLine, nameLine in enumerate(listOfNames):
                    if u' english' in nameLine.text:
                        addLang = u'en'
                    elif u' french' in nameLine.text:
                        addLang = u'fr'
                    originalName = nameLine.text.replace(u' english', u'').replace(u' french', u'')
                    formatChange = originalName[-6:].replace(u'.', u'.{0}.'.format(addLang))
                    nameAndLang = originalName.replace(originalName[-6:], formatChange)
                    # save to the list
                    listOfNames[indexLine] = [originalName, nameAndLang]
                # get the list of download lines
                listOfDwnldNames = archivedDocs.find_elements(By.TAG_NAME, u'h6')
                # download each element if we haven't already
                for indexLine, dwnldLine in enumerate(listOfDwnldNames):
                    # if we haven't sen the file already
                    if listOfNames[indexLine][1] not in dejavuDocs:
                        # find the download button
                        dwnldButton = dwnldLine.find_elements(By.TAG_NAME, u'a')[0]
                        time.sleep(0.8)
                        dwnldButton.click()
                        # rename the downloaded file
                        oldPathAndName = u'{0}{1}'.format(tempPath, listOfNames[indexLine][0])
                        newPathAndName = u'{0}{1}'.format(tempPath, listOfNames[indexLine][1])
                        try:
                            os.rename(oldPathAndName, newPathAndName)
                            # organize the file in the right folder
                            outputFolderPath = u'{0}{1}/{2}/'.format(tempPath, clntName, contextDirection)
                            utilsOs.createEmptyFolder(outputFolderPath)
                            shutil.move(newPathAndName, u'{0}{1}'.format(outputFolderPath, listOfNames[indexLine][1]))
                            # save it to the deja vu docs list
                            dejavuDocs.add(listOfNames[indexLine][1])
                        except FileNotFoundError:
                            pass

                ##################################################33
                # get the download links
                # englishDownloadLink = driver.find_element_by_id('context-document-en')
                # frenchDownloadLink = driver.find_element_by_id('context-document-fr')
                #
                # englishDownloadLink.click()
                # frenchDownloadLink.click()
                ########################################################

                # close the window in the browser
                exitButton = driver.find_elements_by_xpath(
                    '/html/body/div[1]/div/div[6]/div/div/form[1]/div[2]/div/div/div/div/button')[0]
                exitButton.click()
                # add to deja vu
                dejaVu.add(id)
        # scroll to the bottom of the page
        driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
        # if it was not the last page of the client
        actualPage = driver.find_elements_by_xpath(
            '/html/body/div[1]/div/div[6]/div/div/div[4]/div[6]/div[1]/div[5]/span/input')[0].get_attribute('value')
        lastPage = driver.find_elements_by_xpath(
            '/html/body/div[1]/div/div[6]/div/div/div[4]/div[6]/div[1]/div[5]/span/span')[0].text
        # if it's the last, break the loop
        if actualPage == lastPage:
            break

        # go to next page
        nextPage = driver.find_elements_by_xpath(
            u'/html/body/div[1]/div/div[6]/div/div/div[4]/div[6]/div[1]/div[7]/div[1]/span')[0]
        time.sleep(2)
        nextPage.click()
        time.sleep(2.5)
    time.sleep(1.5)
    # close the finished client before selecting a new one
    quitClnt = u'/html/body/div[1]/div/div[6]/div/div/form[1]/div[1]/fieldset/div/div[4]/fieldset/div[1]/div/ul/li[1]/a'
    quitClntButton = driver.find_elements_by_xpath(quitClnt)[0]
    quitClntButton.click()
    time.sleep(1)



    # close current query before sending the next one
    ###choiceQuitButton = driver.find_elements_by_xpath(quitXpath)[0]
    ###choiceQuitButton.click()

    # wait to see the looking glass button
    ### wait = WebDriverWait(columns[6], 30)
    ### lookingGlass = wait.until(EC.element_to_be_clickable((By.TAG_NAME, "span")))
    ### lookingGlass.click()








# print the time the algorithm took to run
print(u'\nTIME IN SECONDS ::', utilsOs.countTime(startTime))

#/u/alfonsda/anaconda3/bin/geckodriver