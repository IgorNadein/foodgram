from django.shortcuts import get_object_or_404, redirect

from .models import Recipe


def recipe_redirect(request, recipe_id):
    """Переход по короткой ссылке."""
    get_object_or_404(Recipe, pk=recipe_id)
    return redirect('recipe', pk=recipe_id)
