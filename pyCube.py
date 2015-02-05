# pyCube.py
# Python Data Cube
# An application level implementation for data cube
# by Chris Lee, John Zhao, Dave Tian
# April 30, 2013
# daveti@cs.uoregon.edu
# http://daveti.blog.com

import os
import MySQLdb
from pyTreeView import *

# Helper functions here
def displayMenu():
	'''
	Display the menu to the user
	'''
	print('==================================')
	print('Python 4D Data Cube')
	print('by Chris Lee, John Zhao, Dave Tian')
	print('----------------------------------')
	print('1 : View Data Cube Tree')
	print('2 : View X-D Cuboid')
	print('3 : Roll-up')
	print('4 : Drill-down')
	print('5 : Slice')
	print('6 : Dice')
	print('7 : Pivot')
	print('0 : quit')
	print('----------------------------------')

def processInput():
	'''
	Process the user's input
	'''
	displayMenu()
	choice = raw_input('Please enter your choice: ')
	choice.strip()
	while choice == '' or choice.isdigit() == False or (int(choice)<0 or int(choice)>7):
		choice = raw_input('Please enter your choice: ')
		choice.strip()
	else:
		return(int(choice))

def processInputSub(choice):
	'''
	Process the user's input based on the choice
	'''
	keyStr0 = ''
	keyStr1 = ''
	print('----------------------------------')
	if choice == 2 or choice == 7:
		keyStr0 = raw_input('Please input the cuboid: ')
		while keyStr0 == '':
			keyStr0 = raw_input('Please input the cuboid: ')
	else:
		keyStr0 = raw_input('Please input the starting cuboid: ')
		keyStr1 = raw_input('Please input the targeting cuboid: ')
		while keyStr0 == '' or keyStr1 == '':
			if keyStr0 == '':
				keyStr0 = raw_input('Please input the starting cuboid: ')
			if keyStr1 == '':
				keyStr1 = raw_input('Please input the targeting cuboid: ')

	return(keyStr0, keyStr1)

# Construct the mapping dictionary between
# the name of data cube and encoded number string
# The name of the data cube follows the order - ('time', 'item', 'location', 'supplier')
dataCubeDict = {}
dataCubeDict[('time', 'item', 'location', 'supplier')] = '1111'
dataCubeDict[('time', 'item', 'location', '*')] = '1110'
dataCubeDict[('time', 'item', '*', 'supplier')] = '1101'
dataCubeDict[('time', '*', 'location', 'supplier')] = '1011'
dataCubeDict[('*', 'item', 'location', 'supplier')] = '0111'
dataCubeDict[('time', 'item', '*', '*')] = '1100'
dataCubeDict[('time', '*', 'location', '*')] = '1010'
dataCubeDict[('*', 'item', 'location', '*')] = '0110'
dataCubeDict[('time', '*', '*', 'supplier')] = '1001'
dataCubeDict[('*', 'item', '*', 'supplier')] = '0101'
dataCubeDict[('*', '*', 'location', 'supplier')] = '0011'
dataCubeDict[('time', '*', '*', '*')] = '1000'
dataCubeDict[('*', 'item', '*', '*')] = '0100'
dataCubeDict[('*', '*', 'location', '*')] = '0010'
dataCubeDict[('*', '*', '*', 'supplier')] = '0001'
dataCubeDict[('*', '*', '*', '*')] = '0000'

# Construct the mapping dictionary between
# the index of the attribute (dimension) and the name
dataAttrDict = {}
dataAttrDict[0] = 'month'
dataAttrDict[1] = 'name'
dataAttrDict[2] = 'city'
dataAttrDict[3] = 'company'
dataAttrDict[4] = 'amount'

# Define debug function, SQL related functions
debugFlag = False
def debugFun(var1, var2):
	'''
	Debug function
	'''
	if debugFlag == True:
		print('DEBUG:', var1, var2)

def generateTableHeader(selectT, whereT):
	'''
	Generate the table header used for better output
	'''
	print('__________________________________________________')

	# Print the where if there is
	whereH = ''
	if len(whereT) != 0:
		for w in whereT:
			whereH += w + ', '
		# Remove the extra ', '
		whereH = whereH[0:-len(', ')]
		print(whereH)
		print('__________________________________________________')

	# Print the select
	selectH = ''
	for s in selectT:
		selectH += s + ', '
	# Remove the extra ', '
	selectH = selectH[0:-len(', ')]
	print(selectH)
	print('__________________________________________________')

