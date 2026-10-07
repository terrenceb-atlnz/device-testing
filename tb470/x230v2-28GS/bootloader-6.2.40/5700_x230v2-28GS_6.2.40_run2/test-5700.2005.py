#!/usr/bin/python3

import sys

from framework import (
    ATTestCase,
    ATTestSet
)

from library_5700 import *


class TestSet(ATTestSet.TestSet):

    FEATURES = ['ACCESS']

    SECURITY_PWORD = '789012'

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
    testCaseDesc   = "Access Security Settings Menu"
    testCaseRef    = "None"
    testCaseMethod = "1. Reboot and enter the Boot Menu\n"
    testCaseMethod += "2. Select the option 'S' for 'S. Security Level'\n"
    testCaseMethod += "3. Check Security Settings Menu is accessed\n"
    testCaseMethod += "4. Select the option '0' for '0. Return to previous menu'\n"
    testCaseMethod += "3. Check returned to Boot Menu\n"

    def configure(self):
        get_all_misc(self)

    def main(self):
        dut = self.dut
        self.log(['', 'Enter the Boot Menu'])
        if not enter_bootrom_with_retry(self, dut):
            self.failed("Problem occurred entering bootloader")
        else:
            clear_bootloader_buffer(dut)
            self.log(['', 'Select the Security Levels option and check that the Security Settings Menu is accessed'])
            output = dut.send('S',strList = ["Security Settings menu"])
            if "Security Settings menu" in output:
                self.passed("Security Settings Menu accessd")
            else:
                self.log(output)
                self.failed("Security Settings Menu not accessd")

            self.log(['', 'Select the "Return to previous menu" option and check that the Boot Menu is accessed'])
            output = dut.send('0',strList = ["Boot Menu"])
            if "Boot Menu" in output:
                self.passed("Boot Menu accessd")
            else:
                self.log(output)
                self.failed("Boot Menu not accessd")
        
        if self.has_failed():
            restore_boot_from_tftp(self, dut)
        else:
            dut.send('0', strList=['Press <Ctrl+B> for the Boot Menu'])
        dut.mode('#')


class TestCase_2(ATTestCase.TestCase):
    testCaseDesc   = "Set Security Level 2"
    testCaseRef    = "AWP-13631, AWP-13632, AWP-13634"
    testCaseMethod = "1. Reboot and enter the Boot Menu\n"
    testCaseMethod += "2. Select the option 'S' for 'S. Security Level'\n"
    testCaseMethod += "3. Select option '1. Set security Level to 2 (Password Protected)' and abort setting\n"
    testCaseMethod += "4. Select option '1. Set security Level to 2 (Password Protected)' and input mismated passwords\n"
    testCaseMethod += "5. Select option '1. Set security Level to 2 (Password Protected)' and set password\n"
    testCaseMethod += "6. Select option '3. Change Password' and reset the password\n"
    testCaseMethod += "7. Select Boot Menu option '1. Perform one-off boot from alternate source' and input incorrect password\n"
    testCaseMethod += "8. Select Boot Menu option '1. Perform one-off boot from alternate source' and input correct password\n"
    testCaseMethod += "9. Select Boot Menu option '2. Change the default boot source (for advanced users)' and input incorrect password\n"
    testCaseMethod += "10. Select Boot Menu option '2. Change the default boot source (for advanced users)' and input correct password\n"
    testCaseMethod += "11. Select Boot Menu option '3. Update Bootloader' and input incorrect password\n"
    testCaseMethod += "12. Select Boot Menu option '3. Update Bootloader' and input correct password\n"
    testCaseMethod += "13. Select Boot Menu option '5. Special boot options' and input incorrect password\n"
    testCaseMethod += "14. Select Boot Menu option '5. Special boot options' and input correct password\n"
    testCaseMethod += "15. Select Boot Menu option '4. Adjust the console baud rate' and check no password is required\n"
    testCaseMethod += "16. Select Boot Menu option '6. System information' and check no password is required\n"
    testCaseMethod += "17. Select Boot Menu option '7. Restore Bootloader factory settings' and check no password is required\n"
    testCaseMethod += "18. Select Boot Menu option '7. Restore Bootloader factory settings' and check that a restore does not clear the security settings\n"
    testCaseMethod += "19. Security Menu option '1. Set security Level to 1 (None)' and check security level has been reset\n"

    def configure(self):
        get_all_misc(self)

    def main(self):
        # security level 2
        dut = self.dut
        self.log(['', 'Enter the Boot Menu'])
        if not enter_bootrom_with_retry(self, dut):
            self.failed("Problem occurred entering bootloader")
        else:
            clear_bootloader_buffer(dut)
            self.log(['', 'Select the Security Levels option and check that the Security Settings Menu is accessed'])
            clear_bootloader_buffer(dut)
            output = dut.send('S', strList = ["Enter selection"], waitTime=60, interval=0.05)
            log_device_output(self, output)
            if "Security Settings menu" in output:
                self.passed("Security Settings Menu accessed")

                # check what security level is currently set
                if "currently set to 1 (None)" not in output:
                    self.log("Security level set, resetting to none")
                    resetBootSecurityLevel(self, dut)

                # select security level 2 but abort
                self.log(['-'*40, 'Step 10'])
                selectSecurityLevelAbort(self, dut, 2)

                # Set security level 2 - password mismatch
                self.log(['-'*40, 'Step 20'])
                selectSecurityLevelPWMismatch(self, dut, 2,'123456')

                # Set security level 2
                self.log(['-'*40, 'Step 30'])
                setSecurityLevel(self, dut, 2,'123456')

                # Set security level 2 - reset password
                self.log(['-'*40, 'Step 40'])
                resetSecurityLevelPW(self, dut, self.SECURITY_PWORD)
                #
                # TODO - Password too short and too long
                #
                #
                # Check correct and incorrect passwords for all menu options that will require password entry, 1,2,3 and 5
                #
                # Check access to Boot Menu option, '1. Perform one-off boot from alternate source'
                # Incorrect password
                # self.log('     @@@ setLevel2 - selectBootMenuOptionIncorrectPW(1)' )
                self.log(['-'*40, 'Step 50'])
                selectBootMenuOptionIncorrectPW(self, dut, 1)
                # Correct password
                self.log(['-'*40, 'Step 60'])
                selectBootMenuOptionCorrectPW(self, dut, 1, self.SECURITY_PWORD)
                # Check access to Boot Menu option, '2. Change the default boot source (for advanced users)'
                # Incorrect password
                # self.log('     @@@ setLevel2 - selectBootMenuOptionIncorrectPW(2)' )
                self.log(['-'*40, 'Step 70'])
                selectBootMenuOptionIncorrectPW(self, dut, 2)
                # Correct password
                self.log(['-'*40, 'Step 80'])
                selectBootMenuOptionCorrectPW(self, dut, 2, self.SECURITY_PWORD)
                # Check access to Boot Menu option, '3. Update Bootloader'
                # Incorrect password
                # self.log('     @@@ setLevel2 - selectBootMenuOptionIncorrectPW(3)' )
                self.log(['-'*40, 'Step 90'])
                selectBootMenuOptionIncorrectPW(self, dut, 3)
                # Correct password
                self.log(['-'*40, 'Step 100'])
                selectBootMenuOptionCorrectPW(self, dut, 3, self.SECURITY_PWORD)
                # Check access to Boot Menu option, '5. Special boot options'
                # Incorrect password
                # self.log('     @@@ setLevel2 - selectBootMenuOptionIncorrectPW(5)' )
                self.log(['-'*40, 'Step 110'])
                selectBootMenuOptionIncorrectPW(self, dut, 5)
                # Correct password
                # selectBootMenuOptionCorrectPW(self, dut, 5, self.SECURITY_PWORD)
                #
                # Check no password is required for non-secure menu options, 4,6 and 7
                #
                # Check access to Boot Menu option, '4. Adjust the console baud rate'
                # self.log('     @@@ setLevel2 - selectBootMenuOptionNoPW(4)' )
                self.log(['-'*40, 'Step 120'])
                selectBootMenuOptionNoPW(self, dut, 4)
                # Check access to Boot Menu option, '6. System information'
                # self.log('     @@@ setLevel2 - selectBootMenuOptionNoPW(6)' )
                self.log(['-'*40, 'Step 130'])
                selectBootMenuOptionNoPW(self, dut, 6)
                # Check access to Boot Menu option, '7. Restore Bootloader factory settings'
                # self.log('     @@@ setLevel2 - selectBootMenuOptionNoPW(7)' )
                self.log(['-'*40, 'Step 140'])
                selectBootMenuOptionNoPW(self, dut, 7)
                #
                # Check that option, '7. Restore Bootloader factory settings'
                # does not clear the security settings
                #
                # Run option, '7. Restore Bootloader factory settings'
                self.log(['-'*40, 'Step 150'])
                runRestoreFactorySettings(self, dut, self.SECURITY_PWORD)
                if not enter_bootrom_with_retry(self, dut, maxAttempts=10):
                    self.failed("Problem occurred entering bootloader, unable to determine what state the DUT is in")
                clear_bootloader_buffer(dut)
                checkSecurityLevel(self, dut, 2)
                #
                # Reset to security level 1 (none)
                #
                self.log(['', 'Reset the Security Level to 1 (None)'])
                self.log("Select the Security Levels option and check that the Security Settings Menu is accessed")
                output = dut.send('S',strList = ["Security Settings menu"])
                if "Security Settings menu" in output:
                    self.passed("Security Settings Menu accessd")
                    # select option 1 to reset secuity level
                    resetBootSecurityLevel(self, dut)
                    # Check the security setting is as expected
                    checkSecurityLevel(self, dut, 1)
                else:
                    self.log(output)
                    self.failed("Security Settings Menu not accessd")
                #
                # Reset feature licenses as setting the security level back to 1 erases them
                dut.send('0', strList=['Boot Menu'], waitTime=60, interval=0.05)
                dut.send('0', strList=['login:'], waitTime=60, interval=0.5, log=True)
                dut.mode('#')
                self.log("Reset the feature licenses")
                output = self.update_feature_licenses(featureList=['ALL'])
                self.log(output)
            else:
                self.log(output)
                self.failed("Security Settings Menu not accessd")
        
        if self.has_failed():
            restore_boot_from_tftp(self, dut)

        dut.mode('#')

    def tear_down(self):
        dut = self.dut
        dut.mode('#')


