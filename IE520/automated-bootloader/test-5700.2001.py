#!/usr/bin/python3

import sys
from framework import ATTestSet, ATTestCase
from framework.ATLibrary.ATTools import download_file_from_tftp
from library_5700 import *

class TestSet(ATTestSet.TestSet):

    FEATURES = ['ACCESS']

    def init(self, setup):
        tb    = setup.init_tb()
        dut   = setup.init_swi('swi_a')
        (dut.portA, tb.ethA) = setup.init_portlink(dut, tb, type1='port')
        if dut.portA == None:
            (dut.portA, tb.ethA) = setup.init_portlink(dut, tb, type1='port', hub=True)
        if dut.portA == None:
            (dut.portA, tb.ethA) = setup.init_portlink(dut, tb, type1='eth')
        if dut.portA == None:
            (dut.portA, tb.ethA) = setup.init_portlink(dut, tb, type1='eth', hub=True)
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
        dut.mode('#')
        dut.cmd(f'delete force *{dut.buildNameSuffix}')
        dut.cmd(f'delete stack-wide force *{dut.buildNameSuffix}')
        self.log(f'DEBUG : MAIN_RELEASE   : {self.MAIN_RELEASE}')
        self.log(f'DEBUG : BACKUP_RELEASE : {self.BACKUP_RELEASE}')
        createFlashBootImages(self, dut,filenames=[self.MAIN_RELEASE, self.BACKUP_RELEASE])


class TestCase_1(ATTestCase.TestCase):
    testCaseDesc   = "Boot System: Check the Boot System Backup release\n cannot be set to the same as the Boot System release."
    testCaseRef    = "TestLink: AWP2642"
    testCaseMethod = (
        "1. Set the Boot System release\n"
        "2. Set the Boot System Backup release to the same file\n"
        "3. Check an error is reported\n"
    )

    def configure(self):
        get_all_misc(self)

    def main(self):
        dut = self.dut
        dut.mode(')#')
        dut.cmd('no boot system')
        dut.cmd('no boot system backup')
        dut.cmd(f'boot system {self.MAIN_RELEASE}')
        checkCurrentBootImage(self, dut, expected=self.MAIN_RELEASE)
        checkBackupBootImage(self, dut)
        
        self.log(["", "Setting backup to same release as current"])
        dut.mode(")#")
        checkExpectedError(self, dut, f'boot system backup {self.MAIN_RELEASE}', 'Can not set the current')

        self.log('')
        checkCurrentBootImage(self, dut, expected=self.MAIN_RELEASE)
        checkBackupBootImage(self, dut)

        dut.mode(')#')
        dut.cmd(f'boot system backup {self.BACKUP_RELEASE}')
        checkBackupBootImage(self, dut, expected=self.BACKUP_RELEASE)
    
    def tear_down(self):
        dut = self.dut
        dut.mode(')#')
        dut.cmd('no boot system')


class TestCase_2(ATTestCase.TestCase):
    testCaseDesc   = 'Boot System: Check that the Boot System current and backup cannot be set to a file name that has now been moved to a different name.'
    testCaseRef    = "TestLink: AWP2643"
    testCaseMethod = (
        "1. Move a release file to a new name\n"
        "2. Set the Boot System current the previous relase file name which is now nonexistent\n"
        "3. Check an error is reported\n"
        )

    def configure(self):
        get_all_misc(self)
        dut = self.dut
        dut.mode(')#')
        dut.cmd('no boot system')
        dut.cmd('no boot system backup')

    def main(self):
        dut = self.dut
        dut.mode('#')

        self.log(["", "Moving the release file to a new name"])
        checkSuccessfulOperation(self, dut, command=f'move {self.MAIN_RELEASE} moved{self.MAIN_RELEASE}', expected=None)

        self.log(["", "Setting the Boot System current to the old release file name"])
        dut.mode(')#')
        checkExpectedError(self, dut, f'boot system {self.MAIN_RELEASE}', 'does not exist')

        self.log(["", "Setting the Boot System backup to the old release file name"])
        dut.mode(')#')
        checkExpectedError(self, dut, f'boot system backup {self.MAIN_RELEASE}', 'does not exist')

        self.log('')
        checkCurrentBootImage(self, dut)
        checkBackupBootImage(self, dut)
    
    def tear_down(self):
        dut = self.dut
        dut.mode('#')
        dut.cmd(f'delete force moved{self.MAIN_RELEASE}')
        dut.cmd(f'copy {self.BACKUP_RELEASE} {self.MAIN_RELEASE}')


