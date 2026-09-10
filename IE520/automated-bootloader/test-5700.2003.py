#!/usr/bin/python3

import sys, time
from framework import ATTestSet, ATTestCase
from framework.ATDrivers.ATBootLoader import *
from framework.ATLibrary.ATTools import watch_consoles_for_bootup

from library_5700 import *

class TestSet(ATTestSet.TestSet):

    FEATURES = ['ACCESS']

    def init(self, setup):
        tb    = setup.init_tb()
        dut   = setup.init_swi('swi_a')
        (dut.portA, tb.ethA) = setup.init_portlink(dut, tb)
        self.tb  = tb
        self.dut = dut

    def configure(self):
        tb = self.tb
        dut = self.dut
        disableStacking(dut)
        dut.mode(')#')
        dut.cmd('no boot system')
        dut.cmd('no boot system backup')
        get_all_misc(self)
        createFlashBootImages(self, dut,filenames=[self.MAIN_RELEASE, self.BACKUP_RELEASE])


class TestCase_1(ATTestCase.TestCase):
    testCaseDesc   = "Diagnostics menu option '0. Restart'"
    testCaseRef    = "AWP2754"
    testCaseMethod =  "1. Enter the Diagnostics menu\n"
    testCaseMethod += "2. Check option '0. Restart' reboots the device\n"

    def configure(self):
        get_all_misc(self)

    def main(self):
        dut = self.dut
        self.log(['', 'Enter the Diagnostics menu'])
        if not enter_diagnostics_menu_with_retry(self, dut):
            self.failed("Problem occurred entering Diagnostics menu")
        else:
            self.passed("in Diagnostics menu")
            time.sleep(2)
            self.log("Check option '0. Restart' reboots the device")
            # Was: gated AND asserted on "Verifying release", which the device never
            # prints - a guaranteed FAIL.  Bounded to 120 s here, so it failed fast
            # rather than stalling; the 120 s ceiling is kept because the correct
            # markers appear early in boot, preserving the intended fast-fail.
            bootOutput, booted = wait_for_release_boot(self, dut, '0', waitTime=120)
            if booted:
                self.passed("device was booted")
            else:
                self.failed("device wasn't booted")
                self.log(bootOutput)
        if self.has_failed():
            restore_boot_from_tftp(self, dut)
        dut.mode('#')


class TestCase_2(ATTestCase.TestCase):
    testCaseDesc   = "Diagnostics menu option '1. Full RAM test'"
    testCaseRef    = "AWP2755"
    testCaseMethod = '1. Enter the Diagnostics menu\n'
    testCaseMethod += '2. Run the full RAM test, Option 1.\n'
    testCaseMethod += '3. Check 5 iterations of the RAM test are run\n'
    testCaseMethod += '4. Check there are no errors reported\n'

    def configure(self):
        get_all_misc(self)

    def main(self):
        dut = self.dut
        self.log(['', 'Enter the Diagnostics menu'])
        if not enter_diagnostics_menu_with_retry(self, dut):
            self.failed("Problem occurred entering Diagnostics menu")
        else:
            # check for two types of output, most switches out put 'Pass 5' and FS980 and routers output '5 iteration'
            self.log(['', 'Run the full RAM test, Option 1.'])
            self.log("Check 5 iterations of the RAM test are run")
            output = dut.send('1',strList=['Pass 5',' 5 iterations with 0 error'])
            dut.cmd('q')
            if ('Pass 5' in output or ' 5 iteration' in output) and 'Full RAM test' in output:
                self.passed("ram test got to iteration 5")
            else:
                self.failed("ram test didn't get to iteration 5")
                log_device_output(self, output)


            self.log(['', 'Check there are no errors reported'])
            if output.count('total errors 0') == 5 or output.count('iteration(s) with 0 error') >= 5 or (output.count('iterations with 0 error') >= 4 and output.count('iteration with 0 error') == 1):
                self.passed("no errors seen")
            else:
                self.failed("errors seen")
                log_device_output(self, output)
        
        if self.has_failed():
            restore_boot_from_tftp(self, dut)
        else:
            dut.cmd('9')
        
        dut.mode('#')


