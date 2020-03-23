#!/usr/bin/python
# -*- coding:utf-8 -*-

import sys
sys.path.append(u"../utils")
sys.path.append(u"./utils")
import re, time, datetime, random, b000path, utilsOs
from tkinter import Tk
from tkinter import TclError
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException
from selenium.webdriver.common.keys import Keys


def authentificateBtUseSelenium(user, passw, session=None):
    """
    opens a deepl session with selenium
    :param user: username string
    :param passw: password string
    :return: opened session
    """
    loginUrl = u"https://www.deepl.com/translator"
    # open session
    if session is None:
        session = webdriver.Firefox(executable_path=u"/u/alfonsda/progs/geckoDriver/geckodriver")
        session.get(loginUrl)
    time.sleep(random.uniform(0.5, 1.8))
    # click on the login button
    logInButton = session.find_element_by_xpath(u'/html/body/header/nav/div/div[3]/div[1]/button')
    logInButton.click()
    # fill fields
    userId = session.find_element_by_xpath(u'//*[@id="login_email"]')
    userId.send_keys(user)
    time.sleep(random.uniform(0.1, 0.7))
    password = session.find_element_by_xpath(u'//*[@id="login_password"]')
    password.send_keys(passw)
    time.sleep(random.uniform(0.7, 1.7))
    # unclick the remember me checkbox
    rememberMeCheckBox = session.find_element_by_xpath(u'/html/body/div[1]/div[2]/div[1]/div/form/div[3]/label/span[1]')
    rememberMeCheckBox.click()
    time.sleep(random.uniform(0.3, 0.9))
    # log in
    enterButton = session.find_element_by_xpath(u'/html/body/div[1]/div[2]/div[1]/div/form/button')
    enterButton.click()
    time.sleep(random.uniform(1.2, 2.0))
    return session

def langSelectClicker(session, langSelectXpath, langOptionXpath):
    # click on the language selector
    langSelector = session.find_element_by_xpath(langSelectXpath)
    langSelector.click()
    time.sleep(random.uniform(0.7, 1.1))
    # click on the english language option
    lang = session.find_element_by_xpath(langOptionXpath)
    lang.click()
    time.sleep(random.uniform(0.9, 1.5))
    return session


def selectLangDeepL(session, srcLang=u'en'):
    """
    given a language and its classification as src or trgt
    selects the right language for the combination en-fr or fr-en
    :param session: selenium opened session
    :param srcLang: language to click on as source
    :return: session: selenium session with the selection made
    """
    srcLangSelectXpath = u"/html/body/div[2]/div[1]/div[1]/div[2]/div[1]/div/button/div"
    trgtLangSelectXpath = u"/html/body/div[2]/div[1]/div[1]/div[3]/div[1]/div/button/div"
    if srcLang == u"en":
        srcXpath = u"//div[2]/div[1]/div/div/button[@dl-value='EN']"
        trgtXpath = u"//div[3]/div[1]/div/div/button[@dl-value='FR']"
    elif srcLang == u"fr":
        srcXpath = u"//div[2]/div[1]/div/div/button[@dl-value='FR']"
        trgtXpath = u"//div[3]/div[1]/div/div/button[@dl-value='EN']"
    # select language for the source
    session = langSelectClicker(session, srcLangSelectXpath, srcXpath)
    # select language for the target
    session = langSelectClicker(session, trgtLangSelectXpath, trgtXpath)
    return session


