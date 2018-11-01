import re

from django import template
from django.contrib.humanize.templatetags.humanize import intcomma

register = template.Library()



##
##  Strips protocol off URL for nice display/hotlink text.
##  
##  INPUT:  http(s)://www.someDomain.com/some/path/here/
##  RETURNS:  www.someDomain.com/some/path/here/
##
##
@register.filter
def noprotocol(fullUrl):
    returnData = re.sub(r"https?://", "", fullUrl)
    returnData = re.sub(r"/$", "", returnData)

    return returnData


##
##  Changes decimal # to whole #s, rounds it to whole num.
##  Used if converting lighthouse perf #s to percents.
##  
##  INPUT:  .83
##  RETURNS:  83
##
##
@register.filter
def toPercent(num):
    try:
        return round(float(num) * 100)
    except Exception as ex:
        return 0


##
##  Adds comma to a #.
##  
##  INPUT:  1529
##  RETURNS:  1,529
##
##
@register.filter
def withComma(num):
    try:
        num = round(float(num))
        returnData = "%s" % (intcomma(int(num)))
    except Exception as ex:
        returnData = "0"
    
    return returnData

##
##  Takes bytes and converts to nice KB or MB
##  
##  INPUT:  1529392
##  RETURNS:  1,529 mb
##
##
@register.filter
def kbToMb(num):
    returnData = num
    unit = "kb"

    try:
        if int(float(num)+1) > 999999:
            num = round((float(num)/1000000),2)
            unit = "mb"
        else:
            num = round((float(num)/1000))
    except Exception as ex:
        num = 0
        print("|%s| is not a num?" % num)
        
    returnData = "%s %s" % (intcomma(num), unit)
    
    return returnData


##
##  Takes bytes and converts to KB # only
##  
##  INPUT:  752392
##  RETURNS:  752
##
##
@register.filter
def byteToKb(num):
    try:
        return round((float(num)/1000))
    except Exception as ex:
        return 0


## TODO: Santelia
##
##  Truncates the middle of the URL with elipsis
##  
##  INPUT:  http(s)://www.someDomain.com/some/really/long/path/here/
##  RETURNS:  www.someDomain.com/some/...here/
##
##
@register.filter
def truncateurl(fullUrl):
    returnData = fullUrl
    
    return returnData

