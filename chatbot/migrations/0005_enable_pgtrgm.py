from django.contrib.postgres.operations import TrigramExtension
from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('chatbot', '0004_alter_knowledgeitem_id'),
    ]


    operations = [
        TrigramExtension(),
    ]
