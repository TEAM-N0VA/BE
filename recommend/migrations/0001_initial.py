from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='RecommendLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('meal_type', models.CharField(
                    choices=[('breakfast', '아침'), ('lunch', '점심'), ('dinner', '저녁'), ('snack', '간식')],
                    max_length=20,
                )),
                ('context', models.JSONField(default=dict)),
                ('result', models.JSONField(default=dict)),
                ('reason', models.TextField(blank=True)),
                ('user_rating', models.IntegerField(blank=True, null=True)),
                ('is_applied', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='recommend_logs',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'db_table': 'recommend_logs',
                'ordering': ['-created_at'],
            },
        ),
    ]
