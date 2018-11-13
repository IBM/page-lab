from django import template

register = template.Library()

##
## Global template HTML helpers for site consistency and easy redesigns.
##
@register.simple_tag(takes_context=True)
def getTemplateHelpers(context):
    
    horizontalSpace = 'ph3 ph4-ns'
    rounded = 'br2'
    commonButton = 'pointer br2 ba ph4 pv3 bg-animate border-box ' + rounded
    
    return {
        'classes': {
            'commonButton': commonButton,
            'viewReport': commonButton + ' b--dark-green bg-green hover-bg-dark-green white',
            'viewAll': commonButton + ' b--blue bg-white hover-bg-blue blue hover-white link',
            'grid': 'w-100 pt2 ' + horizontalSpace,
            'horizontalSpace': horizontalSpace,
            'navItem': 'link near-white f6 f5-ns dib mr4 pv3 hover-green',
            'rounded': rounded,
        }
    }