class TestCase_3(ATTestCase.TestCase):
    testCaseDesc   = "Boot System: Check that the Boot System current and backup release cannot be set to a file that does not have the correct file extension"
    testCaseRef    = "TestLink: AWP2644"
    testCaseMethod = (
        "1. Rename a release file to a '.cfg' file\n"
        "2. Set the Boot System current and then the backup to the '.cfg' file\n"
        "3. Check an error is reported\n"
        )

    def configure(self):
        get_all_misc(self)
        dut = self.dut
        dut.mode(')#')
        dut.cmd('no boot system')
        dut.cmd('no boot system backup')

    def main(self):
        dut = self.dut
        dut.mode("#")

        self.log(["", "Moving the release file to a file name with a suffix of '.cfg'"])
        checkSuccessfulOperation(self, dut, command=f'move {self.MAIN_RELEASE} movedmainrelease.cfg')

        self.log(["", "Setting the Boot System current to the release file renamed with a suffix of '.cfg'"])
        dut.mode(')#')
        checkExpectedError(self, dut, "boot system movedmainrelease.cfg", 'Release files must have')

        self.log(["", "Setting the Boot System backup to the release file renamed with a suffix of '.cfg'"])
        checkExpectedError(self, dut, "boot system backup movedmainrelease.cfg", 'Release files must have')

        self.log('')
        checkCurrentBootImage(self, dut)
        checkBackupBootImage(self, dut)
    
    def tear_down(self):
        dut = self.dut
        dut.mode('#')
        dut.cmd('delete force movedmainrelease.cfg')
        dut.cmd(f'copy {self.BACKUP_RELEASE} {self.MAIN_RELEASE}')


class TestCase_4(ATTestCase.TestCase):
    testCaseDesc   = "Boot System: Check that the Boot System current and backup relesae cannot be set to a validly named release file that is not a valid release version file."
    testCaseRef    = "TestLink: AWP2645"
    testCaseMethod = (
        "1. Create a simple text file named with a valid release file name extension\n"
        "2. Set the Boot System current and then backup release to the fake release file\n"
        "3. Check an error is reported\n"
        )

    def configure(self):
        get_all_misc(self)
        dut = self.dut
        dut.mode(')#')
        dut.cmd('no boot system')
        dut.cmd('no boot system backup')

    def main(self):
        dut = self.dut
        suffix = dut.buildNameSuffix
        dut.mode("#")
        self.log(f"Create a fake release file, named as a '{suffix}' file, from simple text")
        dut.cmd(f'show run > fakerelease{suffix}')

        self.log(["", "Setting the Boot System current to the fake release file"])
        dut.mode(')#')
        checkExpectedError(self, dut, f'boot system fakerelease{suffix}', 'Not a regular file')

        self.log(["", "Setting the Boot System backup to the fake release file"])
        checkExpectedError(self, dut, f'boot system backup fakerelease{suffix}', 'Not a regular file')

        self.log('')
        checkCurrentBootImage(self, dut)
        checkBackupBootImage(self, dut)
    
    def tear_down(self):
        dut = self.dut
        suffix = dut.buildNameSuffix
        dut.mode('#')
        dut.cmd(f'delete force fakerelease{suffix}')


class TestCase_5(ATTestCase.TestCase):
    testCaseDesc   = 'Boot System: Check both the Boot System current and backup cannot be set to a nonexistent file.'
    testCaseRef    = "AWP2648"
    testCaseMethod = (
        "1. Set the Boot System current and then the backup release to the name of a nonexistent file\n"
        "2. Check an error is reported\n"
        )

    def configure(self):
        get_all_misc(self)
        dut = self.dut
        dut.mode(')#')
        dut.cmd('no boot system')
        dut.cmd('no boot system backup')

    def main(self):
        #change release to file that doesn't exist
        dut = self.dut
        suffix = dut.buildNameSuffix
        dut.mode(")#")

        self.log(["", "Setting the Boot System current to a nonexistent release file"])
        checkExpectedError(self, dut, f'boot system asdf1234qwerty{suffix}', 'does not exist')

        self.log(["", "Setting the Boot System backup to a nonexistent release file"])
        checkExpectedError(self, dut, f'boot system backup asdf1234qwerty{suffix}', 'does not exist')

        self.log('')
        checkCurrentBootImage(self, dut)
        checkBackupBootImage(self, dut)

    def tear_down(self):
        dut = self.dut
        dut.mode(')#')
        dut.cmd('no boot system')


