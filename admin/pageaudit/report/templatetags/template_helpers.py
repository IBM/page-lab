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
    
    commonButton = 'pointer mb3 ba ph4 pv3 bg-animate border-box ' + rounded
    smallButton = 'pointer mb3 ba pa2 bg-animate border-box ' + rounded
    
    bluePriButton = 'b--dark-blue bg-blue hover-bg-dark-blue white'
    blueSecButton = 'b--blue bg-white hover-bg-blue blue hover-white link'
    
    greenPriButton = 'b--dark-green bg-green hover-bg-dark-green white'
    
    icons = {
        'chevronForward': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="4 0 24 24" class="icon chevron-forward"><g data-name="Layer 2"><g data-name="arrow-ios-forward"><rect width="24" height="24" transform="rotate(-90 12 12)" opacity="0"/><path d="M10 19a1 1 0 0 1-.64-.23 1 1 0 0 1-.13-1.41L13.71 12 9.39 6.63a1 1 0 0 1 .15-1.41 1 1 0 0 1 1.46.15l4.83 6a1 1 0 0 1 0 1.27l-5 6A1 1 0 0 1 10 19z"/></g></g></svg>',
        'newWindow': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" class="icon new-window"><g data-name="Layer 2"><g data-name="external-link"><rect width="24" height="24" opacity="0"/><path d="M20 11a1 1 0 0 0-1 1v6a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1h6a1 1 0 0 0 0-2H6a3 3 0 0 0-3 3v12a3 3 0 0 0 3 3h12a3 3 0 0 0 3-3v-6a1 1 0 0 0-1-1z"/><path d="M16 5h1.58l-6.29 6.28a1 1 0 0 0 0 1.42 1 1 0 0 0 1.42 0L19 6.42V8a1 1 0 0 0 1 1 1 1 0 0 0 1-1V4a1 1 0 0 0-1-1h-4a1 1 0 0 0 0 2z"/></g></g></svg>',
        'info': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" class="icon info"><g data-name="Layer 2"><g data-name="info"><rect width="24" height="24" transform="rotate(180 12 12)" opacity="0"/><path d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2zm0 18a8 8 0 1 1 8-8 8 8 0 0 1-8 8z"/><circle cx="12" cy="8" r="1"/><path d="M12 10a1 1 0 0 0-1 1v5a1 1 0 0 0 2 0v-5a1 1 0 0 0-1-1z"/></g></g></svg>',
        'modal': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" class="icon info"><g data-name="Layer 2"><g data-name="diagonal-arrow-right-up"><rect width="24" height="24" transform="rotate(180 12 12)" opacity="0"/><path d="M18 7.05a1 1 0 0 0-1-1L9 6a1 1 0 0 0 0 2h5.56l-8.27 8.29a1 1 0 0 0 0 1.42 1 1 0 0 0 1.42 0L16 9.42V15a1 1 0 0 0 1 1 1 1 0 0 0 1-1z"/></g></g></svg>'
    }
            
            
    return {
        'classes': {
            'button': commonButton,
            'smallButton': smallButton,
            'bluePriButton': bluePriButton,
            'blueSecButton': blueSecButton,
            'greenPriButton': greenPriButton,
            'grid': horizontalSpace + ' w-100',
            'horizontalSpace': horizontalSpace,
            'hasIcon': 'inline-flex items-center underline-hover',
            'imageBorder': 'ba b--black-20',
            'navItem': 'link near-white f6 f5-ns fl relative mr4 pv3 hover-%s' % (siteColor),
            'rounded': rounded,
            'siteColor': siteColor,
            'spinner': 'pl-spinner ba br-100',
            'tableListCell': 'pv3 bb b--black-20',
            'tableListCell_bt': 'pv3 bt b--black-20',
            'tooltipCue': 'bb b--black-20 b--dashed pointer bt-0 br-0 bl-0',
            'viewAll': commonButton + ' b--blue bg-white hover-bg-blue blue hover-white link',
            'viewReport': commonButton + ' b--dark-green bg-green hover-bg-dark-green white',
        },
        'html': {
            'hr': '<div class="' + horizontalSpace + ' w-100 mv5"><div class="bb b--silver"></div></div>',
            'icons': icons,
        }
    }
