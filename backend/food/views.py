from django.shortcuts import redirect


def recipe_redirect(request, recipe_id):
    """Переход по короткой ссылке."""
    return redirect(f'/api/recipes/{recipe_id}/')
