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
            name='Restaurant',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('kakao_place_id', models.CharField(max_length=50, unique=True)),
                ('name', models.CharField(max_length=200)),
                ('category', models.CharField(max_length=100)),
                ('address', models.CharField(max_length=300)),
                ('phone', models.CharField(blank=True, max_length=50)),
                ('lat', models.FloatField()),
                ('lng', models.FloatField()),
                ('base_score', models.FloatField(default=50)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'restaurants',
            },
        ),
        migrations.CreateModel(
            name='RestaurantScore',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('personal_score', models.FloatField(default=50)),
                ('total_score', models.FloatField(default=50)),
                ('visit_count', models.IntegerField(default=0)),
                ('last_actual_glucose', models.FloatField(blank=True, null=True)),
                ('ema_updated_at', models.DateTimeField(blank=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('restaurant', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='user_scores',
                    to='location.restaurant',
                )),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='restaurant_scores',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'db_table': 'restaurant_scores',
                'unique_together': {('user', 'restaurant')},
            },
        ),
        migrations.CreateModel(
            name='RestaurantFeedback',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('actual_glucose', models.FloatField(blank=True, null=True)),
                ('user_rating', models.IntegerField(blank=True, null=True)),
                ('memo', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('meal_log', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='restaurant_feedbacks',
                    to='meals.meallog',
                )),
                ('restaurant', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='feedbacks',
                    to='location.restaurant',
                )),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='restaurant_feedbacks',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'db_table': 'restaurant_feedbacks',
                'ordering': ['-created_at'],
            },
        ),
    ]
