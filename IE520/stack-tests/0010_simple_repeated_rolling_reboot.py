#!/usr/bin/python
__author__ = 'Daniel Olynsma'
__lastModifier__ = 'Daniel Olynsma'

import argparse
import sys
from time import sleep, strftime, time

try:
    # noinspection PyUnresolvedReferences
    from framework.ATDrivers import ATSwitch
except ImportError:
    print('Could not find the required framework directory')
    print('Please use the following command to get it.')
    print('[git clone ssh://git.atlnz.lc/data/git/systest/framework.git]')
    sys.exit()


def get_host_name(switch):
    switch.mode('#')
    return switch.cmd('').lstrip().rstrip('#')


def log(string):
    current_time = strftime('%Y-%m-%d %H:%M:%S')
    log_file = open(logFilename, 'a')
    log_file.write(current_time + ': ' + string + '\n')
    log_file.close()
    print(string)


def write_formatted_error_messages_to_log(list_of_strings):
    log('%s\n--------' % '\n--------\n'.join(list_of_strings))


def check_logs_for_errors_warnings_or_user_messages(switch_object, log_strings_to_check_for):
    current_message_count = 0
    for current_log in ('show log', 'show log permanent'):
        for currentSearchString in log_strings_to_check_for:
            log_command = '%s | include "%s"' % (current_log, currentSearchString)
            cmd_response = switch_object.cmd(log_command)
            if (cmd_response.count(currentSearchString) - cmd_response.count(log_command)) >= 1:
                write_formatted_error_messages_to_log(['[%s] contained [%s] messages' % (current_log, currentSearchString), cmd_response])
                current_message_count += 1
            else:
                log('[%s] contained NO [%s] messages' % (current_log, currentSearchString))
                #write_formatted_error_messages_to_log(['[%s] contained NO [%s] messages' % (currentLog, currentSearchString),
                #                                       response])
    return current_message_count


def check_for_stack_audit_inconsistencies(switch_object, number_of_stack_members):
    current_audit_inconsistency_count = 0
    for consistency_cmd in ('remote-diff all show interface brief', 'remote-diff all show hsl infrastructure'):
        found_audit_inconsistencies = False
        consistency_cmd_response = switch_object.cmd(consistency_cmd)
        if consistency_cmd_response.count('Results are identical') != (number_of_stack_members - 1):
            # Only do these checks if is the 'show hsl infrastructure' command
            if 'show hsl infrastructure' in consistency_cmd:
                for currentLine in consistency_cmd_response.splitlines():
                    if currentLine.startswith('+') and not currentLine.startswith('+Unit'):
                        found_audit_inconsistencies = True
                        break
            else:
                found_audit_inconsistencies = True
        # If the remote-diff command found actual inconsistencies then up the loop counter
        if found_audit_inconsistencies:
            list_of_strings_for_error_log = ['[%s] contained inconsistencies' % consistency_cmd, consistency_cmd_response]
            # Only do something if able to get to the start-shell and only do it once
            if current_audit_inconsistency_count == 0:
                list_of_strings_for_error_log.append(get_contents_of_file_and_any_rotated_versions(switch_object, '/var/log/trace'))
            write_formatted_error_messages_to_log(list_of_strings_for_error_log)
            current_audit_inconsistency_count += 1
        else:
            log('[%s] contained NO inconsistencies' % consistency_cmd)
    return current_audit_inconsistency_count


def reboot_stack_to_load_release(switch_object, stack_reboot_successful_strings, sleep_time):
    reboot_was_good = False
    log('Doing reboot to load release set by binary search script')
    output_from_reboot = switch_object.reboot()
    for current_list_item in stack_reboot_successful_strings:
        if output_from_reboot.find(current_list_item) > -1:
            reboot_was_good = True
            log('Reboot successful.  Saw [%s] string in reboot output' % current_list_item)
            break
    if not reboot_was_good:
        log('################  INITIAL/SETUP REBOOT FAILED  ################\n-----\n%s\n-----' % output_from_reboot)
        raise Exception
    else:
        log('Sleep for %d seconds' % sleep_time)
        sleep(sleep_time)


def check_all_stack_members_ready(switch_object, size_of_stack, timeout_time):
    log('Check output of [show stack] to see if all members are [ready]')
    while True:
        number_of_members_ready = switch_object.cmd('show stack').count('Ready')
        # If the number of lines containing ready match the size of the member keys.  then this is okay
        if number_of_members_ready == size_of_stack:
            log('\tStack is ready')
            return True
        elif time() >= timeout_time:
            log('\tStack was NOT ready within timeout period')
            return False
        else:
            sleep(10)


