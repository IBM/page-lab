from django import template
from ..helpers import GOOGLE_SCORE_SCALE

register = template.Library()


##
##  Takes a score value and returns a category class name, used for coloring the circle.
##  Score ranges and categories directly from Lighthouse documentation:
##  https://developers.google.com/web/tools/lighthouse/v3/scoring
##  Periodically check above URL for changes in ranges.
##
@register.filter
def scoreClass(scoreValue=0):
    """
    Returns class name based on the score performance.
    """
    try:
        if scoreValue <= GOOGLE_SCORE_SCALE['poor']['max']:
            returnClass = "pl-poorscore"
        elif scoreValue <= GOOGLE_SCORE_SCALE['average']['max']:
            returnClass = "pl-avgscore"
        elif scoreValue >= GOOGLE_SCORE_SCALE['good']['min']:
            returnClass = "pl-goodscore"
        else:
            returnClass = ""
    except Exception as ex:
        returnClass = ""
    
    return returnClass