class TestCase_3(ATTestCase.TestCase):
    testCaseDesc   = "Diagnostics menu option '2. Quick RAM test'"
    testCaseRef    = "AWP2756"
    testCaseMethod = '1. Enter the Diagnostics menu\n'
    testCaseMethod += '2. Run the quick RAM test, Option 2.\n'
    testCaseMethod += '3. Check the RAM test has passed\n'

    def configure(self):
        get_all_misc(self)

    def main(self):
        dut = self.dut
        self.log(['', 'Enter the Diagnostics menu'])
        if not enter_diagnostics_menu_with_retry(self, dut):
            self.failed("Problem occurred entering Diagnostics menu")
        else:
            self.log(['', 'Run the quick RAM test, Option 2.'])
            self.log("Check the RAM test has passed")
            output = dut.send('2',strList=['Bootup Stage 1 Diagnostics Menu:'])
            if 'Pass 1  total errors 0  PASS' in output or 'Test of DRAM with 1 iteration(s) with 0 error' in output or 'Test of DRAM with 1 iteration with 0 error' in output:
                self.passed("quick ram test passed")
            else:
                self.failed("quick ram test failed")
                log_device_output(self, output)

        if self.has_failed():
            restore_boot_from_tftp(self, dut)
        else:
            dut.cmd('9')


class TestCase_4(ATTestCase.TestCase):
    testCaseDesc   = 'Diagnostics menu option 3, Battery backed RAM (NVS) test'
    testCaseRef    = "AWP2757"
    testCaseMethod = '1. Enter the Diagnostics menu\n'
    testCaseMethod += '2. Run the Battery backed RAM (NVS) test, Option 3.\n'
    testCaseMethod += '3. Check the NVS test has run 10 iterations and passed\n'
    testCaseMethod += '4. Check there are no errors reported\n'

    def configure(self):
        get_all_misc(self)

    def main(self):
        dut = self.dut
        #test option 3, Battery backed RAM (NVS) test
        self.log("Enter the Diagnostics menu.")

        # Enter the diagnostics menu and look fot NVS test option.
        if not enter_diagnostics_menu_with_retry(self, dut):
            self.failed("Problem occurred entering Diagnostics menu")
        else:
            output = dut.cmd(' ')
            if "NVS" in output:
                self.log("Run the Bootloader Battery backed RAM (NVS) test, level 1 Option 3.")
                self.log("Check the NVS test has run 10 iterations and passed")
                dut.send('3',strList=['Press Y'])
                output = dut.send('Y',strList=['Pass 11'])
                self.log("Check there are no errors reported")
                if output.count('total errors 0') >= 10:
                    self.passed("no errors seen")
                    dut.cmd('q')
                    dut.cmd('9')
                else:
                    self.failed("errors seen:")
                    log_device_output(self, output)
            else:
                self.supported = False
                self.failed("Test case not supported on this device. No NVS.")
                self.log("Expected 'NVS' in output:")
                log_device_output(self, output)
                dut.cmd('0')
            
        if self.supported and self.has_failed():
            restore_boot_from_tftp(self, dut)
            dut.mode('#')


class TestCase_5(ATTestCase.TestCase):
    testCaseDesc   = 'Diagnostics menu option 4, Bootloader ROM checksum test'
    testCaseRef    = "AWP2758"
    testCaseMethod = '1. Enter the Diagnostics menu\n'
    testCaseMethod += '2. Run the Bootloader ROM checksum test, Option 4.\n'
    testCaseMethod += '3. Check the checksums have been seen\n'

    def configure(self):
        dut = self.dut
        if dut.software_starts_with(['SBx908NG']):
            self.failed('Bootloader ROM checksum test not supported on this platform, test unsupported')
            self.supported = False
            self.powerCycleOnFail = False
        get_all_misc(self)

    def main(self):
        if not self.supported:
            self.log('Skipping unsupported test')
            return

        dut = self.dut
        # Test option 4, Bootloader ROM checksum test
        # This option can be in one of two places: Diagnostion menu level 1 option (4) or 2 as option (6).
        self.log(['', 'Enter the Diagnostics menu'])
        if not enter_diagnostics_menu_with_retry(self, dut):
            self.failed("Problem occurred entering Diagnostics menu")
        else:
            keyWord = 'Bootloader ROM checksum test'
            self.log(['', f'Find the {keyWord}'])
            output = dut.cmd(' ')
            if keyWord in output:
                self.log(f'Run the {keyWord} level 1 Option 4.')
                output = dut.cmd('4')
            else:
                self.log(f'"{keyWord}" not in menu level 1.')
                output = dut.send('7', strList=['Entering stage 2...'])
                output += dut.send('', strList=['Enter selection'], waitTime=30)
                if keyWord in output:
                    self.log(f'Run the {keyWord}, level 2 Option 6.')
                    output = dut.cmd('6')
                else:
                    self.failed(f'"{keyWord}" not found at level 1 or level 2:')
                    log_device_output(self, output)
                    restore_boot_from_tftp(self, dut)
                    return

            self.log(['', 'Check the checksums have been seen'])
            if dut.software_starts_with(['IE2', 'IE3', 'IE5', 'x510', 'x310','GS900']):
                keyWords = ['ROM checksum0']
            else:
                keyWords = ['ROM checksum0', 'ROM checksum1']
            
            if all(keyWord in output for keyWord in keyWords):
                self.passed("checksum(s) seen:")
                self.log([f'    {line}' for line in output.splitlines() if 'checksum' in line and 'test' not in line])
            else:
                self.failed('checksum(s) not seen, expected "{}":'.format('", "'.join(map(str, keyWords))))
                log_device_output(self, output)
            self.log('')

        if self.has_failed(): 
            restore_boot_from_tftp(self, dut)
        else:
            dut.cmd('9')
        
        dut.mode('#')


