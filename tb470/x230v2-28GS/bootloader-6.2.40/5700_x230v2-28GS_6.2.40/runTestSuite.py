#!/usr/bin/python3
import os
import os.path
import pymysql
import queue
import re
import shutil
import socket
import subprocess
import sys
import time

from argparse import (
    ArgumentParser,
    ArgumentTypeError
)
from configparser import NoSectionError
from datetime import datetime

from framework import (
    ATTestCase,
    ATTestSet,
    config_gen,
    Setup
)
from framework.ATLibrary.ATDB import get_mysql_database

# use pymysql instead of MySQLdb while we're stuck on Python 3.4
pymysql.install_as_MySQLdb()


################################################################################
# Global variables and function definitions
################################################################################

LOG_FILE_NAME = 'runTestSuite.log'
TFTP_DIR = '/tftpboot'
HOSTNAME = socket.gethostname()
TB_NUM = HOSTNAME.replace('tb', '')
RUN_DIR = os.path.abspath(os.path.curdir)
# RUN_DIRr will be something like /home/st-art/tb10/1336_acl or /home/sungb/..../1336_acl
# we want to extract /home/st-art or /home/sungb and store it as RUN_ROOT_DIR
RUN_ROOT_DIR = '/'.join(RUN_DIR.split('/')[:3])
CONFIG_DIR     = Setup.get_default_config_dir(runRootDir=RUN_ROOT_DIR)
DEFAULT_SETUP  = Setup.get_default_setup_file(configDir=CONFIG_DIR, hostName=HOSTNAME)
DEFAULT_CONFIG = Setup.get_default_config_file(configDir=CONFIG_DIR, hostName=HOSTNAME)

VERBOSE = False


def log(logStr):
    curTime = time.strftime('%Y-%m-%d %H:%M:%S')
    logStr = curTime + ': ' + logStr
    if VERBOSE:
        print(logStr)
    logFile = open(LOG_FILE_NAME, 'a')
    logFile.write(logStr  + '\n')
    logFile.close()


def execute_sh_cmd(cmdStr, stdout = subprocess.PIPE, stderr = subprocess.PIPE, logFunc = log):
    logFunc(cmdStr)
    subProc = subprocess.Popen(cmdStr, shell = True, stdout = stdout, stderr = stderr)
    outTuple = subProc.communicate()
    return (subProc.returncode, outTuple[0].decode('utf-8', errors='replace'), outTuple[1].decode('utf-8', errors='replace'))

# Create a log if the waittime between oldTimeStamp and now is greater than maxSecs


def log_if_delay(msgString, oldTimeStamp, logger, maxSecs= 120):
    currentTimeStamp = time.time()
    if (currentTimeStamp - oldTimeStamp > maxSecs):
        logger(msgString + ": " + str(currentTimeStamp - oldTimeStamp) + " secs")


def str2bool(v):
    '''
    Reference: https://stackoverflow.com/a/43357954
    '''
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise ArgumentTypeError('Boolean value expected.')


################################################################################
# Class definitions for post execution processing
################################################################################

class PostRun(ATTestSet.TestSet):

    FEATURES = ['ALL']

    def init(self, setup):
        self.testCaseRunList = None
        self.runPercent = 100

        swiList = []
        swiProcessed = set()
        swiToProcess = []

        switches = setup.setupDict['switches']
        stacks = setup.setupDict['stacks']

        tb = setup.init_tb()
        for stkName in stacks:
            setup.init_stk(stkName)
        for swiName in switches:
            swiList.append(setup.init_swi(swiName))

        swiToProcess = setup.select_control_swi(swiList)
        tb.eth = {}
        for swi in swiToProcess:
            (swi.portTB, tb.eth[swi.name]) = setup.init_portlink(swi, tb)
            if swi.portTB is None:
                self.log('%s has no direct connection to TB - Search for connection via hub' % swi.name)
                (swi.portTB, tb.eth[swi.name]) = setup.init_portlink(swi, tb, hub=True)
            if swi.portTB is None:
                stk = swi.get_stack()
                if stk:
                    self.log('%s has no direct/hub connection to TB - Search for connection via stack' % swi.name)
                    (swi.portTB, tb.eth[swi.name]) = setup.init_portlink(stk, tb)
                    if swi.portTB is None:
                        self.log('%s stack has no direct connection to TB - Search for connection via hub' % swi.name)
                        (swi.portTB, tb.eth[swi.name]) = setup.init_portlink(stk, tb, hub=True)
            if swi.portTB is None:
                self.log('ERROR: %s has no connection to TB' % swi.name)
            else:
                self.log('%s is connected to TB (%s - %s)' % (swi.name, swi.portTB, tb.eth[swi.name]))

        self.tb = tb
        self.swiList = swiList
        self.swiToProcess = swiToProcess

    def configure(self):
        tb = self.tb
        for swi in self.swiToProcess:
            if hasattr(swi, 'portTB') and swi.portTB:
                if hasattr(tb.eth[swi.name], 'swiIPOffset'):
                    swiIPOffset = tb.eth[swi.name].swiIPOffset + 1
                else:
                    swiIPOffset = 2
                tb.eth[swi.name].swiIPOffset = swiIPOffset
                swiIP = tb.eth[swi.name].get_ipv4_addr(swiIPOffset)
                swiIPOffset += 1
                swi.mode(')#')
                swi.cmd('int %s' % (swi.portTB))
                self.log('%s is connected to TB via %s' % (swi.name, swi.portTB.name))
                if swi.portTB.wanPort:
                    swi.cmd('ip address %s/%s' % (swiIP, tb.eth[swi.name].ipv4subnetPrefix))
                else:
                    swi.cmd('spanning-tree portfast')
                    swi.cmd('int vlan1')
                    swi.cmd('ip address %s/%s' % (swiIP, tb.eth[swi.name].ipv4subnetPrefix))


