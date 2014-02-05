'''
Created on 04.02.2014.

@author: Sanja
'''

class GpxFormatException(Exception):
    '''
    classdocs
    '''

    def __str__(self):
        return "GPX format error"

class GpxDateFormatException(Exception):
    '''
    classdocs
    '''

    def __str__(self):
        return "GPX date in wrong format"