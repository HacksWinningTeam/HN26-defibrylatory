"""Celery tasks of mcod.aed (discovered by `app.autodiscover_tasks()` in mcod/celeryapp.py)."""
from celery.signals import task_postrun

from mcod.core.tasks import extended_shared_task

UPSTREAM_RESOURCE_TASK = "mcod.resources.tasks.entrypoint_process_resource_validation_task"
UPSTREAM_FILE_TASK = "mcod.resources.tasks.entrypoint_process_resource_file_validation_task"


@extended_shared_task(ignore_result=True, name="mcod.aed.tasks.validate_resource_standard_task")
def validate_resource_standard_task(resource_id):
    """Validate a resource against its dataset's standard; unpublish it when blocking (DEC-015)."""
    from mcod.aed.resource_validation import validate_resource
    from mcod.resources.models import Resource

    resource = Resource.raw.filter(pk=resource_id, is_removed=False).first()
    if resource is None:
        return None
    report = validate_resource(resource)
    return None if report is None else report["status"]


def on_upstream_task_done(sender=None, task_id=None, task=None, args=None, kwargs=None, **_):
    """After the portal finished downloading/analysing a resource, check it against its standard."""
    name = getattr(sender, "name", "") or getattr(task, "name", "")
    if not args:
        return
    resource_id = None
    if name == UPSTREAM_RESOURCE_TASK:
        resource_id = int(args[0])
    elif name == UPSTREAM_FILE_TASK:
        from mcod.resources.models import ResourceFile

        resource_id = ResourceFile.objects.filter(pk=int(args[0])).values_list("resource_id", flat=True).first()
    if resource_id:
        from mcod.aed.resource_validation import standard_for_resource
        from mcod.resources.models import Resource

        resource = Resource.raw.filter(pk=resource_id).first()
        if resource is not None and standard_for_resource(resource) is not None:
            validate_resource_standard_task.apply_async(args=(resource_id,))


def connect_upstream_hooks():
    task_postrun.connect(on_upstream_task_done, weak=False, dispatch_uid="mcod_aed_validate_after_upstream")
