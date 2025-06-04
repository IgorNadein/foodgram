from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from .models import Recipe


def recipe_redirect(request, recipe_id):
    """Переход по короткой ссылке."""
    get_object_or_404(Recipe, pk=recipe_id)
    return HttpResponseRedirect(f'/recipes/{recipe_id}/')