class TestCase_3(ATTestCase.TestCase):
    testCaseDesc   = "Set Security Level 3"
    testCaseRef    = "AWP-13631, AWP-13633, AWP-13634"
    testCaseMethod = "1. Reboot and enter the Boot Menu\n"
    testCaseMethod += "2. Select the option 'S' for 'S. Security Level'\n"
    testCaseMethod += "3. Select option '2. Set security Level to 3 (Locked Down)' and abort setting\n"
    testCaseMethod += "4. Select option '2. Set security Level to 3 (Locked Down)' and input mismated passwords\n"
    testCaseMethod += "5. Select option '2. Set security Level to 3 (Locked Down)' and set password\n"
    testCaseMethod += "6. Select option '3. Change Password' and reset the password\n"
    testCaseMethod += "7. Select Boot Menu option '1. Perform one-off boot from alternate source' and input incorrect password\n"
    testCaseMethod += "8. Select Boot Menu option '1. Perform one-off boot from alternate source' and input correct password\n"
    testCaseMethod += "9. Select Boot Menu option '2. Change the default boot source (for advanced users)' and input incorrect password\n"
    testCaseMethod += "10. Select Boot Menu option '2. Change the default boot source (for advanced users)' and input correct password\n"
    testCaseMethod += "11. Select Boot Menu option '3. Update Bootloader' and input incorrect password\n"
    testCaseMethod += "12. Select Boot Menu option '3. Update Bootloader' and input correct password\n"
    testCaseMethod += "13. Select Boot Menu option '5. Special boot options' and input incorrect password\n"
    testCaseMethod += "14. Select Boot Menu option '5. Special boot options' and input correct password\n"
    testCaseMethod += "15. Select Boot Menu option '4. Adjust the console baud rate' and check no password is required\n"
    testCaseMethod += "16. Select Boot Menu option '6. System information' and check no password is required\n"
    testCaseMethod += "17. Select Boot Menu option '7. Restore Bootloader factory settings' and check no password is required\n"
    testCaseMethod += "18. Select Boot Menu option '7. Restore Bootloader factory settings' and check that a restore does not clear the security settings\n"
    testCaseMethod += "19. Security Menu option '1. Set security Level to 1 (None)' and check security level has been reset\n"

    def configure(self):
        get_all_misc(self)

    def main(self):
        # security level 3
        dut = self.dut
        self.log(['', 'Enter the Boot Menu'])
        if not enter_bootrom_with_retry(self, dut):
            self.failed("Problem occurred entering bootloader")
        else:
            clear_bootloader_buffer(dut)
            self.log(['', 'Select the Security Levels option and check that the Security Settings Menu is accessed'])
            output = dut.send('S',strList = ["Enter selection"])
            if "Security Settings menu" in output:
                self.passed("Security Settings Menu accessd")
                # check what security level is currently set
                if "currently set to 1 (None)" not in output:
                    self.log("Security level set, resetting to none")
                    resetBootSecurityLevel(self, dut)
                
                self.log(['', '-'*40, 'Step 10'])
                # select security level 3 but abort
                selectSecurityLevelAbort(self, dut, 3)
                
                self.log(['', '-'*40, 'Step 20'])
                # Set security level 3 - password mismatch
                selectSecurityLevelPWMismatch(self, dut, 3,'123456')

                self.log(['', '-'*40, 'Step 30'])
                # Set security level 3
                setSecurityLevel(self, dut, 3,'123456')

                self.log(['', '-'*40, 'Step 40'])
                # Set security level 3 - reset password
                resetSecurityLevelPW(self, dut, self.SECURITY_PWORD)
                #
                # TODO - Password too short and too long
                #
                #
                # Check correct and incorrect passwords for all menu options that will require password entry, 1,2,3 and 5
                #
                # Check access to Boot Menu option, '1. Perform one-off boot from alternate source'
                # Incorrect password

                self.log(['', '-'*40, 'Step 50'])
                # self.log('     @@@ setLevel3 - selectBootMenuOptionIncorrectPW(1)' )
                selectBootMenuOptionIncorrectPW(self, dut, 1)
                # Correct password
                selectBootMenuOptionCorrectPW(self, dut, 1, self.SECURITY_PWORD)
                # Check access to Boot Menu option, '2. Change the default boot source (for advanced users)'
                # Incorrect password
                
                self.log(['', '-'*40, 'Step 60'])
                # self.log('     @@@ setLevel3 - selectBootMenuOptionIncorrectPW(2)' )
                selectBootMenuOptionIncorrectPW(self, dut, 2)
                # Correct password
                selectBootMenuOptionCorrectPW(self, dut, 2, self.SECURITY_PWORD)
                # Check access to Boot Menu option, '3. Update Bootloader'
                # Incorrect password
                
                self.log(['', '-'*40, 'Step 70'])
                # self.log('     @@@ setLevel3 - selectBootMenuOptionIncorrectPW(3)' )
                selectBootMenuOptionIncorrectPW(self, dut, 3)
                # Correct password
                selectBootMenuOptionCorrectPW(self, dut, 3, self.SECURITY_PWORD)
                # Check access to Boot Menu option, '5. Special boot options'
                # Incorrect password
                
                self.log(['', '-'*40, 'Step 80'])
                # self.log('     @@@ setLevel3 - selectBootMenuOptionIncorrectPW(5)' )
                selectBootMenuOptionIncorrectPW(self, dut, 5)
                # Correct password
                selectBootMenuOptionCorrectPW(self, dut, 5, self.SECURITY_PWORD)
                #
                # Check no password is required for non-secure menu options, 4,6 and 7
                #
                # Check access to Boot Menu option, '4. Adjust the console baud rate'
                
                self.log(['', '-'*40, 'Step 90'])
                # self.log('     @@@ setLevel3 - selectBootMenuOptionNoPW(4)' )
                selectBootMenuOptionNoPW(self, dut, 4)
                # Check access to Boot Menu option, '6. System information'
                
                self.log(['', '-'*40, 'Step 100'])
                # self.log('     @@@ setLevel3 - selectBootMenuOptionNoPW(6)' )
                selectBootMenuOptionNoPW(self, dut, 6)
                # Check access to Boot Menu option, '7. Restore Bootloader factory settings'
                
                self.log(['', '-'*40, 'Step 110'])
                # self.log('     @@@ setLevel3 - selectBootMenuOptionNoPW(7)' )
                selectBootMenuOptionNoPW(self, dut, 7)
                
                # Check that option, '7. Restore Bootloader factory settings'
                # does not clear the factory settings
                #
                # Run option, '7. Restore Bootloader factory settings'
                
                self.log(['', '-'*40, 'Step 120'])
                runRestoreFactorySettings(self, dut, self.SECURITY_PWORD)
                # Check the security setting is as expected
                
                self.log(['', '-'*40, 'Step 130'])
                # self.log('     @@@ setLevel3 - checkSecurityLevel(3)' )
                checkSecurityLevel(self, dut, 3)
                #
                # Reset to security level 1 (none)
                #
                self.log(['', '-'*40, 'Step 140'])
                self.log(['', 'Reset the Security Level to 1 (None)'])
                self.log("Select the Security Levels option and check that the Security Settings Menu is accessed")
                output = dut.send('S',strList = ["Security Settings menu"])
                if "Security Settings menu" in output:
                    self.passed("Security Settings Menu accessd")
                    # select option 1 to reset secuity level
                    resetBootSecurityLevel(self, dut)
                    # Check the security setting is as expected
                    checkSecurityLevel(self, dut, 1)
                else:
                    self.log(output)
                    self.failed("Security Settings Menu not accessd")
                #
                # Reset feature licenses as setting the security level back to 1 erases them
                #
                enterAWP(self,dut)
                dut.mode('#')
                self.log("Reset the feature licenses")
                output = self.update_feature_licenses(featureList=['ALL'])
                self.log(output)
            else:
                self.log(output)
                self.failed("Security Settings Menu not accessed")

        if self.has_failed():
            restore_boot_from_tftp(self, dut)

        dut.mode('#')


