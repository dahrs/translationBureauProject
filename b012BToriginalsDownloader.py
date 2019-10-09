#!/usr/bin/python
# -*- coding:utf-8 -*-

import requests, urllib3, ssl, certifi, getpass
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import sys, time, os, shutil, json
from tqdm import tqdm
import b000path
sys.path.append(u'../utils')
sys.path.append(u'./utils')
import utilsOs, utilsString



def getUup(path=u'./b011pathUserPassword'):
    # get url, user and password
    with open(path) as uup:
        url = uup.readline().replace(u'\n', u'')
        user = uup.readline().replace(u'\n', u'')
        passw = uup.readline().replace(u'\n', u'')
    return url, user, passw


def authentificateBtUseRequests():
    baseUrl, user, passw = getUup(path=u'./b011pathUserPassword')
    loginUrl = baseUrl.replace(u'/en', u'/session/en')
    headers = {
        u'user-agent': u'Mozilla/5.0 (X11; Linux x86_64; rv:67.0) Gecko/20100101 Firefox/67.0'
    }
    loginData = {
        u'LoginForm[username]': user,
        u'LoginForm[password]': passw,
        u'yt0': u'Login',
        u'LoginForm[rememberMe]': '0'
    }
    session = requests.Session()
    req = session.post(loginUrl, data=loginData, headers=headers, verify=False)
    return session, req


def fillForm(clientId, documentSent, session, lang=u'fr'):
    if type(clientId) is str:
        clientId = str(int(clientId[:3]))
    data = {u'query': documentSent, u'_meta_client_code': clientId, u'sourceLanguage': lang}
    req = session.post(u'https://recherchebitexte-bitextsearch.btb.gc.ca/site/search', data=data, verify=False)
    return req.json()


def scrapLookingGlassForUrls(reqJson, session):
    sgmntId = reqJson['rows'][0][u'cell'][6][u'id']
    requestNb = reqJson['rows'][0][u'cell'][6][u'brn']
    memoryId = reqJson['rows'][0][u'cell'][6][u'memoryID']
    docName = reqJson['rows'][0][u'cell'][6][u'docname']
    lookingGlassPanelData = {
        u'segment_id': sgmntId,
        u'locale': u'en-ca',
        u'source_language': u'fr',
        u'request_number': requestNb,
        u'document_number': u'NaN',
        u'memory_id': memoryId,
        u'document_name': docName
    }
    req = session.post(u'https://recherchebitexte-bitextsearch.btb.gc.ca/site/bitext',
                       data=lookingGlassPanelData, verify=False)
    try:
        urlEn = u'https://recherchebitexte-bitextsearch.btb.gc.ca/{0}'.format(req.json()['meta_en'])
        urlFr = u'https://recherchebitexte-bitextsearch.btb.gc.ca/{0}'.format(req.json()['meta_fr'])
        return urlEn, urlFr
    # if there is no metadata-en/fr
    except KeyError:
        return None, None
    # if we cannot click on the looking glass (ie: {'page': None, 'total': '1', 'totalFormatted': '1', 'time': '0,1299', 'rows': [{'id': '153291498', 'cell': [1, 'En 2016, les exportations d’huile et de graines de canola canadien représentaient presque 15 pour 100 des exportations totales de produits agricoles et alimentaires, estimées à 9,2 milliards de dollars.', 'In 2016, Canadian canola seed and oil exports accounted for almost 15 per cent of total agriculture and food exports, valued at $9.2 billion.', '351 - ', '9896427', 'eng &#9658; fra', {'brn': '9896427', 'id': '153291498', 'docname': '9896426_001_EN_180829-26 - AAFCAAC-#104278255-v3-News_Release_-_Canola_Cluster_-_MB__;243908 - E.docx', 'memoryID': '1240675'}, None, '1240675', '2019-01-30 18:32:38', '2019-01-30 18:32:38', None]}]})
    except json.decoder.JSONDecodeError:
        return None, None


def getLongerSentence(fPath, lang):
    longerSent = [u'', 0]
    with open(u'{0}.{1}'.format(fPath, lang)) as langFile:
        # look for the longer sentence or at least one with more than 100 char
        for ln in langFile.readlines():
            if len(ln) > 100:
                longerSent = [ln, len(ln)]
                break
            elif len(ln) > longerSent[1]:
                longerSent = [ln, len(ln)]
    return longerSent


def getLongerSentences(fPath, lang):
    eachSent = [u'', 0]
    longerSents = [list(eachSent)]
    with open(u'{0}.{1}'.format(fPath, lang)) as langFile:
        # look for the longer sentence or at least one with more than 100 char
        for ln in langFile.readlines():
            if len(ln) > 100 :
                longerSents = [[ln, len(ln)]] + longerSents[:2]
                if len(longerSents) == 3 and longerSents[-1][1] > 30:
                    break
            elif len(ln) > longerSents[0][1]:
                longerSents = [[ln, len(ln)]] + longerSents[:2]
    return longerSents


