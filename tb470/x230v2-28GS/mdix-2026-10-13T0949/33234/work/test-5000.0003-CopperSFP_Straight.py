#!/usr/bin/python

import sys, time
import library_5000
from framework import ATTestSet, ATTestCase

class TestSet(ATTestSet.TestSet):

	def init(self, setup):
		self.setup = setup
		dut = self.setup.init_swi('swi_a')
		remote = self.setup.init_swi('swi_b')
		all_misc = setup.get_all_misc()
		portA = all_misc['dutSFPCopper']
		portB = all_misc['linkpSFPCopper']
		dut.portA = dut.init_port('portA',portA)
		remote.portB = remote.init_port('portB',portB)
		self.dut = dut
		self.remote = remote

	def configure(self):
		dut = self.dut
		dut.mode('#')
		self.log('---------------------------------------------------')
		self.log(dut.cmd('show sys'))
		self.log(dut.cmd('show sys plug'))
		self.log('---------------------------------------------------')



class TestCase_1(ATTestCase.TestCase):
	testCaseNum = 1
	testCaseDesc = 'SFP Copper - 1 Gig Straight Through - Confirm default settings on both ends'
	testCaseRef = ''
	testCaseMethod =  'step 1 - Confirm link up\n'
	testCaseMethod += 'step 2 - Confirm DUT speed auto , duplex auto, polarity auto\n'
	testCaseMethod += 'step 3 - Confirm Remote speed auto , duplex auto, polarity auto'

	def main(self):
		dut = self.dut
		portA = dut.portA
		remote = self.remote
		portB = remote.portB
		# for checking result
		speed = 'auto'
		duplex = 'auto'
		polarity = 'auto'
		link_status = 'running'
		error_counter = 0	
	
		# check link staus and then port status both ends
		if library_5000.checkLinkStatus(self,dut,portA,link_status)== False:
			error_counter += 1
	
		if library_5000.checkConfiguredPort(self, dut, portA, duplex, speed,polarity) == False:
			error_counter += 1

		if library_5000.checkConfiguredPort(self, remote, portB, duplex, speed,polarity) == False:
			error_counter += 1  
	
		if error_counter == 0:
			self.passed()
		else:
			self.failed()
	
	def tear_down(self):
		pass


class TestCase_2(ATTestCase.TestCase):
	testCaseNum = 2
	testCaseDesc = 'SFP Copper - 1 Gig Straight Through - Mixed Polarity: DUT = MDIX and Remote = MDI'
	testCaseRef = ''
	testCaseMethod =  'step 1 - Configure DUT polarity MDIX\n'
	testCaseMethod += 'step 2 - Configure Remote polarity MDI\n'
	testCaseMethod += 'step 3 - Confirm link up\n'
	testCaseMethod += 'step 4 - Confirm DUT speed auto, duplex auto, polarity MDIX\n'
	testCaseMethod += 'step 5 - Confirm Remote speed auto, duplex auto, polarity MDI'

	def main(self):
		dut = self.dut
		portA = dut.portA
		remote = self.remote	
		portB = remote.portB
		# for DUT configuration
		dut_port_config_1 = 'polarity'
		dut_port_value_1 = 'mdix'
		dut_expected_value_1 = 0
		# for remote configuration
		remote_port_config_1 = 'polarity'
		remote_port_value_1 = 'mdi'
		remote_expected_value_1 = 0
		# for checking dut result
		speed = 'auto'
		duplex = 'auto'
		polarity = 'mdix'
		link_status = 'running'
		# for checking remote result
		remote_speed = 'auto'
		remote_duplex = 'auto'
		remote_polarity = 'mdi'	
		# initialise error counter
		error_counter = 0
	
		if library_5000.configurePort(self, dut, portA, dut_port_config_1, dut_port_value_1, dut_expected_value_1) == False:
			error_counter += 1 
	
		if library_5000.configurePort(self, remote, portB, remote_port_config_1, remote_port_value_1, remote_expected_value_1) == False:
			error_counter += 1
	
		if library_5000.checkLinkStatus(self,dut,portA,link_status)== False:
			error_counter += 1

		if library_5000.checkConfiguredPort(self, dut, portA, duplex, speed, polarity) == False:
			error_counter += 1  

		if library_5000.checkConfiguredPort(self, remote, portB, remote_duplex, remote_speed, remote_polarity) == False:
			error_counter += 1  

		if error_counter == 0:
			self.passed()
		else:
			self.failed()

	def tear_down(self):
		# set port settings back to defaults (auto)
		dut = self.dut
		remote = self.remote
		portA = dut.portA
		portB = remote.portB
		library_5000.configureDefaultPort(self, dut, portA)
		library_5000.configureDefaultPort(self, remote, portB)