def translateOneLang(session, srcLang, langSent, nbTok, translAndAlt):
    # select english as source in deepL
    session = selectLangDeepL(session, srcLang)
    # click on the source text area and paste the english sentence
    textArea = session.find_element_by_xpath(u"/html/body/div[2]/div[1]/div[1]/div[2]/div[2]/div/textarea")
    textArea.click()
    time.sleep(random.uniform(0.4, 0.9))
    textArea.clear()
    textArea.send_keys(langSent)
    time.sleep(random.uniform(nbTok/4.0, nbTok/2.0))
    # click on the copy to clipboard button to copy the target text
    try:
        cpButton = session.find_element_by_xpath(u"/html/body/div[2]/div[1]/div[1]/div[3]/div[3]/div[3]/div[1]/button")
    except NoSuchElementException:
        time.sleep(random.uniform(2.0, 5.0))
        cpButton = session.find_element_by_xpath(u"/html/body/div[2]/div[1]/div[1]/div[3]/div[3]/div[3]/div[1]/button")
    time.sleep(random.uniform(0.2, 0.7))
    # if the button is viewable, click
    try:
        cpButton.click()
    # otherwise scroll down before clicking
    except ElementClickInterceptedException:
        # Scroll down to bottom
        session.execute_script('window.scrollTo(0, document.body.scrollHeight);')
        cpButton.click()
    mainTransl = None
    # close the tkinter window
    tkinterRoot = Tk()
    tkinterRoot.withdraw()
    while mainTransl is None:
        time.sleep(random.uniform(0.5, 0.8))
        cpButton.click()
        time.sleep(random.uniform(1.2, 1.9))
        try:
            mainTransl = tkinterRoot.clipboard_get()
            break
        except TclError:
            pass
    # get the text from the clipboard
    mainTransl = tkinterRoot.clipboard_get()
    translAndAlt.append(mainTransl)
    # look for alternative translations
    for n in range(2, 10):
        try:
            alt = session.find_element_by_xpath(
                u"/html/body/div[2]/div[1]/div[1]/div[3]/div[3]/div[2]/p[{0}]/button[1]".format(n))
            translAndAlt.append(alt)
        except NoSuchElementException:
            break
    # get time stamp
    timeStamp = time.time()
    # delete the content of the text area
    textArea.click()
    time.sleep(random.uniform(0.3, 0.6))
    textArea.clear()
    return session, translAndAlt, timeStamp


def translateSpGetResult(session, sp):
    """
    given an sp, goes to deepl to translate it and returns the results
    :param session: opened session with selenium
    :param sp: an array of 2, containing the sentence pair in english and french
    :return: nbOfTok: number of total tokens translated
    :return: enFrTranslAndAlt: list of strings containing the translation from english to french
    :return: frEnTranslAndAlt: list of strings containing the translation from french to english
    """
    enFrTranslAndAlt, frEnTranslAndAlt = [], []
    # count the number of tokens in each sentence of the sp
    nbTokEn = len(sp[0].split(u" "))
    nbTokFr = len(sp[1].split(u" "))
    nbOfTok = nbTokEn + nbTokFr
    # translate from english to french
    session, enFrTranslAndAlt, timeStampEn = translateOneLang(session, u"en", sp[0], nbTokEn, enFrTranslAndAlt)
    # translate from french to english
    session, frEnTranslAndAlt, timeStampFr = translateOneLang(session, u"fr", sp[1], nbTokFr, frEnTranslAndAlt)
    # translate from french to english
    return session, nbOfTok, enFrTranslAndAlt, frEnTranslAndAlt, timeStampEn, timeStampFr


def makeARefFile(rootFolder=u"/data/rali8/Tmp/rali/bt/burtrad/corpus_renamed/",
                 refFilePath=u"/data/rali5/Tmp/alfonsda/workRali/004tradBureau/017deepLTranslatedCorpus/trRef"):
    # make sure the files does not yet exists
    if utilsOs.theFileExists(refFilePath) is True:
        return None
    utilsOs.createEmptyFile(refFilePath)
    listOfFiles = utilsOs.goDeepGetFiles(u"/data/rali8/Tmp/rali/bt/burtrad/corpus_renamed/", format=u".tmx.en")
    with open(refFilePath, u"a") as refFile:
        for filePath in listOfFiles:
            refFile.write(u"{0}\t-1\n".format(filePath.replace(u".tmx.en", u".tmx")))