class TestCase_4(ATTestCase.TestCase):
    testCaseDesc   = "Check the password length limits, >5 and <24"
    testCaseRef    = "AWP-13836"
    testCaseMethod = "1. Reboot and enter the Boot Menu\n"
    testCaseMethod += "2. Select the option 'S' for 'S. Security Level'\n"
    testCaseMethod += "3. Select option '1. Set security Level to 2 (Password Protected)' and set password to valid max length\n"
    testCaseMethod += "4. Check all Boot Menu options for security passowrd requirement\n"
    testCaseMethod += "5. Reset the password with a passowrd too long - over 23 characters\n"
    testCaseMethod += "6. Reset the password with a valid min length passowrd\n"
    testCaseMethod += "7. Check all Boot Menu options for security passowrd requirement\n"
    testCaseMethod += "8. Reset the password with a passowrd too short - under 6 characters\n"
    testCaseMethod += "9. Security Menu option '1. Set security Level to 1 (None)' and check security level has been reset\n"

    def configure(self):
        get_all_misc(self)

    def main(self):
    # check limits on password length, must be >5 and <24
        dut = self.dut
        self.log(['', 'Enter the Boot Menu'])
        if not enter_bootrom_with_retry(self, dut):
            self.failed("Problem occurred entering bootloader")
        else:
            clear_bootloader_buffer(dut)
            self.log(['', 'Select the Security Levels option and check that the Security Settings Menu is accessed'])
            output = dut.send('S',strList = ["Enter selection"])
            if "Security Settings menu" in output:
                self.passed("Security Settings Menu accessd")
                # check what security level is currently set
                if "currently set to 1 (None)" not in output:
                    self.log("Security level set, resetting to none")
                    resetBootSecurityLevel(self, dut)
                #
                # Set security level 2 with max password (23)
                # Check correct and incorrect passwords for all menu options that will require password entry, 1,2,3 and 5
                #
                self.log("Set security level 2 with max password (23)")
                # Set security level 2 with max password
                # NOTE if the order of the passwords in the list is changed make sure a valid one comes first
                currentpwlist = ["12345678901234567890123","123456789012345678901234","123456","12345"]
                oldpw = "12345678901234567890123"
                for currentpw in currentpwlist:
                    if len(currentpw)>5 and len(currentpw)<24:
                        # Return to Security Settings Menu
                        if not enter_bootrom_with_retry(self, dut, maxAttempts=10):
                            self.failed("Problem occurred entering bootloader, unable to determine what state the DUT is in")
                        clear_bootloader_buffer(dut)
                        self.log(['', '', '-'*80, f'Current password : {currentpw}', '-'*80, 'Select the Security Levels option and check that the Security Settings Menu is accessed'])
                        output = dut.send('S',strList = ["Enter selection"])
                        if "Security Settings menu" in output:
                            self.passed("Security Settings Menu accessd")
                            self.log(f"Set password to, '{currentpw}'")
                            # check what security level is currently set
                            if "currently set to 1 (None)" in output:
                                # set a security level
                                setSecurityLevel(self, dut, 2, currentpw)
                            else:
                                # Reset the password
                                resetSecurityLevelPW(self, dut, currentpw, oldpw)

                            # Test valid max and min length
                            self.log(['', 'Check all secure Boot Menu options with correct and incorrect passwords'])
                            # Check access to Boot Menu option, '1. Perform one-off boot from alternate source'
                            # Incorrect password
                            self.log(['', '-'*40, f'Step 10  : current password : {currentpw}'])
                            # self.log('     @@@ PWLimits - selectBootMenuOptionIncorrectPW(1)' )
                            selectBootMenuOptionIncorrectPW(self, dut, 1)
                            # Correct password
                            self.log(['', '-'*40, f'Step 20  : current password : {currentpw}'])
                            selectBootMenuOptionCorrectPW(self, dut, 1, currentpw)
                            # Check access to Boot Menu option, '2. Change the default boot source (for advanced users)'
                            # Incorrect password
                            self.log(['', '-'*40, f'Step 30  : current password : {currentpw}'])
                            # self.log('     @@@ PWLimits - selectBootMenuOptionIncorrectPW(2)' )
                            selectBootMenuOptionIncorrectPW(self, dut, 2)
                            # Correct password
                            self.log(['', '-'*40, f'Step 40  : current password : {currentpw}'])
                            selectBootMenuOptionCorrectPW(self, dut, 2, currentpw)
                            # Check access to Boot Menu option, '3. Update Bootloader'
                            # Incorrect password
                            self.log(['', '-'*40, f'Step 50  : current password : {currentpw}'])
                            # self.log('     @@@ PWLimits - selectBootMenuOptionIncorrectPW(3)' )
                            selectBootMenuOptionIncorrectPW(self, dut, 3)
                            # Correct password
                            self.log(['', '-'*40, f'Step 60  : current password : {currentpw}'])
                            selectBootMenuOptionCorrectPW(self, dut, 3, currentpw)
                            # Check access to Boot Menu option, '5. Special boot options'
                            # Incorrect password
                            self.log(['', '-'*40, f'Step 70  : current password : {currentpw}'])
                            # self.log('     @@@ PWLimits - selectBootMenuOptionIncorrectPW(5)' )
                            selectBootMenuOptionIncorrectPW(self, dut, 5)
                            # Correct password
                            self.log(['', '-'*40, f'Step 80  : current password : {currentpw}'])
                            selectBootMenuOptionCorrectPW(self, dut, 5, currentpw)
                            #
                            # Check no password is required for non-secure menu options, 4,6 and 7
                            #
                            # Check access to Boot Menu option, '4. Adjust the console baud rate'
                            self.log(['', '-'*40, f'Step 90  : current password : {currentpw}'])
                            # self.log('     @@@ PWLimits - self.selectBootMenuOptionNoPW(4)' )
                            selectBootMenuOptionNoPW(self, dut, 4)
                            # Check access to Boot Menu option, '6. System information'
                            self.log(['', '-'*40, f'Step 100 : current password : {currentpw}'])
                            # self.log('     @@@ PWLimits - self.selectBootMenuOptionNoPW(6)' )
                            selectBootMenuOptionNoPW(self, dut, 6)
                            # Check access to Boot Menu option, '7. Restore Bootloader factory settings'
                            self.log(['', '-'*40, f'Step 110 : current password : {currentpw}'])
                            # self.log('     @@@ PWLimits - self.selectBootMenuOptionNoPW(7)' )
                            selectBootMenuOptionNoPW(self, dut, 7)
                            # store old passowrd
                            oldpw = currentpw
                        else:
                            self.log(output)
                            self.failed("Security Settings Menu not accessed")
                    else:
                        # Return to Security Settings Menu
                        if not enter_bootrom_with_retry(self, dut, maxAttempts=10):
                            self.failed("Problem occurred entering bootloader, unable to determine what state the DUT is in")

                        clear_bootloader_buffer(dut)
                        self.log(['', 'Select the Security Levels option and check that the Security Settings Menu is accessed'])
                        output = dut.send('S',strList = ["Enter selection"], waitTime=60, interval=0.05)
                        if "Security Settings menu" in output:
                            self.log(f"Set password to, '{currentpw}', should fail")
                            # Test below min and over max length
                            # Assume security has already been set
                            # NOTE if the order of the passwords in the list is changed make sure a valid one comes first
                            # Reset the password
                            changePasswordError(self, dut, oldpw, currentpw)
                        else:
                            self.log(output)
                            self.failed("Security Settings Menu not accessd")
                #
                # Reset to security level 1 (none)
                #
                self.log(['', '-'*40, 'Reset the Security Level to 1 (None)'])
                self.log("Select the Security Levels option and check that the Security Settings Menu is accessed")
                output = dut.send('S',strList = ["Security Settings menu"])
                if "Security Settings menu" in output:
                    self.passed("Security Settings Menu accessed")
                    # select option 1 to reset secuity level
                    resetBootSecurityLevel(self, dut)
                    # Check the security setting is as expected
                    checkSecurityLevel(self, dut, 1)
                else:
                    self.log(output)
                    self.failed("Security Settings Menu not accessd")
                #
                # Reset feature licenses as setting the security level back to 1 erases them
                #
                enterAWP(self, dut)
                dut.mode('#')
                self.log("Reset the feature licenses")
                output = self.update_feature_licenses(featureList=['ALL'])
                self.log(output)
            else:
                self.log(output)
                self.failed("Security Settings Menu not accessed")

        if self.has_failed():
            restore_boot_from_tftp(self, dut)

        dut.mode('#')