class TestCase_3(ATTestCase.TestCase):
	testCaseNum = 3
	testCaseDesc = 'SFP Copper - 1 Gig Straight Through - Polarity = MDIX both ends'
	testCaseRef = ''
	testCaseMethod =  'step 1 - Configure DUT polarity MDIX\n'
	testCaseMethod += 'step 2 - Configure Remote polarity MDIX\n'
	testCaseMethod += 'step 3 - Confirm link down\n'
	testCaseMethod += 'step 4 - Confirm DUT speed auto, duplex auto, polarity MDIX\n'
	testCaseMethod += 'step 5 - Confirm Remote speed auto, duplex auto, polarity MDIX'

	def main(self):
		dut = self.dut
		portA = dut.portA
		remote = self.remote	
		portB = remote.portB
		# for DUT configuration
		dut_port_config_1 = 'polarity'
		dut_port_value_1 = 'mdix'
		dut_expected_value_1 = 0
		# for remote configuration
		remote_port_config_1 = 'polarity'
		remote_port_value_1 = 'mdix'
		remote_expected_value_1 = 0
		# for checking dut result
		speed = 'auto'
		duplex = 'auto'
		polarity = 'mdix'
		link_status = 'down'
		# for checking remote result
		remote_speed = 'auto'
		remote_duplex = 'auto'
		remote_polarity = 'mdix'
		# initialise error counter
		error_counter = 0
	
		if library_5000.configurePort(self, dut, portA, dut_port_config_1, dut_port_value_1, dut_expected_value_1) == False:
			error_counter += 1 
	
		if library_5000.configurePort(self, remote, portB, remote_port_config_1, remote_port_value_1, remote_expected_value_1) == False:
			error_counter += 1
	
		if library_5000.checkLinkStatus(self,dut,portA,link_status)== False:
			error_counter += 1

		if library_5000.checkConfiguredPort(self, dut, portA, duplex, speed, polarity) == False:
			error_counter += 1  

		if library_5000.checkConfiguredPort(self, remote, portB, remote_duplex, remote_speed, remote_polarity) == False:
			error_counter += 1  

		if error_counter == 0:
			self.passed()
		else:
			self.failed()


	def tear_down(self):
		# set port settings back to defaults (auto)
		dut = self.dut
		remote = self.remote
		portA = dut.portA
		portB = remote.portB
		library_5000.configureDefaultPort(self, dut, portA)
		library_5000.configureDefaultPort(self, remote, portB)


class TestCase_4(ATTestCase.TestCase):
	testCaseNum = 4
	testCaseDesc = 'SFP Copper - 1 Gig Straight Through - Polarity = MDI both ends'
	testCaseRef = ''
	testCaseMethod =  'step 1 - Configure DUT polarity MDI\n'
	testCaseMethod += 'step 2 - Configure Remote polarity MDI\n'
	testCaseMethod += 'step 3 - Confirm link down\n'
	testCaseMethod += 'step 4 - Confirm DUT speed auto, duplex auto, polarity mdi\n'
	testCaseMethod += 'step 5 - Confirm Remote speed auto, duplex auto, polarity mdi'

	def main(self):
		dut = self.dut
		portA = dut.portA
		remote = self.remote	
		portB = remote.portB
		# for DUT configuration
		dut_port_config_1 = 'polarity'
		dut_port_value_1 = 'mdi'
		dut_expected_value_1 = 0
		# for remote configuration
		remote_port_config_1 = 'polarity'
		remote_port_value_1 = 'mdi'
		remote_expected_value_1 = 0
		# for checking dut result
		speed = 'auto'
		duplex = 'auto'
		polarity = 'mdi'
		link_status = 'down'
		# for checking remote result
		remote_speed = 'auto'
		remote_duplex = 'auto'
		remote_polarity = 'mdi'
		# initialise error counter
		error_counter = 0
	
		if library_5000.configurePort(self, dut, portA, dut_port_config_1, dut_port_value_1, dut_expected_value_1) == False:
			error_counter += 1 
	
		if library_5000.configurePort(self, remote, portB, remote_port_config_1, remote_port_value_1, remote_expected_value_1) == False:
			error_counter += 1
	
		if library_5000.checkLinkStatus(self,dut,portA,link_status)== False:
			error_counter += 1

		if library_5000.checkConfiguredPort(self, dut, portA, duplex, speed, polarity) == False:
			error_counter += 1  

		if library_5000.checkConfiguredPort(self, remote, portB, remote_duplex, remote_speed, remote_polarity) == False:
			error_counter += 1  

		if error_counter == 0:
			self.passed()
		else:
			self.failed()


	def tear_down(self):
		# set port settings back to defaults (auto)
		dut = self.dut
		remote = self.remote
		portA = dut.portA
		portB = remote.portB
		library_5000.configureDefaultPort(self, dut, portA)
		library_5000.configureDefaultPort(self, remote, portB)


