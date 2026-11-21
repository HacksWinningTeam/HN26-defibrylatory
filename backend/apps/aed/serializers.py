"""Serializers documenting the AED API payloads (OpenAPI via drf-spectacular)."""

from rest_framework import serializers


class AllowedValueSerializer(serializers.Serializer):
    value = serializers.CharField()
    label = serializers.CharField()


class FieldGroupSerializer(serializers.Serializer):
    code = serializers.CharField()
    label = serializers.CharField()


class FieldSpecSerializer(serializers.Serializer):
    """One column of the standard AED schema."""

    name = serializers.CharField()
    group = serializers.CharField()
    group_label = serializers.CharField()
    type = serializers.ChoiceField(choices=["string", "number", "integer", "boolean", "date"])
    obligation = serializers.ChoiceField(choices=["wymagane", "zalecane", "opcjonalne"])
    required = serializers.BooleanField()
    label = serializers.CharField()
    description = serializers.CharField()
    description_en = serializers.CharField()
    example = serializers.CharField(allow_blank=True)
    allowed_values = AllowedValueSerializer(many=True)
    pattern = serializers.CharField(allow_null=True)
    minimum = serializers.FloatField(allow_null=True)
    maximum = serializers.FloatField(allow_null=True)
    max_length = serializers.IntegerField(allow_null=True)
    osm_tag = serializers.CharField(allow_null=True)


class SchemaDocumentSerializer(serializers.Serializer):
    """The standard AED schema ("wzorcowy zakres danych")."""

    name = serializers.CharField()
    version = serializers.CharField()
    title = serializers.CharField()
    title_en = serializers.CharField()
    description = serializers.CharField()
    license = serializers.CharField()
    obligations = serializers.ListField(child=serializers.CharField())
    groups = FieldGroupSerializer(many=True)
    fields = FieldSpecSerializer(many=True)


class CoverageSerializer(serializers.Serializer):
    """Share (0-1) of records with a non-empty value, per standard field and per group."""

    records = serializers.IntegerField()
    required = serializers.FloatField()
    recommended = serializers.FloatField()
    overall = serializers.FloatField()
    fields = serializers.DictField(child=serializers.FloatField())


class SourceSerializer(serializers.Serializer):
    """One harvested source dataset with its reference scope (coverage of the standard schema)."""

    id = serializers.CharField(help_text="kind:external_id, e.g. dane_gov_pl:3624")
    title = serializers.CharField()
    publisher = serializers.CharField(allow_blank=True)
    kind = serializers.ChoiceField(choices=["dane_gov_pl", "osm"])
    url = serializers.CharField(allow_blank=True)
    license_name = serializers.CharField(allow_blank=True)
    format = serializers.CharField(allow_blank=True)
    status = serializers.CharField(help_text="ok | not_machine_readable | requires_api_key | error")
    status_note = serializers.CharField(allow_blank=True)
    resources_count = serializers.IntegerField()
    record_count = serializers.IntegerField()
    valid_count = serializers.IntegerField()
    confirmed_by_other_sources = serializers.IntegerField()
    coverage = CoverageSerializer(allow_null=True)
    quality_flags = serializers.DictField(child=serializers.IntegerField())


class SourcesReportSerializer(serializers.Serializer):
    aed_count = serializers.IntegerField()
    multi_source_aed_count = serializers.IntegerField()
    record_count = serializers.IntegerField()
    updated_at = serializers.DateTimeField(allow_null=True)
    schema_version = serializers.CharField()
    sources = SourceSerializer(many=True)