def get_contents_of_file_and_any_rotated_versions(switch_object, filename_interested_in):
    """
    Get the directory listing of trace* files.
    Cat each present file
    [root@x610-6stk /flash]# ls -lrt /var/log/trace*
    -rw-r--r--    1 root     root         10408 Apr  7 14:18 /var/log/trace.1
    -rw-r--r--    1 root     root           955 Apr  7 14:18 /var/log/trace
    [root@x610-6stk /flash]
    """
    complete_log_information = ''
    if switch_object.mode(']#'):
        cmd_response_line_list = switch_object.cmd('ls -lrt --color=never %s*' % filename_interested_in).splitlines()[1:-1]
        # split out the relevant column from each line and then work through the list
        for current_line in cmd_response_line_list:
            current_log_filename = current_line.split()[8].strip()
            complete_log_information += switch_object.cmd('cat %s' % current_log_filename, maxWait=15)
        switch_object.mode('#')
    else:
        complete_log_information = 'NO INFO: Was not able to get to start-shell'
    return complete_log_information


def log_command_line_arguments(arguments_object):
    # Log the commandline and options
    dictionary_of_arguments = vars(arguments_object)
    padding = len(max(dictionary_of_arguments.keys(), key=len)) + 5
    cli_program_and_arguments = '\n'.join(['%s%s' % (('%s:' % key).ljust(padding), value) for key, value in dictionary_of_arguments.items()])
    write_formatted_error_messages_to_log(['PROGRAM ARGUMENTS', cli_program_and_arguments, ' '.join(sys.argv)])


# Get commandline args and put into variables
commandLineArgumentParser = argparse.ArgumentParser()
commandLineArgumentParser.add_argument('-b', '--binary', dest='binarySearch', action='store_const', const=True, default=False,
                                       help='Set this flag when being used with binary search script')
commandLineArgumentParser.add_argument('-s', '--stop', dest='stopOnMessage', action='store_const', const=True, default=False,
                                       help='Set this flag when you want the script to end if it finds the desired messages')
commandLineArgumentParser.add_argument("device", help="Serial device: TBv4 full path (e.g. /dev/u5) or TBv3 port number", type=str)
commandLineArgumentParser.add_argument("reboots", help="The number of reboots to do", type=int)
commandLineArgumentParser.add_argument("logDir", help="Directory where to store logs", type=str)
commandLineArgumentParser.add_argument("stringsToCheckFor", nargs='?',
                                       help="list of strings that you want to check for, separated by COMMA (e.g. err,warning)", default="")
commandLineArgumentParser.add_argument('-v', '--verbose', dest='verbose', action='store_const', const=True, default=False,
                                       help='Set this flag when want the output of commands sent to the console')
args = commandLineArgumentParser.parse_args()

# Define variables/Constants
SCRIPT_PASS = 0
SCRIPT_FAIL = 1
SCRIPT_ERROR = 2
STACK_SYNC_TIME = 120
STACK_SYNC_TIMEOUT = 300
ROLLING_REBOOT_ERROR_MESSAGES = ['Bootup', 'stack has not reformed after a rolling reboot', 'TFTP timeout. Retrying...']
ROLLING_REBOOT_SUCCESS_MESSAGES = ['Configuration update completed for']
STACK_REBOOT_SUCCESSFUL_STRINGS = ['network.configured', 'Configuration update completed']
ROLLING_REBOOT_TIMEOUT = 600
DEFAULT_SLEEP_TIME = 120

# If there are specified strings split them out into list elements
if args.stringsToCheckFor:
    stringsToCheckFor = args.stringsToCheckFor.split(',')
else:
    stringsToCheckFor = ['err', 'warn']

# If the log directory does not have slash at the end.  Add one.  Else file will not be where expected.
if not args.logDir.endswith('/'):
    args.logDir += '/'

# Initialise the Switch Class
dut = ATSwitch.Switch(args.device, debug=args.verbose)
dut.mappedName = None            # framework 'name' is a read-only property derived from
dut.setupName = get_host_name(dut)  # setupName/mappedName; assign the underlying attribute
dut.logFileName = dut.console.logFileName = '%s.log' % dut.name
# Setup the script log filename
logFilename = '%sx950-member.log' % args.logDir

# Store the command line arguments that script was run with
log_command_line_arguments(args)

# This reboot is for when using the binary search script
if args.binarySearch:
    reboot_stack_to_load_release(dut, STACK_REBOOT_SUCCESSFUL_STRINGS, DEFAULT_SLEEP_TIME)

# Get and store the device info in the test log file.
dut.logFileName = logFilename
log('---------------------------------------------------------------------')
dut.get_sys_info()
log('---------------------------------------------------------------------')
dut.logFileName = dut.console.logFileName