class TestCase_5(ATTestCase.TestCase):
	testCaseNum = 5
	testCaseDesc = 'SFP Copper - 1 Gig Straight Through - Polarity mixed = DUT = MDI and Remote = MDIX'
	testCaseRef = ''
	testCaseMethod =  'step 1 - Configure DUT polarity MDI\n'
	testCaseMethod += 'step 2 - Configure Remote polarity MDIX\n'
	testCaseMethod += 'step 3 - Confirm link up\n'
	testCaseMethod += 'step 4 - Confirm DUT speed auto, duplex auto, polarity mdi\n'
	testCaseMethod += 'step 5 - Confirm Remote speed auto, duplex auto, polarity mdix'

	def main(self):
		dut = self.dut
		portA = dut.portA
		remote = self.remote	
		portB = remote.portB
		# for DUT configuration
		dut_port_config_1 = 'polarity'
		dut_port_value_1 = 'mdi'
		dut_expected_value_1 = 0
		# for remote configuration
		remote_port_config_1 = 'polarity'
		remote_port_value_1 = 'mdix'
		remote_expected_value_1 = 0
		# for checking dut result
		speed = 'auto'
		duplex = 'auto'
		polarity = 'mdi'
		link_status = 'running'
		# for checking remote result
		remote_speed = 'auto'
		remote_duplex = 'auto'
		remote_polarity = 'mdix'
		# initialise error counter
		error_counter = 0
	
		if library_5000.configurePort(self, dut, portA, dut_port_config_1, dut_port_value_1, dut_expected_value_1) == False:
			error_counter += 1 
	
		if library_5000.configurePort(self, remote, portB, remote_port_config_1, remote_port_value_1, remote_expected_value_1) == False:
			error_counter += 1
	
		if library_5000.checkLinkStatus(self,dut,portA,link_status)== False:
			error_counter += 1

		if library_5000.checkConfiguredPort(self, dut, portA, duplex, speed, polarity) == False:
			error_counter += 1  

		if library_5000.checkConfiguredPort(self, remote, portB, remote_duplex, remote_speed, remote_polarity) == False:
			error_counter += 1  

		if error_counter == 0:
			self.passed()
		else:
			self.failed()

	def tear_down(self):
		# set port settings back to defaults (auto)
		dut = self.dut
		remote = self.remote
		portA = dut.portA
		portB = remote.portB
		library_5000.configureDefaultPort(self, dut, portA)
		library_5000.configureDefaultPort(self, remote, portB)

