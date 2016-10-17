"""
Daemonizing tools.
"""
import os
import sys
import signal
from time import sleep
from atexit import register

_std = '/dev/null'


class Daemon:
    def __init__(self, pidfile, func=None, stdin=_std, stdout=_std, stderr=_std):
        self.pidfile = pidfile
        self.func = func
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr

    """
    A Class to  daemonizing function func.
    """

    def daemonize(self):
        """
        do the UNIX double-fork magic,
        see Stevens' "Advanced Programming in the UNIX Environment"
        for details (ISBN 0201563177)
        http://www.erlenstar.demon.co.uk/unix/faq_2.html#SEC16
        """
        try:
            pid = os.fork()
            if pid > 0:
                # exit first parent
                sys.exit(0)
        except OSError as e:
            sys.stderr.write("fork #1 failed: %d (%s)\n" %
                             (e.errno, e.strerror))
            sys.exit(1)

        # decouple from parent environment
        os.chdir("/")
        os.setsid()
        os.umask(0)

        # do second fork
        try:
            pid = os.fork()
            if pid > 0:
                # exit from second parent
                sys.exit(0)
        except OSError as e:
            sys.stderr.write("fork #2 failed: %d (%s)\n" %
                             (e.errno, e.strerror))
            sys.exit(1)

        # redirect standard file descriptors
        sys.stdout.flush()
        sys.stderr.flush()
        si = open(self.stdin, 'r')
        so = open(self.stdout, 'a+')
        se = open(self.stderr, 'a+')
        os.dup2(si.fileno(), 0)  # sys.stdin
        os.dup2(so.fileno(), 1)  # sys.stdout
        os.dup2(se.fileno(), 2)  # sys.stderr

        # write pidfile
        register(lambda: os.remove(self.pidfile))
        pid = str(os.getpid())
        with open(self.pidfile, 'w+') as f:
            f.write("%s\n" % pid)

    def start(self):
        """
        Start the daemon
        """
        # Check for a pidfile to see if the daemon already runs
        try:
            with open(self.pidfile, 'r') as pf:
                pid = int(pf.read().strip())
            message = "pidfile %s already exist (pid = %s). Daemon already running?\n"
            sys.stderr.write(message % (self.pidfile, pid))
            sys.exit(1)
        except IOError:
            pass

        # Start the daemon
        self.daemonize()
        if self.func is None:
            self.run()
        else:
            self.func()

    def run(self):
        return

    def stop(self, exit_on_error=True):
        """
        Stop the daemon
        """
        # Get the pid from the pidfile
        try:
            with open(self.pidfile, 'r') as pf:
                pid = int(pf.read().strip())
        except IOError:
            message = "pidfile %s does not exist. Daemon is not running?\n"
            sys.stderr.write(message % self.pidfile)
            if exit_on_error:
                sys.exit(1)
            else:
                return  # not an error in a restart

        # Try killing the daemon process
        try:
            os.kill(pid, signal.SIGTERM)
            sleep(0.1)
            os.kill(pid, signal.SIGHUP)
            sleep(0.1)
            os.kill(pid, signal.SIGKILL)
        except OSError:
            pass
        finally:
            if os.path.isfile(self.pidfile):
                os.remove(self.pidfile)
            # sys.exit(0)

    def restart(self):
        """
        Restart the daemon
        """
        self.stop(False)
        self.start()