class TestCase_6(ATTestCase.TestCase):
    testCaseDesc   = 'Boot System: Check that the file set as the Boot System current and backup cannot be moved to a different name.'
    testCaseRef    = "AWP2659"
    testCaseMethod = (
        "1. Set the Boot System current and backup to a valid release\n"
        "2. Move the file set as Boot Sytem current and backup\n"
        "3. Check an error is reported\n"
        )

    def configure(self):
        get_all_misc(self)
        dut = self.dut
        dut.mode(')#')
        dut.cmd('no boot system')
        dut.cmd('no boot system backup')
    
    def main(self):
        dut = self.dut
        suffix = dut.buildNameSuffix

        dut.mode(")#")

        self.log("Setting the Boot System current and backup to valid release files")
        dut.cmd(f'boot system {self.MAIN_RELEASE}')
        dut.cmd(f'boot system backup {self.BACKUP_RELEASE}')
        dut.mode('#')
        checkCurrentBootImage(self, dut, expected=self.MAIN_RELEASE)
        checkBackupBootImage(self, dut, expected=self.BACKUP_RELEASE)

        dut.mode('#')
        self.log(["", "Move the release file already set as the Boot System current"])
        checkExpectedError(self, dut, f'move {self.MAIN_RELEASE} asdf{suffix}', 'configured as the current boot image')

        self.log(["", "Move the release file already set as the Boot System backup"])
        checkExpectedError(self, dut, f'move {self.BACKUP_RELEASE} asdf{suffix}', 'configured as the backup boot image')

        self.log('')
        checkCurrentBootImage(self, dut, expected=self.MAIN_RELEASE)
        checkBackupBootImage(self, dut, expected=self.BACKUP_RELEASE)

    def tear_down(self):
        dut = self.dut
        dut.mode(')#')
        dut.cmd('no boot system')


class TestCase_7(ATTestCase.TestCase):
    testCaseDesc   = 'Boot System: Check that the file set as the Boot System current and backup cannot be edited.'
    testCaseRef    = "AWP2661"
    testCaseMethod = (
        "1. Set the Boot System current and backup to a valid release\n"
        "2. Edit the file set as Boot Sytem current and backup\n"
        "3. Check an error is reported\n"
        )

    def configure(self):
        get_all_misc(self)
        dut = self.dut
        dut.mode(')#')
        dut.cmd('no boot system')
        dut.cmd('no boot system backup')

    def main(self):
        #edit release files already set
        dut = self.dut
        dut.mode(")#")

        self.log("Setting the Boot System current and backup to valid release files")
        dut.cmd(f'boot system {self.MAIN_RELEASE}')
        dut.cmd(f'boot system backup {self.BACKUP_RELEASE}')
        dut.mode('#')
        checkCurrentBootImage(self, dut, expected=self.MAIN_RELEASE)
        checkBackupBootImage(self, dut, expected=self.BACKUP_RELEASE)

        self.log(["", "Edit the release file already set as the Boot System current"])
        checkSuccessfulOperation(self, dut, command=f'edit {self.MAIN_RELEASE}', expected="must be a text file")

        self.log(["", "Edit the release file already set as the Boot System backup"])
        checkSuccessfulOperation(self, dut, command=f'edit {self.BACKUP_RELEASE}', expected="must be a text file")

        self.log('')
        checkCurrentBootImage(self, dut, expected=self.MAIN_RELEASE)
        checkBackupBootImage(self, dut, expected=self.BACKUP_RELEASE)
    
    def tear_down(self):
        dut = self.dut
        dut.mode(')#')
        dut.cmd('no boot system')


class TestCase_8(ATTestCase.TestCase):
    testCaseDesc   = 'Boot System: Check that the file set as the Boot System current and backup cannot be deleted.'
    testCaseRef    = "AWP2665"
    testCaseMethod = (
        "1. Set the Boot System current and backup to a valid release\n" 
        "2. Delete the file set as Boot Sytem current and backup\n"
        "3. Check an error is reported\n"
        )

    def configure(self):
        get_all_misc(self)
        dut = self.dut
        dut.mode(')#')
        dut.cmd('no boot system')
        dut.cmd('no boot system backup')

    def main(self):
        #delete release files already set
        dut = self.dut
        dut.mode(")#")

        self.log("Setting the Boot System current and backup to valid release files")
        dut.cmd(f'boot system {self.MAIN_RELEASE}')
        dut.cmd(f'boot system backup {self.BACKUP_RELEASE}')
        dut.mode('#')
        checkCurrentBootImage(self, dut, expected=self.MAIN_RELEASE)
        checkBackupBootImage(self, dut, expected=self.BACKUP_RELEASE)

        self.log(["", "Delete the release file already set as the Boot System current"])
        checkExpectedError(self, dut, f'delete {self.MAIN_RELEASE}', 'Cannot delete')

        self.log(["", "Delete the release file already set as the Boot System backup"])
        checkExpectedError(self, dut, f'delete {self.BACKUP_RELEASE}', 'Cannot delete')

        self.log('')
        checkCurrentBootImage(self, dut, expected=self.MAIN_RELEASE)
        checkBackupBootImage(self, dut, expected=self.BACKUP_RELEASE)
    
    def tear_down(self):
        dut = self.dut
        dut.mode(')#')
        dut.cmd('no boot system')


