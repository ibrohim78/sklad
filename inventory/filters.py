from django.db.models import Q


def product_search_filter(queryset, search_term):
    if not search_term:
        return queryset
    return queryset.filter(
        Q(name__icontains=search_term)
        | Q(category__name__icontains=search_term)
    )
