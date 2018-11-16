from django import template

register = template.Library()

##
## Global template HTML helpers for site consistency and easy redesigns.
##
@register.simple_tag(takes_context=True)
def getTemplateHelpers(context):
    
    siteColor = 'gold'
    horizontalSpace = 'ph3 ph4-ns'
    rounded = 'br2'
    commonButton = 'pointer dib mb3 br2 ba ph4 pv3 bg-animate border-box ' + rounded
    smallButton = 'pointer dib mb3 br2 ba pa2 bg-animate border-box ' + rounded
    bluePriButton = 'b--dark-blue bg-blue hover-bg-dark-blue white'
    blueSecButton = 'b--blue bg-white hover-bg-blue blue hover-white link'
    greenPriButton = 'b--dark-green bg-green hover-bg-dark-green white'
    
    return {
        'classes': {
            'button': commonButton,
            'smallButton': smallButton,
            'bluePriButton': bluePriButton,
            'blueSecButton': blueSecButton,
            'greenPriButton': greenPriButton,
            'grid': horizontalSpace + ' w-100',
            'horizontalSpace': horizontalSpace,
            'imageBorder': 'ba b--black-20',
            'navItem': 'link near-white f6 f5-ns dib mr4 pv3 hover-%s' % (siteColor),
            'rounded': rounded,
            'siteColor': siteColor,
            'tableListCell': 'pv3 pr4 bb b--black-20',
            'viewAll': commonButton + ' b--blue bg-white hover-bg-blue blue hover-white link',
            'viewReport': commonButton + ' b--dark-green bg-green hover-bg-dark-green white',
        },
        'html': {
            'hr': '<div class="' + horizontalSpace + ' w-100 mv5"><div class="bb b--silver"></div></div>'
        }
    }
