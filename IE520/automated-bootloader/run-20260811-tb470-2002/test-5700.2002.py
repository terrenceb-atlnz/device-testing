#!/usr/bin/python3

import sys, os
import time
from framework import ATTestSet, ATTestCase
from framework.ATDrivers.ATBootLoader import *
from framework.ATLibrary.ATTools import copy_build
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
        createFlashBootImages(self, dut, filenames=[self.MAIN_RELEASE, self.BACKUP_RELEASE])


class TestCase_1(ATTestCase.TestCase):
    testCaseDesc   = 'SD Card is present'
    testCaseRef    = "-"
    testCaseMethod = "1. If DUT shows an SD card slot, fail if there is no SD card\n"

    def main(self):
        dut = self.dut
        if dut.has_sd_card(current=True):
            self.passed("DUT's SD card slot is populated")
        else:
            dut.mode('#')
            output = dut.cmd('show file systems')
            line = [x for x in output.splitlines() if 'sdcard' in x]
            if line:
                self.failed('DUT supports SD Card but no SD Card installed')
            else:
                self.supported = False
                self.powerCycleOnFail = False
                self.failed('DUT does not support SD Card')


class TestCase_2(ATTestCase.TestCase):
    testCaseDesc   = 'USB Media is present'
    testCaseRef    = "-"
    testCaseMethod = "1. If DUT shows a USB slot, fail if there is no USB media\n"

    def main(self):
        dut = self.dut
        if dut.has_usb_media(current=True):
            self.passed("DUT's USB slot is populated")
        else:
            dut.mode('#')
            output = dut.cmd('show file systems')
            line = [x for x in output.splitlines() if 'usbstick' in x]
            if line:
                self.failed('DUT supports USB Media but no USB Media installed')
            else:
                self.supported = False
                self.powerCycleOnFail = False
                self.failed('DUT does not support USB Media')


class TestCase_10(ATTestCase.TestCase):
    testCaseDesc   = 'Skip Default config'
    testCaseRef    = "AWP2716"
    testCaseMethod = "1. Check default and currrent boot config settings\n"
    testCaseMethod += "2. Add config 'log console level alerts' to the current config\n"
    testCaseMethod += "3. Enter the Boot menu and select option 5 - Special boot options\n"
    testCaseMethod += "4. Select option 1 - Skip startup script (Use system defaults)\n"
    testCaseMethod += "5. On reboot check that the default boot config was used by checking that 'log console level alerts' was not configured\n"

    def configure(self):
        get_all_misc(self)

    def main(self):
        dut = self.dut
        self.log(['',"Check Default boot config is set"])
        checkDefaultBootConfig(self, dut, expected="default.cfg")

        self.log(['',"Check Current boot config is set"])
        expectedConfig = f'{dut}_{self.testSuiteNum}_{self.testSetNum}_{self.testCaseNum}.cfg'
        checkCurrentBootConfig(self, dut, expected=expectedConfig)

        self.log(['',"Set current config to contain config to 'log console level alerts'"])
        dut.mode(')#')
        dut.cmd('log console level alerts')
        dut.mode('#')
        dut.cmd('write')
        output = dut.cmd('show run')
        if 'log console level alerts' in output:
            self.passed("Current config has been updated")
        else:
            self.log(output)
            self.failed("config does not have 'log console level alerts")
        self.log('')
        
        result = set_skip_startup_script(self, dut)
        if result:
            self.passed("correct message when setting skip startup script")
        else:
            self.log(output)
            self.failed("incorrect message when setting skip startup script")

        dut.mode('#')
        self.log(['', "Check that running config does not have the config to 'log console level alerts'"])
        output = dut.cmd('show run')
        if 'log console level' in output:
            self.log(output)
            self.failed("config persisted when skipping boot config")
        else:
            self.passed("default config has been loaded")
            self.log('')

        dut.reboot()
        dut.mode(')#')
        self.log("Set current config to not contain config to 'no log console level alerts'")
        dut.cmd('no log console level alerts')
        dut.mode('#')
        dut.cmd('wr')
        output = dut.cmd('show run')
        if 'log console level' in output:
            self.log(output)
            self.failed("config 'log console level alerts' persisted when config was changed")
        else:
            self.passed("config has been reverted")


class TestCase_release_filenames(ATTestCase.TestCase):

    def configure(self):
        get_all_misc(self)

    def main(self):
        if not self.supported:
            self.log('Skipping unsupported test')
            self.powerCycleOnFail = False
            return

        dut = self.dut
        strangefilename = f"---w-z-03-09-a-y---{self.SUFFIX}"
        dut.mode('#')
        dut.cmd(f'delete force *{self.SUFFIX}')
        createFlashBootImages(self, dut,filenames=[self.BACKUP_RELEASE])
        dut.mode(')#')
        dut.cmd('no boot system')
        dut.cmd('no boot system backup')
        dut.cmd(f'boot system backup {self.BACKUP_RELEASE}')
        dut.mode('#')
        self.log('')

        checkSuccessfulOperation(self, dut, command=f'copy {self.BACKUP_RELEASE} {strangefilename}') 

        if self.TEST_MEDIA in [None, 'flash']:
            # 2. Set current release
            self.log(['', f"Set the Boot System current to {strangefilename}"])
            dut.mode(')#')
            dut.cmd(f'boot system {strangefilename}')
            checkCurrentBootImage(self, dut, expected=strangefilename)

            # 3. Set default boot source
            self.log(['', "Set default boot source to flash and reboot"])
            if not set_swi_boot_from_cli(self, dut, copyCurrentSoftware=False):
                self.log(f'Restore {dut} to booting from default')
                restore_boot_from_tftp(self, dut)
            else:
                # 4. check release file
                checkShowBoot(self, dut, release=strangefilename)

        # Same process for sd card
        if self.TEST_MEDIA == 'sd':
            # 1. Create copies to other storage
            checkSuccessfulOperation(self, dut, command=f'copy {self.BACKUP_RELEASE} card:/{strangefilename}')

            # 2. Set current release
            self.log(['', f"Set the Boot System current to card:{strangefilename}"])
            dut.mode(")#")
            dut.cmd(f'boot system card:/{strangefilename}')
            checkCurrentBootImage(self, dut, expected=f"card:/{strangefilename}")

            # 3. Set default boot source
            self.log(['', 'Set default boot source to SD Card and reboot'])
            if not set_swi_boot_from_media(self, dut, media="SD_CARD", filename=strangefilename):
                self.failed(f'Problem occured setting {dut} to boot {strangefilename} from SD card')
                self.log(f'Restore {dut} to booting from TFTP')
                restore_boot_from_tftp(self, dut)
            else:
                # 4. check release file
                checkShowBoot(self, dut, release=strangefilename, source=BootSource.SDCARD)
        
        # Same process for usb media
        if self.TEST_MEDIA == 'usb':
            # 1. Create copies to other storage
            checkSuccessfulOperation(self, dut, command=f'copy {self.BACKUP_RELEASE} usb:/{strangefilename}')

            # 2. Set current release
            self.log(['', f"Set the Boot System current to usb:{strangefilename}"])
            dut.mode(')#')
            dut.cmd(f'boot system usb:/{strangefilename}')
            checkCurrentBootImage(self, dut, f'usb:/{strangefilename}')

            # 3. Set default boot source
            self.log(['', 'Set default boot source to USB and reboot'])
            if not set_swi_boot_from_media(self, dut, media="USB", filename=strangefilename):
                self.failed(f'Problem occured setting {dut} to boot {strangefilename} from USB media')
                self.log(f'Restore {dut} to booting from TFTP')
                restore_boot_from_tftp(self, dut)
            else:
                # 4. check release file
                checkShowBoot(self, dut, release=strangefilename, source=BootSource.USB)

        # Clean up
        dut.mode(')#')
        dut.cmd('no boot system')
        dut.mode('#')
        checkSuccessfulOperation(self, dut, command=f'move {strangefilename} {self.MAIN_RELEASE}')
        restore_boot_from_tftp(self, dut)
        checkShowBoot(self, dut, release=dut.tftpfilename)
    
    def tear_down(self):
        if not self.supported:
            return

        dut = self.dut
        dut.mode(')#')
        dut.cmd('no boot system')
        dut.cmd('no boot system backup')
        dut.cmd(f'boot system {self.MAIN_RELEASE}')
        dut.cmd(f'boot system backup {self.BACKUP_RELEASE}')
        dut.mode('#')


