"""Automatic validation of portal resources against their dataset's data standard (DEC-015)."""
import logging

from mcod.aed import connectors, validation

logger = logging.getLogger("mcod")


def standard_for_resource(resource):
    from mcod.aed.standards import get_dataset_standard

    if not resource.dataset_id:
        return None
    standard = get_dataset_standard(resource.dataset_id)
    return standard if standard and standard.is_active else None


def store_report(resource, standard, report):
    from mcod.aed.models import ResourceStandardValidation

    obj, _ = ResourceStandardValidation.objects.update_or_create(
        resource_id=resource.pk,
        defaults={
            "standard": standard,
            "standard_version": standard.version,
            "status": report["status"],
            "blocking": report["blocking"],
            "blocking_reasons": report["blocking_reasons"],
            "data_format": report.get("format") or "",
            "rows_total": report["rows_total"],
            "rows_invalid": report["rows_invalid"],
            "column_mapping": report["column_mapping"],
            "coverage": report["coverage"],
            "errors": report["errors"],
            "warnings": report["warnings"],
        },
    )
    return obj


def validate_resource(resource, apply_blocking=True):
    """Validate one resource; store the result; unpublish (draft) when blocking. -> report or None."""
    standard = standard_for_resource(resource)
    if standard is None:
        return None
    try:
        raw, filename, fmt = connectors.resource_bytes(resource)
        report = validation.validate_for_standard(raw, standard=standard, filename=filename, fmt=fmt)
    except (connectors.SourceLoadError, validation.ValidationInputError) as exc:
        report = validation.unreadable_report(str(exc), max_invalid_ratio=standard.max_invalid_ratio,
                                              standard_code=standard.code)
    store_report(resource, standard, report)
    if apply_blocking and report["blocking"] and resource.status == "published":
        block_resource(resource)
    logger.info("mcod.aed: resource %s validated against %s: %s", resource.pk, standard.code, report["status"])
    return report


def block_resource(resource):
    """Unpublish a resource that fails its standard (portal signals update ES/search)."""
    from mcod.resources.models import Resource

    instance = Resource.raw.get(pk=resource.pk)
    if instance.status != "published":
        return
    instance.status = "draft"
    instance.save()
    logger.warning("mcod.aed: resource %s set to draft (blocking validation errors)", resource.pk)


def queue_dataset_validation(dataset_id):
    """Re-validate all resources of a dataset (e.g. after its standard was set)."""
    from mcod.aed.tasks import validate_resource_standard_task
    from mcod.resources.models import Resource

    for pk in Resource.raw.filter(dataset_id=dataset_id, is_removed=False).values_list("pk", flat=True):
        validate_resource_standard_task.apply_async_on_commit(args=(pk,))


def summarize_for_form(report, limit=10):
    lines = list(report["blocking_reasons"])
    for error in report["errors"][:limit]:
        lines.append("wiersz {}: {}".format(error["row"], error["message"]))
    if report["errors_count"] > limit:
        lines.append("… i {} kolejnych błędów (pełny raport: POST /1.4/aed/validate).".format(
            report["errors_count"] - limit))
    return lines