def getANewSpWhereWeLeftOff(refPath=u"/data/rali5/Tmp/alfonsda/workRali/004tradBureau/017deepLTranslatedCorpus/trRef"):
    # check if the ref file already exists
    if utilsOs.theFileExists(refPath) is False:
        utilsOs.createEmptyFile(refPath)
    # open the reference file
    lastSeenIndex, lastSeenPath = None, None
    with open(refPath) as ref:
        # first line
        refLns = ref.readlines()
        refIndex = 0
        for refLn in refLns:
            refList = refLn.replace(u"\n", u"").split(u"\t")
            # test if we have an index for the path
            try:
                lastSeenIndex = int(refList[1])
                lastSeenPath = refList[0]
                break
            # if there is no integral, then it saw all lns for that path
            except ValueError:
                pass
            # next ref index
            refIndex += 1
    # open the last seen file at the (last seen index + 1) and return the sp in the en and fr files
    if lastSeenIndex is None:
        return None
    with open(u"{0}.en".format(lastSeenPath)) as enFile:
        with open(u"{0}.fr".format(lastSeenPath)) as frFile:
            enLn = enFile.readline()
            frLn = frFile.readline()
            indexLn = 0
            while enLn:
                if indexLn == lastSeenIndex+1:
                    # replace the line with its next index and dump the ref file
                    refLns[refIndex] = u"{0}\t{1}\n".format(lastSeenPath, indexLn)
                    # return the sentence pair
                    return [enLn.replace(u"\n", u""), frLn.replace(u"\n", u"")], lastSeenPath, indexLn, refLns
                # next line
                enLn = enFile.readline()
                frLn = frFile.readline()
                indexLn += 1
    # if we went over the whole document and it ended, change the ref line, dump it and start over
    refLns[refIndex] = u"{0}\tdone\n".format(lastSeenPath)
    utilsOs.dumpRawLines(refLns, refPath, addNewline=False, rewrite=True)
    return getANewSpWhereWeLeftOff(refPath)


def transformTimeToLocalTime(sTime):
    return datetime.datetime.fromtimestamp(sTime).strftime('%Y-%m-%d %H:%M:%S')


def launchForOneDay(tokLimit=4000,
                    outputFolderPath=u"/data/rali5/Tmp/alfonsda/workRali/004tradBureau/017deepLTranslatedCorpus/",
                    coffeeBreak=1650):
    """
    launches the deepL bot for one day's worth
    :param tokLimit: maximum number of tokens to treat in the day
    :param outputFolderPath: path to the folder where will be output the files

    :param coffeeBreak: time in seconds when to take a break and start a new deppL session
    :return: tokCount: number of total tokens translated
    """
    start = utilsOs.countTime()
    # path to the referencer, indicating where we left off: path and last index worked
    referencerPath = u"/data/rali5/Tmp/alfonsda/workRali/004tradBureau/017deepLTranslatedCorpus/trRef"
    # info
    deepLUrl = u"https://www.deepl.com/translator"
    mUser, mPass, sUser, sPass = b000path.getDeepLProfileInfo()
    # for each user
    for user, passw in zip([sUser, mUser], [sPass, mPass]):
        tokCount = 0
        # open the driver
        session = webdriver.Firefox()
        session.get(deepLUrl)
        time.sleep(random.uniform(1.3, 3.1))
        # log to deepL
        session = authentificateBtUseSelenium(user, passw, session)
        # while we have not gone over the daily limit
        iterCount = 0
        while tokCount < (tokLimit-10):
            # get the sp
            sp, filePath, fileIndex, refLns = getANewSpWhereWeLeftOff(referencerPath)
            session, nbOfTok, enFrTranslAndAlt, frEnTranslAndAlt, timeEn, timeFr = translateSpGetResult(session, sp)
            # dump the referencer lines
            utilsOs.dumpRawLines(refLns, referencerPath, addNewline=False, rewrite=True)
            # dump original sp
            utilsOs.appendLineToFile(sp[0], u"{0}originalSent.en".format(outputFolderPath), addNewLine=True)
            utilsOs.appendLineToFile(sp[1], u"{0}originalSent.fr".format(outputFolderPath), addNewLine=True)
            # dump translation and variants
            utilsOs.appendLineToFile(enFrTranslAndAlt, u"{0}translated.en2fr".format(outputFolderPath), addNewLine=True)
            utilsOs.appendLineToFile(frEnTranslAndAlt, u"{0}translated.fr2en".format(outputFolderPath), addNewLine=True)
            # dump reference
            utilsOs.appendLineToFile(u"{0}\t{1}\n".format(filePath, fileIndex),
                                     u"{0}reference.tsv".format(outputFolderPath), addNewLine=False)
            # dump timestamp
            utilsOs.appendLineToFile(u"{0}\tlocal time: {1}".format(timeEn, transformTimeToLocalTime(timeEn)),
                                     u"{0}timestamp.en".format(outputFolderPath), addNewLine=True)
            utilsOs.appendLineToFile(u"{0}\tlocal time: {1}".format(timeFr, transformTimeToLocalTime(timeFr)),
                                     u"{0}timestamp.fr".format(outputFolderPath), addNewLine=True)
            # add number of tokens
            tokCount += nbOfTok
            # add nb of iterations
            iterCount += 1
            # take a coffee break if it's time
            if coffeeBreak is not None and utilsOs.countTime(start) >= coffeeBreak:
                session.close()
                time.sleep(random.uniform(60, 80))
                start = utilsOs.countTime()
                # open the driver
                session = webdriver.Firefox()
                session.get(deepLUrl)
                time.sleep(random.uniform(1.3, 3.1))
                # log to deepL
                session = authentificateBtUseSelenium(user, passw, session)
            time.sleep(random.uniform(1.0, 1.5))
        # close the driver
        session.close()
        time.sleep(random.uniform(10.0, 15.0))
    return tokCount, iterCount


