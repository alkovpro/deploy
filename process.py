#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys,re
import os,subprocess
import shutil,pwd
from daemon import Daemon
import time
from config import DEPLOY_DIR, APP_USER #GIT_DIR, GIT_PULL, GIT_RESET, APP_RESTART, CEL_RESTART
import copy

PIDFILE      = '/tmp/deployprocess.pid'
TMPPATH      = '/tmp/deployprocess'
TIMEFILE     = '/home/www/deploy/lastdeploy.time'
LOGFILE      = '/home/www/deploy/lastdeploy.log'
STDFILE      = '/home/www/deploy/lastdeploy.std'
ERRFILE      = '/home/www/deploy/lastdeploy.err'
TRIGGER_PATH = '/home/www/deploy/trigger.'
PROCESS      = TRIGGER_PATH + 'process'
TRIGGER      = TRIGGER_PATH + 'trigger'
QUEUE        = TRIGGER_PATH + 'queue'
WAIT         = TRIGGER_PATH + 'wait'
#CONFIG       = {}
ROOT_USER    = pwd.getpwnam('root')

class DeployProcess(Daemon):
    def cleartriggers(self):
        if os.path.isfile(PROCESS):
            os.remove(PROCESS)
        if os.path.isfile(TRIGGER):
            os.remove(TRIGGER)
        if os.path.isfile(WAIT):
            os.remove(WAIT)
        if os.path.isfile(QUEUE):
            os.remove(QUEUE)

    def start(self):
        _tempdir=DEPLOY_DIR
        _dir='etc'
        _file='config'
        if os.path.isdir(_tempdir):
            if os.path.exists(os.path.join(_tempdir,_dir,_file+'.py')):
                os.chdir(_tempdir)
                needRemove=False
                if _tempdir not in sys.path:
                    sys.path.insert(0,_tempdir)
                    needRemove=True
                _temp = __import__(_dir+'.'+_file, globals(), locals(), ['CONFIG'], -1)
                self.CONFIG=copy.copy(_temp.CONFIG)
                if needRemove:
                    sys.path.remove(_tempdir)

        self.cleartriggers()
        file(WAIT,'w+').write("\n")
        super(DeployProcess,self).start()

    def stop(self):
        super(DeployProcess,self).stop()
        self.cleartriggers()

    def run(self):
        while True:
            if not os.path.isfile(PROCESS):
                if os.path.isfile(TRIGGER):
                    os.rename(TRIGGER,PROCESS)
                elif os.path.isfile(QUEUE):
                    os.rename(QUEUE,PROCESS)
                if os.path.isfile(PROCESS):
                    self.so.truncate(0)
                    fo_r = 'r' if os.path.exists(TIMEFILE) else ''
                    fo = open(TIMEFILE, "%sw+" % fo_r)
                    fo.truncate()
                    fo.writelines([time.ctime()])
                    fo.close()

                    os.chdir(self.CONFIG['GIT_DIR'])
                    p=subprocess.Popen("su --command '%s' %s" % (self.CONFIG['GIT_PULL'],APP_USER),shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                    fo_r = 'r' if os.path.exists(LOGFILE) else ''
                    fo = open(LOGFILE, "%sw+" % fo_r)
                    fo.truncate()
                    fo.write(p.stdout.read())

                    fe_r = 'r' if os.path.exists(ERRFILE) else ''
                    fe = open(ERRFILE, "%sw+" % fe_r)
                    fe.truncate()
                    errmgs=p.stderr.read()
                    fe.write(errmgs)
                    errmgs=errmgs.lower()
                    if ('error:' in errmgs) and ('overwritten' in errmgs) and ('aborting' in errmgs):
                        p=subprocess.Popen("su --command '%s' %s" % (self.CONFIG['GIT_RESET'],APP_USER),shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)

                        fo.writelines(('--[hard reset]--\n'))
                        fo.write(p.stdout.read())

                        fe.writelines(('--[hard reset]--\n'))
                        fe.write(p.stderr.read())

                        p=subprocess.Popen("su --command '%s' %s" % (self.CONFIG['GIT_PULL'],APP_USER),shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                        fo.writelines(('--[pull again]--\n'))
                        fo.write(p.stdout.read())

                        fe.writelines(('--[pull again]--\n'))
                        fe.write(p.stderr.read())

                    # replace system config with files from project
                    file_list=[]
                    for root,dirs,files in os.walk(os.path.join(DEPLOY_DIR,'etc')):
                        file_list+=[os.path.join(root,name)[len(DEPLOY_DIR):] for name in files if name not in ['__init__.py','__init__.pyc','config.py','config.pyc']]

                    for file in file_list:
                        bak=file+'.backup'
                        f_ok=False
                        if os.path.exists(file):
                            if os.path.exists(bak):
                                try:
                                    os.remove(bak)
                                    f_ok=True
                                except:
                                    f_ok=False
                            else:
                                f_ok=True
                            if f_ok:
                                try:
                                    os.rename(file,bak)
                                    f_ok=True
                                except:
                                    f_ok=False
                        else:
                            f_ok=True

                        if f_ok:
                            fromfile=file
                            while fromfile[0]=='/':fromfile=fromfile[1:]
                            fromfile=os.path.join(DEPLOY_DIR,fromfile)
                            # print "\n"+DEPLOY_DIR
                            # print "\n"+file
                            # print "\n"+fromfile
                            try:
                                shutil.copy(fromfile,file)
                                os.chown(file,ROOT_USER[2],ROOT_USER[3])
                                os.chmod(file,0644)
                                f_ok=True
                            except:
                                f_ok=False

                    for CMD_RESTART in self.CONFIG['APP_RESTART']:
                        fo.writelines(('\n--[%s]--\n' % CMD_RESTART))
                        p=subprocess.Popen(CMD_RESTART,shell=True,stdout=subprocess.PIPE)
                        val=p.stdout.read()
                        val=re.sub('\x1b[\/\!]*?[^\x1bm]*?m','',val)
                        fo.write(val)

                    fo.close()
                    if os.path.isfile(PROCESS):
                        os.rename(PROCESS,WAIT)
                    elif os.path.isfile(QUEUE):
                        os.rename(QUEUE,TRIGGER)

            time.sleep(10)


if __name__ == "__main__":
    daemon = DeployProcess(PIDFILE,'/dev/null',STDFILE)
    if len(sys.argv) == 2:
        if 'start' == sys.argv[1]:
            daemon.start()
        elif 'stop' == sys.argv[1]:
            daemon.stop()
        elif 'restart' == sys.argv[1]:
            daemon.restart()
        else:
            print "Unknown command"
            sys.exit(2)
        sys.exit(0)
    else:
        print "usage: %s start|stop|restart" % sys.argv[0]
        sys.exit(2)

