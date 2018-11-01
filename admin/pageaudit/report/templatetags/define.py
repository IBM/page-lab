from django import template

register = template.Library()


##
##  Allows you to set variables in a template. 
##  Used when deciding what class to use based on an object value.
##
@register.simple_tag
def define(val=None):
  return val