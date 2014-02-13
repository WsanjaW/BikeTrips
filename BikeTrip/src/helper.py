'''
Created on 13.02.2014.

@author: Sanja
'''

   
def sec_to_time(time):
    '''
    Convert seconds given as number to string h:m:s
    '''
    time = int(time)
    h = time/3600
    time = time%3600
    m = time/60
    time = time%60
    s = time
    return "{:0>2d}".format(h) + ":" + "{:0>2d}".format(m) + ":" + "{:0>2d}".format(s)

def time_to_sec(time):
    '''
     Converts time in string format h:m:s to seconds
     '''
    if(time ==""):
        return 0
    t = time.split(':')
    h = int(t[0])
    m = int(t[1])
    s = int(t[2])
    return h * 3600 + m * 60 + s 

  
        