class TestCase_1(ATTestCase.TestCase):
    testCaseDesc    = 'Download .gz files from each switch and delete them from flash'
    testCaseRef     = ''
    testCaseMethod  = '\n'

    def __copy_to_tftp(self, swi, tftpURL, hostname=''):
        swi.mode('#')
        if len(hostname) >= 1 and hostname[-1] != '/':
            hostname += '/'

        dirOut = swi.cmd('dir %sflash:/*gz' % hostname)
        dirOut2 = swi.cmd('dir %sflash:/kernel-*.txt' % hostname)
        dirOut3 = swi.cmd('dir %sflash:/*.gui' % hostname)
        if all('No such file' in output for output in [dirOut, dirOut2, dirOut3]):
            return 0

        fileList = []
        fileListDelete = []
        if 'No such file' not in dirOut:
            dirOutList = dirOut.splitlines()
            for line in dirOutList[1:-1]:
                fileToDownload = line.split(' ')[-1]
                if fileToDownload.strip():
                    fileList.append(fileToDownload.strip())
        if 'No such file' not in dirOut2:
            dirOutList = dirOut2.splitlines()
            for line in dirOutList[1:-1]:
                fileToDownload = line.split(' ')[-1]
                if fileToDownload.strip():
                    fileList.append(fileToDownload.strip())
        msgs = ['Downloading files in this list from %s' % swi.name]
        msgs.extend(fileList)
        self.log(msgs)

        if not hasattr(self, 'keepGuiFiles'):
            self.keepGuiFiles = str2bool(config_gen.DEFAULT[config_gen.ConfigParameters.keep_gui_files])
        if not (self.keepGuiFiles or 'No such file' in dirOut3):
            dirOutList = dirOut3.splitlines()
            for line in dirOutList[1:-1]:
                fileToDelete = line.split(' ')[-1]
                fileListDelete.append(fileToDelete)
            if fileListDelete:
                msgs = ['Deleting files in this list from %s' % swi.name]
                msgs.extend(fileListDelete)
                self.log(msgs)
            for fileToDelete in fileListDelete:
                swi.cmd('del force %s' % fileToDelete)

        downloaded = 0
        for fileToDownload in fileList:
            downloadedFile = fileToDownload.split('/')[-1]
            copyCmd = 'copy %s tftp://%s//%s' % (fileToDownload, tftpURL, downloadedFile)
            self.log('Executing this command from %s: %s' % (swi.name, copyCmd))
            out = swi.cmd(copyCmd)
            if "Successful" in out:
                if self.keepGuiFiles is False or not any(guiStr in fileToDownload.lower() for guiStr in ['-gui-', '-gui_']):
                    swi.cmd('del force %s' % fileToDownload)
                self.passed('Successfully copied')
                downloaded += 1
            else:
                self.failed('Copy was not successful: %s' % out)
        return downloaded

    def __archive_lost_and_found(self, swi, stackOrChassis, archiveFileName):
        self.log('Checking for and archiving any /nvs/lost+found files on %s' % swi.name)
        if stackOrChassis:
            dirStr = '/net/192.168.255.*/nvs/lost\\+found/*'
        else:
            dirStr = '/nvs/lost\\+found/*'
        swi.mode(']#')
        nvsFiles = swi.cmd('ls -l %s' % (dirStr))
        self.log(nvsFiles)
        if 'No such file or directory' in nvsFiles:
            return False
        else:
            swi.cmd('sudo tar czf %s %s' % (archiveFileName, dirStr))
            swi.cmd('sudo rm -f %s' % (dirStr))
            return True

    def __clean_up_device(self, tb, targetPathBase, swi, resultQueue):
        tbEth = tb.eth[swi.name]
        try:
            tbEthIP = tbEth.ipv4addr
        except AttributeError:
            self.log('ERROR: TB is unreachable from %s, skipping TFTP download' % swi)
            return

        totalDownloaded = 0

        swi.mode('#')
        out = swi.cmd('')
        hostname = out.strip('\r\r\n').rstrip('#')
        output = swi.cmd('ping %s repeat 2' % tbEthIP)
        self.log(output)
        if '100% packet loss' in output:
            self.log('ERROR: TB is unreachable from %s, skipping TFTP download' % swi)
            return

        self.passed('TB is reachable from %s' % swi)

        output = swi.cmd('sh card')
        cards = None
        if 'Online' in output:
            cards = [line.split()[0] for line in output.splitlines() if 'Online' in line]

        stk = swi.get_stack()
        if cards or (stk and stk.get_stack_size() > 1):
            if cards:
                self.log('%s is a chassis or a stack of chassis' % swi.name)
                memberList = cards
            else:
                self.log('%s is in a stack of non-chassis products' % swi.name)
                memberList = stk.get_member_ids()
            self.__archive_lost_and_found(swi, stackOrChassis=True, archiveFileName='nvs_lost_and_found.tgz')
            self.log('Files will be downloaded from the following members/cards: %s' % memberList)

            if stk:
                targetPathStackBase = os.path.join(targetPathBase, stk.name)
            else:
                targetPathStackBase = os.path.join(targetPathBase, swi.name)

            os.mkdir(targetPathStackBase)
            execute_sh_cmd('chmod -R 777 %s' % targetPathStackBase, logFunc=self.log)
            stackTotalDownloaded = 0
            for mem in memberList:
                targetPath = os.path.join(targetPathStackBase, '{0}-{1}'.format(hostname, mem))
                os.mkdir(targetPath)
                execute_sh_cmd('chmod -R 777 %s' % targetPath, logFunc=self.log)
                targetURL = '%s/%s' % (tbEthIP, targetPath.replace(TFTP_DIR, ''))
                downloaded = self.__copy_to_tftp(swi, targetURL, hostname='{0}-{1}'.format(hostname, mem))
                totalDownloaded += downloaded
                stackTotalDownloaded += downloaded
                if downloaded == 0:
                    self.log('Nothing was downloaded from {0}-{1}'.format(hostname, mem))
                    shutil.rmtree(targetPath, ignore_errors=True)
            if stackTotalDownloaded == 0:
                self.log('Nothing was downloaded from {0}'.format(hostname))
                shutil.rmtree(targetPathStackBase, ignore_errors=True)
        else:
            self.log('%s is a standalone device' % swi.name)
            self.__archive_lost_and_found(swi, stackOrChassis=False, archiveFileName='nvs_lost_and_found.tgz')
            targetPath = os.path.join(targetPathBase, swi.name)
            os.mkdir(targetPath)
            execute_sh_cmd('chmod -R 777 %s' % targetPath, logFunc=self.log)
            targetURL = '%s/%s' % (tbEthIP, targetPath.replace(TFTP_DIR, ''))
            downloaded = self.__copy_to_tftp(swi, targetURL)
            totalDownloaded += downloaded
            if downloaded == 0:
                self.log('Nothing was downloaded from %s' % hostname)
                shutil.rmtree(targetPath, ignore_errors=True)
        resultQueue.put(totalDownloaded)

    def main(self):
        tb = self.testSet.tb
        swiToProcess = self.testSet.swiToProcess
        curPath = os.path.abspath(os.path.curdir)
        date = datetime.now().strftime('%Y%m%d_%H%M%S')
        archiveName = self.testSet.testSuiteNum + '_archives_' + date
        targetPathBase = os.path.join(TFTP_DIR, archiveName)
        os.mkdir(targetPathBase)
        execute_sh_cmd('chmod -R 777 %s' % targetPathBase, logFunc = self.log)

        self.passed("Starting to download *gz files")  # we don't care about its result

        totalDownloaded = 0
        device_threads = []
        resultQueue = queue.Queue()
        for swi in swiToProcess:
            device_thread = ATTestSet.threading.Thread(target=self.__clean_up_device, args=(tb, targetPathBase, swi, resultQueue), name='clean_up-%s' % swi.name)
            device_thread.daemon = True
            device_thread.start()
            device_threads.append(device_thread)

        self.testSet.wait_for_threads_join(device_threads)

        while not resultQueue.empty():
            downloaded = resultQueue.get()
            totalDownloaded += downloaded

        self.log("Total %d files were downloaded" % (totalDownloaded))
        if totalDownloaded > 0:
            tarCmd = 'tar zcvf {}.tgz -C {} {}'.format(archiveName, TFTP_DIR, archiveName)
            self.log("Executing %s" % tarCmd)
            (rc, stdout, stderr) = execute_sh_cmd(tarCmd, logFunc = self.log)
            self.log(stdout)
            self.log(stderr)


class TestCase_3(ATTestCase.TestCase):
    testCaseDesc    = 'Archive all log and pkt capture files'
    testCaseRef     = ''
    testCaseMethod  = '\n'

    def main(self):
        deviceInfoTTYs = self.testSet.deviceInfoTTYs
        if type(deviceInfoTTYs) is list:
            deviceInfoTTYs = ','.join(map(str, deviceInfoTTYs))

        self.passed("Starting to archive log files")  # don't care about the result
        deviceInfoTTYsList = deviceInfoTTYs.split(',')
        deviceInfoTTYsList = [tty.strip() for tty in deviceInfoTTYsList if tty is not None and tty.strip() != '']

        for swi in self.testSet.swiToProcess:
            if swi.tty is not None:
                if (str(swi.tty) in deviceInfoTTYsList or swi.name in deviceInfoTTYsList):
                    break

        version = 'Unknown'
        swi.mode('#')
        output = swi.cmd('sh sys | grep Software')
        lines = output.splitlines()
        for line in lines:
            if 'Software version' in line:
                version = line.split()[3]
                break
        suffix = ''
        i = 0
        archiveName = 'logs-%s.tar.gz' % version

        while os.path.exists(os.path.join(os.path.curdir, archiveName)):
            i += 1
            suffix = '_%d' % i
            archiveName = 'logs-%s%s.tar.gz' % (version, suffix)
        execute_sh_cmd('tar zcvf %s *.log* *.pcap snmp*.stderr snmp*.stdout' % archiveName, logFunc = self.log)
        execute_sh_cmd('rm -f *cap', logFunc = self.log)  # rm pkt capture files