def generateTableHeader4Pivot(selectT, whereT):
	'''
	Generate the table header for pivot used for better output
	and return the initial rows with attribute names
	'''
	print('__________________________________________________')

	# Print the where if there is
	whereH = ''
	if len(whereT) != 0:
		for w in whereT:
			whereH += w + ', '
		# Remove the extra ', '
		whereH = whereH[0:-len(', ')]
		print(whereH)
		print('__________________________________________________')

	# Construct the initial rows for pivot
	pivotList = []
	for s in selectT:
		pivotRow = []
		pivotRow.append(s)
		pivotList.append(pivotRow)

	return(pivotList)

def generateSQL(index, selectT, fromT, whereT, groupByT):
	'''
	Generate the SQL statement based on the view index and all
	parts from select, from, where and group by
	'''
	viewName = 'view_' + index

	# Construct select
	sqlQuery = 'select '
	for s in selectT:
		sqlQuery += s + ', '
	# Remove the extra ', '
	sqlQuery = sqlQuery[0:-len(', ')]

	# Construct from
	sqlQuery += ' from ' + viewName + ' '
	for f in fromT:
		sqlQuery += 'natural join ' + f + ' '

	# Construct where
	if len(whereT) != 0:
		sqlQuery += ' where '
		for w in whereT:
			sqlQuery += w + ' and '
		# Remove the extra ' and '
		sqlQuery = sqlQuery[0:-len(' and ')]

	# Construct groupBy
	if len(groupByT) != 0:
		sqlQuery += ' group by '
		for g in groupByT:
			sqlQuery += g + ', '
		# Remove the extra ', '
		sqlQuery = sqlQuery[0:-len(', ')]
		
	return(sqlQuery)

# Define the operation functions of data cube
# rollUp, drillDown, slice, dice, pivot
# All functions may accept the input like below:L
# start - the data cuboid starting from
# target - the target data cuboid with or without constrains
# All the inputs should be tuples eventually, like:
# ('time', 'item', 'location', 'supplier')
# ('time', 'item', '*', 'supplier')
# ('time.quarter', '*', 'location', '*')
# ('time.time_id = 12', 'item.category = "notebook"', '*', 'supplier')
# ('time.quarter = [1 2 3]', 'item.category = "notebook"', '*', '*')
def parseCuboid(cuboid):
	'''
	Parse the input cuboid to see if this is the basic
	data cuboid or the one with constrains and output
	different parts of SQL.
	NOTE: the input should be a tuple.
	'''
	cube = []
	sqlSelect = []
	sqlFrom = []
	sqlGroupBy = []
	sqlWhere = []
	for i in range(len(cuboid)):
		debugFun('i: ', i)
		debugFun('cuboid-cuboid[i]: ', cuboid[i])
		if cuboid[i].__contains__('.') == True:
			if cuboid[i].__contains__('=') == False:
				# This is a roll-up or drill-down for certain dimension
				sqlSelect.append(cuboid[i].strip())
				sqlGroupBy.append(cuboid[i].strip())
			else:
				# This is a slice or dice for certain dimension
				if cuboid[i].__contains__('[') == False:
					# Normal where
					sqlWhere.append(cuboid[i].strip())
				else:
					# Range where
					whereList = cuboid[i].split('[')
					whereHead = whereList[0].strip()
					rangeStr = whereList[1].strip()
					# Remove the extra ']'
					rangeStr = rangeStr[0:-1]
					rangeList = rangeStr.split()
					debugFun('rangeList: ', rangeList)
					whereClause = ''
					for j in range(len(rangeList)):
						# Construct the where clause
						if j != len(rangeList)-1:
							whereClause += whereHead + ' ' + rangeList[j].strip() + ' or '
						else:
							whereClause += whereHead + ' ' + rangeList[j].strip()
					debugFun('rangeWhere: ', whereClause)
					sqlWhere.append(whereClause)
					
				sqlSelect.append(dataAttrDict[i])
				sqlGroupBy.append(dataAttrDict[i])

			# Save the base attr
			debugFun('cuboid[i]: ', cuboid[i])
			tableName = cuboid[i].split('.')[0].strip()
			debugFun('tableName: ', tableName)
			cube.append(tableName)
			sqlFrom.append(tableName)
		else:
			# This is the cuboid
			cube.append(cuboid[i].strip())
			# Check for '*'
			if cuboid[i].strip() != '*':
				sqlSelect.append(dataAttrDict[i])
				sqlGroupBy.append(dataAttrDict[i])
				sqlFrom.append(cuboid[i].strip())

	# Hack - add the last sum(amount) into select
	sqlSelect.append('sum(amount)')

	cubeTuple = tuple(cube)
	selectTuple = tuple(sqlSelect)
	fromTuple = tuple(sqlFrom)
	groupByTuple = tuple(sqlGroupBy)
	whereTuple = tuple(sqlWhere)

	return(cubeTuple, selectTuple, fromTuple, whereTuple, groupByTuple)

