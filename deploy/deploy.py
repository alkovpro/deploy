# -*- coding: utf-8 -*-
from flask import Flask
import os
from common import *
import config

application = Flask(__name__)


@application.route('/')
def index():
    return 'What\'s up?'


@application.route('/pushed', methods=['GET', 'POST'])
@application.route('/pushed/<which>', methods=['GET', 'POST'])
def pushed(which=''):
    if not rename(config.PROCESS, config.QUEUE):
        rename(config.WAIT, config.TRIGGER, True)

    return """
        done pushing <b>{which}</b><br/>
        <br/>
        Wait a few minutes to process changes and <a href="/last">check last result</a><br/>
        </br>
        <a href="{server}">{server}</a>
    """.format(which=which or 'all', server=config.SERVER)


@application.route('/last', methods=['GET', 'POST'])
def last_deploy():
    time_file = ''
    log_file = ''
    std_file = ''
    err_file = ''
    try:
        time_file = read(config.TIME_FILE)
    except:
        pass
    try:
        log_file = read(config.LOG_FILE) \
            .replace('==[', '<h1>').replace(']==', '</h1>') \
            .replace('--[', '<i><b>').replace(']--', '</b></i>')
    except:
        pass
    try:
        std_file = read(config.STD_FILE)
    except:
        pass
    try:
        err_file = read(config.ERR_FILE) \
            .replace('==[', '<h1>').replace(']==', '</h1>') \
            .replace('--[', '<i><b>').replace(']--', '</b></i>')
    except:
        pass
    if len(time_file) > 0:
        time_file = " (%s)" % time_file
    res = '<b>Log' + time_file + ':</b><br/><pre>' + log_file + \
          '</pre><hr><b>Std out' + time_file + ':</b><br/><pre>' + std_file + \
          '</pre><hr><b>Std err' + time_file + ':</b><br/><pre>' + err_file + \
          '</pre>'

    return res
