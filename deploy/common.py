# -*- coding: utf-8 -*-
import os

def touch(filename):
    with open(filename, 'w+t') as wf:
        wf.write("\n")


def rename(old_file, new_file, force=False):
    result = False
    if os.path.exists(old_file):
        os.rename(old_file, new_file)
        result = True
    elif force:
        touch(new_file)
        result = True
    return result


def delete(filename):
    if os.path.isfile(filename):
        os.remove(filename)


def read(filename):
    result = ''
    with open(filename, 'rt') as rf:
        result = rf.read()
    return result


def write(filename, data, truncate=False):
    with open(filename, 'w+t' if truncate else 'a+t') as wf:
        if type(data) is list:
            wf.writelines(data)
        else:
            wf.write(data)