def getClientName(fPath):
    clientDict = {"0": "000 - Swine Flu", "1": "001 - Agriculture and Agri-Food Canada",
                  "2": "002 - Canadian Nuclear Safety Commission", "3": "003 - Office of the Auditor General of Canada",
                  "4": "004 - The Jacques Cartier and Champlain Bridges Incorporated",
                  "5": "005 - Canadian International Development Agency", "6": "006 - City Of Ottawa",
                  "7": "007 - Gordon Creative Group", "8": "008 - Canada China Business Council", "9": "009 - CRTC",
                  "10": "010 - Correctional Service of Canada",
                  "11": "011 - Edmonton 2001 World Championships In Athletics", "12": "012 - Elections Canada",
                  "13": "013 - Commissioner of Official Languages", "15": "015 - French For The Future",
                  "16": "016 - Disabilities Plus",
                  "18": "018 - Association Of Professional Executives Of The Public Service Of Canada",
                  "19": "019 - Canada - British Columbia Business Service Centre", "20": "020 - Toronto City Hall",
                  "21": "021 - Canadian Forces Grievance Board", "22": "022 - Natural Resources Canada",
                  "23": "023 - Environment Canada", "24": "024 - Foreign Affairs and International Trade Canada",
                  "25": "025 - Canadian Foundation For Innovation", "26": "026 - Courts Administration Service",
                  "27": "027 - Fraser River Estuary Management Program", "28": "028 - Victoria Airport Authority",
                  "29": "029 - Governor General of Canada", "30": "030 - House Of Commons",
                  "31": "031 - Parliament - Cost-Recovery Services", "32": "032 - Indian and Northern Affairs Canada",
                  "33": "033 - The Queen's Royal Hussars", "34": "034 - Marbek Resource Consultant",
                  "35": "035 - Office Of The Superintendant Of Financial Institutions",
                  "36": "036 - International Joint Commission", "37": "037 - Justice Canada",
                  "39": "039 - Ibis Research Inc.", "40": "040 - Human Resources and Skills Development Canada",
                  "41": "041 - Toronto Olympic Bid Committee", "42": "042 - National Arts Centre (Corporation Of The)",
                  "43": "043 - National Capital Commission", "44": "044 - National Defence",
                  "45": "045 - National Energy Board", "46": "046 - National Film Board of Canada",
                  "47": "047 - Health Canada", "48": "048 - National Library Of Canada",
                  "49": "049 - Military Police Complaints Commission", "50": "050 - National Parole Board",
                  "51": "051 - National Research Council Canada", "52": "052 - Canadian Tourism Commission",
                  "53": "053 - Ogilvie And Hogg, Desnoyers Mercure Et Associates",
                  "54": "054 - Canadian Union Of Postal Workers", "55": "055 - Canada Post Corporation",
                  "56": "056 - Privy Council Office", "57": "057 - Library and Archives Canada",
                  "58": "058 - Public Service Commission of Canada",
                  "59": "059 - Public Service Labour Relations Board",
                  "60": "060 - Canadian High Artic Research Station/polar Knowledge Canada (Polar)",
                  "61": "061 - Centre For Curriculum, Transfer And Technology (C2T2)",
                  "62": "062 - Royal Canadian Mint", "63": "063 - Royal Canadian Mounted Police",
                  "64": "064 - Taylor & Associates (1989) Inc.", "65": "065 - Government of the Northwest Territories",
                  "66": "066 - FINTRAC", "68": "068 - Senate", "69": "069 - Public Safety Canada",
                  "70": "070 - Statistics Canada", "71": "071 - Laval University",
                  "72": "072 - Supreme Court of Canada", "73": "073 - Computer For Schools Ontario",
                  "74": "074 - Tax Court Of Canada (The)", "75": "075 - Transport Canada",
                  "76": "076 - Institute Of Peace And Conflict Studies (Ong)", "77": "077 - Bc Buildings Corporation",
                  "78": "078 - The Public Review Commission", "79": "079 - Veterans Affairs Canada",
                  "80": "080 - Canada Council On The Arts", "81": "081 - Export Development Canada",
                  "82": "082 - Radio Advisory Board Of Canada", "83": "083 - Wallace And Associates",
                  "84": "084 - Labour Relations, Personnel Administration Office", "85": "085 - Montreal's Airports",
                  "86": "086 - Guelph University", "87": "087 - Society - Gulf Of Georgia Cannery (Non-Govt. Acct.)",
                  "88": "088 - Translation Services Branch", "89": "089 - Canadian Seed Institute",
                  "90": "090 - Financial Consumer Agency of Canada", "91": "091 - Department Of Family And Childhood",
                  "92": "092 - Bank of Canada", "93": "093 - International Development Research Centre",
                  "94": "094 - Council of Atlantic Premiers", "95": "095 - International Labour Organization",
                  "96": "096 - Canadian Manufacturers And Exporters",
                  "97": "097 - Legal Translation And Terminology Centre Faculty Of Law Moncton Universit",
                  "98": "098 - Canada Mortgage And Housing Corporation",
                  "99": "099 - Canadian International Trade Tribunal",
                  "100": "100 - Foreign Affairs and International Trade Canada",
                  "101": "101 - Horizon Zero, The Banff Centre", "102": "102 - Atomic Energy of Canada Limited",
                  "103": "103 - The Industrial Accident Prevention Association Iapa", "104": "104 - Passport Canada",
                  "105": "105 - Infrastructure Canada", "106": "106 - Canadian Commercial Corporation",
                  "107": "107 - La Societe Hotesse Des Jeux D'hiver Du Canada Acadie Bathurst",
                  "108": "108 - Sustainable Forest Management Network", "109": "109 - Canadian Dairy Commission",
                  "110": "110 - City Of Gatineau", "111": "111 - information_police canadienne",
                  "112": "112 - Canada Public Service Agency", "113": "113 - Canadian Judicial Council",
                  "114": "114 - Teleglobe Canada", "115": "115 - Canada Infrastructure Bank",
                  "116": "116 - Canada Firearms Centre", "117": "117 - Action Canada",
                  "118": "118 - Canadian Council of Ministers of the Environment", "119": "119 - Canadian Wheat Board",
                  "120": "120 - Monitoring And Assessment Of Biodiversity Program-Smithsonian Institution",
                  "121": "121 - Canadian Broadcasting Corporation", "122": "122 - City of Hamilton",
                  "123": "123 - Canadian Association On Water Quality", "124": "124 - Saskatoon Airport Authority",
                  "125": "125 - Indian Residential Schools Resolution Canada",
                  "126": "126 - Canada School Of Public Service", "127": "127 - Canadian Coast Guard",
                  "128": "128 - Canada Border Services Agency", "129": "129 - Médecins Sans Frontieres",
                  "130": "130 - Canadian Ice Service", "131": "131 - Quebec Federal Board",
                  "132": "132 - Foreign Affairs and International Trade Canada", "133": "133 - Canadian Ice Service",
                  "134": "134 - Gros Morne Institute Of Sustainable Tourism", "135": "135 - Downsview Park",
                  "136": "136 - Sadc Du Rocher-Percé",
                  "137": "137 - Town Of Petawawa (Ottawa River Heritage Designation Committee)",
                  "138": "138 - Immersion Studios Inc.", "139": "139 - Conseils_aux_voyageurs",
                  "140": "140 - Human Resources and Skills Development Canada",
                  "141": "141 - Cannor-Canadian Northern Economic Development Agency",
                  "143": "143 - The Business Development Bank Of Canada", "144": "144 - DND Non Public Funds Agencies",
                  "146": "146 - Public Health Agency of Canada", "147": "147 - Canadian Institutes of Health Research",
                  "148": "148 - Assisted Human Reproduction Canada",
                  "150": "150 - Administrative Tribunals Support Service Of Canada (Atssc)",
                  "151": "151 - National Farm Products Council", "170": "170 - Royal Society Of Canada",
                  "174": "174 - Standards Council Of Canada", "180": "180 - Invest In Canada Hub",
                  "184": "184 - Canada Industrial Relations Board",
                  "185": "185 - Canadian Intergovernmental Conference Secretariat",
                  "192": "192 - National Security And Intelligence Committee Of Parliamentarians (Nsicop)",
                  "200": "200 - Status of Women Canada", "201": "201 - Canadian Human Rights Commission",
                  "208": "208 - Northern Pipeline Agency", "213": "213 - Social Sciences And Humanities Research",
                  "217": "217 - Office of the Commissioner for Federal Judicial Affairs", "222": "222 - COSEPAC",
                  "227": "227 - Fisheries and Oceans Canada", "232": "232 - Indigenous Services Canada",
                  "240": "240 - Canadian Grain Commission",
                  "241": "241 - Canadian Centre for Occupational Health and Safety",
                  "244": "244 - Dnd Interpretation Services", "250": "250 - Government Of Saskatchewan",
                  "256": "256 - Province of Alberta", "257": "257 - Elections Alberta",
                  "266": "266 - Natural Sciences and Engineering Research Council of Canada",
                  "270": "270 - Information Commissioner", "277": "277 - Fisheries And Oceans - Lionbridge",
                  "279": "279 - Transportation Safety Board of Canada", "281": "281 - The Service",
                  "282": "282 - Grain Transportation Agency", "283": "283 - Security And Intelligence Review Committee",
                  "289": "289 - Via Rail Canada Inc.", "299": "299 - Library Of Parliament",
                  "300": "300 - Canadian Institute For Health Information",
                  "301": "301 - The Royal College Of Physicians And Surgeons Of Canada",
                  "302": "302 - Ship-source Oil Pollution Fund",
                  "303": "303 - Transportation Appeal Tribunal of Canada", "304": "304 - Competition Tribunal",
                  "305": "305 - Royal Canadian Mounted Police External Review Committee",
                  "306": "306 - Canadian Air Transport Security Authority",
                  "307": "307 - Meteorological Service Of Canada",
                  "308": "308 - Canada-Newfoundland Offshore Petroleum Board",
                  "309": "309 - Hazardous Materials Information Review Commission",
                  "310": "310 - Patented Medicine Prices Review Board",
                  "311": "311 - Canadian Breast Cancer Research Alliance",
                  "312": "312 - Canadian Transportation Agency", "313": "313 - Immigration and Refugee Board of Canada",
                  "314": "314 - Atlantic Canada Opportunities Agency",
                  "315": "315 - Blue Water Bridge Authority (Bwba)",
                  "316": "316 - Commission for Public Complaints Against the RCMP",
                  "317": "317 - Canadian Council on Health Services Accreditation",
                  "318": "318 - Western Economic Diversification Canada", "320": "320 - Marine Atlantic Inc.",
                  "321": "321 - Brent Moore & Associates Inc.", "323": "323 - Theratronics International Ltd",
                  "324": "324 - Canada School of Public Service", "329": "329 - Copyright Board",
                  "330": "330 - Industry Canada", "332": "332 - Canadian Space Agency",
                  "333": "333 - Canadian Food Inspection Agency",
                  "336": "336 - Communications Security Establishment Canada", "337": "337 - NAFTA",
                  "338": "338 - Emergency Preparedness Canada", "344": "344 - Treasury Board of Canada Secretariat",
                  "345": "345 - Canada Economic Development for Quebec regions",
                  "346": "346 - Consulting and Audit Canada", "347": "347 - Canada Revenue Agency",
                  "348": "348 - Canadian Artists-Producers Prof. Relations Tribunal",
                  "349": "349 - Public Works and Government Services Canada",
                  "350": "350 - Citizenship and Immigration Canada",
                  "351": "351 - Canadian Heritage - Patrimoine canadien", "352": "352 - Victoria Shipyard Co. Ltd",
                  "354": "354 - Canadian Polar Commission", "355": "355 - Canada-Nova Scotia Offshore Petroleum Board",
                  "357": "357 - Farm Credit Canada", "359": "359 - Government of Newfoundland",
                  "361": "361 - National Round Table On The Environment",
                  "362": "362 - Canadian Environmental Assessment Agency",
                  "364": "364 - Canada Deposit Insurance Corporation",
                  "367": "367 - Cape Breton Development Corporation", "368": "368 - Defence Construction Canada",
                  "369": "369 - Enterprise Cape Breton Corporation",
                  "370": "370 - Freshwater Fish Marketing Corporation", "372": "372 - Laurentian Pilotage Authority",
                  "373": "373 - Pacific Pilotage Authority Canada", "376": "376 - Canada Ports Corporation",
                  "385": "385 - Canada Communication Group", "386": "386 - Translation Bureau",
                  "387": "387 - Canadian Human Rights Tribunal",
                  "389": "389 - Office of the Privacy Commissioner of Canada",
                  "390": "390 - Bugzilla9301 Mess (3900000)", "391": "391 - New Brunswick",
                  "392": "392 - Government of Nova Scotia", "393": "393 - Prince Edward Island", "395": "395 - Ontario",
                  "396": "396 - Province Of Manitoba", "397": "397 - Saskatchewan", "398": "398 - British Columbia",
                  "400": "400 - National Institute Of Nutrition", "401": "401 - Employment Projects For Women Inc.",
                  "403": "403 - Inter American Institute For Cooperation On Agriculture (Iica)",
                  "404": "404 - Canadian International Grains Institute",
                  "412": "412 - Commission For Labour Cooperation -Washington",
                  "414": "414 - Canadian Intellectual Property Office",
                  "415": "415 - The Lester B. Pearson Canadian International Peacekeeping Training Centre",
                  "416": "416 - National Battlefields Commission", "417": "417 - Nanaimo Harbour Commission",
                  "420": "420 - Asia Pacific Foundation", "421": "421 - North Atlantic Treaty Organization",
                  "422": "422 - Canada 2005 Exposition Corporation", "423": "423 - Communication Canada",
                  "424": "424 - United Nations For Education, Science And Culture Organization",
                  "425": "425 - International Union Of Telecommunications - Iut",
                  "426": "426 - Secretariat Convention On Biological Diversity - Uno Montreal",
                  "427": "427 - United Nations Secretariat - Uno Ny", "428": "428 - Atlantic Pilotage Authority",
                  "429": "429 - Organization For Economic Co-Operation And Development", "430": "430 - Nav Canada",
                  "431": "431 - Universal Postal Union", "432": "432 - World Trade Organization",
                  "433": "433 - Organization Of America States", "434": "434 - Canadian Food Inspection Agency",
                  "435": "435 - Vancouver Fraser Port Authority", "436": "436 - Red Cross International Committee",
                  "437": "437 - International Labour Office", "439": "439 - Cites Secretariat - Uno",
                  "440": "440 - Price Waterhouse Coopers", "441": "441 - Law Commission Of Canada",
                  "442": "442 - Yukon", "443": "443 - Paul Aubut & Associates Limited", "444": "444 - ARLA",
                  "445": "445 - Chancery Software Ltd", "446": "446 - Brookfield Lepage Johnson Controls",
                  "447": "447 - Equidata", "448": "448 - Toronto District School Board",
                  "449": "449 - White Iron Productions", "451": "451 - Minority Advocacy & Rights Council",
                  "452": "452 - Internal Trade Secretariat", "453": "453 - Ispat Sidbec Inc.",
                  "454": "454 - The Arcop Group", "455": "455 - L'association Franco-Yukonnaise",
                  "456": "456 - Cowater International Inc.",
                  "457": "457 - Viii Francophone Summit Secretariat - Moncton 1999",
                  "458": "458 - Millenium Bureau Of Canada", "459": "459 - Raula El-Rifai - Consultant For The Cida",
                  "460": "460 - Vancouver 2010 Bid Society", "461": "461 - Asd Canada",
                  "462": "462 - Agence Metropolitaine De Transport", "463": "463 - Commission For Environmemtal",
                  "464": "464 - Centre For Research And Information On Canada",
                  "465": "465 - Policy Research Secretariat", "466": "466 - Gabel Dodd Energy Soft Llc",
                  "467": "467 - Hydro-Quebec", "468": "468 - City Of Winnipeg",
                  "469": "469 - Friesen, Kaye And Associates", "470": "470 - The Leadership Network",
                  "471": "471 - Parks Canada", "472": "472 - European Centre For Minority Issues",
                  "473": "473 - World Meteorological Organization",
                  "474": "474 - International Civil Aviation Organization", "475": "475 - 2010 Winter Olympic Games",
                  "476": "476 - Agreement On Internal Trade", "480": "480 - City Of Cote Saint-Luc",
                  "490": "490 - Strategic Management Services", "491": "491 - The Canadian Sports Centre - Ontario",
                  "492": "492 - Government Of Nunavut", "493": "493 - Montreal Old Port Corporation",
                  "494": "494 - Veronique Lamontagne - Consultant For The Cida", "495": "495 - Eastern School District",
                  "496": "496 - Bc Work Information Society", "497": "497 - West Coast Leaf Association",
                  "498": "498 - Valerie G Ward Consulting Limited", "499": "499 - Forum Of Federations",
                  "500": "500 - Investment Agriculture Foundation Of Bc", "501": "501 - Canadian Forces Housing Agency",
                  "502": "502 - North Fraser Port Authority",
                  "503": "503 - Enterprise For Youth Group - Burlington Ontario",
                  "504": "504 - Breken Technologies Group", "505": "505 - Canadian Olympic Commitee (Coc)",
                  "506": "506 - Alberta Council Of Senior Federal Officials", "507": "507 - Educacentre",
                  "508": "508 - Santé En Francais, Services De Ressources", "509": "509 - Indian Claims Commission",
                  "510": "510 - Hbs Marketing", "511": "511 - Investment Agriculture Foundation Of Bc",
                  "512": "512 - Raymond Chabot Grant Thornton",
                  "513": "513 - The Canadian Institute Of Chartered Accountants",
                  "514": "514 - Department of Finance Canada", "515": "515 - Ministère Des Transports Du Québec",
                  "516": "516 - Guillemette Julie", "517": "517 - Public Service Staffing Tribunal",
                  "518": "518 - The Manitoba Museum", "519": "519 - Kpmg Lpp", "520": "520 - Gestion Deloitte S.e.c.",
                  "521": "521 - Winnipeg Airports Authority", "522": "522 - Northwestern Ontario Development Network",
                  "523": "523 - Linguistic Services : Isabelle Morin", "524": "524 - Cse : Nathalie Beaulac",
                  "525": "525 - Watson Wyatt Wordwide Canada", "526": "526 - Jolimot Inc.",
                  "527": "527 - Diane Lacasse", "528": "528 - Parlementary (Billable Service)",
                  "529": "529 - United Parcel Service Of Canada Ltd (Ups)", "530": "530 - Ottawa Hospital",
                  "531": "531 - Skidegate Band Council", "532": "532 - Stikeman Elliot S.e.n.c.r.l., Avocats",
                  "533": "533 - Unicef Canada", "534": "534 - Canadian Cancer Society",
                  "535": "535 - Toronto Child Abuse Centre", "536": "536 - Cartier Et Lelarge Inc.",
                  "537": "537 - Conseil Canadien Pour La Cooperation", "538": "538 - Empire Vie",
                  "539": "539 - Office of the Commissioner of Lobbying of Canada",
                  "540": "540 - Institute Of Neurosciences Mental Health & Addiction Douglas Hospital Res Arch Center",
                  "541": "541 - Caisse Canadienne De Dépôt De Valeurs",
                  "542": "542 - Canada Winter Games 2007 (Whitehorse)",
                  "543": "543 - Commission De La Santé, De La Sécurité Et De L'indemnisation Des Accidents Au Ravail",
                  "544": "544 - World Urban Forum", "545": "545 - Financiere Manuvie",
                  "546": "546 - Canadian Red Cross", "547": "547 - Bella Coola Valley Museum",
                  "548": "548 - Snc-Lavalin Profac", "549": "549 - Lexi-Tech International (Head Office)",
                  "550": "550 - Services De Sante En Francais", "551": "551 - Coop Atlantique",
                  "552": "552 - Sector Councils", "553": "553 - Municipality Of La Peche",
                  "554": "554 - Fédération Interprofessionnelle De La", "555": "555 - Courts judgments",
                  "556": "556 - Alliance Events", "557": "557 - Canadian Agency, Canadian War Graves Commission",
                  "558": "558 - Mental Health Commission of Canada", "559": "559 - Td Canada Trust",
                  "560": "560 - Csi Global Education", "561": "561 - Ec Conseil Inc.", "562": "562 - Elections Ontario",
                  "563": "563 - Rights & Democracy", "564": "564 - City Of Montreal - Saint Laurent Borough",
                  "565": "565 - Lawers Michel Cossette", "566": "566 - Acart Communications Inc.",
                  "567": "567 - Office of the Procurement Ombudsman", "568": "568 - Suzanne Sirois",
                  "569": "569 - London Military Family Resource Centre - Sheila Lupson",
                  "570": "570 - Cch Canadienne Limitée", "571": "571 - Ford Canada Limited",
                  "572": "572 - Centre Canadien De Lutte Contre", "573": "573 - Eve Desaulniers",
                  "574": "574 - Public Servants Disclosure Protection Tribunal Canada",
                  "575": "575 - Canadian Public Health Association",
                  "576": "576 - Public Prosecution Service of Canada",
                  "577": "577 - Canadian Partnership Against Cancer",
                  "578": "578 - Office of the Public Sector Integrity Commissioner",
                  "579": "579 - The Federal Bridge Corporation Limited", "580": "580 - Quiller And Blake Advertising",
                  "581": "581 - Josee Malenfant", "582": "582 - Réseau Familles D'aujourd'hui",
                  "583": "583 - Brigitte Turnel", "584": "584 - Telus Translation Service", "585": "585 - Rsm Richter",
                  "586": "586 - Kpmg", "587": "587 - PPP Canada Inc", "588": "588 - National Seafood Sector Council",
                  "589": "589 - Fogo / Fogolabs Laboratory", "590": "590 - International Idea",
                  "591": "591 - Zedevents", "592": "592 - City of Edmonton",
                  "597": "597 - Canadian Cancer Action Network",
                  "598": "598 - Public Appointments Commission  Secretariat",
                  "599": "599 - Truth and Reconciliation Commission", "600": "600 - Public Service Alliance of Canada",
                  "601": "601 - Canadian Cancer Research Alliance",
                  "602": "602 - Registry of the Specific Claims Tribunal of Canada",
                  "603": "603 - Centres jeunesse de l'Outaouais",
                  "604": "604 - Canada Development Investment Corporation",
                  "605": "605 - Lower Souris Watershed Committee Inc.", "606": "606 - Zuza Software Foundation",
                  "607": "607 - The CAPTURE Project",
                  "608": "608 - Office of the Communications Security Establishment Commissioner",
                  "609": "609 - Canadian Museum For Human Rights",
                  "610": "610 - Office Of Francophone And Francophile  Affairs",
                  "611": "611 - Secretariat On Research Ethics",
                  "612": "612 - International Centre for infectious Diseases",
                  "613": "613 - Canadian Association Of Defence And  Security Industries",
                  "614": "614 - Canadian Centre On Substance Abuse",
                  "615": "615 - Vancouver Organizing Committee For The  2010 Olympic Paralympic Winter Games",
                  "616": "616 - National Olympic Committees - Foreign  Countries",
                  "617": "617 - First Nations Statistical Institute", "618": "618 - Assembly Of Manitoba Chiefs",
                  "619": "619 - Cohen Commission", "620": "620 - Public Sector Pension Investment Board",
                  "621": "621 - Interpol Global Learning Centre",
                  "622": "622 - Cannor - Canadian Northern Economic Development Agency",
                  "623": "623 - Federal Economic Development Agency_Southern Ontario",
                  "624": "624 - Petawawa Military Family Resource  Centre", "625": "625 - Nova Scotia Business Inc",
                  "626": "626 - Ogilvy & Mather Toronto", "627": "627 - City Coquitlam Bc", "628": "628 - Expographiq",
                  "629": "629 - Health Technology Assessment International (Htai)",
                  "630": "630 - Canada Employment Insurance Financing  Board", "631": "631 - National Arts Centre",
                  "632": "632 - Blue Water Bridge Canada",
                  "633": "633 - Collegial Centre For Educational Materials Development",
                  "634": "634 - Affiliation Of Multicultural Societies And Service Agencies Of Bc (Amssa)",
                  "635": "635 - Agriculture Financial Services Corporation", "636": "636 - Via Rail Canada Inc.",
                  "637": "637 - Canada Foundation For Innovation",
                  "638": "638 - First Nations Financial Management Board", "639": "639 - Bank Of Montreal",
                  "640": "640 - Parliament Of Canada - Training",
                  "641": "641 - Canadian Museum Of Immigration At Pier  21",
                  "642": "642 - Francoservices Consulting Ltd.", "643": "643 - Institute For Citizen-Centred Service",
                  "644": "644 - Dnd Training", "645": "645 - Interpol", "646": "646 - Biddle Consulting Group",
                  "647": "647 - International Atomic Energy Agency", "648": "648 - Indigenous Bar Association",
                  "649": "649 - Hogg Robinson Canada Inc.", "650": "650 - Medical Council Of Canada (Mcc)",
                  "651": "651 - Superior North Community Futures Development Corporation",
                  "652": "652 - International Communications And Navigation Ltd",
                  "653": "653 - Atomic Energy Of Canada Ltd.", "660": "660 - Windsor-Detroit Bridge Authority",
                  "666": "666 - SAP - SIGMA", "670": "670 - Conseil Des Écoles Catholiques Du Centre-Est",
                  "671": "671 - Canada Lands Company Clc Limited",
                  "700": "700 - Roosevelt Campobello International Park Commission",
                  "701": "701 - Listeriosis Investigative Review Secretariat", "777": "777 - G8_G20_Summits",
                  "829": "829 - Library Of Parliament", "830": "830 - House Of Commons", "850": "850 - Training",
                  "868": "868 - Senate Of Canada", "875": "875 - Gc Contractors", "888": "888 - CUB Decisions",
                  "901": "901 - The National Gallery of Canada", "902": "902 - Canadian Museum Of Nature",
                  "903": "903 - Canadian Museum of civilization and Canadian War Museum",
                  "904": "904 - Canada Science And Technology Museum Corporation", "911": "911 - Acquisitions",
                  "929": "929 - Help From Professional Services  - Library Of Parliament",
                  "930": "930 - Help From Professional Services -  House Of Commons",
                  "968": "968 - Help Of Professional Services - Senate", "969": "969 - Services To Parliament",
                  "970": "970 - Cost Recovery Parliamentary Clients",
                  "971": "971 - Services To Parliament - Terminology  (Spa To Rf)",
                  "996": "996 - Bugzilla9301 Mess (9960000)", "999": "999 - Staffing"}
    clientName = fPath.split(u'/')[-3]
    clientNb = str(int(clientName.split(u'-')[0]))
    return clientDict[clientNb]


