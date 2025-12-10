from django import template
from ..models import Rating

register = template.Library()

@register.filter
def has_rated(user, bb):
    return Rating.objects.filter(user=user, bb=bb).exists()

@register.simple_tag
def user_rating_score(user, bb):
    try:
        return Rating.objects.get(user=user, bb=bb).score
    except Rating.DoesNotExist:
        return 0