class TestCase_6(ATTestCase.TestCase):
    testCaseDesc   = 'Diagnostics menu option 7, Enter the Bootup stage 2 diagnostics menu'
    testCaseRef    = "AWP2759"
    testCaseMethod = '1. Enter the Diagnostics menu\n'
    testCaseMethod += '2. Enter the Bootup stage 2 diagnostics menu, Option 7.\n'
    testCaseMethod += '3. Check the Bootup stage 2 diagnostics menu is displayed\n'

    def configure(self):
        get_all_misc(self)

    def main(self):
        dut = self.dut
        self.log(['', 'Enter the Diagnostics menu'])
        if not enter_diagnostics_menu_with_retry(self, dut):
            self.failed("Problem occurred entering Diagnostics menu")
        else:
            self.log(['', 'Enter the Bootup stage 2 diagnostics menu, Option 7.'])
            output = dut.cmd('7')
            self.log("Check the Bootup stage 2 diagnostics menu is displayed")

            keyWord = 'Bootup Stage 2 Diagnostics Menu'
            if keyWord in output:
                self.passed(f'entered "{keyWord}"')
            else:
                self.failed(f'did not enter diagnostics stage 2 menu, expected "{keyWord}":')
                log_device_output(self, output)
        
        if self.has_failed():
            restore_boot_from_tftp(self, dut)
        else:
            dut.cmd('0')


class TestCase_7(ATTestCase.TestCase):
    testCaseDesc   = 'Diagnostics menu option 8, Quit to U-Boot shell'
    testCaseExcl   = {'dut' : ['ARX200S', 'x240', 'x250', 'x540', 'SE240', 'SE250', 'SE540']} 
    testCaseRef    = "AWP2760"
    testCaseMethod = '1. Enter the Diagnostics menu\n'
    testCaseMethod += '2. Enter the U-Boot shell, Option 8.\n'
    testCaseMethod += '3. Check the system is currently in the U-Boot shell\n'
    testCaseMethod += '4. Reset and reboot\n'

    def configure(self):
        get_all_misc(self)

    def main(self):
        dut = self.dut
        #test option 8, Quit to U-Boot shell
        self.log(['', 'Enter the Diagnostics menu'])
        if not enter_diagnostics_menu_with_retry(self, dut):
            self.failed("Problem occurred entering Diagnostics menu")
        else:
            self.log(['', 'Enter the U-Boot shell, Option 8.'])
            dut.cmd('8')

            self.log("Check the system is currently in the U-Boot shell")
            output = dut.cmd('.') # need to send an invalid char: '.' used.
            keyWord = 'Unknown command'
            if keyWord in output:
                self.passed("entered u-boot from diagnostics menu")
            else:
                self.failed(f'did not enter u-boot from diagnostics menu, expected "{keyWord}":')
                log_device_output(self, output)
        
        if self.has_failed():
            restore_boot_from_tftp(self, dut)
        else:
            self.log("Reset and reboot")
            dut.send('reset\n')		
        
        dut.mode('#')