class TestCase_6(ATTestCase.TestCase):
	testCaseNum = 6
	testCaseDesc = 'SFP Copper - 1 Gig Straight Through - Speed = auto 1000, Duplex = half, Polarity = auto both ends'
	testCaseRef = ''
	testCaseMethod =  'step 1 - Configure DUT speed auto 1000, duplex half, polarity auto - Confirm failure of Duplex command\n'
	testCaseMethod += 'step 2 - Configure Remote speed auto 1000, duplex half, polarity auto - Confirm failure of Duplex command\n'
	testCaseMethod += 'step 3 - Confirm link up\n'
	testCaseMethod += 'step 4 - Confirm DUT speed auto 1000, duplex auto, polarity auto\n'
	testCaseMethod += 'step 5 - Confirm Remote speed auto 1000, duplex auto, polarity auto'

	def main(self):
		dut = self.dut
		portA = dut.portA
		remote = self.remote	
		portB = remote.portB
		# for DUT configuration
		dut_port_config_1 = 'speed'
		dut_port_value_1 = 'auto 1000'
		dut_expected_value_1 = 0
		dut_port_config_2 = 'duplex'
		dut_port_value_2 = 'half'
		dut_expected_value_2 = 1
		dut_port_config_3 = 'polarity'
		dut_port_value_3 = 'auto'
		dut_expected_value_3 = 0
		# for remote configuration
		remote_port_config_1 = 'speed'
		remote_port_value_1 = 'auto 1000'
		remote_expected_value_1 = 0
		remote_port_config_2 = 'duplex'
		remote_port_value_2 = 'half'
		remote_expected_value_2 = 1
		remote_port_config_3 = 'polarity'
		remote_port_value_3 = 'auto'
		remote_expected_value_3 = 0
		# for checking dut result
		speed = 'auto 1000'
		duplex = 'auto'
		polarity = 'auto'
		link_status = 'running'
		# for checking remote result
		remote_speed = 'auto 1000'
		remote_duplex = 'auto'
		remote_polarity = 'auto'
		# initialise error counter
		error_counter = 0
	
		if library_5000.configurePort(self, dut, portA, dut_port_config_1, dut_port_value_1, dut_expected_value_1) == False:
			error_counter += 1 

		if library_5000.configurePort(self, dut, portA, dut_port_config_2, dut_port_value_2, dut_expected_value_2) == False:
			error_counter += 1 
	
		if library_5000.configurePort(self, dut, portA, dut_port_config_3, dut_port_value_3, dut_expected_value_3) == False:
			error_counter += 1 
	
		if library_5000.configurePort(self, remote, portB, remote_port_config_1, remote_port_value_1, remote_expected_value_1) == False:
			error_counter += 1

		if library_5000.configurePort(self, remote, portB, remote_port_config_2, remote_port_value_2, remote_expected_value_2) == False:
			error_counter += 1

		if library_5000.configurePort(self, remote, portB, remote_port_config_3, remote_port_value_3, remote_expected_value_3) == False:
			error_counter += 1

		if library_5000.checkLinkStatus(self,dut,portA,link_status)== False:
			error_counter += 1

		if library_5000.checkConfiguredPort(self, dut, portA, duplex, speed, polarity) == False:
			error_counter += 1  

		if library_5000.checkConfiguredPort(self, remote, portB, remote_duplex, remote_speed, remote_polarity) == False:
			error_counter += 1  

		if error_counter == 0:
			self.passed()
		else:
			self.failed()

	def tear_down(self):
		# set port settings back to defaults (auto)
		dut = self.dut
		remote = self.remote
		portA = dut.portA
		portB = remote.portB
		library_5000.configureDefaultPort(self, dut, portA)
		library_5000.configureDefaultPort(self, remote, portB)


