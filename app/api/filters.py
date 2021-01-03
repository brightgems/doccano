from django.db.models import Count, Q
from django_filters.rest_framework import FilterSet, BooleanFilter, NumberFilter

from .models import Document


class DocumentFilter(FilterSet):
    seq_annotations__isnull = BooleanFilter(field_name='seq_annotations', method='filter_annotations')
    doc_annotations__isnull = BooleanFilter(field_name='doc_annotations', method='filter_annotations')
    seq2seq_annotations__isnull = BooleanFilter(field_name='seq2seq_annotations', method='filter_annotations')
    speech2text_annotations__isnull = BooleanFilter(field_name='speech2text_annotations', method='filter_annotations')
    assigned_to = NumberFilter(field_name='annotations_assign_to', method='filter_assigned_to')
    approved = BooleanFilter(field_name='annotations_approved_by', method='filter_approved')
        
    def filter_approved(self,queryset, field_name, value):
        if value:
            queryset = queryset.filter(annotations_approved_by__isnull=value)
        return queryset

    def filter_assigned_to(self,queryset, field_name, value):
        if value:
            queryset = queryset.filter(annotations_assign_to__id=value)
        return queryset

    def filter_annotations(self, queryset, field_name, value):
        queryset = queryset.annotate(num_annotations=
            Count(field_name, filter=
                Q(**{ f"{field_name}__user": self.request.user}) | Q(project__collaborative_annotation=True)))

        should_have_annotations = not value
        if should_have_annotations:
            queryset = queryset.filter(num_annotations__gte=1)
        else:
            queryset = queryset.filter(num_annotations__lte=0)

        return queryset

    class Meta:
        model = Document
        fields = ('project', 'text', 'meta', 'created_at', 'updated_at',
                  'doc_annotations__label__id', 'seq_annotations__label__id',
                  'doc_annotations__isnull', 'seq_annotations__isnull', 'seq2seq_annotations__isnull',
                  'speech2text_annotations__isnull')