class TestCase_8(ATTestCase.TestCase):
    testCaseDesc   = 'Diagnostics menu option 9, Quit the menu and continue rebooting'
    testCaseRef    = "AWP2761"
    testCaseMethod = '1. Enter the Diagnostics menu\n'
    testCaseMethod += '2. Quit the menu and continue rebooting, Option 9.\n'

    def configure(self):
        get_all_misc(self)

    def main(self):
        dut = self.dut
        #test option 9, Quit and continue booting
        self.log(['', 'Enter the Diagnostics menu'])
        if not enter_diagnostics_menu_with_retry(self, dut):
            self.failed("Problem occurred entering Diagnostics menu")
        else:
            self.log(['', 'Quit the menu and continue rebooting, Option 9.'])
            # Was: keyWord = 'Verifying release' with no waitTime - the device never
            # prints it, so this was a guaranteed FAIL a flat 30 min after a healthy
            # boot out of the stage 1 diagnostics menu.
            output, booted = wait_for_release_boot(self, dut, '9')
            if booted:
                self.passed("device booted from diagnostics stage 1 menu")
            else:
                self.failed(f'device did not boot from diagnostics stage 1 menu, expected one of {BOOT_MARKERS}:')
                log_device_output(self, output)
        
        if self.has_failed():
            restore_boot_from_tftp(self, dut)
        
        dut.mode('#')


class TestCase_9(ATTestCase.TestCase):
    testCaseDesc   = 'Boot stage 2 Diagnostics menu, option 0, Restart'
    testCaseRef    = "AWP2762"
    testCaseMethod = '1. Enter the Boot stage 2 Diagnostics menu\n'
    testCaseMethod += '2. Quit the menu restart the device, Option 0.\n'

    def configure(self):
        get_all_misc(self)

    def main(self):
        dut = self.dut
        if not enter_diagnostics_menu_with_retry(self, dut):
            self.failed("Problem occurred entering Diagnostics menu")
        else:
            self.log("Enter the Boot stage 2 Diagnostics menu")
            keyWord = 'Stage 2 Diagnostics Menu:'
            output = dut.send('7', strList=[keyWord])

            if keyWord not in output:
                self.failed(f'did not enter {keyWord}, expected "{keyWord}":')
                log_device_output(self, output)
            else:
                self.log("Quit the menu restart the device, Option 0.")
                # Was: keyWord = 'Verifying release' with no waitTime - guaranteed
                # FAIL 30 min after a healthy restart from the stage 2 menu.
                output, booted = wait_for_release_boot(self, dut, '0')
                if booted:
                    self.passed("device booted from diagnostics stage 2 menu")
                else:
                    self.failed(f'device did not boot from diagnostics stage 2 menu, expected one of {BOOT_MARKERS}:')
                    log_device_output(self, output)
        
        if self.has_failed():
            restore_boot_from_tftp(self, dut)
        else:
            dut.cmd('9')
        
        dut.mode('#')


