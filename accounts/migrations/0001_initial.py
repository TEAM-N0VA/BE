from django.db import migrations, models
import django.contrib.auth.models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(
                    default=False,
                    help_text='Designates that this user has all permissions without explicitly assigning them.',
                    verbose_name='superuser status',
                )),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('is_staff', models.BooleanField(
                    default=False,
                    help_text='Designates whether the user can log into this admin site.',
                    verbose_name='staff status',
                )),
                ('is_active', models.BooleanField(
                    default=True,
                    help_text='Designates whether this user should be treated as active.',
                    verbose_name='active',
                )),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('email', models.EmailField(max_length=254, unique=True, verbose_name='email address')),
                ('nickname', models.CharField(max_length=50)),
                ('provider', models.CharField(
                    choices=[('email', 'Email'), ('kakao', 'Kakao'), ('google', 'Google')],
                    default='email',
                    max_length=10,
                )),
                ('provider_id', models.CharField(blank=True, max_length=255, null=True)),
                ('groups', models.ManyToManyField(
                    blank=True,
                    help_text='The groups this user belongs to.',
                    related_name='user_set',
                    related_query_name='user',
                    to='auth.group',
                    verbose_name='groups',
                )),
                ('user_permissions', models.ManyToManyField(
                    blank=True,
                    help_text='Specific permissions for this user.',
                    related_name='user_set',
                    related_query_name='user',
                    to='auth.permission',
                    verbose_name='user permissions',
                )),
            ],
            options={
                'db_table': 'users',
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('due_date', models.DateField(blank=True, null=True)),
                ('dietary_restrictions', models.JSONField(blank=True, default=list)),
                ('flavor_preferences', models.JSONField(blank=True, default=list)),
                ('target_carb_per_meal', models.FloatField(blank=True, null=True)),
                ('target_calories', models.FloatField(blank=True, null=True)),
                ('target_bloodsugar', models.FloatField(blank=True, null=True)),
                ('nausea_level', models.IntegerField(blank=True, null=True)),
                ('weight', models.FloatField(blank=True, null=True)),
                ('is_profile_completed', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='profile',
                    to='accounts.user',
                )),
            ],
            options={
                'db_table': 'user_profiles',
            },
        ),
    ]
