from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('meals', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='BloodSugarLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.FloatField()),
                ('measured_at', models.DateTimeField()),
                ('record_type', models.CharField(
                    choices=[
                        ('공복', '공복'), ('식전', '식전'), ('식후1시간', '식후1시간'),
                        ('식후2시간', '식후2시간'), ('취침전', '취침전'),
                    ],
                    max_length=20,
                )),
                ('risk_level', models.CharField(blank=True, max_length=10)),
                ('memo', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('meal_log', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='blood_sugar_logs',
                    to='meals.meallog',
                )),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='blood_sugar_logs',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'db_table': 'blood_sugar_logs',
                'ordering': ['-measured_at'],
            },
        ),
        migrations.CreateModel(
            name='BloodSugarPrediction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fasting_glucose', models.FloatField(blank=True, null=True)),
                ('predicted_value', models.FloatField()),
                ('post_1h_glucose', models.FloatField(blank=True, null=True)),
                ('post_2h_glucose', models.FloatField(blank=True, null=True)),
                ('risk_level', models.CharField(max_length=10)),
                ('confidence', models.FloatField(blank=True, null=True)),
                ('advice', models.TextField(blank=True)),
                ('model_mode', models.CharField(blank=True, max_length=50)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('meal_log', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='predictions',
                    to='meals.meallog',
                )),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='blood_sugar_predictions',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'db_table': 'blood_sugar_predictions',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='FoodSensitivity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('avg_spike', models.FloatField(default=0)),
                ('sample_count', models.IntegerField(default=0)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('food_info', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='sensitivities',
                    to='meals.foodinfo',
                )),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='food_sensitivities',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'db_table': 'food_sensitivities',
                'unique_together': {('user', 'food_info')},
            },
        ),
    ]