class TestCase_5(ATTestCase.TestCase):
    testCaseDesc   = "Check all the valid characters for use in a password"
    testCaseRef    = "AWP-13838"
    testCaseMethod = "1. Reboot and enter the Boot Menu\n"
    testCaseMethod += "2. Select the option 'S' for 'S. Security Level'\n"
    testCaseMethod += "3. Select option '1. Set security Level to 2 (Password Protected)' and set a valid password with uppercase characters\n"
    testCaseMethod += "4. Check all Boot Menu options for security passowrd requirement\n"
    testCaseMethod += "5. Reset the password and set a valid password with lower characters\n"
    testCaseMethod += "6. Check all Boot Menu options for security passowrd requirement\n"
    testCaseMethod += "7. Reset the password and set a valid password with numberic characters\n"
    testCaseMethod += "8. Check all Boot Menu options for security passowrd requirement\n"
    testCaseMethod += "9. Reset the password and set a valid password that includes spece characters\n"
    testCaseMethod += "10. Check all Boot Menu options for security passowrd requirement\n"
    testCaseMethod += "11. Reset the password and set a valid password with special characters characters\n"
    testCaseMethod += "12. Check all Boot Menu options for security passowrd requirement\n"
    testCaseMethod += "13. Reset the password and set a valid password with a combination of all valid characters\n"
    testCaseMethod += "14. Check all Boot Menu options for security passowrd requirement\n"
    testCaseMethod += "15. Security Menu option '1. Set security Level to 1 (None)' and check security level has been reset\n"

    def configure(self):
        get_all_misc(self)

    def main(self):
        dut = self.dut
        # check all the valid characters for use in a password
        self.log(['', 'Enter the Boot Menu'])
        if not enter_bootrom_with_retry(self, dut):
            self.failed("Problem occurred entering bootloader")
        else:
            clear_bootloader_buffer(dut)
            self.log("Select the Security Levels option and check that the Security Settings Menu is accessed")
            output = dut.send('S',strList = ["Enter selection"])
            if "Security Settings menu" in output:
                self.passed("Security Settings Menu accessed")
                # check what security level is currently set
                if "currently set to 1 (None)" not in output:
                    self.log("Security level set, resetting to none")
                    resetBootSecurityLevel(self, dut)
                #
                # Set security level 2 and set various password using a range of valid charaters
                # Check correct and incorrect passwords for all menu options that will require password entry, 1,2,3 and 5
                #
                self.log("Set security level 2 with passowrd using upper case characters")
                # Set security level 2 with valid character passwords:
                #	- upper case
                #	- lower case
                #	- numbers
                #	- includes a space
                #	- special symbols
                #	- combination
                # NOTE if the order of the passwords in the list is changed make sure a valid one comes first
                currentpwlist = ["ABCDEF", "abcdef", "123456", "abc 123", "!@#$%^&*()_+='", r'{}[]|\:;"<,>.?/', "ABC def 123 !@#$%"]
                oldpw = "ABCDEF"
                for currentpw in currentpwlist:
                    # Return to Security Settings Menu
                    self.log(['', '', '-'*80, f'Current password : {currentpw}', '-'*80, 'Select the Security Levels option and check that the Security Settings Menu is accessed'])
                    output = dut.send('S',strList = ["Enter selection"])
                    if "Security Settings menu" in output:
                        self.passed("Security Settings Menu accessd")
                        self.log(f"Set password to, '{currentpw}'")
                        # check what security level is currently set
                        if "currently set to 1 (None)" in output:
                            # set a security level
                            setSecurityLevel(self, dut, 2, currentpw)
                        else:
                            # Reset the password
                            resetSecurityLevelPW(self, dut, currentpw,oldpw)
                        # Test valid max and min length
                        self.log("Check all secure Boot Menu options with correct and incorrect passwords")
                        # Check access to Boot Menu option, '1. Perform one-off boot from alternate source'
                        # Incorrect password
                        self.log(['', '-'*40, f'Step 10  : current password : {currentpw}'])
                        # self.log('     @@@ PWValidChars - selectBootMenuOptionIncorrectPW(1)' )
                        selectBootMenuOptionIncorrectPW(self, dut, 1)
                        # Correct password
                        self.log(['', '-'*40, f'Step 20  : current password : {currentpw}'])
                        selectBootMenuOptionCorrectPW(self, dut, 1, currentpw)
                        # Check access to Boot Menu option, '2. Change the default boot source (for advanced users)'
                        # Incorrect password
                        self.log(['', '-'*40, f'Step 30  : current password : {currentpw}'])
                        # self.log('     @@@ PWValidChars - selectBootMenuOptionIncorrectPW(2)' )
                        selectBootMenuOptionIncorrectPW(self, dut, 2)
                        # Correct password
                        self.log(['', '-'*40, f'Step 40  : current password : {currentpw}'])
                        selectBootMenuOptionCorrectPW(self, dut, 2, currentpw)
                        # Check access to Boot Menu option, '3. Update Bootloader'                    # selectBootMenuOptionIncorrectPW(self, dut, 1)
                        # Correct password
                        self.log(['', '-'*40, f'Step 50  : current password : {currentpw}'])
                        selectBootMenuOptionCorrectPW(self, dut, 1, currentpw)
                        # Check access to Boot Menu option, '2. Change the default boot source (for advanced users)'
                        # Incorrect password
                        self.log(['', '-'*40, f'Step 60  : current password : {currentpw}'])
                        # self.log('     @@@ PWValidChars - selectBootMenuOptionIncorrectPW(2)' )
                        selectBootMenuOptionIncorrectPW(self, dut, 2)
                        # Correct password
                        self.log(['', '-'*40, f'Step 70  : current password : {currentpw}'])
                        selectBootMenuOptionCorrectPW(self, dut, 2, currentpw)
                        # Check access to Boot Menu option, '3. Update Bootloader'
                        # Incorrect password
                        self.log(['', '-'*40, f'Step 80  : current password : {currentpw}'])
                        # self.log('     @@@ PWValidChars - selectBootMenuOptionIncorrectPW(3)' )
                        selectBootMenuOptionIncorrectPW(self, dut, 3)
                        # Correct password
                        self.log(['', '-'*40, f'Step 90  : current password : {currentpw}'])
                        selectBootMenuOptionCorrectPW(self, dut, 3, currentpw)
                        # Check access to Boot Menu option, '5. Special boot options'
                        # Incorrect password
                        self.log(['', '-'*40, f'Step 100 : current password : {currentpw}'])
                        # self.log('     @@@ PWValidChars - selectBootMenuOptionIncorrectPW(5)' )
                        selectBootMenuOptionIncorrectPW(self, dut, 5)
                        # Correct password
                        self.log(['', '-'*40, f'Step 110 : current password : {currentpw}'])
                        selectBootMenuOptionCorrectPW(self, dut, 5, currentpw)
                        #
                        # Check no password is required for non-secure menu options, 4,6 and 7
                        #
                        # Check access to Boot Menu option, '4. Adjust the console baud rate'
                        self.log(['', '-'*40, f'Step 120 : current password : {currentpw}'])
                        # self.log('     @@@ PWValidChars - selectBootMenuOptionNoPW(4)' )
                        selectBootMenuOptionNoPW(self, dut, 4)
                        # Check access to Boot Menu option, '6. System information'
                        self.log(['', '-'*40, f'Step 130 : current password : {currentpw}'])
                        # self.log('     @@@ PWValidChars - selectBootMenuOptionNoPW(6)' )
                        selectBootMenuOptionNoPW(self, dut, 6)
                        # Check access to Boot Menu option, '7. Restore Bootloader factory settings'
                        self.log(['', '-'*40, f'Step 140 : current password : {currentpw}'])
                        # self.log('     @@@ PWValidChars - selectBootMenuOptionNoPW(7)' )
                        selectBootMenuOptionNoPW(self, dut, 7)
                        # Incorrect password
                        self.log(['', '-'*40, f'Step 150 : current password : {currentpw}'])
                        # self.log('     @@@ PWValidChars - selectBootMenuOptionIncorrectPW(3)' )
                        selectBootMenuOptionIncorrectPW(self, dut, 3)
                        # Correct password
                        self.log(['', '-'*40, f'Step 160 : current password : {currentpw}'])
                        selectBootMenuOptionCorrectPW(self, dut, 3, currentpw)
                        # Check access to Boot Menu option, '5. Special boot options'
                        # Incorrect password
                        self.log(['', '-'*40, f'Step 170 : current password : {currentpw}'])
                        # self.log('     @@@ PWValidChars - selectBootMenuOptionIncorrectPW(5)' )
                        selectBootMenuOptionIncorrectPW(self, dut, 5)
                        # Correct password
                        self.log(['', '-'*40, f'Step 180 : current password : {currentpw}'])
                        selectBootMenuOptionCorrectPW(self, dut, 5, currentpw)
                        #
                        # Check no password is required for non-secure menu options, 4,6 and 7
                        #
                        # Check access to Boot Menu option, '4. Adjust the console baud rate'
                        self.log(['', '-'*40, f'Step 190 : current password : {currentpw}'])
                        # self.log('     @@@ PWValidChars - selectBootMenuOptionNoPW(4)' )
                        selectBootMenuOptionNoPW(self, dut, 4)
                        # Check access to Boot Menu option, '6. System information'
                        self.log(['', '-'*40, f'Step 200 : current password : {currentpw}'])
                        # self.log('     @@@ PWValidChars - selectBootMenuOptionNoPW(6)' )
                        selectBootMenuOptionNoPW(self, dut, 6)
                        # Check access to Boot Menu option, '7. Restore Bootloader factory settings'
                        self.log(['', '-'*40, f'Step 210 : current password : {currentpw}'])
                        # self.log('     @@@ PWValidChars - selectBootMenuOptionNoPW(7)' )
                        selectBootMenuOptionNoPW(self, dut, 7)
                    else:
                        self.log(output)
                        self.failed("Security Settings Menu not accessd")
                    # store old passowrd
                    oldpw = currentpw
                #
                # Reset to security level 1 (none)
                #
                self.log(['', '-'*40, 'Reset the Security Level to 1 (None)'])
                self.log("Select the Security Levels option and check that the Security Settings Menu is accessed")
                output = dut.send('S',strList = ["Security Settings menu"])
                if "Security Settings menu" in output:
                    self.passed("Security Settings Menu accessed")
                    # select option 1 to reset secuity level
                    resetBootSecurityLevel(self, dut)
                    # Check the security setting is as expected
                    checkSecurityLevel(self, dut, 1)
                else:
                    self.log(output)
                    self.failed("Security Settings Menu not accessd")
                #
                # Reset feature licenses as setting the security level back to 1 erases them
                #
                enterAWP(self, dut)
                dut.mode('#')
                self.log("Reset the feature licenses")
                output = self.update_feature_licenses(featureList=['ALL'])
                self.log(output)
            else:
                self.log(output)
                self.failed("Security Settings Menu not accessd")

        if self.has_failed():
            restore_boot_from_tftp(self, dut)

        dut.mode('#')