class TestCase_4(ATTestCase.TestCase):
    testCaseDesc    = 'Publish results to the old DB'
    testCaseRef     = ''
    testCaseMethod  = '\n'

    def get_unique_dut_name(self, dut):
        dutl = dut.split(' | ')
        dutl.sort()
        dut = ' | '.join(dutl)
        return dut

    def main(self):
        testSuiteNum = self.testSet.testSuiteNum
        testSuiteName = self.testSet.testSuiteName
        deviceInfoTTYs = self.testSet.deviceInfoTTYs
        if type(deviceInfoTTYs) is list:
            deviceInfoTTYs = ','.join(map(str, deviceInfoTTYs))
        self.testSet.skip_log_file_renaming = False

        db = self.testSet.setup.get_database_by_name('results')
        if not db:
            database = get_mysql_database('framework', 'results')
        else:
            database = pymysql.connect(host=db['host'], user=db['user'], passwd=db['password'], db=db['database'])
        dbCursor = database.cursor()

        self.passed("Publish to DB started")  # we don't care if publish actually succeeded or not.
        timeStampBeforeDbOp = time.time()

        deviceInfoTTYsList = deviceInfoTTYs.split(',')
        deviceInfoTTYsList = [tty.strip() for tty in deviceInfoTTYsList if tty is not None and tty.strip() != '']
        self.log('Publish for device{} connected to {}'.format('s' if len(deviceInfoTTYsList) > 1 else '', ', '.join(map(str, deviceInfoTTYsList))))

        testSuiteRunNum = 0
        numTestCasesPassed = 0
        numTestCasesFailed = 0
        numTestCasesErrored = 0
        version = None
        published = False
        for device in deviceInfoTTYsList:
            useSwi = False
            for swi in self.testSet.swiToProcess:
                if swi.tty is None and swi.ip is None:
                    continue
                if (str(swi.tty) == str(device) or swi.name == str(device)):
                    useSwi = True
                elif swi.get_stack():
                    # Check whether this swi is just a different member of the DUT's stack
                    for member in swi.get_stack().all_members():
                        if member.tty is None and member.ip is None:
                            continue
                        if (str(member.tty) == str(device) or member.name == str(device)):
                            useSwi = True
                            break
                if useSwi:
                    break

            if not useSwi:
                continue

            published = True
            deviceType0 = None
            deviceLogFile = '%s.log' % swi.name
            self.log("Opening %s" % deviceLogFile)
            try:
                file = open(deviceLogFile, 'r')
            except IOError:
                self.log("Error: %s is not available" % deviceLogFile)
                return None
            line = file.readline()
            while line != '':
                if line.find('Switch Board Name') > -1:
                    strList = line.split()
                    startIndex = strList.index('Name:')
                    endIndex = len(strList)
                    deviceType = ''
                    for index in range(startIndex + 1, endIndex):
                        if deviceType == '':
                            deviceType = deviceType + strList[index]
                        else:
                            deviceType = deviceType + ' ' + strList[index]
                    if deviceType0 is None:
                        deviceType0 = deviceType
                if line.find('Switch Software Build Name Suffix') > -1:
                    strList = line.split()
                    suffix = '{}'.format(strList[-1].strip())
                if line.find('Switch Current Software') > -1:
                    strList = line.split()
                    software = strList[-1]
                    software = os.path.split(software)[-1]  # if software name has a directory bit, take it off.
                    if any(software.endswith(suffix) for suffix in ['.rel', '.iso']):
                        suffix = '.{}'.format(software.split('.')[-1])
                        # remove the suffix in case there is no '-' to split on
                        buildType = str(software[0:-len(suffix)]).split('-')[0]
                    else:
                        buildType = software.split('-')[0]
                if line.find('Switch Software Version') > -1:
                    strList = line.split()
                    try:
                        version = strList[-1]
                    except IndexError:
                        pass
                if line.find('Switch Software Build Date') > -1:
                    strList = line.split()
                    try:
                        buildDate = '%s %s' % (strList[-2], strList[-1])
                    except IndexError:
                        pass
                line = file.readline()
            self.log("-Software: " + software)
            self.log("-InitialDeviceType: " + deviceType0)
            self.log("-DeviceType: " + deviceType)
            self.log("-buildType: " + buildType)
            self.log("-version: " + version)
            self.log("-BuildDate: " + buildDate)

            if deviceType0 == deviceType:
                dut_changed = 0
            else:
                dut_changed = 1  # dut_changed = 1: broken. dut_changed = 2: restored

            # If this test suite does not exist in test_suites table already, insert it into the table.
            # If it already exists, overwrite the name and the testbox number in case they have been changed.
            numRows = dbCursor.execute('SELECT * FROM test_suites WHERE test_suite_id = %s', (testSuiteNum))
            if numRows == 0:
                dbCursor.execute('INSERT INTO test_suites (test_suite_id, name) VALUES (%s, %s)', (testSuiteNum, testSuiteName))
                self.log("test suite inserted : %s %s" % (testSuiteNum, testSuiteName))
            else:
                dbCursor.execute('UPDATE test_suites SET name = %s WHERE test_suite_id = %s', (testSuiteName, testSuiteNum))
                self.log("test suite updated : %s %s" % (testSuiteNum, testSuiteName))

            # Will replace above with the following code when test_suite_results retires
            # dbCursor.execute("INSERT INTO test_suites (test_suite_id, name) VALUES ('%d', '%s', '%d')" % (int(testSuiteNum), testSuiteName))

            # If deviceType and deviceType0 are made of multiple units (ie. stack), and the stack order
            # changes each time, the string variable deviceType won't match any DUT in DB and will create
            # a new entry in DB each time, while it is in fact the same setup in different order.
            # To address this, it will work out a unique name for any different permutations of units
            # and match that name in DB.
            normal_deviceType = self.get_unique_dut_name(deviceType)
            normal_deviceType0 = self.get_unique_dut_name(deviceType0)

            numRows = dbCursor.execute('SELECT setup_id, dut FROM test_setups WHERE testbox = %s AND type = %s', (TB_NUM, buildType))

            found = False
            for i in range(numRows):
                row = dbCursor.fetchone()
                setup_id, dut = row[0], row[1]
                normal_dut = self.get_unique_dut_name(dut)
                if normal_deviceType == normal_dut:  # found the setup for the TB in DB
                    found = True
                    self.log("test setup found: %s %s %s" % (testSuiteNum, deviceType, setup_id))
                    if dut_changed == 1:
                        # init and last dut are different, but last dut is available. Meaning that init was broken but restored later
                        dut_changed = 2
                    break  # use this setup
                elif normal_deviceType0 == normal_dut:  # found the initial setup for the TB in DB, setup was broken in the middle of test
                    found = True
                    self.log("test setup found: %s %s %s: But setup changed to %s during test" % (testSuiteNum, deviceType0, setup_id, deviceType))
                    break
            if not found:  # setup not found at all. This setup must be a new one. Add to the DB
                dbCursor.execute('INSERT INTO test_setups (testbox, type, dut) VALUES(%s, %s, %s)', (TB_NUM, buildType, deviceType))
                setup_id = dbCursor.lastrowid
                self.log("test setup inserted :%s %s %s" % (testSuiteNum, deviceType, setup_id))

            # update the date when this setup was last used
            dbCursor.execute("UPDATE test_setups SET last_published = %s WHERE setup_id = %s", (
                datetime.now().strftime('%Y-%m-%d'), setup_id))
            database.commit()

            # check if this setup has ever run this test suite
            numRows = dbCursor.execute('SELECT * FROM test_setup_on_test_suite WHERE test_suite_id = %s AND test_setup_id = %s', (testSuiteNum, setup_id))
            if numRows == 0:  # no, this must be the fist time this setup running this test
                dbCursor.execute('INSERT INTO test_setup_on_test_suite (test_suite_id, test_setup_id) VALUES(%s, %s)', (testSuiteNum, setup_id))
                self.log("test setup/suite relation inserted: %s %s %s" % (testSuiteNum, setup_id, dbCursor.lastrowid))
            else:  # found. this setup has run this test before
                row = dbCursor.fetchone()
                self.log("test setup/suite relation found: %s %s %s" % (testSuiteNum, setup_id, row[0]))

            # version can be something like "5.4.1-0.1" or "rapier48x_proj1558-20110126-1" or "main-johngi" or "rapier48x_proj1558-continuous"
            # If it is in "5.4.1-0.1" format, it may be either an official release or a RC. However, awp doesn't know if the running software is
            # a RC or an official release. The only way we can tell is from the software name. Two options are available.
            # 1. If the original software name was used, it will be something like "r1-5.4.1-0.1-rc2.rel". From this name, the RC version number
            # can be retrieved and it is attached to the version name, such as "5.4.1-0.1-rc2".
            # 2. Most regression tests, however, run software named like "r1-tb148.rel" after downloading from TFTP.
            # The original file name is stored in /tftpboot/r1-tb148.rel.info, and the RC version number is retrieved from that file, if available.
            #
            separator = version.find('-')
            stream = version[:separator]
            rest = version[separator:]

            is_daily_build = False
            if len(rest) == 11:  # possibly a daily build, but not definitive.
                try:
                    bdate = rest.split('-')[1]
                except IndexError:  # not a daily build
                    pass
                else:
                    try:
                        bdatetime = datetime.strptime(bdate, "%Y%m%d")
                    except ValueError:  # not a daily build
                        pass
                    else:
                        is_daily_build = True

            if not is_daily_build:
                # if the rest is only '-','.' and digits, it is a RC or release build. otherwise, we don't bother
                if re.match("^[0-9.-]*$", rest):  # now this build is either RC or release build
                    # see if software name contains rc#
                    rc_num = None
                    if software.find('-rc') > -1:  # if loaded software contains "rc", use it
                        suffix = '.{}'.format(software.split('.')[-1])
                        rc_num = software.split('rc')[1].split(suffix)[0]
                    else:  # software is like r1-tb148.rel. no rc info.
                        # but this run was done by copyBuild.py, it must have kept '/tftpboot/r1-tb148.rel.info'
                        # with the original software name
                        try:
                            f = open('/tftpboot/%s.info' % software, 'r')
                        except IOError:
                            pass  # nothing we can do...
                        else:
                            software_name = f.readline()
                            suffix = '.{}'.format(software_name.split('.')[-1].strip())
                            try:
                                rc_num = software_name.split('-rc')[1].split(suffix)[0]
                            except IndexError:
                                rc_num = None
                            f.close()
                    if rc_num:
                        version += '-rc%s' % rc_num

            if is_daily_build:
                numRows = dbCursor.execute('SELECT * FROM software WHERE version = %s', (version))
            else:  # if not daily build, within 1 hours build time difference is considered the same build
                numRows = dbCursor.execute('SELECT * FROM software WHERE version = %s and ABS(TIMEDIFF(build_date, %s)) < 10000', (version, buildDate))
            if numRows == 0:
                dbCursor.execute('INSERT INTO software (stream, version, build_date, daily_build) VALUES (%s, %s, %s, %s)', (stream, version, buildDate, 1 if is_daily_build else 0))
                software_id = dbCursor.lastrowid
                self.log("software inserted: %s %s %s" % (version, buildDate, software_id))
            else:
                row = dbCursor.fetchone()
                software_id = row[0]  # take the software id
                self.log("software found: %s %s %s" % (version, buildDate, software_id))

            # Insert the test suite results and get the unique test suite run number (run_num) from the database.
            # The special_request column can be removed because it is no longer used.
            dbCursor.execute("""INSERT INTO test_suite_results2 (test_suite_id, test_setup_id, software, software_id, special_request, dut_changed, test_published)
                                VALUES (%s, %s, %s, %s, %s, %s, %s)""", (testSuiteNum, setup_id, software, software_id, 0, dut_changed, datetime.now().strftime('%Y-%m-%d')))
            testSuiteRunNum = dbCursor.lastrowid

            # Grab data from all TestSet logs and insert into the database (with run_num from above).
            files = os.listdir('.')
            testlogFiles = []
            for fileName in files:
                if fileName.startswith('test-') and fileName.endswith('.log') and not fileName.endswith('.0.log'):
                    testlogFiles.append(fileName)
            testlogFiles.sort()
            numTestCases = 0
            numTestCasesPassed = 0
            numTestCasesFailed = 0
            numTestCasesErrored = 0
            testDetails = {}
            for testlogFileName in testlogFiles:
                file = open(testlogFileName, 'r')
                line = file.readline()
                while line != '':
                    if line.find('>> test-') > -1:
                        testCaseStartTime = None
                        testCaseDesc = None
                        testCaseEndTime = None
                        testCaseResult = None
                        testCaseRef = None
                        testCaseMethod = None
                        testCaseLogs = None
                        tempStr = line.replace('>> test-', '')
                        strList = tempStr.split('.')
                        testSetNum = strList[1]
                        if testSetNum == '0':
                            break
                        testCaseNum = strList[2].replace('\n', '')
                        numTestCases = numTestCases + 1
                        line = file.readline()
                        while line.find('TEST_CASE_DATETIME_STARTED') < 0 and line != '':
                            line = file.readline()
                        line = file.readline()
                        testCaseStartTime = line.replace('\n', '')
                        line = file.readline()
                        while line.find('TEST_CASE_DESCRIPTION') < 0 and line != '':
                            line = file.readline()
                        testCaseDesc = ''
                        line = file.readline()
                        while line.find('TEST_CASE_REFERENCES') < 0 and line != '':
                            testCaseDesc = testCaseDesc + line
                            line = file.readline()
                        testCaseRef = ''
                        line = file.readline()
                        while line.find('TEST_CASE_METHOD') < 0 and line != '':
                            testCaseRef = testCaseRef + line
                            line = file.readline()
                        testCaseMethod = ''
                        line = file.readline()
                        while line.find('TEST_CASE_LOGS') < 0 and line != '':
                            testCaseMethod = testCaseMethod + line
                            line = file.readline()
                        testCaseLogs = ''
                        line = file.readline()
                        while line.find('TEST_CASE_DATETIME_ENDED') < 0 and line != '':
                            testCaseLogs += line
                            line = file.readline()
                        # testCaseLogs = pymysql.escape_string(testCaseLogs)
                        # Truncate if too long, otherwise can't insert into the DB.
                        # MySQLdb.escape_string() can add a substantial number of bytes
                        # depending on the content of the logs.
                        if len(testCaseLogs) > 1000000:
                            testCaseLogs = testCaseLogs[:1000000] + '\n\n ---- TOO LONG, TRUNCATED ---- \n\n'
                        # Ensure the log is encoded in the same character set as the database
                        testCaseLogs = testCaseLogs.encode('latin-1', 'replace')
                        testCaseLogs = testCaseLogs.decode('latin-1', 'replace')
                        line = file.readline()
                        testCaseEndTime = line.replace('\n', '')
                        line = file.readline()
                        strList = line.split()
                        if len(strList) > 0:
                            testCaseResult = strList[2]
                        else:
                            testCaseResult = 'ERROR'
                        if testCaseResult == 'PASS':
                            numTestCasesPassed = numTestCasesPassed + 1
                        elif testCaseResult == 'FAIL':
                            numTestCasesFailed = numTestCasesFailed + 1
                        else:
                            numTestCasesErrored = numTestCasesErrored + 1
                        testDetails['%d.%d.%d' % (int(testSuiteNum), int(testSetNum), int(testCaseNum))] = (testCaseResult, testCaseDesc)

                        if not testCaseEndTime:
                            testCaseEndTime = testCaseStartTime

                        if testCaseStartTime and testCaseEndTime and testCaseDesc:
                            # Insert test case results into the database.
                            sql = """INSERT INTO test_case_results (run_num,
                                                                    test_suite_id,
                                                                    test_set_id,
                                                                    test_case_id,
                                                                    time_started,
                                                                    time_ended,
                                                                    result,
                                                                    log)
                                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                            """
                            dbCursor.execute(sql, (testSuiteRunNum,
                                                   testSuiteNum,
                                                   testSetNum,
                                                   testCaseNum,
                                                   testCaseStartTime,
                                                   testCaseEndTime,
                                                   testCaseResult,
                                                   testCaseLogs)
                                             )

                            # If the test case exists in test_cases table, update the table (because test case info might have been updated).
                            # If not (i.e. first time test case was executed), insert into the table.
                            numRows = dbCursor.execute('SELECT * FROM test_cases WHERE test_suite_id = "{}" AND test_set_id = "{}" AND test_case_id = "{}"'.format(testSuiteNum, testSetNum, testCaseNum))
                            if numRows > 0:
                                dbCursor.execute("""UPDATE test_cases SET description = %s, method = %s, reference = %s
                                            WHERE test_suite_id = %s AND
                                                test_set_id = %s AND
                                                test_case_id = %s""", (
                                    testCaseDesc, testCaseMethod, testCaseRef, testSuiteNum, testSetNum, testCaseNum))
                            else:
                                dbCursor.execute('INSERT INTO test_cases (test_suite_id, test_set_id, test_case_id, description, method, reference) '
                                                 'VALUES (%s, %s, %s, %s, %s, %s)', (testSuiteNum, testSetNum, testCaseNum, testCaseDesc, testCaseMethod, testCaseRef))
                            # See if there is known info about this test case on this testbox in test_manager table
                            numRows = dbCursor.execute("""SELECT * FROM test_manager WHERE test_suite_id = %s
                                                            AND test_set_id = %s
                                                            AND    test_case_id = %s AND testbox = %s""",
                                                       (testSuiteNum, testSetNum, testCaseNum, TB_NUM)
                                                       )
                            if numRows > 0:
                                pass  # nothing to do. Don't need to update as we know that this test case is supposed to "Run"
                            else:
                                # this test is not known. Insert the info
                                dbCursor.execute("""INSERT INTO test_manager (testbox, test_suite_id, test_set_id, test_case_id)
                                                    VALUES (%s, %s, %s, %s)""",
                                                 (TB_NUM, testSuiteNum, testSetNum, testCaseNum)
                                                 )
                    line = file.readline()

        if not published:
            self.failed('ERROR: No device found to publish results for to the old DB, with device matching {}'.format(', '.join(map(str, deviceInfoTTYsList))))

        database.commit()
        database.close()
        # Log to capture db lockups
        log_if_delay("DB operation took longer than normal", timeStampBeforeDbOp, self.log, maxSecs= 120)

        return numTestCasesFailed, numTestCasesErrored, version