def launchForOneWeek(tokLimit=20000,
                     outputFolderPath=u"/data/rali5/Tmp/alfonsda/workRali/004tradBureau/017deepLTranslatedCorpus/",
                     coffeeBreak=1650):
    """
    launches the one day launch during the business days of the week
    :param tokLimit: maximum number of tokens to translate
    :param outputFolderPath:
    :param coffeeBreak:
    :return: totalTokCount: total number of translated tokens
    """
    dailyTokLimit = int(tokLimit/5.0)
    totalTokCount = 0
    # take note of the launch day
    launchDay = datetime.datetime.today().weekday()
    today = None
    while today != launchDay:
        # launch only on business days
        if today not in [2, 4]: # not on wednesdays / fridays[2, 4] # not on weekends : [5, 6]
            # launch between 22h and 8h
            actualHour = datetime.datetime.today().hour
            while actualHour not in [22, 23, 24, 0, 1, 2, 3, 4, 5, 6, 7, 8]:
                time.sleep(random.randint(3600, 7200))
                actualHour = datetime.datetime.today().hour
                # break the loop if we barely exceeded the hour
                if actualHour in [9, 10]:
                    break
            # launch for one day
            tokCount, lnCount = launchForOneDay(dailyTokLimit, outputFolderPath, coffeeBreak)
            # break the loop if we do more than the limit
            totalTokCount += tokCount
            if totalTokCount >= tokLimit:
                break
            # print the day nb and the number of lines translated
            print(u"\nday : ", datetime.datetime.today().weekday(), u"lines translated : ", lnCount)
        # wait for approx one day (btw 22 and 25 hours)
        time.sleep(random.randint(79200, 90000))
        # get what day is today
        today = datetime.datetime.today().weekday()
    return totalTokCount