class TestCase_20(TestCase_release_filenames):
    testCaseDesc   = 'Filenames named ---w-z-03-09-a-y---.rel - Flash'
    testCaseRef    = "AWP2750, AWP2751"
    testCaseMethod  = '1. Create copies of the main release file called ---w-z-03-09-a-y---.rel and store it in flash'
    testCaseMethod += '2. Set the Boot System current to a release file called ---w-z-03-09-a-y---.rel\n'
    testCaseMethod += '3. Set the default Boot Source to flash\n'
    testCaseMethod += '4. Check the release file ---w-z-03-09-a-y---.rel is used to boot from after each reboot\n'
    TEST_MEDIA = None


class TestCase_21(TestCase_release_filenames):
    testCaseDesc   = 'Filenames named ---w-z-03-09-a-y---.rel - SD Card'
    testCaseRef    = "AWP2750, AWP2751"
    testCaseMethod  = '1. Create copies of the main release file called ---w-z-03-09-a-y---.rel and store it in flash and SD card'
    testCaseMethod += '2. Set the Boot System current to a release file called ---w-z-03-09-a-y---.rel\n'
    testCaseMethod += '3. Set the default Boot Source to flash and to SD card with a reboot in between\n'
    testCaseMethod += '4. Check the release file ---w-z-03-09-a-y---.rel is used to boot from after each reboot\n'
    TEST_MEDIA = 'sd'

    def configure(self):
        dut = self.dut
        if not dut.has_sd_card():
            self.failed('No SD card present, test unsupported')
            self.supported = False
            self.powerCycleOnFail = False
        else:
            return super().configure()


class TestCase_22(TestCase_release_filenames):
    testCaseDesc   = 'Filenames named ---w-z-03-09-a-y---.rel - USB media'
    testCaseRef    = "AWP2750, AWP2751"
    testCaseMethod  = '1. Create copies of the main release file called ---w-z-03-09-a-y---.rel and store it in flash and USB media'
    testCaseMethod += '2. Set the Boot System current to a release file called ---w-z-03-09-a-y---.rel\n'
    testCaseMethod += '3. Set the default Boot Source to flash and to USB media with a reboot in between\n'
    testCaseMethod += '4. Check the release file ---w-z-03-09-a-y---.rel is used to boot from after each reboot\n'
    TEST_MEDIA = 'usb'

    def configure(self):
        dut = self.dut
        if not dut.has_usb_media():
            self.failed('No USB media present, test unsupported')
            self.supported = False
            self.powerCycleOnFail = False
        else:
            return super().configure()


class TestCase_30(ATTestCase.TestCase):
    testCaseDesc   = 'Try release for different platform'
    testCaseRef    = "AWP2684"
    testCaseMethod = '1. From the Boot Menu, perform a one off TFTP boot using a release intended for a different platform\n'
    testCaseMethod += '2. Check an error is reported\n'

    def configure(self):
        tb = self.tb
        dut = self.dut
        get_all_misc(self)
        dut.mode('#')
        dut.cmd(f'delete force {self.MAIN_RELEASE}')
        dut.cmd(f'delete force {self.BACKUP_RELEASE}')
        tftpFileName = f'{dut.incorrectfilename.split("-")[0]}-{tb.name}{tb.num}{self.SUFFIX}'
        if not copy_build(dut.incorrectfilename, log=self.log):
            self.failed(f'Failed to copy {dut.incorrectfilename} to local TFTP server')
        else:
            _, _, copied = download_file_from_tftp(self, dut, remoteFileName=tftpFileName, localFileName=dut.incorrectfilename)
            if not copied:
                self.failed(f'Failed to copy {tftpFileName} from local TFTP server to {dut.incorrectfilename} on flash')

    def main(self):
        if self.has_failed():
            self.failed('Skip test due to failure in preparation')
            return

        dut = self.dut
        self.log("Perform a one-off boot using a release intended for a different platform, should fail")
        booting, output = perform_one_off_boot_from_alternate_source_with_output(self, dut, fileName=dut.incorrectfilename)
        # AWP2684 FALSE PASS.  The polarity of `booting` was right, but the
        # "did we actually try?" guard sat on the booting==True branch, where it
        # cannot protect the PASS.  So `not booting` passed UNCONDITIONALLY - and
        # `not booting` is also what you get when the DUT never reached the file
        # menu at all.  On 2026-08-07 this "passed" 12 s after power-on
        # (16:10:47 on -> 16:10:59 PASS) while the device was still booting: the
        # requirement was never exercised, but it counted as verified coverage.
        # A pass now requires positive evidence that the bad file was offered.
        if booting:
            self.failed(f"no error loading an invalid release, {dut.incorrectfilename}")
            log_device_output(self, output)
        elif dut.incorrectfilename not in output:
            self.failed(f"inconclusive: never saw {dut.incorrectfilename} offered in the one-off boot selection, so "
                        f"'correctly rejected' cannot be distinguished from 'never got that far':")
            log_device_output(self, output)
        else:
            self.passed("correct error loading an invalid release")
        dut.mode('#')
        checkShowBoot(self, dut, dut.tftpfilename)
    
    def tear_down(self):
        dut = self.dut
        dut.mode('#')
        dut.cmd(f'delete force {dut.incorrectfilename}')
        createFlashBootImages(self, dut, filenames=[self.MAIN_RELEASE, self.BACKUP_RELEASE])


class TestCase_boot_from_media(ATTestCase.TestCase):

    def configure(self):
        get_all_misc(self)

    def main(self):
        if not self.supported:
            self.log('Skipping unsupported test')
            self.powerCycleOnFail = False
            return

        dut = self.dut
        self.log("Set Boot System current and backup")
        dut.mode(')#')
        dut.cmd('no boot system')
        dut.cmd(f'boot system backup {self.BACKUP_RELEASE}')
        dut.mode('#')

        if self.TEST_MEDIA == 'sd':
            checkSuccessfulOperation(self, dut, command=f'delete force card:/mainreleasecard{self.SUFFIX}')
            dut.mode(']#')
            dut.cmd('sync')
            dut.mode('#')
            checkSuccessfulOperation(self, dut, command=f'copy {self.MAIN_RELEASE} card:mainreleasecard{self.SUFFIX}')
            dut.mode(')#')
            dut.cmd(f'boot system card:mainreleasecard{self.SUFFIX}')
            dut.mode('#')
            checkCurrentBootImage(self, dut, expected=f"card:/mainreleasecard{self.SUFFIX}")
            checkBackupBootImage(self, dut, expected=self.BACKUP_RELEASE)
            self.log("Reboot and check Boot System current and backup are as set")
            set_swi_boot_from_media(self, dut, media='SD_CARD', filename=f'mainreleasecard{self.SUFFIX}')

            checkShowBoot(self, dut, release=f"mainreleasecard{self.SUFFIX}")
            checkCurrentBootImage(self, dut, expected=f"card:/mainreleasecard{self.SUFFIX}")
            checkBackupBootImage(self, dut, expected=self.BACKUP_RELEASE)

        if self.TEST_MEDIA == 'usb':
            checkSuccessfulOperation(self, dut, command=f'delete force usb:/mainreleaseusb{self.SUFFIX}')
            dut.mode(']#')
            dut.cmd('sync')
            dut.mode('#')
            checkSuccessfulOperation(self, dut, command=f'copy {self.MAIN_RELEASE} usb:/mainreleaseusb{self.SUFFIX}')
            dut.mode(')#')
            dut.cmd(f'boot system usb:mainreleaseusb{self.SUFFIX}')
            dut.mode('#')
            checkCurrentBootImage(self, dut, expected=f"usb:/mainreleaseusb{self.SUFFIX}")
            checkBackupBootImage(self, dut, expected=self.BACKUP_RELEASE)
            self.log("Reboot and check Boot System current and backup are as set")
            set_swi_boot_from_media(self, dut, media='USB', filename=f'mainreleaseusb{self.SUFFIX}')

            checkShowBoot(self, dut, release=f"mainreleaseusb{self.SUFFIX}")
            checkCurrentBootImage(self, dut, expected=f"usb:/mainreleaseusb{self.SUFFIX}")
            checkBackupBootImage(self, dut, expected=self.BACKUP_RELEASE)
        
    def tear_down(self):
        if not self.supported:
            return

        dut = self.dut
        dut.mode(')#')
        dut.cmd(f'boot system {self.MAIN_RELEASE}')
        dut.cmd(f'boot system backup {self.BACKUP_RELEASE}')
        dut.mode('#')
        restore_boot_from_tftp(self, dut)


