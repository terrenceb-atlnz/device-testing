#!/usr/bin/python
__author__ = 'Daniel Olynsma'

from validation_library import *
import argparse
import traceback

try:
    # noinspection PyUnresolvedReferences
    from framework.ATDrivers import ATSwitch
except ImportError:
    print('\n'.join(['Could not find the required framework directory',
                    'Please use the following command to get it.',
                    '[git clone ssh://git.atlnz.lc/data/git/systest/framework.git]']))


class StackReformError(Exception):
    def __init__(self, error_info_list):
        self.error_info_list = error_info_list

    def __str__(self):
        return repr(self.error_info_list)


def check_output_against_list_of_strings_remove_if_found(output_to_check, list_of_strings):
    copy_of_input_list = list(list_of_strings)
    for current_string in copy_of_input_list:
        if current_string in output_to_check:
            log('\tSaw [%s]' % current_string)
            list_of_strings.remove(current_string)
    return list_of_strings


# noinspection PyPep8Naming
def main():
    # Define variables/Constants
    list_of_available_backup_member_keys = stack_membership_dictionary = {}
    audit_inconsistency_count = log_message_count = 0

    SCRIPT_PASS = 0
    SCRIPT_FAIL = 1
    SCRIPT_ERROR = 2
    STACK_SYNC_TIME = 120
    # Raised from 300s: this stack netboots via TFTP from tb105, and a single unit was
    # measured at 5m44s to reach 'Configuration update completed' during the 0010 run.
    # 300s is shorter than one unit's boot, let alone 7 booting concurrently.
    MEMBER_REBOOT_TIMEOUT = STACK_REFORM_TIMEOUT = 900
    STACK_SYNC_TIMEOUT = 300
    STACK_MEMBERS_KEY_TEMPLATE = 'member-'
    STACK_REFORM_SUCCESSFUL_STRINGS = ['Configuration update completed for port']
    STACK_SEPARATION_STRINGS = ['High-availability failover has occurred', 'Waiting for coredump file sync', 'critical process failure']
    STACK_REFORM_ERROR_STRINGS = []
    STACK_REBOOT_SUCCESSFUL_STRINGS = ['network.configured', 'Configuration update completed']
    STACK_REBOOT_ERROR_STRINGS = ['Bootup', 'TFTP timeout. Retrying...']
    DEFAULT_SLEEP_TIME = 120

    exit_code = SCRIPT_PASS

    # Get the start time
    script_start_time = strftime('%Y-%m-%d_%H-%M')

    # Get commandline args and put into variables
    command_line_arguments = argparse.ArgumentParser()
    # Required arguments
    command_line_arguments.add_argument("reboots", help="The number of Backup-member reboots to do", type=int)
    command_line_arguments.add_argument("logDir", help="Directory where to store logs", type=str)
    command_line_arguments.add_argument("bms_to_reboot", help="list of BMs to reboot, separated by COMMA (e.g. 4,5,6)", type=str)
    command_line_arguments.add_argument("devices", help="Devices with consoles (ID, Console) e.g. 1,6 2,7", nargs='+')
    # Optional arguments
    command_line_arguments.add_argument('-b', '--binary', dest='binary_search', action='store_const', const=True, default=False,
                                        help='Set this flag when being used with binary search script')
    command_line_arguments.add_argument('-s', '--stop', dest='stop_on_message', action='store_const', const=True, default=False,
                                        help='Set this flag when you want the script to end if it finds the desired messages')
    command_line_arguments.add_argument('-a', '--audit', dest='stop_on_audit_inconsistency', action='store_const', const=True, default=False,
                                        help='Set this flag when you want the script to end if it finds the desired messages')
    command_line_arguments.add_argument('-c', '--check', dest="strings_to_check_for", type=str, nargs=1, default="",
                                        help="list of strings that you want to check for, separated by COMMA (e.g. err,warning)")
    command_line_arguments.add_argument('-v', '--verbose', dest='verbose', action='store_const', const=True, default=False,
                                        help='Set this flag when want the output of commands sent to the console')
    args = command_line_arguments.parse_args()

    # If the log directory does not have slash at the end.  Add one.  Else file will not be where expected.
    if not args.logDir.endswith('/'):
        args.logDir += '/'

    # If there are specified strings split them out into list elements
    if args.strings_to_check_for:
        log_strings_to_check_for = args.strings_to_check_for[0].split(',')
    else:
        log_strings_to_check_for = ['err', 'warn']

    # Sort out the info around backup-members to be rebooted
    list_backup_member_ids_to_reboot = args.bms_to_reboot.split(',')
    number_backup_members_to_reboot = len(list_backup_member_ids_to_reboot)

    # Create the list of config complete messages for the members that will be rebooted.
    list_of_member_rejoin_successful_strings = []
    for current_member_id in list_backup_member_ids_to_reboot:
        list_of_member_rejoin_successful_strings.append('%s%s' % (STACK_REFORM_SUCCESSFUL_STRINGS[0], current_member_id))

    # Setup and initialise the log file
    log_filename = '%sx950-member.log' % args.logDir
    initialise_log(log_filename)

    # Store the command line arguments that script was run with
    log_command_line_arguments(args)

    # Initialize ATSwitch objects for each of the members with consoles
    for strCurrentDevice in args.devices:
        # Split out the device ID and the console numbers from the first item
        current_device_list = strCurrentDevice.split(',')
        stack_membership_dictionary['%s%d' % (STACK_MEMBERS_KEY_TEMPLATE, int(current_device_list[0]))] = \
            ATSwitch.Switch(current_device_list[1], debug=args.verbose)   # TBv4: full path, not an int

    # noinspection PyBroadException
    try:
        list_of_stack_member_keys = sorted(stack_membership_dictionary.keys())
        stack_master_key, stack_master = set_stack_master(stack_membership_dictionary)
        stack_master.mappedName = None            # 'name' is a read-only property
        stack_master.setupName = get_host_name(stack_master)
        list_of_available_backup_member_keys = list(list_of_stack_member_keys)
        list_of_available_backup_member_keys.remove(stack_master_key)

        # Check that the Active-master is not in the list of members to be rebooted
        stack_master_id = stack_master_key.split(STACK_MEMBERS_KEY_TEMPLATE)[1]
        if stack_master_id in list_backup_member_ids_to_reboot:
            raise Exception('Stack Active-Master ID [%s] was in list of devices to be rebooted %s' %
                            (stack_master_id, list_backup_member_ids_to_reboot))

        # Set the per device log files before doing anything significant
        for stack_member_key in list_of_stack_member_keys:
            current_member_key = stack_membership_dictionary[stack_member_key]
            current_member_key.logFileName = current_member_key.console.logFileName = '%s_%s.log' % (stack_master.name, str(current_member_key.tty).rsplit('/', 1)[-1])   # tty is a path now, not an int

        # Format the actual reboot command string
        backup_members_reboot_command = ''
        for current_member_id in list_backup_member_ids_to_reboot:
            # canonical form, not the 'reboot stack' abbreviation used by this script's lineage
            backup_members_reboot_command = '%s%s' % (backup_members_reboot_command, 'reboot stack-member %s\ny\n' % current_member_id)

        # This reboot is for when using the binary search script
        if args.binary_search:
            stack_master_key, stack_master = reboot_stack_to_load_release(stack_master, stack_membership_dictionary, STACK_REBOOT_SUCCESSFUL_STRINGS,
                                                                          DEFAULT_SLEEP_TIME)

        # Get and store the device info in the test log file.
        stack_master.logFileName = log_filename
        log('---------------------------------------------------------------------')
        stack_master.get_sys_info()
        log('---------------------------------------------------------------------')
        stack_master.logFileName = stack_master.console.logFileName
        number_stack_members_at_start_of_test = len(stack_master.serialNum)
        log('Total number of stack members: %d' % number_stack_members_at_start_of_test)
        log('Backup-members to be rebooted: %s' % list_backup_member_ids_to_reboot)
        log('Total number of backup-members rebooting: %d' % number_backup_members_to_reboot)

        # Write the created reboot command to the log file
        write_formatted_error_messages_to_log(['Reboot command:', backup_members_reboot_command])

        remove_console_paging_and_timeout(stack_master, write_changes=True)

        log('Clear exception log and store its baseline output')
        stack_master.cmd('clear exception log')
        baseline_exception_log = stack_master.cmd('show exception log')

        for reboot_loop_counter in range(1, (args.reboots + 1)):
            # Make a copy of the config complete messages for use in this iteration of the loop
            current_list_of_rejoin_successful_strings = list(list_of_member_rejoin_successful_strings)

            log('---------------------------------------------------------------------')
            log('-------- Backup-members reboot #%d' % reboot_loop_counter)
            # Clear consoles
            log("Purging the asyn ports of stack")
            for current_member_key in list_of_stack_member_keys:
                log("\tPurging the asyn of [%s]" % current_member_key)
                stack_membership_dictionary[current_member_key].send('', 2)
            # Setup monitoring of all defined Backup-member consoles
            log('Monitor %s for:' % list_of_available_backup_member_keys)
            for current_message_list in (STACK_REBOOT_SUCCESSFUL_STRINGS, STACK_REBOOT_ERROR_STRINGS):
                log('\t%s' % current_message_list)
            log('Begin monitoring')
            for current_member_key in list_of_available_backup_member_keys:
                stack_membership_dictionary[current_member_key].read(STACK_REFORM_TIMEOUT,
                                                                     STACK_REBOOT_SUCCESSFUL_STRINGS + STACK_REBOOT_ERROR_STRINGS)
                log('\t[%s] started' % current_member_key)

            # Reboot the backup-members
            stack_master.cmd('clear log')
            start_of_reboot_time = time()
            reboot_time_timeout = start_of_reboot_time + STACK_REFORM_TIMEOUT
            log('Reboot backup-members - Read Active-master console for [%d] or until see:' % MEMBER_REBOOT_TIMEOUT)
            for current_message_list in (current_list_of_rejoin_successful_strings, STACK_REFORM_ERROR_STRINGS):
                if len(current_message_list) > 0:
                    for current_message in current_message_list:
                        log('\t%s' % current_message)
            reboot_output = stack_master.send(backup_members_reboot_command, waitTime=MEMBER_REBOOT_TIMEOUT,
                                              strList=current_list_of_rejoin_successful_strings + STACK_REFORM_ERROR_STRINGS)
            log('Checking Active-master console output for any defined error strings')
            for current_error in STACK_REFORM_ERROR_STRINGS:
                if current_error in reboot_output:
                    log('\tString [%s] found' % current_error)
                    raise StackReformError(["Errors seen during Backup-members' reboot", 'Active-Master Console output:', reboot_output])
                    #write_formatted_error_messages_to_log(['Active-Master Console output:', reboot_output])

            log('Checking Master for member connection messages')
            # Check that at least one of the wanted strings were found
            current_list_of_rejoin_successful_strings = \
                check_output_against_list_of_strings_remove_if_found(reboot_output, current_list_of_rejoin_successful_strings)
            # Check which members have rejoined.
            if len(current_list_of_rejoin_successful_strings) > 0:
                log('Reading Active-master console for more connection messages')
                while current_list_of_rejoin_successful_strings and (time() < reboot_time_timeout):
                    current_read_thread = stack_master.read(10, current_list_of_rejoin_successful_strings)
                    while not current_read_thread.has_finished():
                        sleep(1)
                    # put the preReadBuf and that read.buffer at the end of the reboot output.
                    reboot_output += '%s%s' % (stack_master.console.preReadBuf, stack_master.console.buffer)
                    # Check the list of strings against the reboot output
                    current_list_of_rejoin_successful_strings = \
                        check_output_against_list_of_strings_remove_if_found(reboot_output, current_list_of_rejoin_successful_strings)
                # If not all seen.  Check the show log as sometimes messages are dropped from the console
                if current_list_of_rejoin_successful_strings:
                    log('Checking log just in case message was dropped from console')
                    # Check the list of strings against the command output
                    current_list_of_rejoin_successful_strings = \
                        check_output_against_list_of_strings_remove_if_found(stack_master.cmd('show log | grep "Configuration update completed for"'),
                                                                             current_list_of_rejoin_successful_strings)
            if not current_list_of_rejoin_successful_strings:
                log('All expected backup-member rejoin messages seen')
            else:
                raise StackReformError(['ERROR: Not all Backup-members rejoined stack', 'Active-Master Console output:', reboot_output])

            log('Check for stack separation messages')
            log('\t%s' % STACK_SEPARATION_STRINGS)
            if any(current_string in reboot_output for current_string in STACK_SEPARATION_STRINGS):
                raise StackReformError(['ERROR: Stack has separated', 'Active-Master Console output:', reboot_output])

            # Put delay here so that system can sort itself out
            stack_settle_end_time = time() + DEFAULT_SLEEP_TIME
            read_thread = None

            while time() < stack_settle_end_time:
                if read_thread:
                    log('\tRead() looks like it got tripped over previous read().  Trying again.')
                    read_time = stack_settle_end_time - time()
                else:
                    read_time = DEFAULT_SLEEP_TIME
                log('Read Active-master console for %d seconds' % read_time)
                read_thread = stack_master.read(read_time, STACK_SEPARATION_STRINGS)
                while not read_thread.has_finished():
                    sleep(1)
                # put the preReadBuf and that read.buffer at the end of the reboot output.
                reboot_output += '%s%s' % (stack_master.console.preReadBuf, stack_master.console.buffer)
                if read_thread.is_keyword_found():
                    raise StackReformError(['ERROR: Stack has separated', 'Active-Master Console output:', reboot_output])

            log('\tRead() completed without seeing any stack separation messages')
            log('Login to the Active-master')
            stack_master.mode('#')
            # Check exception log.  Pretty sure should see nothing
            log('Checking exception log')
            mismatch, exception_log_response = compare_command_outputs(stack_master, 'show exception log', baseline_exception_log)
            if mismatch:
                raise StackReformError(['ERROR: Exception logs did not match', 'Active-Master Console output:', reboot_output,
                                        'Show exception log (Differences)', diff_multiline_strings(baseline_exception_log, exception_log_response)])

            # Check if the stack is ready.
            if not check_all_stack_members_ready(stack_master, number_stack_members_at_start_of_test,
                                                 time() + (STACK_SYNC_TIMEOUT - DEFAULT_SLEEP_TIME - STACK_SYNC_TIME)):
                raise StackReformError(['ERROR: Stack is not READY', 'Active-Master Console output:', reboot_output])

            # Check logs for messages
            if check_logs_for_errors_warnings_or_user_messages(stack_master, log_strings_to_check_for) > 0:
                log_message_count += 1
            # Check for audit inconsistencies
            if check_for_stack_audit_inconsistencies(stack_master, number_stack_members_at_start_of_test) > 0:
                audit_inconsistency_count += 1

            log('==== Loop counters are (Log messages: %d\tInconsistencies: %d\tLoops done: %d)' %
                (log_message_count, audit_inconsistency_count, reboot_loop_counter))

            # Exit loop if messages found and cli arg '-s' passed in or if audit inconsistencies nad cli arg 'a'.
            if (args.stop_on_message and log_message_count > 0) or (args.stop_on_audit_inconsistency and audit_inconsistency_count > 0):
                break
    except StackReformError as e:
        write_formatted_error_messages_to_log(e.error_info_list)
        exit_code = SCRIPT_FAIL
    except KeyboardInterrupt:
        log('################  Saw Keyboard Interrupt  ################')
    except:
        log('################  Internal issue  ################')
        log(traceback.format_exc())
        exit_code = SCRIPT_ERROR
    else:
        if log_message_count or audit_inconsistency_count:
            exit_code = SCRIPT_FAIL
        else:
            log('NO ISSUES SEEN')
    finally:
        # Stop any read thread that was running before exiting with the correct code.
        log('Stop any read() that are running on Backup-members')
        for current_member_key in list_of_available_backup_member_keys:
            if stack_membership_dictionary[current_member_key].console.readThread:
                if not stack_membership_dictionary[current_member_key].console.readThread.has_finished():
                    log('\t%s' % current_member_key)
                    stack_membership_dictionary[current_member_key].console.readThread.stop()
        log('################  Script Completed  ################')
        return exit_code


if __name__ == "__main__":
    # the return value from main is used as the argument to
    # sys.exit, which you can test for in the shell.
    # program exit codes are usually 0 for ok, and non-zero for something
    # going wrong.
    sys.exit(main())