def rollUp(start, target):
	'''
	Roll-up the data cuboid either to eliminate one dimension
	or to get the more general summary for certain dimension.
	'''

def pivot(row, data):
	'''
	Pivot the original data table and output the pivot'd table
	'''
	pTable = []
	# Add the data into new rows
	for d in data:
		for i in range(len(d)):
			row[i].append(d[i])
	# Convert to tuples and add them into the table
	for r in row:
		pTable.append(tuple(r))

	return(pTable)

def drawCubeTree():
	'''
	Draw the data cube tree
	'''
	l = lattice()
	drawlattice(l)

def constructCuboid(str0, str1, choice):
	'''
	Construct the cuboid from user's input string
	'''
	debugFun('str0: ', str0)
	debugFun('str1: ', str1)
	# Make str1 as the default
	keyStr = str1
	if choice == 2 or choice == 7:
		# Focus on str0
		keyStr = str0

	cuboidList = keyStr.split(',')
	cuboid = []
	for c in cuboidList:
		cuboid.append(c.strip())

	return(tuple(cuboid))
	
# Configure the db connection
hostname = "dm.chrislee.pro"
portnum = 3306
username = "DMDBA"
password = "cis553"
dbname = "DM"

	
def main():
	'''
	Main function to run pyCube
	'''
	# Create db connection
	dbConn = MySQLdb.connect(host=hostname,
			port=portnum,
			user=username,
			passwd=password,
			db=dbname)

	# Create a cursor obj before query
	curObj = dbConn.cursor()

	# Display the menu and process the input
	while True:
		choice = processInput()
		if choice == 0:
			# Safely exit
			curObj.close()
			dbConn.close()
			return
		elif choice == 1:
			drawCubeTree()
			continue

		str0, str1 = processInputSub(choice)
		
		# Construct the cuboid
		cuboid = constructCuboid(str0, str1, choice)
		debugFun('cuboid: ', cuboid)

		# Construct the sql query
		cube, selectT, fromT, whereT, groupByT = parseCuboid(cuboid)
		debugFun('cube: ', cube)
		debugFun('select: ', selectT)
		debugFun('from: ', fromT)
		debugFun('where: ', whereT)
		debugFun('groupBy: ', groupByT)
		index = dataCubeDict[cube]
		sqlQ = generateSQL(index, selectT, fromT, whereT, groupByT)
		debugFun('index: ', index)
		debugFun('sql: ', sqlQ)
		debugFun('------------------', '--------------------')
		#continue

		# Do the query
		try:
			# Execute the query
			curObj.execute(sqlQ)
		
			# Open a new file for logging
			#fnObj = open("./pyCube.log", "w")

			# Dispaly the results
			pivotList = []
			dataList = []
			if choice != 7:
				generateTableHeader(selectT, whereT)
			else:
				pivotList = generateTableHeader4Pivot(selectT, whereT)
				debugFun('pivotList: ', pivotList)

			for row in curObj.fetchall():
				if choice != 7:
					print(row)
				else:
					dataList.append(row)

			if choice == 7:
				# Pivot processing
				pivotTable = pivot(pivotList, dataList)
				debugFun('pivotTable: ', pivotTable)
				for row in pivotTable:
					print(row)

				# Write the table into file?
				# fnObj.write(row + '\n')
			print('__________________________________________________')
			print()
		finally:
			pass
			# Close the cursor and the connection and the file
			# curObj.close()
			# dbConn.close()
			#fnObj.close()


if __name__ == '__main__':
    main()

