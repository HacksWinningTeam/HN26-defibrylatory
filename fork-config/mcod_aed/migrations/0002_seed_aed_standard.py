from django.db import migrations


def seed(apps, schema_editor):
    from mcod.aed.standards import ensure_aed_standard

    ensure_aed_standard(apps.get_model("aed", "DataStandard"))


def unseed(apps, schema_editor):
    apps.get_model("aed", "DataStandard").objects.filter(code="aed-pl").delete()


class Migration(migrations.Migration):

    dependencies = [("aed", "0001_initial")]

    operations = [migrations.RunPython(seed, unseed)]
