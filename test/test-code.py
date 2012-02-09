# -*- coding: utf-8 -*-
# script for testing some thoughts

from validictory import validate
a= '2012-1-a1'
try:
    schema  = {'format':'date'}
    validate(a,schema)
    b = a
    print 'b:'+str(b)
except ValueError, errormsg:
    print errormsg