class TestCase_40(ATTestCase.TestCase):
    testCaseDesc    = 'Force Publish results to the old DB using information from the DB'
    testCaseRef     = ''
    testCaseMethod  = '\n'

    def main(self):
        testSuiteNum = self.testSet.testSuiteNum
        testSuiteName = self.testSet.testSuiteName
        deviceInfoTTYs = self.testSet.deviceInfoTTYs
        if type(deviceInfoTTYs) is list:
            deviceInfoTTYs = ','.join(map(str, deviceInfoTTYs))
        self.testSet.skip_log_file_renaming = False

        db = self.testSet.setup.get_database_by_name('results')
        if not db:
            database = get_mysql_database('framework', 'results')
        else:
            database = pymysql.connect(host=db['host'], user=db['user'], passwd=db['password'], db=db['database'])
        dbCursor = database.cursor()

        self.passed("Publish to DB started")  # we don't care if publish actually succeeded or not.
        timeStampBeforeDbOp = time.time()

        deviceInfoTTYsList = deviceInfoTTYs.split(',')
        deviceInfoTTYsList = [tty.strip() for tty in deviceInfoTTYsList if tty is not None and tty.strip() != '']
        self.log('Publish for device{} connected to {}'.format('s' if len(deviceInfoTTYsList) > 1 else '', ', '.join(map(str, deviceInfoTTYsList))))

        testSuiteRunNum = 0
        numTestCasesPassed = 0
        numTestCasesFailed = 0
        numTestCasesErrored = 0
        version = None
        published = False

        dut_changed = 0

        # If this test suite does not exist in test_suites table already, insert it into the table.
        # If it already exists, overwrite the name and the testbox number in case they have been changed.
        numRows = dbCursor.execute('SELECT * FROM test_suites WHERE test_suite_id = {}'.format(testSuiteNum))
        if numRows == 0:
            dbCursor.execute('INSERT INTO test_suites (test_suite_id, name) VALUES (%s, %s)', (testSuiteNum, testSuiteName))
            self.log("test suite inserted : %s %s" % (testSuiteNum, testSuiteName))
        else:
            dbCursor.execute('UPDATE test_suites SET name = %s WHERE test_suite_id = %s', (testSuiteName, testSuiteNum))
            self.log("test suite updated : %s %s" % (testSuiteNum, testSuiteName))

        # Find the setup, dut and dut type from the database, as the most recently publish
        numRows = dbCursor.execute('SELECT setup_id, dut, type FROM test_setups WHERE testbox = {} ORDER BY last_published DESC'.format(TB_NUM))
        if numRows:
            row = dbCursor.fetchone()
            setup_id = row[0]
            dut = row[1]
            buildType = row[2]
        else:
            # There's really nothing we can do now
            return

        # update the date when this setup was last used
        dbCursor.execute("UPDATE test_setups SET last_published = %s WHERE setup_id = %s", (datetime.now().strftime('%Y-%m-%d'), setup_id))
        database.commit()

        # check if this setup has ever run this test suite
        numRows = dbCursor.execute('SELECT * FROM test_setup_on_test_suite WHERE test_suite_id = {} AND test_setup_id = {}'.format(testSuiteNum, setup_id))
        if numRows == 0:  # no, this must be the fist time this setup running this test
            dbCursor.execute('INSERT INTO test_setup_on_test_suite (test_suite_id, test_setup_id) VALUES({}, {})'.format(testSuiteNum, setup_id))
            self.log("test setup/suite relation inserted: {} {} {}".format(testSuiteNum, setup_id, dbCursor.lastrowid))
        else:  # found. this setup has run this test before
            row = dbCursor.fetchone()
            self.log("test setup/suite relation found: {} {} {}".format(testSuiteNum, setup_id, row[0]))

        # Try to determine the version from the filesystem
        version = None
        for suffix in ['.rel', '.iso']:
            softwareFileName = '{}-tb{}{}'.format(buildType, TB_NUM, suffix)
            infoFileName = '{}.info'.format(softwareFileName)
            software = softwareFileName
            if os.path.exists(os.path.join(TFTP_DIR, infoFileName)):
                try:
                    f = open(os.path.join(TFTP_DIR, infoFileName))
                except IOError:
                    pass  # nothing we can do...
                else:
                    software_name = f.readline().strip()
                try:
                    version = software_name[(software_name.index('-') + 1):-4]
                except IndexError:
                    version = None
                f.close()
            if version:
                break

        if version is None:
            return

        # version can be something like "5.4.1-0.1" or "rapier48x_proj1558-20110126-1" or "main-johngi" or "rapier48x_proj1558-continuous"
        # If it is in "5.4.1-0.1" format, it may be either an official release or a RC. However, awp doesn't know if the running software is
        # a RC or an official release. The only way we can tell is from the software name. Two options are available.
        # 1. If the original software name was used, it will be something like "r1-5.4.1-0.1-rc2.rel". From this name, the RC version number
        # can be retrieved and it is attached to the version name, such as "5.4.1-0.1-rc2".
        # 2. Most regression tests, however, run software named like "r1-tb148.rel" after downloading from TFTP.
        # The original file name is stored in /tftpboot/r1-tb148.rel.info, and the RC version number is retrieved from that file, if available.
        #
        separator = version.find('-')
        stream = version[:separator]
        rest = version[separator:]

        is_daily_build = False
        if len(rest) == 11:  # possibly a daily build, but not definitive.
            try:
                bdate = rest.split('-')[1]
            except IndexError:  # not a daily build
                pass
            else:
                try:
                    bdatetime = datetime.strptime(bdate, "%Y%m%d")
                except ValueError:  # not a daily build
                    pass
                else:
                    is_daily_build = True

        if is_daily_build:
            numRows = dbCursor.execute('SELECT * FROM software WHERE version = %s', (version))
        else:
            numRows = dbCursor.execute('SELECT * FROM software WHERE version = %s ORDER BY build_date DESC', (version))
        if numRows:
            row = dbCursor.fetchone()
            software_id = row[0]  # take the software id
            self.log("software found: %s %s " % (version, software_id))
        else:
            return

        # Insert the test suite results and get the unique test suite run number (run_num) from the database.
        # The special_request column can be removed because it is no longer used.
        dbCursor.execute("""INSERT INTO test_suite_results2 (test_suite_id, test_setup_id, software, software_id, special_request, dut_changed, test_published)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)""", (testSuiteNum, setup_id, software, software_id, 0, dut_changed, datetime.now().strftime('%Y-%m-%d')))
        testSuiteRunNum = dbCursor.lastrowid

        # Grab data from all TestSet logs and insert into the database (with run_num from above).
        files = os.listdir('.')
        testlogFiles = []
        for fileName in files:
            if fileName.startswith('test-') and fileName.endswith('.log'):
                testlogFiles.append(fileName)
        testlogFiles.sort()
        numTestCases = 0
        numTestCasesPassed = 0
        numTestCasesFailed = 0
        numTestCasesErrored = 0
        testDetails = {}
        for testlogFileName in testlogFiles:
            published = True
            file = open(testlogFileName, 'r')
            line = file.readline()
            while line != '':
                if line.find('>> test-') > -1:
                    tempStr = line.replace('>> test-', '')
                    strList = tempStr.split('.')
                    testSetNum = strList[1]
                    testCaseNum = strList[2].replace('\n', '')
                    numTestCases = numTestCases + 1
                    line = file.readline()
                    while line.find('TEST_CASE_DATETIME_STARTED') < 0 and line != '':
                        line = file.readline()
                    line = file.readline()
                    testCaseStartTime = line.replace('\n', '')
                    line = file.readline()
                    while line.find('TEST_CASE_DESCRIPTION') < 0 and line != '':
                        line = file.readline()
                    testCaseDesc = ''
                    line = file.readline()
                    while line.find('TEST_CASE_REFERENCES') < 0 and line != '':
                        testCaseDesc = testCaseDesc + line
                        line = file.readline()
                    testCaseRef = ''
                    line = file.readline()
                    while line.find('TEST_CASE_METHOD') < 0 and line != '':
                        testCaseRef = testCaseRef + line
                        line = file.readline()
                    testCaseMethod = ''
                    line = file.readline()
                    while line.find('TEST_CASE_LOGS') < 0 and line != '':
                        testCaseMethod = testCaseMethod + line
                        line = file.readline()
                    testCaseLogs = ''
                    line = file.readline()
                    while line.find('TEST_CASE_DATETIME_ENDED') < 0 and line != '':
                        testCaseLogs += line
                        line = file.readline()
                    if 'TEST_CASE_DATETIME_ENDED' in line:
                        line = file.readline()
                        testCaseEndTime = line.replace('\n', '')
                    else:
                        testCaseEndTime = None
                    # testCaseLogs = pymysql.escape_string(testCaseLogs)
                    # Truncate if too long, otherwise can't insert into the DB.
                    # MySQLdb.escape_string() can add a substantial number of bytes
                    # depending on the content of the logs.
                    if len(testCaseLogs) > 1000000:
                        testCaseLogs = testCaseLogs[:1000000] + '\n\n ---- TOO LONG, TRUNCATED ---- \n\n'
                    # Ensure the log is encoded in the same character set as the database
                    testCaseLogs = testCaseLogs.encode('latin-1', 'replace')
                    testCaseLogs = testCaseLogs.decode('latin-1', 'replace')
                    line = file.readline()
                    strList = line.split()
                    if len(strList) > 0:
                        testCaseResult = strList[2]
                    else:
                        testCaseResult = 'ERROR'
                    if testCaseResult == 'PASS':
                        numTestCasesPassed = numTestCasesPassed + 1
                    elif testCaseResult == 'FAIL':
                        numTestCasesFailed = numTestCasesFailed + 1
                    else:
                        numTestCasesErrored = numTestCasesErrored + 1
                    testDetails['%d.%d.%d' % (int(testSuiteNum), int(testSetNum), int(testCaseNum))] = (testCaseResult, testCaseDesc)

                    if testCaseEndTime:
                        # Insert test case results into the database.
                        sql = """INSERT INTO test_case_results (run_num,
                                                                test_suite_id,
                                                                test_set_id,
                                                                test_case_id,
                                                                time_started,
                                                                time_ended,
                                                                result,
                                                                log)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """
                        dbCursor.execute(sql, (testSuiteRunNum,
                                               testSuiteNum,
                                               testSetNum,
                                               testCaseNum,
                                               testCaseStartTime,
                                               testCaseEndTime,
                                               testCaseResult,
                                               testCaseLogs)
                                         )

                        # If the test case exists in test_cases table, update the table (because test case info might have been updated).
                        # If not (i.e. first time test case was executed), insert into the table.
                        numRows = dbCursor.execute('SELECT * FROM test_cases WHERE test_suite_id = "{}" AND test_set_id = "{}" AND test_case_id = "{}"'.format(testSuiteNum, testSetNum, testCaseNum))
                        if numRows > 0:
                            dbCursor.execute("""UPDATE test_cases SET description = %s, method = %s, reference = %s
                                        WHERE test_suite_id = %s AND
                                            test_set_id = %s AND
                                            test_case_id = %s""", (
                                testCaseDesc, testCaseMethod, testCaseRef, testSuiteNum, testSetNum, testCaseNum))
                        else:
                            dbCursor.execute('INSERT INTO test_cases (test_suite_id, test_set_id, test_case_id, description, method, reference) '
                                             'VALUES (%s, %s, %s, %s, %s, %s)', (testSuiteNum, testSetNum, testCaseNum, testCaseDesc, testCaseMethod, testCaseRef))
                        # See if there is known info about this test case on this testbox in test_manager table
                        numRows = dbCursor.execute("""SELECT * FROM test_manager WHERE test_suite_id = %s
                                                        AND test_set_id = %s
                                                        AND    test_case_id = %s AND testbox = %s""",
                                                   (testSuiteNum, testSetNum, testCaseNum, TB_NUM)
                                                   )
                        if numRows > 0:
                            pass  # nothing to do. Don't need to update as we know that this test case is supposed to "Run"
                        else:
                            # this test is not known. Insert the info
                            dbCursor.execute("""INSERT INTO test_manager (testbox, test_suite_id, test_set_id, test_case_id)
                                                VALUES (%s, %s, %s, %s)""",
                                             (TB_NUM, testSuiteNum, testSetNum, testCaseNum)
                                             )
                line = file.readline()

        if not published:
            self.failed('ERROR: No device found to publish results for to the old DB, with device matching {}'.format(', '.join(map(str, deviceInfoTTYsList))))

        database.commit()
        database.close()
        # Log to capture db lockups
        log_if_delay("DB operation took longer than normal", timeStampBeforeDbOp, self.log, maxSecs= 120)

        return numTestCasesFailed, numTestCasesErrored, version


