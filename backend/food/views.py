from django.http import Http404
from django.shortcuts import redirect

from .models import Recipe


def recipe_redirect(request, recipe_id):
    """Переход по короткой ссылке."""
    if not Recipe.objects.filter(pk=recipe_id).exists():
        raise Http404(f"Рецепт с ID {recipe_id} не найден")
    return redirect(f'/recipes/{recipe_id}/')
