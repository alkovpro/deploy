# -*- coding: utf-8 -*-
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
if not os.path.exists(DATA_DIR):
    os.mkdir(DATA_DIR)

PIDFILE = os.path.join(DATA_DIR, 'deploy.pid')

TIME_FILE = os.path.join(DATA_DIR, 'deploy.time')
LOG_FILE = os.path.join(DATA_DIR, 'deploy.log')
STD_FILE = os.path.join(DATA_DIR, 'deploy.std')
ERR_FILE = None  # os.path.join(DATA_DIR, 'deploy.err')

FLAG_PATH = os.path.join(DATA_DIR, 'flag.')
TRIGGER = FLAG_PATH + 'trigger'
QUEUE = FLAG_PATH + 'queue'
PROCESS = FLAG_PATH + 'process'
WAIT = FLAG_PATH + 'wait'

SERVER = 'http://my-deployed-app.org/'

USERNAME = 'www'
MANAGE_PY = '../env/bin/python ./manage.py'

COMMANDS = {
    '1.frontend': {
        1: {'cd': '/home/www/myproject/front'},
        2: {'cmd': 'git pull',
            'user': USERNAME},
        3: {'if': "('error:' in stderr) and ('overwritten' in stderr) and ('Aborting' in stderr)",
            'then': {
                1: {'cmd': 'git reset --hard',
                    'user': USERNAME},
                2: {'cmd': 'git pull',
                    'user': USERNAME},
            },
            'else': {

            }},
    },
    '2.backend': {
        1: {'cd': '/home/www/myproject/back'},
        2: {'cmd': "find ./ -name '*.pyc' -exec rm {} \;"},
        3: {'cmd': 'git pull',
            'user': USERNAME},
        4: {'if': "('error:' in stderr) and ('overwritten' in stderr) and ('Aborting' in stderr)",
            'then': {
                1: {'cmd': 'git reset --hard',
                    'user': USERNAME},
                2: {'cmd': 'git pull',
                    'user': USERNAME},
            },
            'else': {
            }},
        5: {'cmd': """for file in `find ./ -name '*models.py' | sed -e "s/\.\///g;s/\/models.py//g"`;do """ +
                   MANAGE_PY + " makemigrations $file;done",
            'user': USERNAME},
        6: {'cmd': MANAGE_PY + ' migrate',
            'user': USERNAME},
        7: {'cmd': MANAGE_PY + ' collectstatic --noinput',
            'user': USERNAME},
        8: {'cmd': 'service uwsgi restart myproject'},
        9: {'cmd': 'nginx -s reload'},
    },
}
