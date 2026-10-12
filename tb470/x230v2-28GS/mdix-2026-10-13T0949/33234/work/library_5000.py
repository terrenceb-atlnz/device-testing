#!/usr/bin/python
import time


def logTestSetHeader(myTestSet):
	"""
	Write Test Set information to the Test Set log file.
	
	Parameter(s):
	myTestSet - Test Set object for which log should be updated
	
	Returns:
	Nothing
	
	Description
	Appends to the log file for the Test Set:
	- Test Suite Number
	- Test Set Number
	- Test Set Name
	as defined by the Test Set script name.
	Assumes a file name format of:
	xxxx-<test suite number>.<test set number>-<test set name>.py
	
	"""
	
	myTestSet.log('\n')
	myTestSet.log('TEST SUITE NUMBER: %s' %(myTestSet.testSuiteNum))
	myTestSet.log('TEST SET NUMBER:   %s' %(myTestSet.testSetNum))
	tempStrList = myTestSet.testSetFileName.split('-')
	tempStrList = tempStrList[2].replace('.py', '')
	myTestSet.log('TEST SET NAME:     %s' %(tempStrList))
	myTestSet.log('\n')



def deviceReboot(myTestSet, duts):
	"""
	Perform a reboot for each device in test set up.
	
	Parameter(s):
	myTestSet - Test Set object for which log should be updated
	duts -	dictionary containing the device name as the key and at least tty as a property
		Assumed to come from config.py for test
  
	Returns:
	Nothing
	
	Description
	Perform a reboot for each device in the test set up.
	
	"""

	# for each device, reboot
	for key, device in duts.iteritems():
		myTestSet.log('LOG {}: Rebooting device: {}'.format(device.tty, key))
		output = device.reboot(None, timeOut = -1)
		device.mode('#')
		myTestSet.log('\n')


def configurePort(testCase, dut, portA, port_config, port_value,expect_value):
	
	testCase.log('LOG {}: Changing port {} {} to {}'.format(dut.tty, portA.name, port_config, port_value))
	dut.mode(')#')
	dut.cmd('int %s' % (portA.name))
	output = dut.cmd('%s %s' % (port_config, port_value))
	testCase.log(output)
	#dut.mode('#')
	dut.cmd('end')
	time.sleep(3)
	
	if (output.count('failed') or output.count('Cannot') or output.count('Invalid')) == 1:
		if expect_value == 1:
			testCase.log('RESULT>>>> The command failed as expected')
			return True
		else:
			testCase.log('RESULT!!!! Unexpected command failure')
			return False
	else:
		if expect_value == 0:
			testCase.log('RESULT>>>> The command passed as expected')
			return True
		else:
			testCase.log('RESULT!!!! Unexpected command pass')
			return False


def configureDefaultPort(testCase, dut, portA):
	"""
	Configure a port on a device to default Speed, Duplex and Polarity settings.
	
	Parameter(s):
	testcase - Test case object for which log should be updated
	dut - switch object for device to be configured
	portA - port object from the switch object to be configured
	
	Returns:
	Nothing
	
	Description
	Configure port, portA, of device, dut, with the following defauts:
		Speed = auto
		Duplex = auto
		Polarity = auto
	
	"""

	testCase.log('LOG {}: Changing port {} back to default configuration'.format(dut.tty, portA.name))
	dut.mode(')#')
	dut.cmd('int %s' % (portA.name))
	dut.cmd('speed auto')
	dut.cmd('duplex auto')
	dut.cmd('polarity auto')
	#dut.mode('#')
	dut.cmd('end')
	time.sleep(3)
	#TODO: how to call this function from here?
	#library_1103.checkConfiguredPort(testcase, dut, portA, 'auto', 'auto', 'auto')
	return


