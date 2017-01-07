#!/bin/env python3
import sys
import argparse

from daemonize import Daemonize

from pueue.helper.files import cleanup
from pueue.daemon.daemon import Daemon
from pueue.client.factories import print_command_factory
from pueue.client.displaying import (
    execute_status,
    execute_log,
    execute_show,
)
from pueue.client.manipulation import (
    execute_add,
    execute_remove,
    execute_restart,
    execute_pause,
    execute_stop,
    execute_kill,
    execute_switch,
    execute_send,
)


def main():
    # Specifying commands
    parser = argparse.ArgumentParser(description='Pueue client/daemon')
    parser.add_argument('--daemon', action='store_true', help='Starts the pueue daemon')
    parser.add_argument(
        '--no-daemon', action='store_true',
        help='Starts the pueue daemon in the current terminal', dest='nodaemon'
    )
    parser.add_argument(
        '--stop-daemon', action='store_true',
        help='Daemon will shut down instantly. All running processes die', dest='stopdaemon')

    parser.add_argument(
        '--root', type=str,
        help='The root directory for configs and logs. Used for testing')

    # Initialze supbparser
    subparsers = parser.add_subparsers(
        title='Subcommands', description='Various client')

    # Add
    add_Subcommand = subparsers.add_parser(
        'add', help='Adds a command to the queue')
    add_Subcommand.add_argument(
        'command', type=str, help='The command to be added')
    add_Subcommand.set_defaults(func=execute_add)

    # Remove
    remove_Subcommand = subparsers.add_parser(
        'remove', help='Removes a specific command from the queue')
    remove_Subcommand.add_argument(
        'key', help='The index of the command to be deleted', type=int)
    remove_Subcommand.set_defaults(func=execute_remove)

    # Switch
    switch_Subcommand = subparsers.add_parser(
        'switch', help='Switches two command in the queue')
    switch_Subcommand.add_argument('first', help='The first command', type=int)
    switch_Subcommand.add_argument('second', help='The second command', type=int)
    switch_Subcommand.set_defaults(func=execute_switch)

    # Send
    switch_Subcommand = subparsers.add_parser(
        'send', help='Send any input to the current running process.')
    switch_Subcommand.add_argument('input', help='The input string', type=str)
    switch_Subcommand.set_defaults(func=execute_send)

    # Status
    status_Subcommand = subparsers.add_parser(
        'status', help='Lists all commands in the queue, '
        'daemon state and state/returncode of the current/last process'
    )
    status_Subcommand.set_defaults(func=execute_status)

    # Show
    show_Subcommand = subparsers.add_parser('show', help='Shows the output of the currently running process')
    show_Subcommand.add_argument(
        '-w', '--watch', action='store_true',
        help='Starts the pueue daemon in the current terminal'
    )
    show_Subcommand.set_defaults(func=execute_show)

    # Logs
    logs_Subcommand = subparsers.add_parser(
        'log', help='Prints the current log file to the command line')
    logs_Subcommand.set_defaults(func=execute_log)

    # Reset
    reset_Subcommand = subparsers.add_parser(
        'reset', help='Daemon will kill the current command, reset queue and rotate logs.')
    reset_Subcommand.set_defaults(func=print_command_factory('reset'))

    # Pause
    pause_Subcommand = subparsers.add_parser(
        'pause', help='Daemon will pause the current process and stops processing the queue.')
    pause_Subcommand.add_argument(
        '-w', '--wait', action='store_true',
        help='Stops the daemon, but waits for the current process to finish.'
    )
    pause_Subcommand.set_defaults(func=execute_pause)

    # Start
    start_Subcommand = subparsers.add_parser(
        'start', help='Daemon will start a paused process and continue processing the queue.')
    start_Subcommand.set_defaults(func=print_command_factory('start'))

    # Restart
    restart_Subcommand = subparsers.add_parser(
        'restart', help='Daemon will enqueue a finished process.')
    restart_Subcommand.add_argument(
        'key', help='The index of the command to be restart', type=int)
    restart_Subcommand.set_defaults(func=execute_restart)

    # Kills the current running process and starts the next
    kill_Subcommand = subparsers.add_parser(
        'kill', help='Kills the current running process and starts the next one')
    kill_Subcommand.add_argument(
        '-r', '--remove', action='store_true',
        help='If this flag is set, the current entry will be removed from the queue.'
    )
    kill_Subcommand.set_defaults(func=execute_kill)

    # Terminate the current running process and starts the next
    stop_Subcommand = subparsers.add_parser(
        'stop', help='Daemon will stop the current command and pauses afterwards.')
    stop_Subcommand.add_argument(
        '-r', '--remove', action='store_true',
        help='If this flag is set, the current entry will be removed from the queue.'
    )
    stop_Subcommand.set_defaults(func=execute_stop)

    args = parser.parse_args()

    # Create a closure to get the proper arguments
    def daemon_factory(args):
        args_dict = vars(args)
        path = None
        if 'root' in args:
            path = args_dict['root']

        def start_daemon():
            print(path)
            daemon = Daemon(root_dir=path)
            try:
                daemon.main()
            except KeyboardInterrupt:
                print('Keyboard interrupt. Shutting down')
                cleanup(daemon.config_dir)
                sys.exit(0)
                return daemon
            except:
                if not path:
                    path = os.path.expanduser('~')
                cleanup(path)
        return start_daemon

    if args.stopdaemon:
        print_command_factory('STOPDAEMON')(vars(args))
    elif args.nodaemon:
        daemon_factory(args)()
    elif args.daemon:
        daemon = Daemonize(app='pueue', pid='/tmp/pueue.pid', action=daemon_factory(args))
        daemon.start()
    elif hasattr(args, 'func'):
        try:
            args.func(vars(args))
        except EOFError:
            print('Apparently the daemon just died. Sorry for that :/.')
    else:
        print('Invalid Command. Please check -h')