class TestCase_6(ATTestCase.TestCase):
    testCaseDesc   = "Check that the security level is displayed in the Show Boot output"
    testCaseRef    = "AWP-13858"
    testCaseMethod = "1. Reboot and enter the Boot Menu\n"
    testCaseMethod += "2. Check that security level is displayed correctly in Show Boot when set to 1 (none)\n"
    testCaseMethod += "3. Set security menu option '1. Set security Level to 2 (Password Protected)'\n"
    testCaseMethod += "4. Check that security level is displayed correctly in Show Boot when set to 2 (Password Protected)\n"
    testCaseMethod += "5. Set security menu option '2. Set security Level to 3 (Locked Down)'\n"
    testCaseMethod += "6. Check that security level is displayed correctly in Show Boot when set to 3 (Locked Down)\n"
    testCaseMethod += "7. Security Menu option '1. Set security Level to 1 (None)' and check security level has been reset\n"

    def configure(self):
        get_all_misc(self)

    def main(self):
        dut = self.dut
        # Check that the security level is displayed in the Show Boot output
        self.log(['', 'Enter the Boot Menu'])
        if not enter_bootrom_with_retry(self, dut):
            self.failed("Problem occurred entering bootloader")
        else:
            clear_bootloader_buffer(dut)
            self.log("Select the Security Levels option and check that the Security Settings Menu is accessed")
            output = dut.send('S',strList = ["Enter selection"])
            if "Security Settings menu" in output:
                self.passed("Security Settings Menu accessd")
                # check what security level is currently set
                if "currently set to 1 (None)" not in output:
                    self.log("Security level set, resetting to none")
                    resetBootSecurityLevel(self, dut)
                # Check that Show Boot displays the correct information with security level 1 (none) set
                self.log("Check that Show Boot displays the correct information with security level 1 (none) set")
                enterAWP(self, dut)
                dut.mode('#')
                output = dut.cmd('show boot')
                if "Boot Security Level: none" in output:
                    self.passed("Security level displayed correctly in Show Boot")
                else:
                    self.failed("Security level not displayed correctly in Show Boot")
                    self.log(output)

                if not enter_bootrom_with_retry(self, dut, maxAttempts=10):
                    self.failed("Problem occurred entering bootloader, unable to determine what state the DUT is in")

                clear_bootloader_buffer(dut)
                self.log("Select the Security Levels option and check that the Security Settings Menu is accessed")
                output = dut.send('S',strList = ["Enter selection"])
                if "Security Settings menu" in output:
                    self.passed("Security Settings Menu accessd")
                    # Set security level and check that Show Boot displays the correct information
                    self.log("Set security level and check that Show Boot displays the correct information")
                    currentlevellist = [2,3]
                    currentpw = '123456'
                    for currentlevel in currentlevellist:
                        if currentlevel == 2:
                            levelname = "password"
                        elif currentlevel == 3:
                            levelname = "lockdown"
                        else:
                            # not a valid level name so will force an error
                            levelname = "xxxx"
                        # Check if  a security level has been set
                        output = dut.send('\n',strList = ["Enter selection"])
                        if "Security Settings menu" in output:
                            self.passed("Security Settings Menu accessd")
                            self.log(f"Set password to, '{currentpw}'")
                            # Set the security level
                            setSecurityLevel(self, dut, currentlevel, currentpw)
                            # Check that Show Boot displays the correct information
                            self.log("Check that Show Boot displays the correct information with security level %s set" %(currentlevel))
                            enterAWP(self, dut)
                            dut.mode('#')
                            output = dut.cmd('show boot')
                            if f"Boot Security Level: {levelname}" in output:
                                self.passed("Security level displayed correctly in Show Boot")
                            else:
                                self.failed("Security level not displayed correctly in Show Boot")
                                self.log(output)
                            if not enter_bootrom_with_retry(self, dut, maxAttempts=10):
                                self.failed("Problem occurred entering bootloader, unable to determine what state the DUT is in")

                            clear_bootloader_buffer(dut)
                            self.log("Select the Security Level option and check that the Security Settings Menu is accessed")
                            dut.cmd('s')
                        else:
                            self.log(output)
                            self.failed("Security Settings Menu not accessed")
                else:
                    self.log(output)
                    self.failed("Security Settings Menu not accessed")
                #
                # Reset to security level 1 (none)
                #
                self.log(['', 'Reset the Security Level to 1 (None)'])
                self.log("Select the Security Levels option and check that the Security Settings Menu is accessed")
                output = dut.send('S',strList = ["Security Settings menu"])
                if "Security Settings menu" in output:
                    self.passed("Security Settings Menu accessed")
                    # select option 1 to reset secuity level
                    resetBootSecurityLevel(self, dut)
                    # Check the security setting is as expected
                    checkSecurityLevel(self, dut, 1)
                else:
                    self.log(output)
                    self.failed("Security Settings Menu not accessed")
                #
                # Reset feature licenses as setting the security level back to 1 erases them
                #
                enterAWP(self, dut)
                dut.mode('#')
                self.log("Reset the feature licenses")
                output = self.update_feature_licenses(featureList=['ALL'])
                if output == True:
                    self.log('...done')
                else:
                    self.log(output)
            else:
                self.log(output)
                self.failed("Security Settings Menu not accessed")
            enterAWP(self, dut)

        if self.has_failed():
            restore_boot_from_tftp(self, dut)

        dut.mode('#')