class TestCase_41(TestCase_boot_from_media):
    testCaseDesc   = 'Boot default off sdcard'
    testCaseRef    = "AWP2707"
    testCaseMethod = '1. Set Boot System default current to sd card and backup to flash, then reboot\n'
    testCaseMethod += '2. Check Boot System to confirm device has booted from sd card\n'
    TEST_MEDIA = 'sd'

    def configure(self):
        dut = self.dut
        if not dut.has_sd_card():
            self.failed('No SD card present, test unsupported')
            self.supported = False
            self.powerCycleOnFail = False
        else:
            return super().configure()


class TestCase_42(TestCase_boot_from_media):
    testCaseDesc   = 'Boot default off usb'
    testCaseRef    = "AWP2707"
    testCaseMethod = '1. Set Boot System default current to USB and backup to flash, then reboot\n'
    testCaseMethod += '2. Check Boot System to confirm device has booted from USB\n'
    TEST_MEDIA = 'usb'

    def configure(self):
        dut = self.dut
        if not dut.has_usb_media():
            self.failed('No USB media present, test unsupported')
            self.supported = False
            self.powerCycleOnFail = False
        else:
            return super().configure()


class TestCase_50(ATTestCase.TestCase):
    testCaseDesc   = 'Boot fails with no release set'
    testCaseRef    = "AWP2640"
    testCaseMethod = '1. Set Boot System current and backup\n'
    testCaseMethod += '2. Set Boot Menu Default Boot from Boot System current and backup and reboot\n'
    testCaseMethod += '3. Delete release file set as Boot System current\n'
    testCaseMethod += '4. Check Boot System current is blank  and reboot\n'
    testCaseMethod += '5. Check boot fails with appropriate error message\n'

    def configure(self):
        get_all_misc(self)

    def main(self):
        dut = self.dut
        self.log("Set Boot System current and backup")
        dut.mode(')#')
        dut.cmd('no boot system')
        dut.cmd('no boot system backup')
        createFlashBootImages(self, dut,filenames=[self.MAIN_RELEASE, self.BACKUP_RELEASE])
        dut.mode(')#')
        dut.cmd(f'boot system {self.MAIN_RELEASE}')
        dut.cmd(f'boot system backup {self.BACKUP_RELEASE}')
        dut.mode('#')
        checkCurrentBootImage(self, dut, expected=self.MAIN_RELEASE)
        checkBackupBootImage(self, dut, expected=self.BACKUP_RELEASE)
        self.log("Set Boot Menu Default Boot to boot from Boot System current and backup setting and reboot")
        set_swi_boot_from_cli(self, dut, copyCurrentSoftware=False)
        checkCurrentBootImage(self, dut, expected=self.MAIN_RELEASE)
        checkBackupBootImage(self, dut, expected=self.BACKUP_RELEASE)

        self.log("Delete release file set as Boot System current")
        dut.mode('#')
        dut.cmd(f'delete force {self.MAIN_RELEASE}')
        self.log("Check Boot System current is a non-existent file and reboot, boot should fail as release file should not be found")
        checkCurrentBootImage(self, dut, expected=f'{self.MAIN_RELEASE} (file not found)')
        
        self.log("Check boot fails with appropriate error message")
        dut.cmd('reboot')

        checkBootFailed(self, dut, ['Error: There is no primary release file set', 'Error: Preferred release:', f'Error loading flash:{self.MAIN_RELEASE}'])

        self.log(f'Wait for DUT to boot {self.BACKUP_RELEASE}')
        dut.mode('#')
        checkShowBoot(self, dut, release=self.BACKUP_RELEASE)
        dut.cmd(f'copy {self.BACKUP_RELEASE} {self.MAIN_RELEASE}')
        dut.mode(')#')
        dut.cmd('no boot system')
        dut.cmd('no boot system backup')
        dut.cmd(f'boot system {self.MAIN_RELEASE}')
        dut.cmd(f'boot system backup {self.BACKUP_RELEASE}')
        dut.mode('#')
        self.log(f'Check Boot System current is set to flash:{self.MAIN_RELEASE} and file exists')
        checkCurrentBootImage(self, dut, expected=f'{self.MAIN_RELEASE} (file exists)')
    
    def tear_down(self):
        dut = self.dut
        restore_boot_from_tftp(self, dut)
    

class TestCase_60(ATTestCase.TestCase):
    testCaseDesc   = 'Boot with release, same name as cli'
    testCaseRef    = "AWP2682"
    testCaseMethod = '1. Set Boot System current and backup\n'
    testCaseMethod += '2. Set Boot Menu Default Boot to boot from TFTP and reboot\n'
    testCaseMethod += '3. Set Boot Menu Default Boot to boot from flash and reboot\n'
    testCaseMethod += '4. Set Boot Menu Default Boot to boot from SD card and reboot\n'
    testCaseMethod += '5. Set Boot Menu Default Boot to boot from USB and reboot\n'

    def configure(self):
        get_all_misc(self)

    def main(self):
        dut = self.dut
        self.log("Set Boot System current and backup")
        dut.mode(')#')
        dut.cmd('no boot system')
        dut.cmd(f'boot system backup {self.BACKUP_RELEASE}')
        dut.mode('#')
        dut.cmd(f'move {self.MAIN_RELEASE} {dut.tftpfilename}')
        dut.mode(')#')
        dut.cmd(f'boot system {dut.tftpfilename}')
        dut.mode('#')
        checkCurrentBootImage(self, dut, expected=dut.tftpfilename)
        self.log("Set Boot Menu Default Boot and reboot")
        set_swi_boot_from_cli(self, dut)
        checkShowBoot(self, dut, release=dut.tftpfilename, source=BootSource.CLI)

        #boot off filesystem
        self.log("Set Boot Menu Default Boot to boot from Flash and reboot")
        set_swi_boot_from_media(self, dut, media='FLASH', filename=dut.tftpfilename)
        checkShowBoot(self, dut, release=dut.tftpfilename)

    def tear_down(self):
        dut = self.dut
        dut.mode(')#')
        dut.cmd('no boot system')
        dut.mode('#')
        dut.cmd(f'move {dut.tftpfilename} {self.MAIN_RELEASE}')
        dut.mode(')#')
        dut.cmd(f'boot system {self.MAIN_RELEASE}')
        dut.mode('#')
        restore_boot_from_tftp(self, dut)