class TestCase_9(ATTestCase.TestCase):
    testCaseDesc   = 'Boot System: Check that the file set as the Boot System current and backup can be copied.'
    testCaseRef    = "AWP2663"
    testCaseMethod =  "1. Set the Boot System current to a valid release\n"
    testCaseMethod += "2. Set the Boot System backup to nothing\n"
    testCaseMethod += "3. Delete the backup release from flash\n"
    testCaseMethod += f"4. Copy MAIN_RELEASE to a new file name\n"
    testCaseMethod += f"5. Move the new file to BACKUP_RELEASE\n"
    testCaseMethod += "6. Clear the boot system current setting and set backup to a valid file name\n"
    testCaseMethod += "7. Delete the main releas from flash\n"
    testCaseMethod += f"8. Copy BACKUP_RELEASE to a new file name\n"

    def configure(self):
        get_all_misc(self)
        dut = self.dut
        dut.mode(')#')
        dut.cmd('no boot system')
        dut.cmd('no boot system backup')
    
    def main(self):
        #copy release files already set
        dut = self.dut
        dut.mode(")#")

        self.log("Setting the Boot System current to valid release files")
        dut.cmd(f'boot system {self.MAIN_RELEASE}')
        dut.mode('#')
        checkCurrentBootImage(self, dut, expected=self.MAIN_RELEASE)
        checkBackupBootImage(self, dut, expected="Not set")

        self.log(["", f'Delete {self.BACKUP_RELEASE} file'])
        checkSuccessfulOperation(self, dut, command=f'delete {self.BACKUP_RELEASE}')

        self.log(["", "Copy the release file already set as the Boot System current"])
        checkSuccessfulOperation(self, dut, command=f'copy {self.MAIN_RELEASE} copy{self.MAIN_RELEASE}')

        self.log(["", f'Move copy{self.MAIN_RELEASE} to {self.BACKUP_RELEASE} file'])
        checkSuccessfulOperation(self, dut, command=f'move copy{self.MAIN_RELEASE} {self.BACKUP_RELEASE}')

        dut.mode(")#")
        self.log("Unset the Boot System current release")
        dut.cmd('no boot system')
        dut.cmd('no boot system backup')
        self.log("Setting the Boot System backup to valid release files")
        dut.cmd(f'boot system backup {self.BACKUP_RELEASE}')

        dut.mode('#')
        checkCurrentBootImage(self, dut, expected="Not set")
        checkBackupBootImage(self, dut, expected=self.BACKUP_RELEASE)

        self.log(["", f'Delete {self.MAIN_RELEASE} file'])
        checkSuccessfulOperation(self, dut, command=f'delete {self.MAIN_RELEASE}')

        self.log(["", "Copy the release file already set as the Boot System backup"])
        checkSuccessfulOperation(self, dut, command=f'copy {self.BACKUP_RELEASE} copy{self.BACKUP_RELEASE}')

        self.log(["", f'Move copy{self.BACKUP_RELEASE} to {self.MAIN_RELEASE} file'])
        checkSuccessfulOperation(self, dut, command=f'move copy{self.BACKUP_RELEASE} {self.MAIN_RELEASE}')

        dut.mode(")#")
        dut.cmd('no boot system')
        dut.cmd('no boot system backup')
        self.log("Setting the Boot System current and backup to valid release files")
        dut.cmd(f'boot system {self.MAIN_RELEASE}')
        dut.cmd(f'boot system backup {self.BACKUP_RELEASE}')

        self.log('')
        checkCurrentBootImage(self, dut, expected=self.MAIN_RELEASE)
        checkBackupBootImage(self, dut, expected=self.BACKUP_RELEASE)

    def tear_down(self):
        dut = self.dut
        dut.mode(')#')
        dut.cmd('no boot system')


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
    ts.run(sys.argv)