def dumpPathsToNotFlaggedFiles():
    notFlaggedFilePaths = b000path.getBtFilePaths(fileFormat=u'tmx', folders=[u'NOT-FLAGGED'])
    notFlaggedFilePaths = [b000path.anonymizePath(filePath) for filePath in notFlaggedFilePaths]
    utilsOs.dumpRawLines(notFlaggedFilePaths,
                         '/data/rali5/Tmp/alfonsda/workRali/004tradBureau/008originalDocumentsBt/notFlaggedPaths.txt',
                         addNewline=True, rewrite=True)


def getNotFlaggedPaths():
    pathToFile = '/data/rali5/Tmp/alfonsda/workRali/004tradBureau/008originalDocumentsBt/notFlaggedPaths.txt'
    with open(pathToFile) as notFlaggedFile:
        notFlaggedFilePaths = [filePath.replace(u'\n', u'') for filePath in notFlaggedFile.readlines()]
    notFlaggedFilePaths = [b000path.desAnonymizePath(filePath) for filePath in notFlaggedFilePaths]
    return notFlaggedFilePaths


def searchAndDumpOriginalDocsUrls(allFilePaths=None, session=None):
    # get path to all files [u'ALIGNMENT-QUALITY', u'MISALIGNED', u'QUALITY', u'NOT-FLAGGED']
    if allFilePaths is None:
        allFilePaths = b000path.getBtFilePaths(fileFormat=u'tmx',
                                               folders=[u'ALIGNMENT-QUALITY', u'MISALIGNED', u'QUALITY'])
    # open the reference paths file in order to check if we already found that file's url
    with open(u'/data/rali5/Tmp/alfonsda/workRali/004tradBureau/008originalDocumentsBt/reference.paths') as refs:
        refsPaths = refs.readlines()
    with open(
            u'/data/rali5/Tmp/alfonsda/workRali/004tradBureau/008originalDocumentsBt/unindexedReference.paths') as unindRefs:
        unindPaths = unindRefs.readlines()
    dejaVusRefPaths = set([b000path.desAnonymizePath(ln.replace(u'\n', u'')) for ln in refsPaths + unindPaths])
    # prepare the files to append the lines
    fileLoc = open(u'/data/rali5/Tmp/alfonsda/workRali/004tradBureau/008originalDocumentsBt/reference.paths', u'a')
    unindexedLoc = open(u'/data/rali5/Tmp/alfonsda/workRali/004tradBureau/008originalDocumentsBt/unindexedReference.paths', u'a')
    enDocsUrls = open(u'/data/rali5/Tmp/alfonsda/workRali/004tradBureau/008originalDocumentsBt/docsUrl.en', u'a')
    frDocsUrls = open(u'/data/rali5/Tmp/alfonsda/workRali/004tradBureau/008originalDocumentsBt/docsUrl.fr', u'a')
    # scrap the web to get the get the document's url where the sentence appears
    if session is None:
        session, reqA = authentificateBtUseRequests()
        time.sleep(5)
    # open each path to the original file
    for indFpath, fPath in tqdm(enumerate(allFilePaths)):
        # take a couple of seconds off every n queries
        # if indFpath % 19 == 0:
        #     time.sleep(1.5)
        # elif indFpath % 100 == 0:
        #     time.sleep(2)
        # if we haven't already scrapped that file's urls
        if fPath not in dejaVusRefPaths:
            # open the french file as default
            lang = u'en'
            longerSents = getLongerSentences(fPath, lang)
            # if there is no long line in the french file, open the english file
            if longerSents[0][1] < 5:
                # print(7777, 'small sent in english : ', longerSents, fPath)
                lang = u'fr'
                longerSents = getLongerSentences(fPath, lang)
                # if it's still too short, write it with the unindexed
                if longerSents[0][1] < 3:
                    print(888888, 'longer sent in french (final) but still short : ', longerSents)
                    unindexedLoc.write(u'{0}\n'.format(b000path.anonymizePath(fPath)))
                    fPath = None
            # get the name of the client
            if fPath is not None:
                clientCodeName = getClientName(fPath)
                tableJson = fillForm(clientCodeName, longerSents[0][0].replace(u'\n', u''), session, lang)
                if tableJson != []:
                    for ind in [1, 2]:
                        tableJson = fillForm(clientCodeName, longerSents[ind][0].replace(u'\n', u''), session, lang)
                        if tableJson != []:
                            break
                if tableJson != []:
                    urlEn, urlFr = scrapLookingGlassForUrls(tableJson, session)
                    if urlEn is None:
                        # print(999999, 'UNABLE to get to the looking glass tab for file : ', fPath)
                        unindexedLoc.write(u'{0}\n'.format(b000path.anonymizePath(fPath)))
                    else:
                        # dump to the files
                        fileLoc.write(u'{0}\n'.format(b000path.anonymizePath(fPath)))
                        enDocsUrls.write(u'{0}\n'.format(urlEn))
                        frDocsUrls.write(u'{0}\n'.format(urlFr))
                else:
                    unindexedLoc.write(u'{0}\n'.format(b000path.anonymizePath(fPath)))
    # close the opened files
    fileLoc.close()
    enDocsUrls.close()
    frDocsUrls.close()
    # close the session
    session.close()