class TestCase_61(ATTestCase.TestCase):
    testCaseDesc   = 'Boot with release, same name as cli - SD Card'
    testCaseRef    = "AWP2682"
    testCaseMethod  = '1. Set Boot System current and backup\n'
    testCaseMethod += '4. Set Boot Menu Default Boot to boot from SD card and reboot\n'

    def configure(self):
        dut = self.dut
        if not dut.has_sd_card():
            self.failed('No SD card present, test unsupported')
            self.supported = False
            self.powerCycleOnFail = False
        else:
            get_all_misc(self)

    def main(self):
        dut = self.dut
        if not self.supported:
            self.log('Skipping unsupported test')
            return

        self.log("Set Boot Menu Default Boot to boot from SD card and reboot")
        set_swi_boot_from_media(self, dut, media='SD_CARD', filename=f'mainreleasecard{self.SUFFIX}')
        checkShowBoot(self, dut, release=f'mainreleasecard{self.SUFFIX}', source=BootSource.SDCARD)

    def tear_down(self):
        dut = self.dut
        if not self.supported:
            return

        dut.mode(')#')
        dut.cmd('no boot system')
        dut.mode('#')
        dut.cmd(f'move {dut.tftpfilename} {self.MAIN_RELEASE}')
        dut.mode(')#')
        dut.cmd(f'boot system {self.MAIN_RELEASE}')
        dut.mode('#')
        restore_boot_from_tftp(self, dut)


class TestCase_62(ATTestCase.TestCase):
    testCaseDesc   = 'Boot with release, same name as cli - USB Media'
    testCaseRef    = "AWP2682"
    testCaseMethod  = '1. Set Boot System current and backup\n'
    testCaseMethod += '2. Set Boot Menu Default Boot to boot from USB and reboot\n'

    def configure(self):
        dut = self.dut
        if not dut.has_usb_media():
            self.failed('No USB media present, test unsupported')
            self.supported = False
            self.powerCycleOnFail = False
        else:
            get_all_misc(self)

    def main(self):
        dut = self.dut
        if not self.supported:
            self.log('Skipping unsupported test')
            return

        self.log("Set Boot Menu Default Boot to boot from USB and reboot")
        set_swi_boot_from_media(self, dut, media='USB', filename=f'mainreleaseusb{self.SUFFIX}')
        checkShowBoot(self, dut, release=f'mainreleaseusb{self.SUFFIX}', source=BootSource.USB)

    def tear_down(self):
        dut = self.dut
        dut.mode(')#')
        dut.cmd('no boot system')
        dut.mode('#')
        dut.cmd(f'move {dut.tftpfilename} {self.MAIN_RELEASE}')
        dut.mode(')#')
        dut.cmd(f'boot system {self.MAIN_RELEASE}')
        dut.mode('#')
        restore_boot_from_tftp(self, dut)


class TestCase_70(ATTestCase.TestCase):
    testCaseDesc   = 'Check bootloader version'
    testCaseRef    = "AWP2718"
    testCaseMethod = '1. Show system information in Bootloader Menu and check the bootloader version\n'
    testCaseMethod += '2. Restart from Bootloader Menu and check bootloader version is seen at boot time\n'

    def configure(self):
        get_all_misc(self)

    def main(self):
        dut = self.dut
        self.log("Show system information in Bootloader Menu and check the bootloader version")
        enter_bootrom_with_retry(self, dut)
        clear_bootloader_buffer(dut)
        output = dut.cmd('6')
        if dut.version in output:
            self.passed("bootloader version seen in system information")
        else:
            self.log(output)
            self.failed(f"bootloader version, {dut.version}, not seen in system information")
        self.log("Restart from Bootloader Menu and check bootloader version is seen at boot time")
        # Was: dut.send('0', strList=["Verifying release"]) with no waitTime.
        # The device never prints "Verifying release", so this inherited send()'s
        # 1800 s default and returned only after a flat 30 min stall.  The assertion
        # below is on dut.version, which IS present, so this case still "passed" -
        # just half an hour late.  A silent 30 min tax, not a failure.
        output, _booted = wait_for_release_boot(self, dut, '0')
        if dut.version in output:
            self.passed(f"bootloader version, {dut.version}, seen at boot")
        else:
            self.log(output)
            self.failed("bootloader version not seen at boot")
        dut.mode('#')


class TestCase_80(ATTestCase.TestCase):
    testCaseDesc   = 'Restart from boot menu'
    testCaseRef    = "AWP2670"
    testCaseMethod = '1. Enter Boot Menu and select option, 0. Restart and check the device boots\n'

    def configure(self):
        get_all_misc(self)

    def main(self):
        dut = self.dut
        self.log("Enter Boot Menu and select option 0. Restart and check the device boots")
        enter_bootrom_with_retry(self, dut)
        clear_bootloader_buffer(dut)
        # Was: gated AND asserted on "Verifying release", which the device never
        # prints - so this was a guaranteed FAIL 30 min after a healthy restart.
        output, booted = wait_for_release_boot(self, dut, '0')
        if booted:
            self.passed("device restarted from bootmenu")
        else:
            self.log(output)
            self.failed("didn't boot from bootmenu")
        dut.mode('#')


class TestCase_90(ATTestCase.TestCase):
    testCaseExcl    = {'dut': ['AR.*','FS980']}	# Exclude routers and FS980
    testCaseDesc   = 'Boot from backup (b)'
    testCaseRef    = "AWP2654"
    testCaseMethod = '1. Enter Boot Menu and select option, B. Boot backup software\n'
    testCaseMethod += '2. Check that the current release loaded is the backup release\n'

    def configure(self):
        get_all_misc(self)

    def main(self):
        dut = self.dut
        # check if the test case is supported as this option is not supported on routers
        if not self.supported:
            if not self.has_failed():
                self.powerCycleOnFail = False
            self.failed("Test case not supported on this device")
            return
        self.log("Enter Boot Menu and select option, B. Boot backup software")
        dut.mode(')#')
        dut.cmd('no boot system')
        dut.cmd('no boot system backup')
        dut.cmd(f'boot system {self.MAIN_RELEASE}')
        dut.cmd(f'boot system backup {self.BACKUP_RELEASE}')
        checkCurrentBootImage(self, dut, expected=self.MAIN_RELEASE)
        checkBackupBootImage(self, dut, expected=self.BACKUP_RELEASE)
        enter_bootrom_with_retry(self, dut)
        clear_bootloader_buffer(dut)
        # Was: gated AND asserted on "Verifying release" - guaranteed FAIL 30 min
        # after a healthy backup boot.  AWP2654 was never actually exercised.
        output, booted = wait_for_release_boot(self, dut, 'b')
        if booted:
            self.passed("device booted")
        else:
            self.log(output)
            self.failed("didn't boot")
        self.log("Check that the current release loaded is the backup release")
        checkShowBoot(self, dut, release=self.BACKUP_RELEASE)