def checkConfiguredPort(testCase, dut, portA, duplex, speed, polarity, expect_value = True):
	"""
	Check the "configured" status (for speed, duplex and polarity) of a port on a device is as expected.
	
	Parameter(s):
	testcase - <test case object> for which log should be updated
	dut - <switch object> for device to be configured
	portA - <port object> from the switch object to be configured
	duplex - <string> expected configuration
	speed - <string> expected configuration
	polarity - <string> expected configuration
	expect_value - <boolean> are the "configured" values expected to be found (default is True)
	
	Returns:
	True = all as expected (found or not found)
	False = not as expected
	
	Description
	Check the "configured" status for a port by searching the output for the SHOW INTERFACE command.
	The expect_value parameter was added to cater for when the link status is 'down' as the current 
	functionality is that the 'current' and 'configured' statuses for the port are not displayed
	in this situation.
	If expect_value = True, search and expect to find the exact strings
	Else do not expect to find the string.
	
	"""

	testCase.log('LOG {}: Checking for the port status'.format(dut.tty))
	dut.mode('#')
	output = dut.cmd('show interface %s' % (portA.name))
	testCase.log(output)
  
	duplex_string = 'configured duplex %s' % (duplex)
	# add comma to the end of the string to ensure "speed auto" 
	# is distinquished from the likes of "speed auto 100"
	speed_string = 'configured speed %s,' % (speed)
	polarity_string = 'configured polarity %s' % (polarity)
  
	check_counter = 0

	if output.count(duplex_string) == 1:
		if expect_value:
			testCase.log('RESULT>>>> Duplex configuration as expected : %s' % (duplex_string))
		else:
			testCase.log('RESULT!!!! Found Duplex configuration unexpectedly : %s' % (duplex_string))
			check_counter += 1
	else:
		if expect_value:
			testCase.log('RESULT!!!! Failed to find expected duplex configuration : %s' % (duplex_string))
			check_counter += 1
		else:
			testCase.log('RESULT>>>> Duplex configuration as expected : Not Found, assumed to be %s' %(duplex_string))
  	
	if output.count(speed_string) == 1:
		if expect_value:
			testCase.log('RESULT>>>> Speed configuration as expected : %s' % (speed_string))
		else:
			testCase.log('RESULT!!!! Found Speed configuration unexpectedly : %s' % (speed_string))
			check_counter += 1
	else:
		if expect_value:
			testCase.log('RESULT!!!! Failed to find expected Speed configuration : %s' % (speed_string))
			check_counter += 1
		else:
			testCase.log('RESULT>>>> Speed configuration as expected : Not Found, assumed to be %s' %(speed_string))
  	
	if output.count(polarity_string) == 1:
		if expect_value:
			testCase.log('RESULT>>>> Polarity configuration as expected : %s' % (polarity_string))
		else:
			testCase.log('RESULT!!!! Found Polarity configuration unexpectedly : %s' % (polarity_string))
			check_counter += 1
	else:
		if expect_value:
			testCase.log('RESULT!!!! Failed to find expected Polarity configuration : %s' % (polarity_string))
			check_counter += 1
		else:
			testCase.log('RESULT>>>> Polarity configuration as expected : Not Found, assumed to be %s' %(polarity_string))
  	
	if check_counter == 0:
		return True
	else:
		return False		


def checkCurrentPort(testCase, dut, portA, cur_speed, cur_duplex, cur_polarity):
	"""
	Function not used as current and configured settings are not displayed when the link status is "down"
	When this is changed, the checkConfiguredPort() function should be re-written/changed to ignore the
	expect_value parameter setting and this function re-written to perform the same function for the
	current settings.
	Current logic is not correct, requires to be changed to same logic as checkConfiguredPort().
	"""
	testCase.log('LOG {}: Checking for the port status'.format(dut.tty))
	output = dut.cmd('show interface %s' % (portA.name))
	testCase.log(output)
	
	cur_speed_string = 'current speed %s' % (cur_speed)
	cur_duplex_string = 'current duplex %s' % (cur_duplex)
	cur_polarity_string = 'current polarity %s' % (cur_polarity)
	
	if output.count(cur_speed_string) == 1:
		testCase.log('RESULT>>>> Speed configuration as expected : %s' % (cur_speed_string))
		if output.count(cur_duplex_string) == 1:
			testCase.log('RESULT>>>> Duplex configuration as expected : %s' % (cur_duplex_string))
			if output.count(cur_polarity_string) == 1:
				testCase.log('RESULT>>>> Polarity configuration as expected : %s' % (cur_polarity_string))
				return True
			else:
				testCase.log('RESULT!!!! Failed to find expected polarity configuration as expected : %s' % (cur_polarity_string))
				return False        
		else:
			testCase.log('RESULT!!!! Failed to find expected duplex configuration : %s ' % (cur_duplex_string))
			return False
	else:
		testCase.log('RESULT!!!!! Failed to find expected speed configuration : %s ' % (cur_speed_string))
		return False


def checkLinkStatus(testCase, dut, portA, link_status):
	"""
	Check the link status of a port on a device is as expected.
	
	Parameter(s):
	testcase - <test case object> for which log should be updated
	dut - <switch object> for device to be configured
	portA - <port object> from the switch object to be configured
	link_status - <string> expected status
	
	Returns:
	True = as expected
	False = not as expected
	
	Description
	Check the link status for a port by searching for the string in the output for the "SHOW INTERFACE <port number> BRIEF" command.
	
	"""

	testCase.log('LOG {}: Checking link status'.format(dut.tty))
	dut.mode('#')
	output = dut.cmd('sh int %s brief' % portA.name)
	testCase.log(output)
  
	if output.count(link_status) == 1:
		testCase.log('RESULT>>>> Link status is as expected : %s' % (link_status))  
		return True
	else:
		testCase.log('RESULT!!!! Unexpected link status, expecting : %s' % (link_status))
		return False
