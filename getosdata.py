# coding is utf-8
from bs4 import BeautifulSoup, SoupStrainer
import re
import json
import csv
from csv import DictWriter
import requests
import codecs
import datetime

# Get main page of Time values
url = requests.get("http://www.os.amsterdam.nl/feiten-en-cijfers/buurtcombinaties")
#print url.text

# Create iterable variable
soup = BeautifulSoup(url.text)

# Select theme's
themeTab = soup.find('div', attrs={"id":"tab_20401"})
#print themeTab

# Get all links
links= themeTab.findAll("a")

# Create dictionary to store links in
themes={"themes":[]}

# Set variables
fieldNames=[]	
TotalDataSet =[]
counter = 0
themeId = 0
stadsdNaam = ''
stadsdCode = ''

# Get Theme id and names
for i in links:
	# select id numbers
	themeLinkString = '%s' % i.get("onclick")
	
	themeLink = re.search(r'\((.*)\)',themeLinkString)
	# if it is not a nonetype do...
	if themeLink:
		themeId = themeLink.group(1)
		#print themeId
		themeName = i.contents[0]	
		#print themeName
		# Add theme id's and names to dict
		themes["themes"].append({"themeId":themeId, "themeName":themeName, "themeItems": []})
# print themes

# For each theme do...
for themeId in range(len(themes["themes"])):
	# Get list of Subthemes
	url_themePage = requests.get("http://www.os.amsterdam.nl/subcontent/%s" % themes["themes"][themeId]["themeId"]) 
	#print url_themePage.text
	
	# Format to searchable text
	themeSubTab = BeautifulSoup(url_themePage.text)

	# Find all url's
	themeSublinks= themeSubTab.findAll("a")
	
	# For each url do...
	for a in themeSublinks:
		themeSublinks = '%s' % a.get("href")
		print themeSublinks
		# Get Id number of page
		itemId = re.search(r'\/(\d+)$',themeSublinks).group(1)
		#print itemId 
		itemName = a.contents[0]	
		#print itemName
		#print themes["themes"][i]
		url_itemPage = requests.get("http://www.os.amsterdam.nl/popup/%s" % itemId)
		
		#url_itemPage = requests.get("http://www.os.amsterdam.nl/popup/1702")
		soupItems = BeautifulSoup(url_itemPage.text)
		#print soupItems
		# Ignore image datasets:
		if soupItems.find('table'):
			# Start empty dataset for each request to optimize memory and dump each set incremental to file
			dataSet =[]
			# Get Header names and col numbers
			headers=[]
			headerTotal=soupItems.findAll('tr', attrs={"class":"header"})
			for a in range(len(headerTotal)):
				headerList=headerTotal[a].findAll('th')
				colnr = 0
				
				for i in range(len(headerList)):
					if a==0:
						header = headerList[i].text.replace(u'\xa0', u' ').strip()
						headers.append({"colnr": colnr, "headerTitle":header})
						colnr+=1
					else:
						x=i-colnr
						header = headerList[i].text.replace(u'\xa0', u' ').strip()
						headers[x].update({"headerTitle": headers[x]["headerTitle"]+' '+header})
			print headers
		
			BuurtName=[]
			# Get tbody
			themeSublinks = soupItems.findAll("a")
			tBody = soupItems.find('tbody')
			
			# Get remarks at bottom of excel file and put in a list
			remarks = soupItems.findAll('span',attrs={"class":"footer"})
			#print remarks
			remarkList=[]

			if remarks:
				for i in remarks:
					try:
						remarkList.append(re.search(r'\)(.*)', i.text).group(1).strip())
						print remarkList
					except:
						continue
			
			# Get SetName with pre-number and footnote number
			SetNameTotal = soupItems.find('h4').text
			print SetNameTotal
			# Get Chapter number
			SetId = re.search(r'^(.*?)\s+',SetNameTotal).group(1)
			# Get SetName, ignore ,year
			if re.search(r'\s+(.*?),',SetNameTotal):
				SetName = re.search(r'\s+(.*?),',SetNameTotal).group(1)
			# If only name is present, just get entire name:
			else:
				SetName = re.search(r'\s+(.*?)',SetNameTotal).group(1)

			# Get Row names
			rowNames = tBody.find_all('th')
			for rowName in rowNames:
				BuurtName.append(rowName.text)
			print BuurtName
			
			# Get Column values only for year columns
			rows = tBody.find_all('tr')
			gebiedJaar = ''	
			
			# Get one row
			for row in range(len(rows)):
				
				# Get td fields
				cols = rows[row].find_all('td')	
				
				# Check for each header name
				for h in range(len(headers)):
					#print gebiedJaar
					opmerking = ''
					
					# For each cell check if they correspond to a header value index number, except first col of neighbourhood names.
					for col in range(1,len(cols)):
						# If match, do...
						if col==headers[h]["colnr"]:
							# Get code value
							try:
								gebiedCode = re.search(r'(\w+)[\s\:](.*)',BuurtName[row]).group(1)
								stadsdCode = gebiedCode[:1]
								if stadsdCode == 'A':
									stadsdNaam = 'Centrum'
								elif stadsdCode == 'B':
									stadsdNaam = 'Westpoort'
								elif stadsdCode == 'E':
									stadsdNaam = 'West'
								elif stadsdCode == 'F':
									stadsdNaam = 'Nieuw-West'
								elif stadsdCode == 'N':
									stadsdNaam = 'Noord'
								elif stadsdCode == 'K':
									stadsdNaam = 'Zuid'
								elif stadsdCode == 'M':
									stadsdNaam = 'Oost'
								elif stadsdCode == 'T':
									stadsdNaam = 'Zuidoost'	
								else:
									stadsdNaam = ''
							#print gebiedCode
							except:
								gebiedCode = ''
							# Get Area name
							try:
								gebiedNaam =  re.search(r'(\w+)[\s\:](.*)',BuurtName[row]).group(2) 
							except:
								# To get eg. Amsterdam
								gebiedNaam = BuurtName[row]
								if gebiedNaam == 'Amsterdam':
									gebiedCode = 'STAD'
							# Get value that matches current index match of header
							waarde = cols[col].text
							# substitute text for digits
							waarde = re.sub(r'[x\.\*-]','-99', waarde)	
							waarde = waarde.replace(',', '.')
							#print waarde
							# Set type to header value name eg. 2011 or % of ...
							gebiedType = headers[h]["headerTitle"]
							#print gebiedType

							# remove footnote numbers from type field and add remarks field where present
							if remarkList:
								for i in range(len(remarkList)):
									footerNumber = i+1
									#print footerNumber
									try:
										typeNumber = re.search(r'\b(\d)\)$',gebiedType).group(1)
										#print typeNumber
										if int(typeNumber)==int(footerNumber):
											#print gebiedType
											gebiedType = re.sub(r'\s\d\)$', '',gebiedType)
											#print gebiedType
											opmerking = remarkList[i]
									except:
										opmerking = ''
							
							# Year search
							reYear = re.compile(r'^.*(\d{4}).*$')
							
							# Find Year values in dataSet
							# Search in each header field
							if re.search(reYear, headers[h]["headerTitle"]):
								gebiedJaar = re.search(reYear, headers[h]["headerTitle"]).group(1)
							
							# Else search in raw SetName before optimizing
							elif re.search(reYear, SetNameTotal):
								gebiedJaar = re.search(reYear, SetNameTotal).group(1)
							# Else insert no year field
							else:	
								gebiedJaar = ''	

							# Format year field for date readability
							gebiedJaar = "01-01-%s" % gebiedJaar

							# Add all variables to Dict
							dataSet.append({"Thema": themes["themes"][themeId]["themeName"], "SetId":SetId, "SetNaam":SetName, "Gebiedjaar": gebiedJaar, "Stadsdeel": stadsdNaam,"StadsdeelCode": stadsdCode, "Gebiedcode": gebiedCode, "Gebiednaam" : gebiedNaam, "Waarde": waarde, "Gebiedtype": gebiedType, "Opmerking": opmerking })
							
							# Add metadata
							meta = soupItems.find_all('li')
							for i in meta:
								#print i.text
								key = re.search(r"(.*):",i.text).group(1).strip()
								#print key
								#print i
								urlLink = i.find('a')
								if urlLink:
									key = "DatasetUrl"
									value = "http://os.amsterdam.nl%s" % urlLink.get("href")
								else: 
									value = re.search(r":(.*)",i.text).group(1).strip()
								#print key 
								#print value
								dataSet[-1].update({key:value})
							# Print last row
							print dataSet[-1]
							# Counter for console status
							counter+=1

				print "%s lines added" % (counter)
			
			# Write dataSet incremental:
			filename = 'os_amsterdam_%s' % (datetime.date.today().strftime("%d_%B_%Y"))

			# Add title fieldnames	
			if not fieldNames:
				for k in dataSet[0].keys():	
					fieldNames.append(k)
				print fieldNames
				with open(filename+'.csv', 'wb+') as csvfile:
					csvwriter = csv.writer(csvfile, delimiter=';',quotechar='"', quoting=csv.QUOTE_MINIMAL)
					csvwriter.writerow(fieldNames)
					csvfile.close()
			# Only add data
			else:
				with open(filename+'.csv', 'ab') as csvfile:
					csvwriter = csv.writer(csvfile, delimiter=';',quotechar='"', quoting=csv.QUOTE_MINIMAL)
					for i in dataSet:
					#print i
						row =[]
						for k,v in i.iteritems():						
							row.append(v.encode('utf-8'))
							#print row			
						csvwriter.writerow(row)
			# Write and append to JSON File
			

			with codecs.open(filename+".json", 'ab', encoding='utf-8') as outfile:
			    json.dump(dataSet, outfile, sort_keys=True, indent=4, ensure_ascii=False)

		#TotalDataSet.append(dataSet)
		