class TestCase_100(ATTestCase.TestCase):
    testCaseDesc   = 'Test all options for default boot'
    testCaseRef    = "AWP2639, 2646, 2647, 2651,\n"
    testCaseRef    += "2652, 2655, 2656, 2657,\n"
    testCaseRef    += "2707, 2708, 2709, 2669,\n"
    testCaseRef    += "2683, 2686, 2703, 2691"
    testCaseMethod = '1. Check menu return to Boot Menu\n'
    testCaseMethod += '2. Check default boot from flash - will boot to current boot image when set\n'
    testCaseMethod += '3. Check default boot from CLI - will boot to backup boot image when current boot image is not set\n'
    testCaseMethod += '4. Check default boot from CLI - will boot to current boot image when backup boot image is not set\n'
    testCaseMethod += '5. Check default boot from CLI - will fail to boot when both current boot image and backup boot image are not set\n'
    testCaseMethod += '6. Check default boot from SD Card - boot using a file from the SD Card, if supported\n'
    testCaseMethod += '7. Check default boot from USB - boot using a file from the USB storage device, if supported\n'

    def configure(self):
        get_all_misc(self)

    def main(self):
        dut = self.dut
        #Flash
        dut.mode(')#')
        dut.cmd('no boot system')
        dut.cmd('no boot system backup')
        dut.cmd(f'boot system {self.BACKUP_RELEASE}')
        dut.cmd(f'boot system backup {self.MAIN_RELEASE}')
        
        self.log(['', '-'*60, 'Checking menu return to Boot Menu'])
        enter_bootrom_with_retry(self, dut)
        clear_bootloader_buffer(dut)
        output = dut.send('2', strList = ["Select device:"])
        if 'Select device:' in output:
            self.passed("Default Boot menu selected")
        else:
            self.log(output)
            self.failed("did not select Default Boot menu")
        output = dut.send('0', strList = ["Boot Menu:"])
        if 'Boot Menu:' in output:
            self.passed("return to Boot Menu")
        else:
            self.log(output)
            self.failed("did not return to Boot Menu")

        self.log(['', '-'*60, 'Checking default boot from flash - note the change in boot system settings so can check change in default'])
        set_swi_boot_from_media(self, dut, media='FLASH', filename=self.MAIN_RELEASE)
        checkCurrentBootImage(self, dut, expected=self.BACKUP_RELEASE)
        checkShowBoot(self, dut, release=self.MAIN_RELEASE)
        dut.mode(')#')
        dut.cmd('no boot system')
        dut.cmd('no boot system backup')
        dut.cmd(f'boot system {self.MAIN_RELEASE}')
        dut.cmd(f'boot system backup {self.BACKUP_RELEASE}')
        dut.mode('#')
        
        #default
        ##main backup 1 1
        self.log(['', '-'*60, 'Checking default boot from flash - will boot to backup boot image when current boot image is not set'])
        set_swi_boot_from_cli(self,dut)
        checkShowBoot(self, dut, release=self.MAIN_RELEASE)
        checkCurrentBootImage(self, dut, expected=self.MAIN_RELEASE)
        checkBackupBootImage(self, dut, expected=self.BACKUP_RELEASE)
        ##main backup 0 1
        dut.mode(')#')
        dut.cmd('no boot system')
        dut.mode('#')
        checkCurrentBootImage(self, dut, expected="Not set")
        # cant use this function because it dosent all for booting from backup to be a pass
        enter_bootrom_with_retry(self,dut)
        clear_bootloader_buffer(dut)
        dut.send('2', strList=['Select device'])
        dut.send('9', strList=['Saving settings'], waitTime=120)
        dut.send('9', strList=['Error'], waitTime=120)
        checkShowBoot(self, dut, release=self.BACKUP_RELEASE)
        checkCurrentBootImage(self, dut, expected="Not set")
        checkBackupBootImage(self, dut, expected=self.BACKUP_RELEASE)

        ##main backup 1 0
        self.log(['', '-'*60, 'Checking default boot from CLI - will boot to current boot image when backup boot image is not set'])
        dut.mode(')#')
        dut.cmd(f'boot system {self.MAIN_RELEASE}')
        dut.cmd('no boot system backup')
        dut.mode('#')

        set_swi_boot_from_cli(self, dut)
        checkShowBoot(self, dut, release=self.MAIN_RELEASE)
        checkCurrentBootImage(self, dut, expected=self.MAIN_RELEASE)
        checkBackupBootImage(self, dut, expected="Not set")

        ##main backup 0 0
        self.log(['', '-'*60, 'Checking default boot from CLI - will fail to boot whern both current boot image and backup boot image are not set'])
        dut.mode(')#')
        dut.cmd('no boot system')
        dut.cmd('no boot system backup')
        dut.mode('#')
        enter_bootrom_with_retry(self,dut)
        clear_bootloader_buffer(dut)
        dut.send('2', strList=['Select device'])
        dut.send('9', strList=['Enter selection'], waitTime=120)
        checkBootFailed(self, dut, strList=["Boot failed"])
        restore_boot_from_tftp(self, dut)
        dut.mode('#')
        checkCurrentBootImage(self, dut, expected="Not set")
        checkBackupBootImage(self, dut, expected="Not set")
        #TFTP
        checkShowBoot(self, dut, release=dut.tftpfilename)

    def tear_down(self):
        dut = self.dut
        dut.mode(')#')
        dut.cmd('no boot system')
        dut.cmd('no boot system backup')
        dut.cmd(f'boot system {self.MAIN_RELEASE}')
        dut.cmd(f'boot system backup {self.BACKUP_RELEASE}')
        dut.mode('#')
        dut.cmd(f'delete usb:/mainreleaseusb{self.SUFFIX}')
        dut.cmd('y')
        dut.cmd(f'delete usb:/backupreleaseusb{self.SUFFIX}')
        dut.cmd('y')
        restore_boot_from_tftp(self, dut)


class TestCase_101(ATTestCase.TestCase):
    testCaseDesc   = 'Test all options for default boot - SD Card'
    testCaseRef    = "AWP2639, 2646, 2647, 2651,\n"
    testCaseRef    += "2652, 2655, 2656, 2657,\n"
    testCaseRef    += "2707, 2708, 2709, 2669,\n"
    testCaseRef    += "2683, 2686, 2703, 2691"
    testCaseMethod  = '1. Check menu return to Boot Menu\n'
    testCaseMethod += '2. Check default boot from SD Card - boot using a file from the SD Card\n'

    def configure(self):
        dut = self.dut
        if not dut.has_sd_card():
            self.failed('No SD card present, test unsupported')
            self.supported = False
            self.powerCycleOnFail = False
        else:
            get_all_misc(self)

    def main(self):
        dut = self.dut
        if not self.supported:
            self.log('Skipping unsupported test')
            return

        dut.mode(')#')
        dut.cmd('no boot system')
        dut.cmd('no boot system backup')
        dut.cmd(f'boot system {self.BACKUP_RELEASE}')
        dut.cmd(f'boot system backup {self.MAIN_RELEASE}')

        self.log(['', '-'*60, 'Checking default boot from SD Card - boot using a file from the SD Card'])
        dut.mode('#')
        checkSuccessfulOperation(self, dut, command=f'copy {self.MAIN_RELEASE} card:mainreleasecard{self.SUFFIX}')
        set_swi_boot_from_media(self, dut, media='SD_CARD', filename=f'mainreleasecard{self.SUFFIX}')
        checkShowBoot(self, dut, release=f"mainreleasecard{self.SUFFIX}")

        dut.mode('#')
        checkSuccessfulOperation(self, dut, command=f'copy {self.BACKUP_RELEASE} card:backupreleasecard{self.SUFFIX}')
        set_swi_boot_from_media(self, dut, media='SD_CARD', filename=f'backupreleasecard{self.SUFFIX}')
        checkShowBoot(self, dut, release=f"backupreleasecard{self.SUFFIX}")

    def tear_down(self):
        dut = self.dut
        if not self.supported:
            return

        dut.mode(')#')
        dut.cmd('no boot system')
        dut.cmd('no boot system backup')
        dut.cmd(f'boot system {self.MAIN_RELEASE}')
        dut.cmd(f'boot system backup {self.BACKUP_RELEASE}')
        dut.mode('#')
        dut.cmd(f'delete usb:/mainreleaseusb{self.SUFFIX}')
        dut.cmd('y')
        dut.cmd(f'delete usb:/backupreleaseusb{self.SUFFIX}')
        dut.cmd('y')
        restore_boot_from_tftp(self, dut)