class TestCase_7(ATTestCase.TestCase):
    testCaseDesc   = "Check that the passowrd timeout activates after 60 seconds and reboot the device"
    testCaseRef    = "AWP-13839"
    testCaseMethod = "1. Reboot and enter the Boot Menu\n"
    testCaseMethod += "2. Set security menu option '1. Set security Level to 2 (Password Protected)'\n"
    testCaseMethod += "3. Check that the passowrd functions correctly, including one character every 50 seconds\n"
    testCaseMethod += "4. Check that passowed timeout reboots the device when not entry is made for 60 seconds\n"
    testCaseMethod += "5. Check that passowed timeout reboots the device when a partial entry is made and no furhter entry for 60 seconds\n"
    testCaseMethod += "6. Check that passowed timeout reboots the device when a valid entry is made and no Return for 60 seconds\n"
    testCaseMethod += "7. Security Menu option '1. Set security Level to 1 (None)' and check security level has been reset\n"

    def configure(self):
        get_all_misc(self)
    
    def main(self):
        # Check that the passowrd timeout activates after 60 seconds and reboot the device
        dut = self.dut
        self.log(['', 'Enter the Boot Menu'])
        if not enter_bootrom_with_retry(self, dut):
            self.failed("Problem occurred entering bootloader")
        else:
            clear_bootloader_buffer(dut)
            self.log("Select the Security Levels option and check that the Security Settings Menu is accessed")
            output = dut.send('S',strList = ["Enter selection"])
            if "Security Settings menu" in output:
                self.passed("Security Settings Menu accessed")
                # check what security level is currently set
                if "currently set to 1 (None)" not in output:
                    self.log("Security level set, resetting to none")
                    resetBootSecurityLevel(self, dut)
                #
                # Set security level 2
                # Check that the passowrd functions correctly, including one character every 50 seconds
                # Check that different forms of incomplete password entry will reboot the device:
                #	- no input
                #	- partial correct input
                #	- complete correct input no Return
                #
                currentpw = '123456'
                self.log("Set security level 2 and check a valid password entry")
                # Set security level 2
                setSecurityLevel(self, dut, 2, currentpw)
                # Correct password
                selectBootMenuOptionCorrectPW(self, dut, 1, currentpw)
                # Correct password - with timeout = 50 seconds per character
                selectBootMenuOptionPWTimeout(self, dut, 1, currentpw, 50, True)
                # No password - with timeout = 60, should reboot
                selectBootMenuOptionPWTimeout(self, dut, 1, "", 60)
                #
                # TODO: Add a test for security level 3
                #
            else:
                self.log(output)
                self.failed("Security Settings Menu not accessed")
                enter_bootrom_with_retry(self, dut)

            clear_bootloader_buffer(dut)
            self.log("Select the Security Levels option and check that the Security Settings Menu is accessed")
            output = dut.send('S',strList = ["Enter selection"])
            if "Security Settings menu" in output:
                self.passed("Security Settings Menu accessed")
                # check what security level is currently set
                if "currently set to 1 (None)" not in output:
                    self.log("Security level set, resetting to none")
                    resetBootSecurityLevel(self, dut)
                    # Check the security setting is as expected
                    checkSecurityLevel(self, dut, 1)
                    #
                    # Reset feature licenses as setting the security level back to 1 erases them
                    #
                    enterAWP(self, dut)
                    dut.mode('#')
                    self.log("Reset the feature licenses")
                    output = self.update_feature_licenses(featureList=['ALL'])
                    self.log(output)
            enterAWP(self, dut)

        if self.has_failed():
            restore_boot_from_tftp(self, dut)

        dut.mode('#')


