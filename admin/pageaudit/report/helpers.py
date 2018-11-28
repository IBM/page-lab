import os
import datetime
import requests, json

from django.contrib.auth.models import User
from django.core.mail import send_mail


##  Global var to be used any time we need to use the range or min/max # of
##   Google's category scoring scale. Names changed for more global usage.
##   Ex: An accessibility score isn't "slow", it's "poor".
##  Comes from Google documentation:  https://developers.google.com/web/tools/lighthouse/v3/scoring
##
##
GOOGLE_SCORE_SCALE = {
        "poor": {
            "min": 0,
            "max": 49
        },
        "average": {
            "min": 50,
            "max": 89
        },
        "good": {
            "min": 90,
            "max": 100
        }
    }


##
##  User timings is an array of generic non-property-named objects.
##  To get the one you want, you have to loop thru the array and find the one with the name you want.
##  This is a common function that will do that for you.
##  Simply pass the name of the timing you want, and the ARRAY OF OBJECTS to loop thru.
##  @return {object} The requred timing object which you can then get the values (duration, start, etc) from.
##
##
def getUserTimingValue(timingName, userTimingsObject=None, userTimingsArray=None):
    ## Allows us to pass top level Lighthouse report "user-timing" object 
    ##  in here and single try/catch.
    ## Otherwise, assume an array of objects
    returnObject = {
        "name": "",
        "duration": 0,
        "startTime": 0,
        "timingType": ""
    }
    
    try:
        userTimings = userTimingsObject['details']['items']
    except Exception as ex:
        userTimings = userTimingsArray

    ## Try and find the user-timing they requested, else return an empty one.  
    try:
        for item in userTimings:
            if item['name'] == timingName:
                returnObject = item
                break
    
    except Exception as ex:
        pass
    
    ## Debug            
    #print(returnObject)

    return returnObject

   
##
##  Takes the HTTP error code passed and the message and pushes 
##   a message to the Slack web hook URL for our room.
##
##
def sendSlackAlert (errorCode, msg):
    slackUrl = os.getenv('DJANGO_SLACK_ALERT_URL', '')
    payload = {"text": "*[PageLab]  %s just happened* \n%s" % (errorCode, msg)}
    
    if slackUrl:
        r = requests.post(slackUrl, json=payload)


##
##  Generic "send email" method, accepts three simple arguements. 
##  NOTE: send_mail function requires email to be array.
##
##
def sendEmailNotification(sendToArr, emailTitle, emailBody):
    ## Debug and console print instead of actually sending while testing:
    #print("[FRM notification] " + emailTitle, sendToArr, emailBody)
    #return
    
    ## If no emails were setup or passed to us, then we can't send anything.
    if len(sendToArr) == 0:
        return;
        
    try:
        send_mail(
            "[PageLab notification] %s" % emailTitle,
            emailBody,
            "do-not-reply@fakedomain.com",
            sendToArr,
            fail_silently=True,
            html_message='<div style="font-family:sans-serif;">%s</div>' % emailBody
        )
    except:
        #TODO: LOG THIS as an error so we know if email sending is failing.
        pass
	
	
##
##  Takes a LighthouseRun queryset (for a given URL) and filters it to a given date scope.
##  This is used in several views, so it's here. Also allows us to write a test for it.
##  Use cases:
##     Show chart/data with ALL lighthouse runs.
##     Show chart/data with runs from the past X # days (default, 3 weeks back).
##     Show chart/data with runs from Sept 5 to Oct 24.
##     Show chart/data with runs up to Oct 16
##     Show chart/data with runs from Oct 17 and later
##
##
def lighthouseRunsByDate(LighthouseRunQueryset, startDate=None, endDate=None):
    if startDate is not None:
        LighthouseRunQueryset = LighthouseRunQueryset.filter(created_date__gt=startDate)

    if endDate is not None:
        LighthouseRunQueryset = LighthouseRunQueryset.filter(created_date__lt=endDate)

    return LighthouseRunQueryset
    



