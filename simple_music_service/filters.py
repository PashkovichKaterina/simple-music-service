from rest_framework.filters import OrderingFilter
from django.db.models import F


class NotNoneValuesLargerOrderingFilter(OrderingFilter):
    def filter_queryset(self, request, queryset, view):
        ordering = self.get_ordering(request, queryset, view)

        if ordering:
            order = ordering[0]
            return queryset.order_by(F(order[1:]).desc(nulls_last=True)) if order.startswith("-") \
                else queryset.order_by(F(order).asc(nulls_first=True))

        return queryset