# Make sure that the console exec timeout and length have been removed.
# Else script will hit errors during main loop
if 'line con 0\r\n exec-timeout 0 0\r\n length 0' not in dut.cmd('show run'):
    dut.mode(')#')
    dut.cmd('line console 0')
    dut.cmd('length 0')
    dut.cmd('exec-timeout 0')
    dut.cmd('end')
    dut.cmd('wr')
    dut.cmd('exit')
    # Log back in
    dut.mode('#')

# Main loop.
# The program executes until killed/stopped externally.
# Log file is updated each iteration so that data is not lost when this program is killed.
try:
    auditInconsistencyCount = messageCount = 0

    log('Clear exception log and store its baseline output')
    dut.cmd('clear exception log')
    baseline_exception_log = dut.cmd('show exception log')
    length_of_baseline_exception_log = len(baseline_exception_log)

    for currentCount in range(1, args.reboots + 1):
        currentAuditInconsistencyCount = currentMessageCount = 0
        rebootIsGood = False
        workingListOfRebootErrorMessages = list(ROLLING_REBOOT_ERROR_MESSAGES)
        log('-------- Rolling Reboot (%d/%d) --------' % (currentCount, args.reboots))
        # Clear log before beginning loop
        dut.cmd('clear log')
        log('Issuing the command [reboot rolling]')
        dut.send('reboot rolling\n')
        log('Waiting for [reboot rolling] to see following strings or timeout [%d]' % ROLLING_REBOOT_TIMEOUT)
        for currentMessageList in (ROLLING_REBOOT_SUCCESS_MESSAGES, ROLLING_REBOOT_ERROR_MESSAGES):
            log('\t%s' % currentMessageList)
        rebootOutput = dut.send('y\r\n', waitTime=ROLLING_REBOOT_TIMEOUT, strList=ROLLING_REBOOT_SUCCESS_MESSAGES + ROLLING_REBOOT_ERROR_MESSAGES)
        log('Checking console output for any defined error strings')
        while workingListOfRebootErrorMessages:
            currentErrorString = workingListOfRebootErrorMessages.pop(0)
            if rebootOutput.find(currentErrorString) > -1:
                log('\tString [%s] found' % currentErrorString)
                break
        if len(workingListOfRebootErrorMessages) == 0:
            log('\tNo Errors seen')
            # Check that at least one of the wanted strings were found
            for currentCheckString in ROLLING_REBOOT_SUCCESS_MESSAGES:
                if rebootOutput.find(currentCheckString) > -1:
                    log('Saw [%s] string in rolling reboot output' % currentCheckString)
                    rebootIsGood = True
                    break
        if rebootIsGood:
            log('Rolling Reboot SUCCESSFUL.')
            # Put delay here so that system can sort itself out
            log('Sleep for %d seconds' % DEFAULT_SLEEP_TIME)
            sleep(DEFAULT_SLEEP_TIME)
            log('Login to the Active-master')
            dut.mode('#')
            # Capture console output since end of rolling reboot
            rebootOutput = '%s%s' % (rebootOutput, dut.console.preModeBuf)

            log('Checking exception log')
            exception_log_response = dut.cmd('show exception log')
            if len(exception_log_response) > length_of_baseline_exception_log:
                write_formatted_error_messages_to_log(['ERROR: Exception logs did not match',
                                                       'Active-Master Console output:', rebootOutput, 'Show exception log', exception_log_response])
                raise Exception

            # Check if the stack is ready.
            is_stack_ready = check_all_stack_members_ready(dut, len(dut.serialNum),
                                                           time() + (STACK_SYNC_TIMEOUT - DEFAULT_SLEEP_TIME - STACK_SYNC_TIME))

            # Check logs for messages
            if check_logs_for_errors_warnings_or_user_messages(dut, stringsToCheckFor) > 0:
                messageCount += 1
            # Check for audit inconsistencies
            if check_for_stack_audit_inconsistencies(dut, len(dut.serialNum)) > 0:
                auditInconsistencyCount += 1
        else:
            write_formatted_error_messages_to_log(['Rolling Reboot FAILED', rebootOutput])
            raise Exception
        log('==== Loop counters are (Log messages: %d\tInconsistencies: %d\tLoops done: %d)' % (messageCount, auditInconsistencyCount, currentCount))
        # If the stack is not ready.  Then go no further
        if not is_stack_ready:
            log('ERROR: Stack is not ready, so can not continue.')
            raise Exception
        # Exit loop if messages found and cli arg '-s' passed in.
        if args.stopOnMessage and (messageCount > 0 or auditInconsistencyCount > 0):
            break
except KeyboardInterrupt:
    log('################  Saw Keyboard Interrupt  ################')
except:
    log('################  Internal issue  ################')
    sys.exit(SCRIPT_ERROR)
else:
    log('################  Script Completed  ################')
    if messageCount == 0:
        log('NO ISSUES SEEN')
        sys.exit(SCRIPT_PASS)
    else:
        sys.exit(SCRIPT_FAIL)