def launchForACorpusDeepL(inPath, outPath=None, continueWhereWeLeftOf=True):
    outPath = outPath if outPath is not None else re.sub(r"[._]en", ".fr2en", re.sub(r"[._]en", ".en2fr", inPath))
    with open(inPath) as cn10k:
        if continueWhereWeLeftOf is not True:
            with open(outPath, "w") as out10k:
                out10k.write("")
                lastSeenInd = float("-inf")
        else:
            with open(outPath) as out10k:
                lastSeenInd = 0
                ouLn = out10k.readline()
                while ouLn:
                    lastSeenInd += 1
                    ouLn = out10k.readline()
        with open(outPath, "a") as out10k:
            session = webdriver.Firefox(executable_path=u"/u/alfonsda/progs/geckoDriver/geckodriver")
            session.get("https://www.deepl.com/translator")
            counter = 0
            cnLn = cn10k.readline()
            start = utilsOs.countTime()
            while cnLn:
                if counter >= lastSeenInd:
                    cnLn = cnLn.replace("\n", "")
                    session, enFrTranslAndAlt, timeStampEn = translateOneLang(session, u"en", cnLn,
                                                                              len(cnLn.split(" ")), [])
                    out10k.write("{0}\n".format(enFrTranslAndAlt[0]))
                    # take a coffee break if it's time
                    if utilsOs.countTime(start) >= 600:
                        session.close()
                        time.sleep(random.uniform(20, 60))
                        start = utilsOs.countTime()
                        # open the driver
                        try:
                            session = webdriver.Firefox()
                        except OSError:
                            time.sleep(600)
                            session = webdriver.Firefox()
                        session.get("https://www.deepl.com/translator")
                # next
                cnLn = cn10k.readline()
                counter += 1
    session.close()


def chooseLangGoogleTrans(session):
    # choose english
    langChoice = session.find_element_by_xpath(
        "/html/body/div[2]/div[2]/div[1]/div[2]/div[1]/div[1]/div[1]/div[1]/div[1]/div[3]")
    langChoice.click()
    time.sleep(0.2)
    textArea = session.find_element_by_xpath('//*[@id="sl_list-search-box"]')
    textArea.click()
    time.sleep(0.2)
    textArea.send_keys("english")
    srcLang = session.find_element_by_xpath(
        "/html/body/div[2]/div[2]/div[3]/div/div[2]/div[1]/div[3]/div[21]/div[2]/div/b")
    srcLang.click()
    time.sleep(0.2)
    # choose french
    langChoice = session.find_element_by_xpath(
        "/html/body/div[2]/div[2]/div[1]/div[2]/div[1]/div[1]/div[1]/div[1]/div[4]/div[3]")
    langChoice.click()
    time.sleep(0.2)
    textArea = session.find_element_by_xpath('//*[@id="tl_list-search-box"]')
    textArea.click()
    time.sleep(0.2)
    textArea.send_keys("french")
    trgtLang = session.find_element_by_xpath(
        "/html/body/div[2]/div[2]/div[3]/div/div[2]/div[2]/div[3]/div[27]/div[2]/div")
    trgtLang.click()
    return session


def writeSrcGetTrgt(session, srcString):
    # send src text
    srcTextArea = session.find_element_by_xpath('//*[@id="source"]')
    srcTextArea.click()
    time.sleep(0.2)
    srcTextArea.send_keys(srcString)
    srcTextArea.send_keys(Keys.ENTER)
    time.sleep(random.uniform(0.7, 1.0))
    # get trgt (translation)
    try:
        trgtTextArea = session.find_element_by_xpath(
            "/html/body/div[2]/div[2]/div[1]/div[2]/div[1]/div[1]/div[2]/div[3]/div[1]/div[2]/div/span[1]")
        translation = trgtTextArea.text
        time.sleep(random.uniform(0.4, 0.6))
    except NoSuchElementException:
        try:
            trgtTextArea = session.find_element_by_xpath(
                "/html/body/div[2]/div[2]/div[1]/div[2]/div[1]/div[1]/div[2]/div[3]/div[1]/div[2]/div/span[1]/span")
            translation = trgtTextArea.text
            time.sleep(random.uniform(0.4, 0.6))
        except NoSuchElementException:
            translation = ""
            for n in range(1, 10):
                trgtTextArea = session.find_element_by_xpath(
                    "/html/body/div[2]/div[2]/div[1]/div[2]/div[1]/div[1]/div[2]/div[3]/div[1]/div[2]/div/span[1]/span[{0}]".format(n))
                translation += "{0} ".format(trgtTextArea.text)
            translation = translation[:-1]
    srcTextArea.clear()
    return translation, session