class TestCase_7(ATTestCase.TestCase):
	testCaseNum = 7
	testCaseDesc = 'SFP Copper - 1 Gig Straight Through - Speed = auto 100, Duplex = full, Polarity = auto both ends'
	testCaseRef = ''
	testCaseMethod =  'step 1 - Configure DUT speed auto 100, duplex full, polarity auto\n'
	testCaseMethod += 'step 2 - Configure Remote speed auto 100, duplex full, polarity auto\n'
	testCaseMethod += 'step 3 - Confirm link up\n'
	testCaseMethod += 'step 4 - Confirm DUT speed auto 100, duplex full, polarity auto\n'
	testCaseMethod += 'step 5 - Confirm Remote speed auto 100, duplex full, polarity auto'

	def main(self):
		dut = self.dut
		portA = dut.portA
		remote = self.remote	
		portB = remote.portB
		# for DUT configuration
		dut_port_config_1 = 'speed'
		dut_port_value_1 = 'auto 100'
		dut_expected_value_1 = 0
		dut_port_config_2 = 'duplex'
		dut_port_value_2 = 'full'
		dut_expected_value_2 = 0
		dut_port_config_3 = 'polarity'
		dut_port_value_3 = 'auto'
		dut_expected_value_3 = 0
		# for remote configuration
		remote_port_config_1 = 'speed'
		remote_port_value_1 = 'auto 100'
		remote_expected_value_1 = 0
		remote_port_config_2 = 'duplex'
		remote_port_value_2 = 'full'
		remote_expected_value_2 = 0
		remote_port_config_3 = 'polarity'
		remote_port_value_3 = 'auto'
		remote_expected_value_3 = 0
		# for checking dut result
		speed = 'auto 100'
		duplex = 'full'
		polarity = 'auto'
		link_status = 'running'
		# for checking remote result
		remote_speed = 'auto 100'
		remote_duplex = 'full'
		remote_polarity = 'auto'
		# initialise error counter
		error_counter = 0
	
		if library_5000.configurePort(self, dut, portA, dut_port_config_1, dut_port_value_1, dut_expected_value_1) == False:
			error_counter += 1 

		if library_5000.configurePort(self, dut, portA, dut_port_config_2, dut_port_value_2, dut_expected_value_2) == False:
			error_counter += 1 
	
		if library_5000.configurePort(self, dut, portA, dut_port_config_3, dut_port_value_3, dut_expected_value_3) == False:
			error_counter += 1 
	
		if library_5000.configurePort(self, remote, portB, remote_port_config_1, remote_port_value_1, remote_expected_value_1) == False:
			error_counter += 1

		if library_5000.configurePort(self, remote, portB, remote_port_config_2, remote_port_value_2, remote_expected_value_2) == False:
			error_counter += 1

		if library_5000.configurePort(self, remote, portB, remote_port_config_3, remote_port_value_3, remote_expected_value_3) == False:
			error_counter += 1

		if library_5000.checkLinkStatus(self,dut,portA,link_status)== False:
			error_counter += 1

		if library_5000.checkConfiguredPort(self, dut, portA, duplex, speed, polarity) == False:
			error_counter += 1  

		if library_5000.checkConfiguredPort(self, remote, portB, remote_duplex, remote_speed, remote_polarity) == False:
			error_counter += 1  

		if error_counter == 0:
			self.passed()
		else:
			self.failed()
	
	def tear_down(self):
		# set port settings back to defaults (auto)
		dut = self.dut
		remote = self.remote
		portA = dut.portA
		portB = remote.portB
		library_5000.configureDefaultPort(self, dut, portA)
		library_5000.configureDefaultPort(self, remote, portB)

class TestCase_8(ATTestCase.TestCase):
	testCaseNum = 8
	testCaseDesc = 'SFP Copper - 1 Gig Straight Through - Speed = auto 100, Duplex = half, Polarity = auto both ends'
	testCaseRef = ''
	testCaseMethod =  'step 1 - Configure DUT speed auto 100, duplex half, polarity auto\n'
	testCaseMethod += 'step 2 - Configure Remote speed auto 100, duplex half, polarity auto\n'
	testCaseMethod += 'step 3 - Confirm link up\n'
	testCaseMethod += 'step 4 - Confirm DUT speed auto 100, duplex half, polarity auto\n'
	testCaseMethod += 'step 5 - Confirm Remote speed auto 100, duplex half, polarity auto'

	def main(self):
		dut = self.dut
		portA = dut.portA
		remote = self.remote	
		portB = remote.portB
		# for DUT configuration
		dut_port_config_1 = 'speed'
		dut_port_value_1 = 'auto 100'
		dut_expected_value_1 = 0
		dut_port_config_2 = 'duplex'
		dut_port_value_2 = 'half'
		dut_expected_value_2 = 0
		dut_port_config_3 = 'polarity'
		dut_port_value_3 = 'auto'
		dut_expected_value_3 = 0
		# for remote configuration
		remote_port_config_1 = 'speed'
		remote_port_value_1 = 'auto 100'
		remote_expected_value_1 = 0
		remote_port_config_2 = 'duplex'
		remote_port_value_2 = 'half'
		remote_expected_value_2 = 0
		remote_port_config_3 = 'polarity'
		remote_port_value_3 = 'auto'
		remote_expected_value_3 = 0
		# for checking dut result
		speed = 'auto 100'
		duplex = 'half'
		polarity = 'auto'
		link_status = 'running'
		# for checking remote result
		remote_speed = 'auto 100'
		remote_duplex = 'half'
		remote_polarity = 'auto'
		# initialise error counter
		error_counter = 0
	
		if library_5000.configurePort(self, dut, portA, dut_port_config_1, dut_port_value_1, dut_expected_value_1) == False:
			error_counter += 1 

		if library_5000.configurePort(self, dut, portA, dut_port_config_2, dut_port_value_2, dut_expected_value_2) == False:
			error_counter += 1 
	
		if library_5000.configurePort(self, dut, portA, dut_port_config_3, dut_port_value_3, dut_expected_value_3) == False:
			error_counter += 1 
	
		if library_5000.configurePort(self, remote, portB, remote_port_config_1, remote_port_value_1, remote_expected_value_1) == False:
			error_counter += 1

		if library_5000.configurePort(self, remote, portB, remote_port_config_2, remote_port_value_2, remote_expected_value_2) == False:
			error_counter += 1

		if library_5000.configurePort(self, remote, portB, remote_port_config_3, remote_port_value_3, remote_expected_value_3) == False:
			error_counter += 1

		if library_5000.checkLinkStatus(self,dut,portA,link_status)== False:
			error_counter += 1

		if library_5000.checkConfiguredPort(self, dut, portA, duplex, speed, polarity) == False:
			error_counter += 1  

		if library_5000.checkConfiguredPort(self, remote, portB, remote_duplex, remote_speed, remote_polarity) == False:
			error_counter += 1  

		if error_counter == 0:
			self.passed()
		else:
			self.failed()

	def tear_down(self):
		# set port settings back to defaults (auto)
		dut = self.dut
		remote = self.remote
		portA = dut.portA
		portB = remote.portB
		library_5000.configureDefaultPort(self, dut, portA)
		library_5000.configureDefaultPort(self, remote, portB)