class TestCase_5(ATTestCase.TestCase):
    testCaseDesc    = 'Turn off all power sockets'
    testCaseRef     = ''
    testCaseMethod  = '\n'

    def main(self):
        self.passed("Turn off all power sockets used in this setup")
        power_off_threads = []
        for devName, dev in self.devDict.items():
            if 'ATSwitch.Switch' in str(dev.__class__):
                if dev.has_power():
                    self.log('Turning off %s' % (devName))
                    power_off_threads.append(ATTestSet.threading.Thread(target=dev.off, name='powerOff-%s' % dev.name))
                    power_off_threads[-1].start()
                else:
                    self.log('%s is not connected via managed power socket, leaving on' % (devName))
        self.testSet.wait_for_threads_join(power_off_threads)

################################################################################
# End of class definitions
################################################################################


if __name__ == '__main__':

    # Define the syntax
    parser = ArgumentParser(description='Execute ATPylib test suites')
    parser.add_argument('-a', '--archive', dest='archive', action='store_const', const=True, default=False, help='Download *gz files from all devices and archive those files.')
    parser.add_argument('-d', '--device', dest='deviceInfoTTYs', nargs=1, default=None, help='serial port or name of device(s) whose test result to be published. The default is None and will be resolved from %s.' % DEFAULT_CONFIG)
    parser.add_argument('-e', '--exclude', dest='excludeTestSetList', action='store_const', const=True, default=False, help='Exclude test sets specified with "-t" option')
    parser.add_argument('-k', '--keepguifiles', dest='keepGuiFiles', type=str2bool, default=None, help='False|True: Don\'t remove gui files from devices when archiving *gz files.')
    parser.add_argument('-l', '--licenses', dest='restoreLicenses', action='store_const', const=True, default=False, help='Restore feature licenses to \'ALL\' if any post run actions are performed')
    parser.add_argument('-n', '--norun', dest='norun', action='store_const', const=True, default=False, help='Don\'t actually execute the tests')
    parser.add_argument('-o', '--off', dest='powerOff', action='store_const', const=True, default=False, help='Turn off all power sockets at the end')
    parser.add_argument('-p', '--publish', dest='publish', action='store_const', const=True, default=False, help='Publish results to database')
    parser.add_argument('-q', '--quit', dest='quitOnFail', action='store_const', const=True, default=False, help='Quit from the test suite run as soon as a test case fails')
    parser.add_argument('-s', '--setup', dest='setup', nargs=1, default=None, help='Specify the physical setup file. The default is None and will load %s' % DEFAULT_SETUP)
    parser.add_argument('-u', '--unsupported', dest='runUnsupported', action='store_const', const=True, default=False, help='Executed test cases that are marked as unsupported')
    parser.add_argument('-v', '--verbose', dest='verbose', action='store_const', const=True, default=False, help='Print all log messages to STDOUT')
    parser.add_argument('-t', '--test-set-list', dest='testSetListFile', nargs=1, help='Test sets to include. To exclude, set "-e" option')
    args, unknown = parser.parse_known_args()
    programName = os.path.basename(__file__)

    archive = args.archive
    keepGuiFiles = args.keepGuiFiles
    deviceInfoTTYs = args.deviceInfoTTYs
    excludeTestSetList = args.excludeTestSetList
    noRun = args.norun
    powerOff = args.powerOff
    publish = args.publish
    quitOnFail = args.quitOnFail
    runUnsupported = args.runUnsupported
    verbose = args.verbose
    restoreLicenses = args.restoreLicenses

    if args.setup:
        if type(args.setup) is list:
            setup = args.setup[0]
        else:
            setup = args.setup
    else:
        setup = DEFAULT_SETUP

    if args.testSetListFile:
        if type(args.testSetListFile) is list:
            testSetListFile = args.testSetListFile[0]
        else:
            testSetListFile = args.testSetListFile
    else:
        testSetListFile = None

    # Create a blank log file.
    logFile = open(LOG_FILE_NAME, 'w')
    logFile.close()

    if verbose:
        VERBOSE = True

    log('If a setup file was specified, check whether it exists or not')
    if setup:
        if not os.path.exists(setup):
            log('Error: {} does not exist. {} terminates.' .format(setup, programName))
            sys.exit(2)
        else:
            log('Setup file {} exists'.format(setup))

    log('Ensure /usr/local/atlbin is in the PATH')
    # This is needed to make sure calls to ATL binaries in the test scripts actually execute (eg sendigmp)
    path = os.getenv("PATH")
    if path != None and path.find('/usr/local/atlbin') == -1:
        path = path + os.pathsep + "/usr/local/atlbin"
        os.environ['PATH'] = path

    log('Grab the Test Suite number from the current directory')
    # There are better ways of getting the test suite number
    # but this method was chosen to enforce strict naming of the test suite directories.
    pwd = os.getcwd()
    dirList = pwd.split('/')
    testSuiteName = dirList[-1]
    strList = testSuiteName.split('_')
    testSuiteNum = strList[0]
    log('Test Suite number is %s' % (testSuiteNum))

    testConfig = None
    if publish and not deviceInfoTTYs:
        if DEFAULT_CONFIG and os.path.exists(DEFAULT_CONFIG):
            log('No device option was specified, attempt to read it from the .cfg file')
            testConfig = Setup.LoadConfig(DEFAULT_CONFIG)
            try:
                deviceInfoTTYs = testConfig.get_test_option(testSuiteName, config_gen.ConfigParameters.device)
            except NoSectionError:
                log('Error: {} does not exist in .cfg file {}, terminate.' .format(testSuiteName, DEFAULT_CONFIG))
                sys.exit(2)
            else:
                deviceInfoTTYs = deviceInfoTTYs
        else:
            log('No device option was specified and no .cfg file found, default to 0')
            deviceInfoTTYs = '0'

    if archive and keepGuiFiles is None:
        defaultKeepGui = str2bool(config_gen.DEFAULT[config_gen.ConfigParameters.keep_gui_files])
        if DEFAULT_CONFIG and os.path.exists(DEFAULT_CONFIG):
            log('No keep gui files option was specified, attempt to read it from the .cfg file')
            if not testConfig:
                testConfig = Setup.LoadConfig(DEFAULT_CONFIG)
            try:
                keepGuiFiles = testConfig.get_test_option(testSuiteName, config_gen.ConfigParameters.keep_gui_files)
                if keepGuiFiles == '':
                    keepGuiFiles = defaultKeepGui
                log('keep gui files set to {}'.format(keepGuiFiles))
            except NoSectionError:
                log('Info: {} does not exist in .cfg file {}, default keep gui files to {}.' .format(testSuiteName, DEFAULT_CONFIG, defaultKeepGui))
                keepGuiFiles = defaultKeepGui
        else:
            log('Info: {} no .cfg file found, default keep gui files to {}.'.format(testSuiteName, defaultKeepGui))
            keepGuiFiles = defaultKeepGui

    defaultNoConf = str2bool(config_gen.DEFAULT[config_gen.ConfigParameters.noconf])
    noConf = defaultNoConf
    if DEFAULT_CONFIG and os.path.exists(DEFAULT_CONFIG):
        if not testConfig:
            testConfig = Setup.LoadConfig(DEFAULT_CONFIG)
        try:
            noConf = testConfig.get_test_option(testSuiteName, config_gen.ConfigParameters.noconf)
        except NoSectionError:
            noConf = defaultNoConf
        else:
            if noConf == '':
                noConf = defaultNoConf

    log('Get all Test Set scripts (test-x.y.py)')
    files = os.listdir('.')
    allTestSets = []
    for file in files:
        if file.find('test-') != -1 and file.endswith('.py'):
            allTestSets.append(file)
    allTestSets.sort()

    log('Exclude Test Sets if required')
    testSetList = []
    if testSetListFile:
        log("Test Set list file has been specified: {}".format(testSetListFile))
        try:
            testSetListFile = open(testSetListFile, 'r')
        except IOError:
            testSetList = allTestSets
        else:
            testSets = testSetListFile.readlines()
            testSets = [x.strip('\n').strip(' ') for x in testSets if x != '\n']  # remove the '\n' and ' ' at the end of mail address and newline
            for test in testSets:
                if ' ' in test:
                    testName = test[:test.find(' ')]  # only take the "test-xxx.xxx.py" bit
                else:
                    testName = test
                if testName in allTestSets:
                    testSetList.append(test)
            log("Test Sets in the list: %s" % str(testSetList))
    else:
        testSetList = allTestSets
    if excludeTestSetList:
        log("The exclude option has been specified")
        testSetList = list(set(allTestSets) - set(testSetList))

    testSetList.sort()
    log("List of Test Sets to be executed: %s" % str(testSetList))

    log('Execute each Test Set one by one')
    returnCode = ATTestSet.TestSet.RC_PASS
    if not noRun:
        testOptions = []
        if quitOnFail:
            testOptions.append('-q')
        if setup:
            testOptions.append('-s {}'.format(setup))
        if runUnsupported:
            testOptions.append('-u')
        if verbose:
            testOptions.append('-v')
        if noConf:
            testOptions.append('-n -p')

        testOptionsStr = ' '.join([str(x) for x in testOptions])
        unknownStr = ' '.join([str(x) for x in unknown])
        for test in testSetList:

            try:
                testLog = test.split()[0].replace('.py', '.log')
                parentDir = '/'.join(map(str, pwd.split("/")[0:-1]))
                symLink = f'{parentDir}/current_test.log'
                lnCmdStr = f'ln -sf {pwd}/{testLog} {symLink}'
                log(f'Creating symbolic link {symLink} linking to current Test Set log {pwd}/{testLog}')
                execute_sh_cmd(lnCmdStr, stdout=subprocess.PIPE, stderr=subprocess.PIPE, logFunc=log)
            except Exception:
                pass

            log('================ %s ================' % (test))
            log('%s BEGINS' % (test))
            (rc, stdout, stderr) = execute_sh_cmd('{}/{} {} {}'.format(os.getcwd(), test, testOptionsStr, unknownStr))
            log('%s STDOUT:\n%s' % (test, stdout))
            log('%s STDERR:\n%s' % (test, stderr))
            log('%s FINISHED (return code: %d)' % (test, rc))
            if rc > returnCode:
                # We return whatever the highest return code was out of all TestSets.
                # RC_PASS  = 0
                # RC_FAIL  = 1
                # RC_ERROR = 2
                # RC_STOP  = 3
                # e.g. the fact than RC_ERROR(s) occurred is more important than the fact that RC_FAIL(s) occurred.
                returnCode = rc
            if returnCode == ATTestSet.TestSet.RC_STOP:
                log('!!! quitOnFail flag is set and a TestCase failed. Stop all executions now !!!')
                break

    log('Use the framework itself to perform post Test Suite operations (if required)')
    # The Test Set created for this purpose will have testSetNum == 0
    testSet = PostRun()
    testSet.testSuiteNum = testSuiteNum
    testSet.testSuiteName = testSuiteName
    testSet.deviceInfoTTYs = deviceInfoTTYs
    testSet.create_log_file()

    if restoreLicenses:
        testSet.FEATURES = ['ALL']

    if archive and not quitOnFail:
        log('TestCase_1 added to download *gz files from all devices')
        tc = TestCase_1(conf=False, tear=False, confCheck=False)
        tc.keepGuiFiles = keepGuiFiles
        testSet.add_testCase(tc)
    if publish:
        log('TestCase_4 added to publish results into the DB')
        testSet.add_testCase(TestCase_4(conf=False, tear=False, confCheck=False))
        testSet.skip_log_file_renaming = True    # TestCase_4 and TestCase_40 will reset this
    if not noRun:
        log('TestCase_3 added to backup log files')
        testSet.add_testCase(TestCase_3(conf=False, tear=False, confCheck=False))
    if powerOff and not quitOnFail:
        log('TestCase_5 added to power off all switches (if connected to power sockets)')
        testSet.add_testCase(TestCase_5(conf=False, tear=False, confCheck=False))

    if len(testSet.testCaseList) > 0:
        testSetArgs = []
        if (not archive) or (quitOnFail) or (noConf):
            testSetArgs.append('-n')  # don't create default.cfg and reboot
            testSetArgs.append('-p')  # don't power cycle at the start
        if setup:
            testSetArgs.append('-s %s' % setup)

        try:
            testSet.run(testSetArgs)
        except SystemExit:
            # TestSet calls sys.exit() at the end.
            # This is OK for executing *normal* TestSets because we execute them
            # as shell scripts, but here we are calling testSet.run() directly,
            # which means the sys.exit() call in the TestSet will cause
            # runTestSuite.py to exit prematurely.
            pass
        except Exception as e:
            # We actually want to carry on anyway because it is important the email is
            # processed if it is configured
            returnCode = ATTestSet.TestSet.RC_ERROR

        if publish:
            try:
                tc = [tc for tc in testSet.testCaseList if str(tc.testCaseNum) == "4"][0]
            except Exception as e:
                tc = None
            if tc and not tc.hasBeenRun:
                returnCode = ATTestSet.TestSet.RC_ERROR
                errorTestSet = PostRun()
                errorTestSet.appendToLogFile = True
                errorTestSet.testSuiteNum = testSuiteNum
                errorTestSet.testSuiteName = testSuiteName
                errorTestSet.deviceInfoTTYs = deviceInfoTTYs
                errorTestSet.skipDeviceCommunication = True
                errorTestSet.create_log_file()
                errorTestSet.devDict = {}

                log('TestCase_0 added to log failure to communicate with the DUT')
                log('TestCase_40 added to force publishing results into the old DB')

                tcName = 'Log TestSuite PostRun failure for results publishing'
                tcMethod  = '# Log a failure result at the TestSet level\n'
                tc = ATTestSet.TestCase_0(tcName, tcMethod)
                tc.set_testSet(errorTestSet)
                tc.failures = 'failed to communicate with the DUT'
                messages = []
                messages.append('runTestSuite PostRun has been unable to communicate with the DUT,')
                messages.append('this is indicative of the DUT either failing to boot or failing to form a stack')
                messages.append('')
                tc.messages = messages
                errorTestSet.licenseStatusGood = True
                if not hasattr(errorTestSet, 'devDict'):
                    errorTestSet.devDict = {}
                errorTestSet.add_testCase(tc)
                errorTestSet.add_testCase(TestCase_40(conf=False, tear=False, confCheck=False, stackCheck=False))
                testSetArgs = []
                testSetArgs.append('--noconf')  # don't create default.cfg and reboot
                testSetArgs.append('--nopower')  # don't power cycle at the start
                testSetArgs.append('--noupdate')
                if setup:
                    testSetArgs.append('-s %s' % setup)
                try:
                    errorTestSet.run(testSetArgs)
                except Exception as e:
                    pass

    if setup:
        setup = Setup.LoadSetup(setup)
        mailDict = setup.get_all_email()
    elif testSet.setup:
        mailDict = testSet.setup.get_all_email()
    else:
        mailDict = None

    if mailDict:
        try:
            mailSubject = 'ATPyLib TestSuite {} has finished on testbox {}{} with return code {}'.format(testSet.testSuiteNum, testSet.tb.name, testSet.tb.num, returnCode)
        except:
            returnCode = ATTestSet.TestSet.RC_ERROR
            mailSubject = 'ATPyLib TestSuite {} has CRASHED on {} with return code {}'.format(testSuiteNum, socket.gethostname(), returnCode)
        for mailType, addresses in mailDict.items():
            if mailType == 'test_suite' or mailType not in ['test_set', 'failure', 'error', 'notification']:
                testSet.send_email(recipient=addresses, subject=mailSubject)
            elif mailType == 'failure' and returnCode != ATTestSet.TestSet.RC_PASS:
                testSet.send_email(recipient=addresses, subject=mailSubject)
            elif mailType == 'error' and returnCode >= ATTestSet.TestSet.RC_ERROR:
                testSet.send_email(recipient=addresses, subject=mailSubject)

    log('======== %s has completed with return code %d' % (programName, returnCode))
    sys.exit(returnCode)