class TestCase_102(ATTestCase.TestCase):
    testCaseDesc   = 'Test all options for default boot - USB Media'
    testCaseRef    = "AWP2639, 2646, 2647, 2651,\n"
    testCaseRef    += "2652, 2655, 2656, 2657,\n"
    testCaseRef    += "2707, 2708, 2709, 2669,\n"
    testCaseRef    += "2683, 2686, 2703, 2691"
    testCaseMethod = '1. Check menu return to Boot Menu\n'
    testCaseMethod += '2. Check default boot from USB - boot using a file from the USB storage device\n'

    def configure(self):
        dut = self.dut
        if not dut.has_usb_media():
            self.failed('No USB media present, test unsupported')
            self.supported = False
            self.powerCycleOnFail = False
        else:
            get_all_misc(self)

    def main(self):
        dut = self.dut
        if not self.supported:
            self.log('Skipping unsupported test')
            return

        dut.mode(')#')
        dut.cmd('no boot system')
        dut.cmd('no boot system backup')
        dut.cmd(f'boot system {self.BACKUP_RELEASE}')
        dut.cmd(f'boot system backup {self.MAIN_RELEASE}')

        self.log(['', '-'*60, 'Checking default boot from USB - boot using a file from the USB storage device'])
        dut.mode('#')
        checkSuccessfulOperation(self, dut, command=f'copy {self.MAIN_RELEASE} usb:/mainreleaseusb{self.SUFFIX}')
        set_swi_boot_from_media(self, dut, media='USB', filename=f'mainreleaseusb{self.SUFFIX}')
        checkShowBoot(self, dut, release=f"mainreleaseusb{self.SUFFIX}")

        dut.mode('#')
        checkSuccessfulOperation(self, dut, command=f'copy {self.BACKUP_RELEASE} usb:/backupreleaseusb{self.SUFFIX}')
        set_swi_boot_from_media(self, dut, media='USB', filename=f'backupreleaseusb{self.SUFFIX}')
        checkShowBoot(self, dut, release=f"backupreleaseusb{self.SUFFIX}")

    def tear_down(self):
        dut = self.dut
        if not self.supported:
            return

        dut.mode(')#')
        dut.cmd('no boot system')
        dut.cmd('no boot system backup')
        dut.cmd(f'boot system {self.MAIN_RELEASE}')
        dut.cmd(f'boot system backup {self.BACKUP_RELEASE}')
        dut.mode('#')
        dut.cmd(f'delete usb:/mainreleaseusb{self.SUFFIX}')
        dut.cmd('y')
        dut.cmd(f'delete usb:/backupreleaseusb{self.SUFFIX}')
        dut.cmd('y')
        restore_boot_from_tftp(self, dut)


class TestCase_110(ATTestCase.TestCase):
    testCaseDesc   = 'Test all options for one-off boot'
    testCaseRef    = "AWP2641, 2687, 2690, 2679, 2680, 2658,\n"
    testCaseRef    += "2671, 2681, 2673, 2674, 2675"
    testCaseMethod =  '1. Check menu return to Boot Menu\n'
    testCaseMethod += '2. Check one-off boot main release filesystem and check default boot reverts to tftp boot\n'
    testCaseMethod += '3. Check one-off boot backup release filesystem and check default boot reverts to tftp boot\n'
    testCaseMethod += '4. Check one-off boot tftp copy and check default boot reverts to tftp boot\n'

    def configure(self):
        get_all_misc(self)

    def main(self):
        dut = self.dut

        self.log(['', '-'*60, 'Checking menu return to Boot Menu'])
        enter_bootrom_with_retry(self, dut)
        clear_bootloader_buffer(dut)
        output = dut.send('1', strList = ["Select device:"])
        if 'Select device:' in output:
            self.passed("One-off Boot menu selected")
        else:
            self.log(output)
            self.failed("did not select One-off Boot menu")
        output = dut.send('0', strList = ["Boot Menu:"])
        if 'Boot Menu:' in output:
            self.passed("return to Boot Menu")
        else:
            self.log(output)
            self.failed("did not return to Boot Menu")

        self.log(['', '-'*60, 'Checking one-off boot main release filesystem'])
        booting, output = perform_one_off_boot_from_alternate_source_with_output(self, dut, fileName=self.MAIN_RELEASE)
        if not booting:
            self.failed('Problem occurred during one-off boot')
            log_device_output(self, output)
            restore_boot_from_tftp(self, dut)
        else:
            self.passed('One-off boot in progress')
        checkShowBoot(self, dut, release=self.MAIN_RELEASE)

        self.log(['', 'Checking release reverts to default boot option'])
        dut.reboot()
        checkShowBoot(self, dut, release=dut.tftpfilename)

        self.log(['', '-'*60, 'Checking one-off boot backup release filesystem'])
        booting, output = perform_one_off_boot_from_alternate_source_with_output(self, dut, fileName=self.BACKUP_RELEASE)
        if not booting:
            self.failed('Problem occurred during one-off boot')
            log_device_output(self, output)
            restore_boot_from_tftp(self, dut)
        else:
            self.passed('One-off boot in progress')
        checkShowBoot(self, dut, release=self.BACKUP_RELEASE)

        self.log(['', 'Checking release reverts to default boot option'])
        dut.reboot()
        checkShowBoot(self, dut, release=dut.tftpfilename)

        self.log(['', '-'*60, 'Checking one-off boot tftp copy'])
        copy_tftp_server_file(self, dut.tftpfilename, dut.filenamecopy)
        settingsDict = get_default_bootloader_settings_copy(self)
        settingsDict.fileName = dut.filenamecopy
        booting, output = perform_one_off_boot_from_alternate_source_with_output(self, dut, source='tftp', tftpSettings=settingsDict)
        if not booting:
            self.failed('Problem occurred during one-off boot')
            log_device_output(self, output)
            restore_boot_from_tftp(self, dut)
        else:
            self.passed('One-off boot in progress')
        checkShowBoot(self, dut, release=dut.filenamecopy)

        self.log(['', 'Checking release reverts to default boot option'])
        dut.reboot()
        checkShowBoot(self, dut, release=dut.tftpfilename)


class TestCase_111(ATTestCase.TestCase):
    testCaseDesc   = 'Test all options for one-off boot - SD Card'
    testCaseRef    = "AWP2641, 2687, 2690, 2679, 2680, 2658,\n"
    testCaseRef    += "2671, 2681, 2673, 2674, 2675"
    testCaseMethod =  '1. Check menu return to Boot Menu\n'
    testCaseMethod += '2. Check one-off boot from SD Card and check default boot reverts to tftp boot, if supported\n'
    testCaseMethod += '6. Check one-off boot from USB storage device and check default boot reverts to tftp boot, if supported\n'

    def configure(self):
        dut = self.dut
        if not dut.has_sd_card():
            self.failed('No SD card present, test unsupported')
            self.supported = False
            self.powerCycleOnFail = False
        else:
            get_all_misc(self)

    def main(self):
        dut = self.dut
        if not self.supported:
            self.log('Skipping unsupported test')
            return

        dut.mode('#')
        self.log(['', ''])
        checkSuccessfulOperation(self, dut, command=f'copy {self.MAIN_RELEASE} card:mainreleasecard{self.SUFFIX}')
        checkSuccessfulOperation(self, dut, command=f'copy {self.BACKUP_RELEASE} card:backupreleasecard{self.SUFFIX}')

        self.log(['', '-'*60, f'Checking one-off boot from SD Card, mainreleasecard{self.SUFFIX}'])
        booting, output = perform_one_off_boot_from_alternate_source_with_output(self, dut, fileName=f'mainreleasecard{self.SUFFIX}', source='card')
        if not booting:
            self.failed('Problem occurred during one-off boot')
            log_device_output(self, output)
            restore_boot_from_tftp(self, dut)
        else:
            self.passed('One-off boot in progress')
        checkShowBoot(self, dut, release=f"mainreleasecard{self.SUFFIX}", source=BootSource.SDCARD)

        self.log(['', '-'*60, f'Checking one-off boot from SD Card, backupreleasecard{self.SUFFIX}'])
        booting, output = perform_one_off_boot_from_alternate_source_with_output(self, dut, fileName=f'backupreleasecard{self.SUFFIX}', source='card')
        if not booting:
            self.failed('Problem occurred during one-off boot')
            log_device_output(self, output)
            restore_boot_from_tftp(self, dut)
        else:
            self.passed('One-off boot in progress')
        checkShowBoot(self, dut, release=f"backupreleasecard{self.SUFFIX}", source=BootSource.SDCARD)

        self.log(['', 'Checking release reverts to default boot option'])
        dut.reboot()
        checkShowBoot(self, dut, release=dut.tftpfilename)


