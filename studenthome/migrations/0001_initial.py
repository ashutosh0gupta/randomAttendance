# Generated by Django 2.1.4 on 2019-02-25 11:16

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Call',
            fields=[
                ('created_on', models.DateTimeField(auto_now_add=True, primary_key=True, serialize=False)),
                ('rollno', models.CharField(max_length=10)),
                ('status', models.CharField(default='ABSENT', max_length=200)),
                ('prevCall', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='studenthome.Call')),
            ],
        ),
        migrations.CreateModel(
            name='StudentInfo',
            fields=[
                ('name', models.CharField(max_length=100)),
                ('imagePath', models.CharField(max_length=200)),
                ('rollno', models.CharField(max_length=10, primary_key=True, serialize=False)),
                ('presentCount', models.IntegerField(default=0)),
                ('absentCount', models.IntegerField(default=0)),
                ('awakeCount', models.IntegerField(default=0)),
                ('calls', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='studenthome.Call')),
            ],
        ),
    ]