class TestCase_10(ATTestCase.TestCase):
    testCaseDesc   = 'Boot stage 2 Diagnostics menu, option 2. Test FLASH (Filesystem only)'
    testCaseRef    = "AWP2763"
    testCaseMethod = 'Diagnostics menu option 22\n'

    def configure(self):
        get_all_misc(self)

    def main(self):
        dut = self.dut
        if not enter_diagnostics_menu_with_retry(self, dut):
            self.failed("Problem occurred entering Diagnostics menu")
        else:
            self.log("Enter the Boot stage 2 Diagnostics menu")
            keywords = ['Entering stage 2']
            output = dut.send('7', strList=keywords)
            dut.send('', strList=['Enter selection'], waitTime=30)
            if any(keyword in output for keyword in keywords):
                self.log("Initiating FLASH test")
                keywords = ['Press Y to proceed']
                output = dut.send('2', strList=keywords)
                if any(keyword in output for keyword in keywords):
                    goodKeywords = ['Result for test 2/2 (pass 1): PASS']
                    badKeywords = ['FAIL', 'Fail', 'Error']
                    # The full-filesystem FLASH test (128 MB, TWO passes) needs far
                    # more than the 3600 s originally allowed.  This case has NEVER
                    # completed - it failed the same way in bidhanc's 2026-08-07 run
                    # and again on 2026-08-10 - so the hedged "may have succeed"
                    # message below has been firing on a test that was simply still
                    # running.
                    # Measured on tb504 2026-08-10 (01:47:21 -> 02:47:21, 3600 s):
                    # got through test 1/2 only as far as
                    #   Erasing 50/50, Making 50/50, Writing 50/50, Reading 20/50
                    # i.e. ~170 of ~200 progress units for the FIRST of two tests,
                    # ~21 s/unit -> ~4200 s per test -> ~8400 s for both.  As with the
                    # security erase, real cost runs LONGER than linear, so 10800 s.
                    # waitTime is a ceiling - send() returns the moment a keyword
                    # matches - so this costs nothing extra on a healthy run.
                    #
                    # NOTE: 'Result for test 2/2 (pass 1): PASS' is still UNVERIFIED.
                    # No run has ever reached the end of this operation, so we have no
                    # capture of its completion text.  If it times out at 10800 s with
                    # both tests visibly finished, suspect gate-string rot next.
                    output = dut.send('Y', strList=goodKeywords + badKeywords, waitTime=10800)

                    if any(keyword in output for keyword in badKeywords):
                        self.failed('Flash test failed in some way')
                        self.log('Expected pass string "{}"'.format('", "'.join(map(str, goodKeywords))))
                        self.log('')
                        self.log(output)
                        self.log('')
                    elif any(keyword in output for keyword in goodKeywords):
                        self.passed('Flash test succeeded')
                        self.log(output)
                        self.log('')
                    else:
                        self.failed('Did not see expected succeesful completion, but flash test may have succeed')
                        self.log('Expected pass string "{}"'.format('", "'.join(map(str, goodKeywords))))
                        self.log('')
                        self.log(output)
                        self.log('')

                    keywords = ['Bootup Stage 2 Diagnostics Menu']
                    output = dut.send('Q', strList=keywords, waitTime=120)
                    if not any(keyword in output for keyword in keywords):
                        output = dut.send(CTRL_C, strList=keywords, waitTime=120)
                    if any(keyword in output for keyword in keywords):
                        self.passed('Returned to stage 2 diagnostics menu after stopping flash test')
                    else:
                        self.failed('Failed to return to stage 2 diagnostics menu after stopping flash test')
                        self.log(output)
                else:
                    self.failed('Failed to see confirmation prompt: "{}":'.format('", "'.join(map(str, keywords))))
                    self.log(output)
            else:
                self.failed('Failed to enter stage 2 Diagnostics menu:')
                self.log(output)

        restore_boot_from_tftp(self, dut, login=False)
        outputDict = watch_consoles_for_bootup([dut], self, waitTime=3600)
        dut.mode('#')
        self.doConfCheck = False


class TestCase_11(ATTestCase.TestCase):
    testCaseDesc   = 'Boot stage 2 Diagnostics menu, option 4. Erase FLASH (Filesystem only)'
    testCaseRef    = "AWP2764"
    testCaseMethod = 'Diagnostics menu option 24\n'

    def configure(self):
        get_all_misc(self)

    def main(self):
        dut = self.dut
        #Erase flash (also long)(erases flash) in stage 2 menu
        if not enter_diagnostics_menu_with_retry(self, dut):
            self.failed("Problem occurred entering Diagnostics menu")
        else:
            self.log("Enter the Boot stage 2 Diagnostics menu")
            dut.send('7', strList=['Entering stage 2...'])
            dut.send('', strList=['Enter selection'], waitTime=30)
            output= dut.send('4', strList=["Press Y to proceed"])
            # Stage 2 option 4 erases the whole flash.  1200 s was too small: on
            # 2026-08-07 this returned with only 36/50 blocks erased (bidhanc's
            # capture), so the case reported "device erase flash failed" on an
            # operation that was simply still running.
            # The comparable full-flash erase (security level 2/3 -> 1) was MEASURED
            # end-to-end twice on this platform at 2143 s and 2150 s - see
            # resetBootSecurityLevel() in library_5700.py.  Do NOT size this from the
            # "n/50 blocks" counter: the operation runs longer than linear, which is
            # exactly how the 1200 s figure came to look sufficient.
            # 3000 s matches the library budget and leaves ~40% headroom.  waitTime is
            # a ceiling - send() returns as soon as strList matches - so a generous
            # value costs nothing on a healthy run.
            output= dut.send('y', strList=["Enter selection"], waitTime=3000)
            try:
                line = [x for x in output.splitlines() if 'Erasing' in x][0]
            except IndexError:
                self.failed('could not find "Erasing flash" line in output:')
                log_device_output(self, output)
            else:
                if parseErasingFlashLine(line):
                    self.passed('device erased flash successfully')
                elif 'Bootup Stage 2 Diagnostics Menu' in output:
                    self.failed('device returned to Stage 2 Diagnostics Menu before completing flash erasure:')
                    log_device_output(self, output)
            
            if 'Bootup Stage 2 Diagnostics Menu' in output:
                dut.send('0')
                outputDict = watch_consoles_for_bootup([dut], self)
                output = outputDict[dut]
                if output.count('Booting...') > 1:
                    self.failed("Silent reboot observed during bootup")
                    log_device_output(self, output)
                else:
                    self.passed("Device rebooted successfully")
            else:
                self.failed("device erase flash failed")
                log_device_output(self, output)

        if self.has_failed():
            restore_boot_from_tftp(self, dut)
        
        dut.mode('#')

    def tear_down(self):
        self.doConfCheck = False


