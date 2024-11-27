# Generated by Django 4.2.16 on 2024-11-20 22:03

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0007_postanalytics'),
    ]

    operations = [
        migrations.AlterField(
            model_name='heading',
            name='post',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='headings', to='blog.post'),
        ),
        migrations.AlterField(
            model_name='postanalytics',
            name='post',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='post_analytics', to='blog.post'),
        ),
        migrations.AlterField(
            model_name='postview',
            name='post',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='post_view', to='blog.post'),
        ),
    ]