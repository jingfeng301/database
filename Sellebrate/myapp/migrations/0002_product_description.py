# Generated by Django 4.2.13 on 2024-06-19 07:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='Description',
            field=models.CharField(blank=True, max_length=512, null=True),
        ),
    ]
