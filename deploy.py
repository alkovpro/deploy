from flask import Flask
import os

TIMEFILE = '/home/www/deploy/lastdeploy.time'
LOGFILE = '/home/www/deploy/lastdeploy.log'
STDFILE = '/home/www/deploy/lastdeploy.std'
ERRFILE = '/home/www/deploy/lastdeploy.err'
TRIGGER_PATH = '/home/www/deploy/trigger.'
PROCESS = TRIGGER_PATH + 'process'
TRIGGER = TRIGGER_PATH + 'trigger'
QUEUE = TRIGGER_PATH + 'queue'
WAIT = TRIGGER_PATH + 'wait'

application = Flask(__name__)


@application.route('/')
def index():
    return 'What\'s up?'


@application.route('/pushed', methods=['GET', 'POST'])
def pushed():
    if not os.path.isfile(PROCESS):
        if os.path.isfile(WAIT):
            os.rename(WAIT, TRIGGER)
    else:
        os.rename(PROCESS, QUEUE)

    return 'done<br/><br/><a href="/last">Check last result</a>'


@application.route('/last', methods=['GET', 'POST'])
def lastdeploy():
    timefile = ''
    logfile = ''
    stdfile = ''
    errfile = ''
    try:
        timefile = file(TIMEFILE).read()
    except:
        pass
    try:
        logfile = file(LOGFILE).read()
    except:
        pass
    try:
        stdfile = file(STDFILE).read()
    except:
        pass
    try:
        errfile = file(ERRFILE).read()
    except:
        pass
    if len(timefile) > 0:
        timefile = " (%s)" % timefile
    res = '<b>Log' + timefile + ':</b><br/><pre>' + logfile + \
          '</pre><hr><b>Std out' + timefile + ':</b><br/><pre>' + stdfile + \
          '</pre><hr><b>Std err' + timefile + ':</b><br/><pre>' + errfile + \
          '</pre>'

    return res
