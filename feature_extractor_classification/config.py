#!/usr/bin/python
from configparser import ConfigParser
import codecs 
 
def config(filename='database.ini', section='postgresql'):
    
    options ={}
    '''with codecs.open(filename, 'r', 'utf-8') as data:
        for line in data:
            opt = line.split('=')
            options[opt[0]] = opt[1].strip()
	'''
    # create a parser
    parser = ConfigParser()
    # read config file
    parser.read(filename)
 
    # get section, default to postgresql

    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            options[param[0]] = param[1]
    else:
        raise Exception('Section {0} not found in the {1} file'.format(section, filename))
    return options
