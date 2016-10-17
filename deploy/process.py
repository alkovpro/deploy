#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
from daemon import Daemon
from common import *
import config
import time
import subprocess


class CommandProcessor:
    no_err_file = False

    def __init__(self):
        self.file_std = open(config.LOG_FILE, 'w+t')  # ''a+' if os.path.exists(config.LOG_FILE) else 'w+')
        self.file_std.truncate()

        if not config.ERR_FILE:
            self.no_err_file = True
        else:
            self.file_err = open(config.ERR_FILE, 'w+t')  # 'a+' if os.path.exists(config.ERR_FILE) else 'w+')
            self.file_err.truncate()

        write(config.TIME_FILE, [time.ctime()], True)

        for cmd_part, cmd_list in sorted(config.COMMANDS.items()):
            self.file_std.writelines(['\n==[%s]==\n' % cmd_part])
            if not self.no_err_file:
                self.file_err.writelines(['\n==[%s]==\n' % cmd_part])
            self.do_sequence(cmd_list)

        self.file_std.close()
        if not self.no_err_file:
            self.file_err.close()

    def do_sequence(self, cmd_list):
        stdout, stderr = '', ''
        success = True
        returncode = 0
        for cmd_key in sorted(cmd_list.keys()):
            command = cmd_list[cmd_key]
            function = self.cmd_none
            cmd_name = ''
            cmd_text = ''
            if 'cd' in command:
                function = self.cmd_cd
                cmd_name = 'cd'
                cmd_text = command['cd']
            if 'cmd' in command:
                function = self.cmd_cmd
                cmd_name = 'cmd'
                cmd_text = command['cmd']
            if 'if' in command:
                function = self.cmd_if
                cmd_name = 'if'
                cmd_text = command['if']

            self.file_std.writelines(['\n--[%s: %s]--\n' % (cmd_name, cmd_text)])
            if not self.no_err_file:
                self.file_err.writelines(['\n--[%s: %s]--\n' % (cmd_name, cmd_text)])

            stdout, stderr, success, returncode = function(cmd_text, command, {'stdout': stdout,
                                                                               'stderr': stderr,
                                                                               'success': success,
                                                                               'returncode': returncode})

            if type(stdout) is bytes:
                stdout = stdout.decode()
            else:
                stdout = str(stdout)
            if type(stderr) is bytes:
                stderr = stderr.decode()
            else:
                stderr = str(stderr)

            self.file_std.write(stdout)
            if self.no_err_file:
                if stderr:
                    self.file_std.write('<span style="color:red">\n')
                    self.file_std.write(stderr)
                    self.file_std.write('</span>\n')
            else:
                self.file_err.write(stderr)

            tmp = '<span style="color:{color}">[returncode: {code}]</span>\n'.format(
                color='green' if returncode == 0 else 'red',
                code=returncode)

            self.file_std.write(tmp)
            if not self.no_err_file:
                self.file_err.write(tmp)

    def cmd_none(self, cmd='', params=None, extra=None):
        return '', '', True, 0

    def cmd_cd(self, cmd='', params=None, extra=None):
        try:
            os.chdir(cmd)
            success = True
        except:
            success = False
        return '', '', success, 0 if success else -1

    def cmd_cmd(self, cmd='', params=None, extra=None):
        stdout = ''
        stderr = ''
        success = False
        returncode = -1
        try:
            if 'user' in params:
                cmd = "su --command '%s' %s" % (cmd, params['user'])
            p = subprocess.Popen(cmd, shell=True,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout = p.stdout.read()
            stderr = p.stderr.read()
            success = True
            returncode = p.wait()
        except:
            pass
        return stdout, stderr, success, returncode

    def cmd_if(self, cmd='', params=None, extra=None):
        if extra is None:
            extra = {}
        try:
            res = eval(cmd, {}, extra)
            success = True
        except:
            res = False
            success = False
        if success:
            if res:
                self.do_sequence(params.get('then', {}))
            else:
                self.do_sequence(params.get('else', {}))
        return '', '', success, 0 if success else -1


class DeployProcess(Daemon):
    def clear_triggers(self):
        delete(config.PROCESS)
        delete(config.QUEUE)
        delete(config.TRIGGER)
        delete(config.WAIT)

    def start(self):
        self.clear_triggers()
        touch(config.WAIT)
        super(DeployProcess, self).start()

    def stop(self, exit_on_error=True):
        super(DeployProcess, self).stop(exit_on_error)
        self.clear_triggers()

    def run(self):
        while True:
            if rename(config.TRIGGER, config.PROCESS):

                # write(config.LOG_FILE, "\n%s - start process\n" % time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))

                cmd_run = CommandProcessor()
                cmd_run = None

                # write(config.LOG_FILE, "%s - end process\n" % time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))

                if not rename(config.PROCESS, config.WAIT):
                    rename(config.QUEUE, config.TRIGGER)

            time.sleep(10)


if __name__ == "__main__":
    daemon = DeployProcess(config.PIDFILE, None, '/dev/null', config.STD_FILE)
    if len(sys.argv) == 2:
        if 'start' == sys.argv[1]:
            daemon.start()
        elif 'stop' == sys.argv[1]:
            daemon.stop()
        elif 'restart' == sys.argv[1]:
            daemon.restart()
        else:
            print("Unknown command")
            sys.exit(2)
        sys.exit(0)
    else:
        print("usage: %s start|stop|restart" % sys.argv[0])
        sys.exit(2)