def downloadSmallNbOfWholeBadNotFlaggedDocs(nbOfDocsToDownload=20):
    """ download the whole document for a small sample of
    documents tagged as not-Flagged but showing bad qual (manual annot) """
    origPath = u'/data/rali5/Tmp/alfonsda/workRali/004tradBureau/008originalDocumentsBt/'
    # open BT session
    session, req = authentificateBtUseRequests()
    time.sleep(5)
    # get the reference paths for troublesome (manually annotated) SPs
    referenceSet = set()
    for folderPath in ["/u/alfonsda/Documents/workRALI/004tradBureau/002manuallyAnnotated/",
                       "/u/alfonsda/Documents/workRALI/004tradBureau/003negativeNaiveExtractors/000manualAnnotation/",
                       "/u/alfonsda/Documents/workRALI/004tradBureau/007corpusExtraction/000manualAnnotation/problematic/annotatedButUseless4Eval/"]:
        with open(u"{0}sampleAnnotation.tsv".format(folderPath)) as annotFile:
            with open(u"{0}sampleReference.tsv".format(folderPath)) as refFile:
                # if we find a bad annotation, capture the reference into the set
                annot = annotFile.readline().replace(u'\n', u'')
                ref = refFile.readline().split(u'\t')[0]
                while annot:
                    if annot != u'1.0':
                        referenceSet.add(ref)
                    # next line
                    annot = annotFile.readline().replace(u'\n', u'')
                    ref = refFile.readline().split(u'\t')[0]
    # get the reference from the extracted url, if they match the reference from the annotated SPs, download
    with open(u'{0}reference.paths'.format(origPath)) as extRefFile:
        with open(u'{0}docsUrl.en'.format(origPath)) as urlEnF:
            with open(u'{0}docsUrl.fr'.format(origPath)) as urlFrF:
                extRef = extRefFile.readline().replace(u'\n', u'')
                urlEn = urlEnF.readline().replace(u'\n', u'')
                urlFr = urlFrF.readline().replace(u'\n', u'')
                counter = 0
                while extRef:
                    if extRef in referenceSet:
                        # download english and french docs
                        enDoc = session.get(urlEn, allow_redirects=True)
                        frDoc = session.get(urlFr, allow_redirects=True)
                        docFolder = extRef.replace(u'**--**/', u'').replace(u'/', u'*').replace(u'.tmx', u'')
                        utilsOs.createEmptyFolder(u'{0}{1}'.format(origPath, docFolder))
                        # find out which of the english or the french docs are source and target
                        enSrcTrgt = u'src' if u'en-fr' in docFolder else u'trgt'
                        frSrcTrgt = u'trgt' if u'en-fr' in docFolder else u'src'
                        # dump the english document
                        enDocName = enDoc.headers[u'Content-Disposition'].split(u'filename="')[1].replace(u'"', u'').replace(u' ', u'_')
                        enDocPath = u'{0}{1}/{2}'.format(origPath, docFolder, enDocName)
                        open(enDocPath, 'wb').write(enDoc.content)
                        # dump the english headers
                        enHeadersPath = u'{0}{1}/{2}.{3}.headers.json'.format(origPath, docFolder, enDocName.split(u'.')[0], enSrcTrgt)
                        utilsOs.dumpDictToJsonFile(dict(enDoc.headers), enHeadersPath)
                        time.sleep(2)
                        # dump the french document
                        frDocName = frDoc.headers[u'Content-Disposition'].split(u'filename="')[1].replace(u'"', u'').replace(u' ', u'_')
                        frDocPath = u'{0}{1}/{2}'.format(origPath, docFolder, frDocName)
                        open(frDocPath, 'wb').write(frDoc.content)
                        # dump the french headers
                        frHeadersPath = u'{0}{1}/{2}.{3}.headers.json'.format(origPath, docFolder, frDocName.split(u'.')[0], frSrcTrgt)
                        utilsOs.dumpDictToJsonFile(dict(frDoc.headers), frHeadersPath)
                        time.sleep(2)
                        # each time we find a not-flagged document with errors, we add one to the counter
                        counter += 1
                    # if we achieve the expected number of docs, we break the loop
                    if counter == nbOfDocsToDownload:
                        break
                    # next line
                    extRef = extRefFile.readline().replace(u'\n', u'')
                    urlEn = urlEnF.readline().replace(u'\n', u'')
                    urlFr = urlFrF.readline().replace(u'\n', u'')
    session.close()
    return None


# disable the warnings
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# count the time the algorithm takes to run
startTime = utilsOs.countTime()


# the not flagged corpus takes too much time to get extracted
# from the directories so we have previously saved the paths in a doc
# notFlaggedFilePaths = getNotFlaggedPaths()

# search and dump the original docs for the not flagged documents alone
# searchAndDumpOriginalDocsUrls(notFlaggedFilePaths)

# download the whole document for a small sample of documents tagged as not-Flagged but showing bad qual (manual annot)
downloadSmallNbOfWholeBadNotFlaggedDocs()


# print the time the algorithm took to run
print(u'\nTIME IN SECONDS ::', utilsOs.countTime(startTime))