class TestCase_12(ATTestCase.TestCase):
    testCaseDesc   = 'Boot stage 2 Diagnostics menu, option 5. Card slot test'
    testCaseRef    = "AWP2765"
    testCaseMethod = '1. Check the SD card slot is supported\n'
    testCaseMethod += '2. Enter the Boot stage 2 Diagnostics menu\n'
    testCaseMethod += '3. Run the card slot test\n'
    testCaseMethod += '4. Check the responses as all good\n'

    def configure(self):
        dut = self.dut
        if not dut.has_sd_card():
            self.failed('No SD card present, test unsupported')
            self.supported = False
            self.powerCycleOnFail = False
        if dut.software_starts_with(['AR']):
            self.failed('No SD card slot test available on AR series routers, test unsupported')
            self.supported = False
            self.powerCycleOnFail = False
        get_all_misc(self)

    def main(self):
        if not self.supported:
            self.log('Skipping unsupported test')
            return

        dut = self.dut
        if not enter_diagnostics_menu_with_retry(self, dut):
            self.failed("Problem occurred entering Diagnostics menu")
        else:
            self.log("Enter the Boot stage 2 Diagnostics menu")
            dut.send('7', strList=['Entering stage 2...'])
            dut.send('', strList=['Enter selection'], waitTime=30)

            self.log(['', 'Run the card slot test'])
            output= dut.send('5',strList = ["Bootup Stage 2 Diagnostics Menu:"])
            
            self.log('Check the responses as all good')
            keyWord = 'All SD card responses are good'
            if keyWord in output:
                self.passed('Card slot test passed in diagnostics stage 2 menu')
            else:
                self.failed(f'Card slot test failed in diagnostics stage 2 menu, expected "{keyWord}":')
                log_device_output(self, output)
        
        if self.has_failed():
            restore_boot_from_tftp(self, dut)
        else:
            dut.cmd('0')
        
        dut.mode('#')
    
    def tear_down(self):
        self.doConfCheck = False


class TestCase_13(ATTestCase.TestCase):
    testCaseDesc   = 'Boot stage 2 Diagnostics menu, option 7. USB slot test'
    testCaseRef    = "AWP11517"
    testCaseMethod = '1. Check the USB slot is supported\n'
    testCaseMethod += '2. Enter the Boot stage 2 Diagnostics menu\n'
    testCaseMethod += '3. Run the USB slot test\n'
    testCaseMethod += '4. Check USB is initialised and device info has been read\n'

    def configure(self):
        dut = self.dut
        if not dut.has_usb_media():
            self.failed('No USB media present, test unsupported')
            self.supported = False
            self.powerCycleOnFail = False
        get_all_misc(self)

    def main(self):
        if not self.supported:
            self.log('Skipping unsupported test')
            return

        dut = self.dut
        if not enter_diagnostics_menu_with_retry(self, dut):
            self.failed("Problem occurred entering Diagnostics menu")
        else:
            self.log("Enter the Boot stage 2 Diagnostics menu")
            dut.send('7', strList=['Entering stage 2...'])
            dut.send('', strList=["Enter selection"], waitTime=10)

            self.log(['', 'Run the USB slot test'])
            output= dut.send('7', strList=["Enter selection"])

            self.log('Check USB is initialised and device info has been read')
            keyWords = ['PASS: USB initialized and read storage device info', 'PASS: USB slot was able to init and read card information.']
            if any(keyWord in output for keyWord in keyWords):
                self.passed("USB - Card slot test passed in diagnostics stage 2 menu")
            else:
                self.failed("USB - Card slot test failed in diagnostics stage 2 menu")
                self.log('Expected "{}":'.format('" or "'.join(map(str, keyWords))))
                log_device_output(self, output)
        
        if self.has_failed():
            restore_boot_from_tftp(self, dut)
        else:
            dut.cmd('0')

        dut.mode('#')

    def tear_down(self):
        self.doConfCheck = False


