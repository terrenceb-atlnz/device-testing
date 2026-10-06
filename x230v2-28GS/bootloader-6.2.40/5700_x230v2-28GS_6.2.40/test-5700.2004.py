#!/usr/bin/python3

import datetime
import sys

from framework import (
    ATTestCase,
    ATTestSet
)

from framework.ATLibrary.ATTools import watch_consoles_for_bootup

from framework.ATDrivers.ATBootLoader import *

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
    testCaseDesc   = 'Access U-boot'
    testCaseRef    = "None"
    testCaseMethod = '1. Reboot and issue a Ctrl-u to enter Uboot\n'
    testCaseMethod += '2. Check Uboot has been accessed\n'

    def configure(self):
        get_all_misc(self)

    def main(self):
        dut = self.dut
        #can enter uboot via ctrl-u at boot
        self.log("Reboot and issue a Ctrl-u to enter Uboot")
        if not enter_uboot_with_retry(self, dut):
            self.failed("Problem occurred entering Uboot")
        else:
            self.log("Check Uboot has been accessed")
            output = dut.cmd('.')
            if 'Unknown command' in output:
                self.passed("reached uboot via ctrl-u")
            else:
                self.failed("didn't reach uboot via ctrl-u")
                self.log(output)
    
        if self.has_failed():
            restore_boot_from_tftp(self, dut)
        else:
            self.log("Reset and reboot")
            dut.send('reset\n')		
        
        dut.mode('#')


class TestCase_2(ATTestCase.TestCase):
    testCaseDesc   = 'Change date in U-boot'
    testCaseRef    = "None"
    testCaseMethod = "1. Enter Uboot from Boot Menu\n"
    testCaseMethod += "2. Check 'date reset' command works\n"
    testCaseMethod += "3. Check 'date' command allows a new date and time to be set\n"

    def configure(self):
        dut = self.dut
        get_all_misc(self)

        if not dut.hasRealTimeClock:
            self.failed('date reset command not supported due to no real-time-clock on this platform, test unsupported')
            self.supported = False
    
    def main(self):
        if not self.supported:
            self.log('Skipping unsupported test')
            return

        dut = self.dut
        self.log("Enter Uboot from Boot Menu")
        if not enter_uboot_with_retry(self, dut):
            self.failed("Problem occurred entering Uboot")
        else:
            self.log(['', 'Check "date reset" command is recognised'])
            output = dut.cmd('date reset')
            # most devices will return '1970-01-01' but x550 returns '2000-01-01'
            expectedDates = []
            expectedDates.append('1970-01-01')
            expectedDates.append('2000-01-01')
            if any(expectedDate in output for expectedDate in expectedDates):
                self.passed("date reset works")
            else:
                self.failed('date reset does not work, expected to see one of: "{}"'.format('", "'.join(map(str, expectedDates))))
                log_device_output(self, output)

            dt = datetime.datetime.now() - datetime.timedelta(days=30)      # dt = datetime # today - 1 month
            fdt_a = dt.strftime("%d %b %Y 01:01")                           # fdt = formatted date time # readable format
            fdt_b = dt.strftime("Date: %Y-%m-%d (%A)    Time:  1:01:00")    # uboot output format
            fdt_c = dt.strftime("%-d %b %Y 01:")                            # "show clock" output format
            fdt_cmd = dt.strftime("%m%d0101%Y.00")                          # uboot date command argument

            self.log(['', 'Check "date" command allows a new date and time to be set'])
            output = dut.cmd("date")
            log_device_output(self, output)

            self.log(['', 'Set date and time to a date in the past'])
            self.log(f'Setting uboot time to {fdt_a}')
            output = dut.cmd(f'date {fdt_cmd}')
            if fdt_b in output:
                self.log('Successfully set date in uboot')
            else:
                self.failed('')
            log_device_output(self, output)

            self.log(['', 'Set date and time to now'])
            dt = datetime.datetime.now()                                    # dt = datetime # today
            fdt_a = dt.strftime("%d %b %Y 01:01")                           # fdt = formatted date time # readable format
            fdt_b = dt.strftime("Date: %Y-%m-%d (%A)    Time:  1:01:00")    # uboot output format
            fdt_c = dt.strftime("%-d %b %Y 01:")                            # "show clock" output format
            fdt_cmd = dt.strftime("%m%d0101%Y.00")                          # uboot date command argument
            output = dut.cmd(f'date {fdt_cmd}')
            if fdt_b in output:
                self.passed("date has changed to today's date")
            else:
                self.failed("date has not changed to today's date")
            log_device_output(self, output)

            self.log(['', 'Set date and time to a time in the future'])
            dt = datetime.datetime.now() + datetime.timedelta(days=30)      # dt = datetime # today + 1 month
            fdt_a = dt.strftime("%d %b %Y 01:01")                           # fdt = formatted date time # readable format
            fdt_b = dt.strftime("Date: %Y-%m-%d (%A)    Time:  1:01:00")    # uboot output format
            fdt_c = dt.strftime("%-d %b %Y 01:")                            # "show clock" output format
            fdt_cmd = dt.strftime("%m%d0101%Y.00")                          # uboot date command argument
            output = dut.cmd(f'date {fdt_cmd}')
            if fdt_b in output:
                self.passed("date has changed to a date in the future")
            else:
                self.failed("date has not changed to a date in the future")
            log_device_output(self, output)

            if not self.has_failed():
                self.log(['', 'Confirm date and time set in uboot is preserved after bootup'])
                dut.send('reset\n')
                output = watch_consoles_for_bootup(dut, self, waitTime=600, watchForLoginPrompt=True)[dut]
                rebooted = False
                try:
                    dut.mode('#', timeOut=300)
                except Exception:
                    self.failed('DUT appears to have failed to reboot after setting date in uboot')
                else:
                    rebooted = True

                expectedDateStr = fdt_c
                if not rebooted:
                    self.log(['', '-'*80, 'Bootup console output:'] + output.splitlines() + ['', '-'*80, ''])
                    if dut.has_power():
                        self.log('Attempting to power-cycle {} to recover'.format(dut))
                        dut.off()
                        dut.on()
                        dut.mode('#')

                output = dut.cmd('show clock')
                lines = output.splitlines()
                if expectedDateStr in lines[2]:
                    self.passed('DUT sucessfully synced with uboot time')
                    self.log(lines[2])
                else:
                    self.failed('DUT time did not sync with uboot time correctly it should be "{}*" but {} was displayed'.format(expectedDateStr, lines[2]))
        
        if self.has_failed():
            restore_boot_from_tftp(self, dut)

        dut.mode('#')

    def tear_down(self):
        dut = self.dut
        if not self.supported and not self.has_failed():
            if not dut.hasRealTimeClock:
                self.log(['', '-'*80])
                self.log(f'Test needs updating, {dut} appears to have no real-time-clock')
                self.log('thus the assumption is the "date reset" command is not supported')
                self.log('however this assumption appears to be incorrect.')
                self.log('Test should change from using dut.hasRealTimeClock to using a list')
                self.log('of unsupported platforms.')
                self.log(['-'*80, '', ''])


if __name__ == '__main__':
    ts = TestSet()
    ts.add_testCase(TestCase_1())
    ts.add_testCase(TestCase_2())
    ts.run(sys.argv)
