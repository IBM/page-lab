from django import template

register = template.Library()


##
##  Takes a score value and returns a category class name, used for coloring the circle.
##  Score ranges and categories directly from Lighthouse documentation:
##  https://developers.google.com/web/tools/lighthouse/v3/scoring
##
@register.filter
def scoreClass(scoreValue=0):
    """
    Returns class name based on the score performance.
    """
    try:
        if scoreValue < 45:
            returnClass = "pl-poorscore"
        elif scoreValue < 75:
            returnClass = "pl-avgscore"
        elif scoreValue > 74:
            returnClass = "pl-goodscore"
        else:
            returnClass = ""
    except Exception as ex:
        returnClass = ""
    
    return returnClass