class TestCase_9(ATTestCase.TestCase):
	testCaseNum = 9
	testCaseDesc = 'SFP Copper - 1 Gig Straight Through - Speed = auto 10, Duplex = full, Polarity = auto both ends'
	testCaseRef = ''
	testCaseMethod =  'step 1 - Configure DUT speed auto 10, duplex full, polarity auto\n'
	testCaseMethod += 'step 2 - Configure Remote speed auto 10, duplex full, polarity auto\n'
	testCaseMethod += 'step 3 - Confirm link up\n'
	testCaseMethod += 'step 4 - Confirm DUT speed auto 10, duplex full, polarity auto\n'
	testCaseMethod += 'step 5 - Confirm Remote speed auto 10, duplex full, polarity auto'

	def main(self):
		dut = self.dut
		portA = dut.portA
		remote = self.remote	
		portB = remote.portB
		# for DUT configuration
		dut_port_config_1 = 'speed'
		dut_port_value_1 = 'auto 10'
		dut_expected_value_1 = 0
		dut_port_config_2 = 'duplex'
		dut_port_value_2 = 'full'
		dut_expected_value_2 = 0
		dut_port_config_3 = 'polarity'
		dut_port_value_3 = 'auto'
		dut_expected_value_3 = 0
		# for remote configuration
		remote_port_config_1 = 'speed'
		remote_port_value_1 = 'auto 10'
		remote_expected_value_1 = 0
		remote_port_config_2 = 'duplex'
		remote_port_value_2 = 'full'
		remote_expected_value_2 = 0
		remote_port_config_3 = 'polarity'
		remote_port_value_3 = 'auto'
		remote_expected_value_3 = 0
		# for checking dut result
		speed = 'auto 10'
		duplex = 'full'
		polarity = 'auto'
		link_status = 'running'
		# for checking remote result
		remote_speed = 'auto 10'
		remote_duplex = 'full'
		remote_polarity = 'auto'
		# initialise error counter
		error_counter = 0
	
		if library_5000.configurePort(self, dut, portA, dut_port_config_1, dut_port_value_1, dut_expected_value_1) == False:
			error_counter += 1 

		if library_5000.configurePort(self, dut, portA, dut_port_config_2, dut_port_value_2, dut_expected_value_2) == False:
			error_counter += 1 
	
		if library_5000.configurePort(self, dut, portA, dut_port_config_3, dut_port_value_3, dut_expected_value_3) == False:
			error_counter += 1 
	
		if library_5000.configurePort(self, remote, portB, remote_port_config_1, remote_port_value_1, remote_expected_value_1) == False:
			error_counter += 1

		if library_5000.configurePort(self, remote, portB, remote_port_config_2, remote_port_value_2, remote_expected_value_2) == False:
			error_counter += 1

		if library_5000.configurePort(self, remote, portB, remote_port_config_3, remote_port_value_3, remote_expected_value_3) == False:
			error_counter += 1

		if library_5000.checkLinkStatus(self,dut,portA,link_status)== False:
			error_counter += 1

		if library_5000.checkConfiguredPort(self, dut, portA, duplex, speed, polarity) == False:
			error_counter += 1  

		if library_5000.checkConfiguredPort(self, remote, portB, remote_duplex, remote_speed, remote_polarity) == False:
			error_counter += 1  

		if error_counter == 0:
			self.passed()
		else:
			self.failed()

	def tear_down(self):
		# set port settings back to defaults (auto)
		dut = self.dut
		remote = self.remote
		portA = dut.portA
		portB = remote.portB
		library_5000.configureDefaultPort(self, dut, portA)
		library_5000.configureDefaultPort(self, remote, portB)

