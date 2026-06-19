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
            name='FoodInfo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('food_name', models.CharField(max_length=200)),
                ('kcal_per_100', models.FloatField()),
                ('carbs_per_100', models.FloatField()),
                ('protein_per_100', models.FloatField()),
                ('fat_per_100', models.FloatField()),
                ('fiber_per_100', models.FloatField(default=0)),
                ('sugar_per_100', models.FloatField(default=0)),
                ('sodium_per_100', models.FloatField(default=0)),
                ('gi_index', models.IntegerField(blank=True, null=True)),
                ('serving_size', models.FloatField(default=100)),
                ('is_user_added', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('added_by', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='added_foods',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'db_table': 'food_info',
            },
        ),
        migrations.CreateModel(
            name='MealLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('meal_type', models.CharField(
                    choices=[('breakfast', '아침'), ('lunch', '점심'), ('dinner', '저녁'), ('snack', '간식')],
                    max_length=20,
                )),
                ('eaten_at', models.DateTimeField()),
                ('img_url', models.TextField(blank=True)),
                ('restaurant_id', models.BigIntegerField(blank=True, null=True)),
                ('nausea_level', models.IntegerField(blank=True, null=True)),
                ('user_rating', models.IntegerField(blank=True, null=True)),
                ('total_kcal', models.FloatField(default=0)),
                ('total_carbs', models.FloatField(default=0)),
                ('total_protein', models.FloatField(default=0)),
                ('total_fat', models.FloatField(default=0)),
                ('predicted_glucose', models.FloatField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='meal_logs',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'db_table': 'meal_logs',
                'ordering': ['-eaten_at'],
            },
        ),
        migrations.CreateModel(
            name='MealItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('recorded_name', models.CharField(max_length=200)),
                ('predicted_name', models.CharField(blank=True, max_length=200)),
                ('amount_g', models.FloatField()),
                ('is_user_modified', models.BooleanField(default=False)),
                ('yolo_confidence', models.FloatField(blank=True, null=True)),
                ('bbox', models.JSONField(blank=True, null=True)),
                ('kcal', models.FloatField(default=0)),
                ('carbs', models.FloatField(default=0)),
                ('protein', models.FloatField(default=0)),
                ('fat', models.FloatField(default=0)),
                ('sugar', models.FloatField(default=0)),
                ('food_info', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='meal_items',
                    to='meals.foodinfo',
                )),
                ('meal_log', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='items',
                    to='meals.meallog',
                )),
            ],
            options={
                'db_table': 'meal_items',
            },
        ),
    ]
