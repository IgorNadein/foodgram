from django.http import HttpResponseRedirect


def recipe_redirect(request, recipe_id):
    """Переход по короткой ссылке."""
    return HttpResponseRedirect(
        request.build_absolute_uri(f'/recipes/{recipe_id}/')
    )