class TestCase_14(ATTestCase.TestCase):
    testCaseDesc   = 'Boot stage 2 Diagnostics menu, option 8. Quit to U-Boot shell'
    testCaseExcl   = {'dut' : ['ARX200S', 'x240', 'x250', 'x540', 'SE240', 'SE250', 'SE540']} 
    testCaseRef    = "AWP2766"
    testCaseMethod = '1. Enter the Boot stage 2 Diagnostics menu\n'
    testCaseMethod += '2. Enter the U-Boot shell - option 8\n'
    testCaseMethod += '3. Check that the system is in the U-Boot shell\n'
    testCaseMethod += '4. Reset out of the U-Boot shell and go back to AWP\n'

    def configure(self):
        get_all_misc(self)

    def main(self):
        dut = self.dut
        if not enter_diagnostics_menu_with_retry(self, dut):
            self.failed("Problem occurred entering Diagnostics menu")
        else:
            self.log("Enter the Boot stage 2 Diagnostics menu")
            dut.send('7', strList=['Entering stage 2...'])
            dut.send('', strList=['Enter selection'], waitTime=30)

            self.log("Enter the U-Boot shell - option 8")
            dut.cmd('8')

            self.log("Check that the system is in the U-Boot shell")
            output = dut.cmd('.')
            keyWord = 'Unknown command'
            if keyWord in output:
                self.passed("entered uboot from diagnostics stage 2 menu")
            else:
                self.failed(f'did not enter u-boot from diagnostics stage 2 menu, expected "{keyWord}":')
                log_device_output(self, output)
        
        if self.has_failed():
            restore_boot_from_tftp(self, dut)
        else:
            self.log("Reset and reboot")
            dut.send('reset\n')		
        
        dut.mode('#')
        
    def tear_down(self):
        self.doConfCheck = False


class TestCase_15(ATTestCase.TestCase):
    testCaseDesc   = 'Boot stage 2 Diagnostics menu, option 9. Quit and continue booting'
    testCaseRef    = "AWP2767"
    testCaseMethod = "1. Enter the Boot stage 2 Diagnostics menu\n"
    testCaseMethod += "2. Select 'Quit and continue booting' - Option 9\n"

    def configure(self):
        get_all_misc(self)

    def main(self):
        dut = self.dut
        # quit and continue booting in stage 2 menu
        if not enter_diagnostics_menu_with_retry(self, dut):
            self.failed("Problem occurred entering Diagnostics menu")
        else:
            self.log("Enter the Boot stage 2 Diagnostics menu")
            dut.send('7', strList=['Entering stage 2...'])
            dut.send('', strList=['Enter selection'], waitTime=30)

            self.log("Select 'Quit and continue booting' - Option 9")
            # Was: keyWord = 'Verifying release' with no waitTime - guaranteed FAIL
            # 30 min after a healthy boot out of the stage 2 diagnostics menu.
            output, booted = wait_for_release_boot(self, dut, '9')
            if booted:
                self.passed("device booted from diagnostics stage 2 menu")
            else:
                self.failed(f'device did not boot from diagnostics stage 2 menu, expected one of {BOOT_MARKERS}:')
                log_device_output(self, output)

        if self.has_failed():
            restore_boot_from_tftp(self, dut)
        
        dut.mode('#')
        
    def tear_down(self):
        self.doConfCheck = False


if __name__ == '__main__':
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
    ts.add_testCase(TestCase_12())
    ts.add_testCase(TestCase_13())
    ts.add_testCase(TestCase_14())
    ts.add_testCase(TestCase_15())
    ts.add_testCase(TestCase_11())
    ts.add_testCase(TestCase_10(tear=False))
    ts.run(sys.argv)