class TestCase_8(ATTestCase.TestCase):
    testCaseDesc   = "Check that security levels 2 & 3 stop access to Start-Shell"
    testCaseRef    = "AWP-13857"
    testCaseMethod = "1. Reboot and enter the Boot Menu\n"
    testCaseMethod += "2. Set security menu option '1. Set security Level to 1 (None)'\n"
    testCaseMethod += "3. Check that Start-Shell can be accessed\n"
    testCaseMethod += "4. Set security menu option '1. Set security Level to 2 (Password Protected)'\n"
    testCaseMethod += "5. Check that Start-Shell can be accessed\n"
    testCaseMethod += "6. Set security menu option '2. Set security Level to 3 (Locked Down)'\n"
    testCaseMethod += "7. Check that Start-Shell can not be accessed\n"
    testCaseMethod += "8. Security Menu option '1. Set security Level to 1 (None)' and check security level has been reset\n"

    def configure(self):
        get_all_misc(self)
    
    def main(self):
        # Check that security levels 2 & 3 stop access to Start-Shell
        dut = self.dut
        # check a start-shell license has been installed, if not install
        checkLicenseACCESS(self, dut)
        self.log(['', 'Enter the Boot Menu'])
        if not enter_bootrom_with_retry(self, dut):
            self.failed("Problem occurred entering bootloader")
        else:
            clear_bootloader_buffer(dut)
            self.log("Select the Security Levels option and check that the Security Settings Menu is accessed")
            output = dut.send('S',strList = ["Enter selection"])
            if "Security Settings menu" in output:
                self.passed("Security Settings Menu accessed")
                # check what security level is currently set
                if "currently set to 1 (None)" not in output:
                    self.log("Security level set, resetting to none")
                    resetBootSecurityLevel(self, dut)
                # Reboot the device and check access to Start-Shell is not restricted
                self.log("Reboot device and check access to start-shell, should be allowed")
                enterAWP(self, dut)
                # check a start-shell license has been installed, if not log as fail and install
                checkLicenseACCESS(self, dut, True)
                # check access to Start-Shell is not restricted
                output = dut.cmd('start-shell')
                if "Type 'exit' to return to the imi shell." in output:
                    self.passed("Start-Shell is accessible when in security level 1")
                    outputexit = dut.cmd('exit')
                    output = dut.cmd('sho sys')
                    if "System Status" in output:
                        self.passed("Start-Shell exited")
                    else:
                        self.passed("Start-Shell not exited")
                        self.log (outputexit)
                        self.log (output)
                else:
                    self.failed("Start-Shell is not accessible when in security level 1")
                    self.log (output)
                # return to Boot Menu
                enter_bootrom_with_retry(self, dut)
                clear_bootloader_buffer(dut)
                self.log("Select the Security Levels option and check that the Security Settings Menu is accessed")
                output = dut.send('S',strList = ["Enter selection"])
                if "Security Settings menu" in output:
                    self.log("Set security level 2")
                    # Set security level 2
                    setSecurityLevel(self, dut, 2, '123456')
                    self.log("Reboot device and check access to start-shell, should be allowed")
                    enterAWP(self,dut)
                    # check a start-shell license has been installed, if not log as fail and install
                    checkLicenseACCESS(self, dut, True)
                    # check access to Start-Shell is restricted
                    output = dut.cmd('start-shell')
                    if "Type 'exit' to return to the imi shell." in output:
                        self.passed("Start-Shell is accessible when in security level 2")
                        outputexit = dut.cmd('exit')
                        output = dut.cmd('sho sys')
                        if "System Status" in output:
                            self.passed("Start-Shell exited")
                        else:
                            self.passed("Start-Shell not exited")
                            self.log (outputexit)
                            self.log (output)
                    else:
                        self.failed("Start-Shell is not accessible when in security level 2")
                        self.log (output)
                else:
                    self.log(output)
                    self.failed("Security Settings Menu not accessd")
                # return to Boot Menu
                enter_bootrom_with_retry(self, dut)
                clear_bootloader_buffer(dut)
                self.log("Select the Security Levels option and check that the Security Settings Menu is accessed")
                output = dut.send('S',strList = ["Enter selection"])
                if "Security Settings menu" in output:
                    self.log("Set security level 3")
                    # Set security level 3
                    setSecurityLevel(self, dut, 3, '123456')
                    self.log("Reboot device and check access to start-shell, should be disallowed")
                    enterAWP(self, dut)
                    # check a start-shell license has been installed, if not log as fail and install
                    checkLicenseACCESS(self, dut, True)
                    # check access to Start-Shell is restricted
                    output = dut.cmd('start-shell')
                    if "Invalid input detected" in output:
                        self.passed("Start-Shell is not accessible when in security level 3")
                    else:
                        self.failed("Start-Shell is not restricted when in security level 3")
                        outputexit = dut.cmd('exit')
                    output = dut.cmd('sho sys')
                    if "System Status" in output:
                        self.passed("Start-Shell exited")
                    else:
                        self.passed("Start-Shell not exited")
                        self.log (outputexit)
                        self.log (output)
                else:
                    self.log(output)
                    self.failed("Security Settings Menu not accessed")
            else:
                self.log(output)
                self.failed("Security Settings Menu not accessed")

            if not enter_bootrom_with_retry(self, dut, maxAttempts=10):
                self.failed("Problem occurred entering bootloader, unable to determine what state the DUT is in")

            clear_bootloader_buffer(dut)
            self.log("Select the Security Levels option and check that the Security Settings Menu is accessed")
            output = dut.send('S',strList = ["Enter selection"])
            if "Security Settings menu" in output:
                self.passed("Security Settings Menu accessd")
                # check what security level is currently set
                if "currently set to 1 (None)" not in output:
                    self.log("Security level set, resetting to none")
                    resetBootSecurityLevel(self, dut)
                    # Check the security setting is as expected
                    checkSecurityLevel(self, dut, 1)
                    #
                    # Reset feature licenses as setting the security level back to 1 erases them
                    #
                    enterAWP(self, dut)
                    dut.mode('#')
                    self.log("Reset the feature licenses")
                    output = self.update_feature_licenses(featureList=['ALL'])
                    self.log(output)
            enterAWP(self, dut)

        if self.has_failed():
            restore_boot_from_tftp(self, dut)

        dut.mode('#')


if __name__ == '__main__':
    ts = TestSet()
    ts.add_testCase(TestCase_1())
    ts.add_testCase(TestCase_2(confCheck=False))
    ts.add_testCase(TestCase_3(confCheck=False))
    ts.add_testCase(TestCase_4(confCheck=False))
    ts.add_testCase(TestCase_5(confCheck=False))
    ts.add_testCase(TestCase_6(confCheck=False))
    ts.add_testCase(TestCase_7(confCheck=False))
    ts.add_testCase(TestCase_8(confCheck=False))
    ts.run(sys.argv)