class TestCase_10(ATTestCase.TestCase):
	testCaseNum = 10
	testCaseDesc = 'SFP Copper - 1 Gig Straight Through - Speed = auto 10, Duplex = half, Polarity = auto both ends'
	testCaseRef = ''
	testCaseMethod =  'step 1 - Configure DUT speed auto 10, duplex half, polarity auto\n'
	testCaseMethod += 'step 2 - Configure Remote speed auto 10, duplex half, polarity auto\n'
	testCaseMethod += 'step 3 - Confirm link up\n'
	testCaseMethod += 'step 4 - Confirm DUT speed auto 10, duplex half, polarity auto\n'
	testCaseMethod += 'step 5 - Confirm Remote speed auto 10, duplex half, polarity auto'

	def main(self):
		dut = self.dut
		portA = dut.portA
		remote = self.remote	
		portB = remote.portB
		# for DUT configuration
		dut_port_config_1 = 'speed'
		dut_port_value_1 = 'auto 10'
		dut_expected_value_1 = 0
		dut_port_config_2 = 'duplex'
		dut_port_value_2 = 'half'
		dut_expected_value_2 = 0
		dut_port_config_3 = 'polarity'
		dut_port_value_3 = 'auto'
		dut_expected_value_3 = 0
		# for remote configuration
		remote_port_config_1 = 'speed'
		remote_port_value_1 = 'auto 10'
		remote_expected_value_1 = 0
		remote_port_config_2 = 'duplex'
		remote_port_value_2 = 'half'
		remote_expected_value_2 = 0
		remote_port_config_3 = 'polarity'
		remote_port_value_3 = 'auto'
		remote_expected_value_3 = 0
		# for checking dut result
		speed = 'auto 10'
		duplex = 'half'
		polarity = 'auto'
		link_status = 'running'
		# for checking remote result
		remote_speed = 'auto 10'
		remote_duplex = 'half'
		remote_polarity = 'auto'
		# initialise error counter
		error_counter = 0
	
		if library_5000.configurePort(self, dut, portA, dut_port_config_1, dut_port_value_1, dut_expected_value_1) == False:
			error_counter += 1 

		if library_5000.configurePort(self, dut, portA, dut_port_config_2, dut_port_value_2, dut_expected_value_2) == False:
			error_counter += 1 
	
		if library_5000.configurePort(self, dut, portA, dut_port_config_3, dut_port_value_3, dut_expected_value_3) == False:
			error_counter += 1 
	
		if library_5000.configurePort(self, remote, portB, remote_port_config_1, remote_port_value_1, remote_expected_value_1) == False:
			error_counter += 1

		if library_5000.configurePort(self, remote, portB, remote_port_config_2, remote_port_value_2, remote_expected_value_2) == False:
			error_counter += 1

		if library_5000.configurePort(self, remote, portB, remote_port_config_3, remote_port_value_3, remote_expected_value_3) == False:
			error_counter += 1

		if library_5000.checkLinkStatus(self,dut,portA,link_status)== False:
			error_counter += 1

		if library_5000.checkConfiguredPort(self, dut, portA, duplex, speed, polarity) == False:
			error_counter += 1  

		if library_5000.checkConfiguredPort(self, remote, portB, remote_duplex, remote_speed, remote_polarity) == False:
			error_counter += 1  

		if error_counter == 0:
			self.passed()
		else:
			self.failed()

	def tear_down(self):
		# set port settings back to defaults (auto)
		dut = self.dut
		remote = self.remote
		portA = dut.portA
		portB = remote.portB
		library_5000.configureDefaultPort(self, dut, portA)
		library_5000.configureDefaultPort(self, remote, portB)