def launchForACorpusGoogle(inPath, outPath=None, continueWhereWeLeftOf=True):
    outPath = outPath if outPath is not None else re.sub(r"[._]en", ".fr2en", re.sub(r"[._]en", ".en2fr", inPath))
    with open(inPath) as cn10k:
        if continueWhereWeLeftOf is not True:
            with open(outPath, "w") as out10k:
                out10k.write("")
                lastSeenInd = float("-inf")
        else:
            with open(outPath) as out10k:
                lastSeenInd = 0
                ouLn = out10k.readline()
                while ouLn:
                    lastSeenInd += 1
                    ouLn = out10k.readline()
        with open(outPath, "a") as out10k:
            session = webdriver.Firefox(executable_path=u"/u/alfonsda/progs/geckoDriver/geckodriver")
            session.get("https://translate.google.ca/")
            counter = 0
            cnLn = cn10k.readline()
            start = utilsOs.countTime()
            while cnLn:
                if counter >= lastSeenInd:
                    cnLn = cnLn.replace("\n", "")

                    session = chooseLangGoogleTrans(session)
                    translation, session = writeSrcGetTrgt(session, cnLn)
                    out10k.write("{0}\n".format(translation))
                    # take a coffee break if it's time
                    if utilsOs.countTime(start) >= 600:
                        session.close()
                        time.sleep(random.uniform(20, 60))
                        start = utilsOs.countTime()
                        # open the driver
                        try:
                            session = webdriver.Firefox(executable_path=u"/u/alfonsda/progs/geckoDriver/geckodriver")
                        except OSError:
                            time.sleep(600)
                            session = webdriver.Firefox(executable_path=u"/u/alfonsda/progs/geckoDriver/geckodriver")
                        session.get("https://translate.google.ca/")
                # next
                cnLn = cn10k.readline()
                counter += 1
    session.close()


# count the time the algorithm takes to run
startTime = utilsOs.countTime()

# start a reference list
# makeARefFile()

# launch downloader for one day
# launchForOneDay(tokLimit=4000,
#                 outputFolderPath=u"/data/rali5/Tmp/alfonsda/workRali/004tradBureau/017deepLTranslatedCorpus/")

# # launch downloader for one week
# launchForOneWeek(tokLimit=20000,
#                  outputFolderPath=u"/data/rali5/Tmp/alfonsda/workRali/004tradBureau/017deepLTranslatedCorpus/",
#                  coffeeBreak=1650)

#######################
# # launch downloader until stopped
# while True:
#     launchForOneWeek(tokLimit=20000,
#                      outputFolderPath=u"/data/rali5/Tmp/alfonsda/workRali/004tradBureau/017deepLTranslatedCorpus/",
#                      coffeeBreak=1650)
########################

# translate 10k sentences as test set for shiv 2nd article
# time.sleep(10000)
# # with DEEPL
# inPath = "/data/rali5/Tmp/alfonsda/workRali/004tradBureau/017.2nonBTdeepLTranslatedCorpus/CN_parliament_all_DeepL.en"
# outPath = "/data/rali5/Tmp/alfonsda/workRali/004tradBureau/017.2nonBTdeepLTranslatedCorpus/CN_parliament_all_DeepL.en2fr"
# launchForACorpusDeepL(inPath, outPath, continueWhereWeLeftOf=True)
# with GOOGLE
inPath = "/data/rali5/Tmp/alfonsda/workRali/004tradBureau/017.2nonBTdeepLTranslatedCorpus/CN_parliament_all_DeepL.en"
outPath = "/data/rali5/Tmp/alfonsda/workRali/004tradBureau/017.2nonBTdeepLTranslatedCorpus/CN_parliament_all_GoogleTranslate.en2fr"
launchForACorpusGoogle(inPath, outPath, continueWhereWeLeftOf=True)


# print the time the algorithm took to run
print(u'\nTIME IN SECONDS ::', utilsOs.countTime(startTime))

# REMINDER : weekMax = 20000 words, shiv = 2k words/day, michel=2k words/day, free = 5000 char