class TestCase_112(ATTestCase.TestCase):
    testCaseDesc   = 'Test all options for one-off boot - USB Media'
    testCaseRef    = "AWP2641, 2687, 2690, 2679, 2680, 2658,\n"
    testCaseRef    += "2671, 2681, 2673, 2674, 2675"
    testCaseMethod =  '1. Check menu return to Boot Menu\n'
    testCaseMethod += '2. Check one-off boot from USB storage device and check default boot reverts to tftp boot, if supported\n'

    def configure(self):
        dut = self.dut
        if not dut.has_usb_media():
            self.failed('No USB media present, test unsupported')
            self.supported = False
            self.powerCycleOnFail = False
        else:
            get_all_misc(self)

    def main(self):
        dut = self.dut
        if not self.supported:
            self.log('Skipping unsupported test')
            return

        dut.mode('#')
        self.log(['', ''])
        checkSuccessfulOperation(self, dut, command=f'copy {self.MAIN_RELEASE} usb:/mainreleaseusb{self.SUFFIX}')
        checkSuccessfulOperation(self, dut, command=f'copy {self.BACKUP_RELEASE} usb:/backupreleaseusb{self.SUFFIX}')

        self.log(['', '-'*60, f'Checking one-off boot from USB, mainreleaseusb{self.SUFFIX}'])
        booting, output = perform_one_off_boot_from_alternate_source_with_output(self, dut, fileName=f'mainreleaseusb{self.SUFFIX}', source='usb')
        if not booting:
            self.failed('Problem occurred during one-off boot')
            log_device_output(self, output)
            restore_boot_from_tftp(self, dut)
        else:
            self.passed('One-off boot in progress')
        checkShowBoot(self, dut, release=f"mainreleaseusb{self.SUFFIX}", source=BootSource.USB)

        self.log(['', '-'*60, f'Checking one-off boot from USB, backupreleaseusb{self.SUFFIX}'])
        booting, output = perform_one_off_boot_from_alternate_source_with_output(self, dut, fileName=f'backupreleaseusb{self.SUFFIX}', source='usb')
        if not booting:
            self.failed('Problem occurred during one-off boot')
            log_device_output(self, output)
            restore_boot_from_tftp(self, dut)
        else:
            self.passed('One-off boot in progress')
        checkShowBoot(self, dut, release=f"backupreleaseusb{self.SUFFIX}", source=BootSource.USB)

        self.log(['', 'Checking release reverts to default boot option'])
        dut.reboot()
        checkShowBoot(self, dut, release=dut.tftpfilename)


class TestCase_113(ATTestCase.TestCase):
    testCaseDesc   = 'Test all options for one-off boot - YMODEM'
    testCaseRef    = "AWP2641, 2687, 2690, 2679, 2680, 2658,\n"
    testCaseRef    += "2671, 2681, 2673, 2674, 2675"
    testCaseMethod =  '1. Check menu return to Boot Menu\n'
    testCaseMethod += '2. Check one-off boot from YMODEM and check default boot reverts to tftp boot, if supported\n'
    testCaseRunPriority = 10    # Will take 12 hours at 9600 baud rate

    def configure(self):
        get_all_misc(self)

    def main(self):
        dut = self.dut
        if not self.supported:
            self.log('Skipping unsupported test')
            return

        dut.mode('#')
        self.log(['', ''])
        self.log(['', '-'*60, 'Checking one-off boot from YMODEM, tftp copy'])
        copy_tftp_server_file(self, dut.tftpfilename, dut.filenamecopy)
        booting, output = perform_one_off_boot_from_alternate_source_with_output(self, dut, fileName=os.path.join(TFTP_SERVER_PATH, dut.filenamecopy), source='ymodem')
        if not booting:
            self.failed('Problem occurred during one-off boot')
            log_device_output(self, output)
            restore_boot_from_tftp(self, dut)
        else:
            self.passed('One-off boot in progress')
        checkShowBoot(self, dut, release=dut.filenamecopy)

        self.log(['', 'Checking release reverts to default boot option'])
        dut.reboot()
        checkShowBoot(self, dut, release=dut.tftpfilename)


class TestCase_119(ATTestCase.TestCase):
    testCaseDesc   = 'Test one-off boot can read all of the flash'
    testCaseRef    = "CR-82742"
    testCaseMethod =  '1. Fill flash with release files\n'
    testCaseMethod += '2. Check one-off boot lists all release files\n'

    def configure(self):
        get_all_misc(self)

    def main(self):
        dut = self.dut

        fill_flash_with_release_files(self, dut)

        dut.mode('#')
        output = dut.cmd(f'dir *{self.SUFFIX}')
        allReleaseFiles = [x for x in output.splitlines() if self.SUFFIX in x and f' *{self.SUFFIX}' not in x]
        allReleaseFiles = [x.split('/')[-1] for x in allReleaseFiles]
        self.log(['', 'All release files:'])
        self.log([f'   {fileName}' for fileName in allReleaseFiles])

        self.log(['', '-'*60, 'Checking one-off boot lists all release files'])
        booting, bootloaderOutput = perform_one_off_boot_from_alternate_source_with_output(self, dut, fileName=f'not_a_release_file{self.SUFFIX}')
        missingReleaseFiles = [x for x in allReleaseFiles if x not in bootloaderOutput]
        if missingReleaseFiles:
            self.failed(f'One-off boot option listed {len(allReleaseFiles)-len(missingReleaseFiles)} out of {len(allReleaseFiles)} release files')
            self.log('Missing release files:')
            self.log([f'   {fileName}' for fileName in missingReleaseFiles])
            self.log(bootloaderOutput)
        else:
            self.passed(f'One-off boot listed all {len(allReleaseFiles)} release files:')
            self.log([f'   {x}' for x in bootloaderOutput.splitlines() if self.SUFFIX in x])
        
        extraReleaseFiles = [x for x in allReleaseFiles if x not in [self.MAIN_RELEASE, self.BACKUP_RELEASE]]
        if extraReleaseFiles:
            self.log(['', 'Delete extra release files from flash'])
            dut.mode('#')
            for releaseFile in extraReleaseFiles:
                dut.cmd(f'delete force {releaseFile}')


