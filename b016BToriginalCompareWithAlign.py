#!/usr/bin/python
# -*- coding:utf-8 -*-

import sys
sys.path.append(u'../utils')
sys.path.append(u'./utils')

tikaPath = u'/u/alfonsda/progs/tika/tika-app-1.22.jar'
folderPath = u'/data/rali5/Tmp/alfonsda/workRali/004tradBureau/008originalDocumentsBt/NOT-FLAGGED*471-PARKS_CANADA*en-fr*9829943-3332957/'
filePath = u'/data/rali5/Tmp/alfonsda/workRali/004tradBureau/008originalDocumentsBt/NOT-FLAGGED*471-PARKS_CANADA*en-fr*9829943-3332957/9829943_001_EN_backgrounder_Fort_Walsh_VRC.doc'

from tika import parser
parsed = parser.from_file(filePath)

print(11111)
print(parsed)