class TestCase_11(ATTestCase.TestCase):
	testCaseNum = 11
	testCaseDesc = 'SFP Copper - 1 Gig Straight Through - Speed = auto, Duplex = auto, Polarity = auto'
	testCaseRef = ''
	testCaseMethod =  'step 1 - Configure DUT speed auto, duplex auto, polarity auto\n'
	testCaseMethod += 'step 2 - Configure Remote speed auto auto, duplex auto, polarity auto\n'
	testCaseMethod += 'step 3 - Confirm link up\n'
	testCaseMethod += 'step 4 - Confirm DUT speed auto, duplex auto, polarity auto\n'
	testCaseMethod += 'step 5 - Confirm Remote speed auto, duplex auto, polarity auto'

	def main(self):
		dut = self.dut
		portA = dut.portA
		remote = self.remote	
		portB = remote.portB
		# for DUT configuration
		dut_port_config_1 = 'speed'
		dut_port_value_1 = 'auto'
		dut_expected_value_1 = 0
		dut_port_config_2 = 'duplex'
		dut_port_value_2 = 'auto'
		dut_expected_value_2 = 0
		dut_port_config_3 = 'polarity'
		dut_port_value_3 = 'auto'
		dut_expected_value_3 = 0
		# for remote configuration
		remote_port_config_1 = 'speed'
		remote_port_value_1 = 'auto'
		remote_expected_value_1 = 0
		remote_port_config_2 = 'duplex'
		remote_port_value_2 = 'auto'
		remote_expected_value_2 = 0
		remote_port_config_3 = 'polarity'
		remote_port_value_3 = 'auto'
		remote_expected_value_3 = 0
		# for checking dut result
		speed = 'auto'
		duplex = 'auto'
		polarity = 'auto'
		link_status = 'running'
		# for checking remote result
		remote_speed = 'auto'
		remote_duplex = 'auto'
		remote_polarity = 'auto'	
		# initialise error counter
		error_counter = 0
	
		if library_5000.configurePort(self, dut, portA, dut_port_config_1, dut_port_value_1, dut_expected_value_1) == False:
			error_counter += 1 

		if library_5000.configurePort(self, dut, portA, dut_port_config_2, dut_port_value_2, dut_expected_value_2) == False:
			error_counter += 1 

		if library_5000.configurePort(self, dut, portA, dut_port_config_3, dut_port_value_3, dut_expected_value_3) == False:
			error_counter += 1 
			
		if library_5000.configurePort(self, remote, portB, remote_port_config_1, remote_port_value_1, remote_expected_value_1) == False:
			error_counter += 1

		if library_5000.configurePort(self, remote, portB, remote_port_config_2, remote_port_value_2, remote_expected_value_2) == False:
			error_counter += 1

		if library_5000.configurePort(self, remote, portB, remote_port_config_3, remote_port_value_3, remote_expected_value_3) == False:
			error_counter += 1

		if library_5000.checkLinkStatus(self,dut,portA,link_status)== False:
			error_counter += 1

		if library_5000.checkConfiguredPort(self, dut, portA, duplex, speed,polarity) == False:
			error_counter += 1  

		if library_5000.checkConfiguredPort(self, remote, portB, remote_duplex, remote_speed,remote_polarity) == False:
			error_counter += 1  

		if error_counter == 0:
			self.passed()
		else:
			self.failed()
	def tear_down(self):
		# set port settings back to defaults (auto)
		dut = self.dut
		remote = self.remote
		portA = dut.portA
		portB = remote.portB
		library_5000.configureDefaultPort(self, dut, portA)
		library_5000.configureDefaultPort(self, remote, portB)

if __name__=='__main__':
	ts = TestSet()
	ts.add_testCase(TestCase_1())
	ts.add_testCase(TestCase_2())
	ts.add_testCase(TestCase_3())
	ts.add_testCase(TestCase_4())
	ts.add_testCase(TestCase_5())
	ts.add_testCase(TestCase_6())
	ts.add_testCase(TestCase_7())
	ts.add_testCase(TestCase_8())
	ts.add_testCase(TestCase_9())
	ts.add_testCase(TestCase_10())
	ts.add_testCase(TestCase_11())
	ts.run(sys.argv)