class TestCase_120(ATTestCase.TestCase):
    testCaseDesc   = 'Test one-off boot can boot from all of the flash'
    testCaseRef    = "CR-86835"
    testCaseMethod =  '1. Fill flash with release files\n'
    testCaseMethod += '2. Check one-off boot lists all release files\n'
    testCaseMethod += '3. Check one-off boot can boot each of the release files\n'

    def configure(self):
        get_all_misc(self)

    def main(self):
        dut = self.dut

        fill_flash_with_release_files(self, dut)

        dut.mode('#')
        output = dut.cmd(f'dir *{self.SUFFIX}')
        allReleaseFiles = [x for x in output.splitlines() if self.SUFFIX in x and f' *{self.SUFFIX}' not in x]
        allReleaseFiles = [x.split('/')[-1] for x in allReleaseFiles]
        allReleaseFiles.sort()
        self.log(['', 'All release files:'])
        self.log([f'   {fileName}' for fileName in allReleaseFiles])

        self.log(['', '-'*60, 'Checking one-off boot lists all release files'])
        booting, bootloaderOutput = perform_one_off_boot_from_alternate_source_with_output(self, dut, fileName=f'not_a_release_file{self.SUFFIX}')
        missingReleaseFiles = [x for x in allReleaseFiles if x not in bootloaderOutput]
        if missingReleaseFiles:
            self.failed(f'One-off boot option listed {len(allReleaseFiles)-len(missingReleaseFiles)} out of {len(allReleaseFiles)} release files')
            self.log('Missing release files:')
            self.log([f'   {fileName}' for fileName in missingReleaseFiles])
            self.log(bootloaderOutput)
        else:
            self.passed(f'One-off boot listed all {len(allReleaseFiles)} release files:')
            self.log([f'   {x}' for x in bootloaderOutput.splitlines() if self.SUFFIX in x])

        self.log(['', '-'*60, 'Perform one-off boot to each copied release file'])
        skipShowTech = False
        fileCount = 0
        for file in allReleaseFiles:
            fileCount += 1
            self.log(['', '-'*40, f'Release file {fileCount} of {len(allReleaseFiles)}', file, '-'*40])
            if file in missingReleaseFiles:
                self.log(f'Skipping {file} due to missing from one-off boot list')
            else:
                booting, output = perform_one_off_boot_from_alternate_source_with_output(self, dut, fileName=file)
                if not booting:
                    self.failed('Problem occurred during one-off boot')
                    log_device_output(self, output)
                    restore_boot_from_tftp(self, dut)
                else:
                    self.passed('Device is booting')
                if not checkShowBoot(self, dut, release=file):
                    if not skipShowTech:
                        dut.mode('#')
                        self.log(dut.cmd('show tech'))
                        skipShowTech = True

        extraReleaseFiles = [x for x in allReleaseFiles if x not in [self.MAIN_RELEASE, self.BACKUP_RELEASE]]
        if extraReleaseFiles:
            self.log(['', 'Delete extra release files from flash'])
            dut.mode('#')
            for releaseFile in extraReleaseFiles:
                dut.cmd(f'delete force {releaseFile}')


class TestCase_121(ATTestCase.TestCase):
    testCaseDesc   = 'Test setting Boot System to SD Card without a backup'
    testCaseRef    = ""
    testCaseMethod = '1. Unset Boot System and Boot System Backup\n'
    testCaseMethod += '2. Set the Boot System current to a release on SD card\n'
    testCaseMethod += '3. Check for the correct error message\n'
    testCaseMethod += '4. Set the Boot System current to a release on SD card\n'
    testCaseMethod += '5. Check for the correct error message\n'

    def configure(self):
        dut = self.dut
        if not dut.has_sd_card():
            self.failed('No SD card present, test unsupported')
            self.supported = False
            self.powerCycleOnFail = False
        else:
            get_all_misc(self)

    def main(self):
        if not self.supported:
            self.log('Skipping unsupported test')
            return

        dut = self.dut
        dut.mode(')#')
        dut.cmd('no boot system')
        dut.cmd('no boot system backup')
        dut.mode('#')
        # boot off external storage
        checkSuccessfulOperation(self, dut, command=f'copy {self.MAIN_RELEASE} card:mainreleasecard{self.SUFFIX}')
        checkSuccessfulOperation(self, dut, command=f'copy {self.BACKUP_RELEASE} card:backupreleasecard{self.SUFFIX}')
        self.log(['', f'Set the Boot System current to card:mainreleasecard{self.SUFFIX}, should fail as no backup set'])
        dut.mode(')#')
        output = dut.cmd(f'boot system card:mainreleasecard{self.SUFFIX}')
        if '% A backup file must be set' in output:
            self.passed("correct error message when setting Boot System to external storage without a backup set.")
        else:
            self.failed("expected error message not displayed when setting Boot System to external storage with a backup set.")
        
    def tear_down(self):
        if not self.supported:
            return

        dut = self.dut
        restore_boot_from_tftp(self, dut)
        dut.mode(')#')
        dut.cmd('no boot system')
        dut.cmd('no boot system backup')
        dut.mode('#')
        if dut.has_sd_card(self):
            dut.cmd(f'delete card:/mainreleasecard{self.SUFFIX}')
            dut.cmd('y')
            dut.cmd(f'delete card:/backupreleasecard{self.SUFFIX}')
            dut.cmd('y')


class TestCase_122(ATTestCase.TestCase):
    testCaseDesc   = 'Test setting Boot System to USB Media without a backup'
    testCaseRef    = ""
    testCaseMethod = '1. Unset Boot System and Boot System Backup\n'
    testCaseMethod += '2. Set the Boot System current to a release on USB\n'
    testCaseMethod += '3. Check for the correct error message\n'
    testCaseMethod += '4. Set the Boot System current to a release on USB\n'
    testCaseMethod += '5. Check for the correct error message\n'
    
    def configure(self):
        dut = self.dut
        if not dut.has_usb_media():
            self.failed('No USB media present, test unsupported')
            self.supported = False
            self.powerCycleOnFail = False
        else:
            get_all_misc(self)

    def main(self):
        if not self.supported:
            self.log('Skipping unsupported test')
            return

        dut = self.dut
        dut.mode(')#')
        dut.cmd('no boot system')
        dut.cmd('no boot system backup')
        dut.mode('#')
        # boot off external storage
        checkSuccessfulOperation(self, dut, command=f'copy {self.MAIN_RELEASE} usb:/mainreleaseusb{self.SUFFIX}')
        checkSuccessfulOperation(self, dut, command=f'copy {self.BACKUP_RELEASE} usb:/backupreleaseusb{self.SUFFIX}')
        self.log(['', f'Set the Boot System current to usb:/mainreleaseusb{self.SUFFIX}, should fail as no backup set'])
        dut.mode(')#')
        output = dut.cmd(f'boot system usb:/mainreleaseusb{self.SUFFIX}')
        expected = '% A backup file must be set'
        if expected in output:
            self.passed("correct error message when setting Boot System to external storage without a backup set.")
        else:
            self.failed("expected error message not displayed when setting Boot System to external storage with a backup set.")
            self.log('Expected: {}'.format(expected))
            self.log(output)

    
    def tear_down(self):
        if not self.supported:
            return

        dut = self.dut
        restore_boot_from_tftp(self, dut)
        dut.mode(')#')
        dut.cmd('no boot system')
        dut.cmd('no boot system backup')
        dut.cmd(f'boot system {self.MAIN_RELEASE}')
        dut.cmd(f'boot system backup {self.BACKUP_RELEASE}')
        dut.mode('#')
        if dut.has_usb_media(self):
            dut.cmd(f'delete usb:/mainreleaseusb{self.SUFFIX}')
            dut.cmd('y')
            dut.cmd(f'delete usb:/backupreleaseusb{self.SUFFIX}')
            dut.cmd('y')

if __name__ == '__main__':
    ts = TestSet()
    ts.add_testCase(TestCase_1())
    ts.add_testCase(TestCase_2())
    ts.add_testCase(TestCase_10())
    ts.add_testCase(TestCase_20())
    ts.add_testCase(TestCase_21())
    ts.add_testCase(TestCase_22())
    ts.add_testCase(TestCase_30())
    ts.add_testCase(TestCase_41())
    ts.add_testCase(TestCase_42())
    ts.add_testCase(TestCase_50())
    ts.add_testCase(TestCase_60())
    ts.add_testCase(TestCase_61())
    ts.add_testCase(TestCase_62())
    ts.add_testCase(TestCase_70())
    ts.add_testCase(TestCase_80())
    ts.add_testCase(TestCase_90())
    ts.add_testCase(TestCase_100())
    ts.add_testCase(TestCase_101())
    ts.add_testCase(TestCase_102())
    ts.add_testCase(TestCase_110())
    ts.add_testCase(TestCase_111())
    ts.add_testCase(TestCase_112())
    ts.add_testCase(TestCase_113())
    ts.add_testCase(TestCase_119())
    ts.add_testCase(TestCase_120())
    ts.add_testCase(TestCase_121())
    ts.add_testCase(TestCase_122())
    ts.run(sys.argv)
