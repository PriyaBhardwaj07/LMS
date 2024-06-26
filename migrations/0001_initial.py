# Generated by Django 4.0.8 on 2024-03-27 07:15

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import re


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ActivityLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message', models.TextField()),
                ('created_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Course',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('summary', models.TextField(blank=True, max_length=200, null=True)),
                ('created_at', models.DateTimeField(auto_now=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('active', models.BooleanField(default=False)),
                ('version_number', models.IntegerField(null=True)),
                ('original_course', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='exam.course')),
            ],
        ),
        migrations.CreateModel(
            name='Customer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, null=True)),
                ('is_active', models.BooleanField(default=True, null=True)),
            ],
            options={
                'verbose_name_plural': 'Customers',
                'db_table': 'customer',
            },
        ),
        migrations.CreateModel(
            name='Progress',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.CreateModel(
            name='Quiz',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=60, verbose_name='Title')),
                ('slug', models.SlugField(blank=True, unique=True)),
                ('description', models.TextField(blank=True, help_text='A detailed description of the quiz', verbose_name='Description')),
                ('answers_at_end', models.BooleanField(default=False, help_text='Correct answer is NOT shown after question. Answers displayed at the end.', verbose_name='Answers at end')),
                ('exam_paper', models.BooleanField(default=False, help_text='If yes, the result of each attempt by a user will be stored. Necessary for marking.', verbose_name='Exam Paper')),
                ('single_attempt', models.BooleanField(default=False, help_text='If yes, only one attempt by a user will be permitted.', verbose_name='Single Attempt')),
                ('pass_mark', models.SmallIntegerField(blank=True, default=50, help_text='Percentage required to pass exam.', validators=[django.core.validators.MaxValueValidator(100)], verbose_name='Pass Mark')),
                ('created_at', models.DateField(auto_now_add=True)),
                ('updated_at', models.DateField(auto_now=True)),
                ('active', models.BooleanField(default=True)),
                ('courses', models.ManyToManyField(related_name='quizzes', to='exam.course')),
            ],
            options={
                'verbose_name': 'Quiz',
                'verbose_name_plural': 'Quizzes',
            },
        ),
        migrations.CreateModel(
            name='Resources',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('resource_name', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='Role',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='UserRolePrivileges',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('resource', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='role_privileges', to='exam.resources')),
            ],
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(max_length=255, null=True)),
                ('last_name', models.CharField(max_length=255, null=True)),
                ('role_id', models.IntegerField(null=True)),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='users', to='exam.customer')),
            ],
            options={
                'db_table': 'users',
            },
        ),
        migrations.CreateModel(
            name='UploadVideo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100)),
                ('slug', models.SlugField(blank=True, unique=True)),
                ('video', models.FileField(help_text='Valid video formats: mp4, mkv, wmv, 3gp, f4v, avi, mp3', upload_to='course_videos/', validators=[django.core.validators.FileExtensionValidator(['mp4', 'mkv', 'wmv', '3gp', 'f4v', 'avi', 'mp3'])])),
                ('summary', models.TextField(blank=True, null=True)),
                ('uploaded_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('courses', models.ManyToManyField(related_name='video_materials', to='exam.course')),
            ],
        ),
        migrations.CreateModel(
            name='UploadReadingMaterial',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100)),
                ('reading_content', models.TextField()),
                ('uploaded_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('courses', models.ManyToManyField(related_name='reading_materials', to='exam.course')),
            ],
        ),
        migrations.CreateModel(
            name='QuizAttemptHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('question_list_order', models.CharField(max_length=1024, validators=[django.core.validators.RegexValidator(re.compile('^\\d+(?:,\\d+)*\\Z'), code='invalid', message='Enter only digits separated by commas.')], verbose_name='Question Order')),
                ('unattempted_question', models.CharField(max_length=255)),
                ('incorrect_questions', models.CharField(blank=True, max_length=1024, validators=[django.core.validators.RegexValidator(re.compile('^\\d+(?:,\\d+)*\\Z'), code='invalid', message='Enter only digits separated by commas.')], verbose_name='Incorrect questions')),
                ('current_score', models.IntegerField(verbose_name='Current Score')),
                ('complete', models.BooleanField(default=False, verbose_name='Complete')),
                ('user_answers', models.TextField(blank=True, default='{}', verbose_name='User Answers')),
                ('start', models.DateTimeField(auto_now_add=True, verbose_name='Start')),
                ('end', models.DateTimeField(blank=True, null=True, verbose_name='End')),
                ('course', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='exam.course', verbose_name='Course')),
                ('enrolled_user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='exam.user')),
                ('quiz', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='exam.quiz', verbose_name='Quiz')),
            ],
            options={
                'permissions': (('view_sittings', 'Can see completed exams.'),),
            },
        ),
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('figure', models.ImageField(blank=True, help_text="Add an image for the question if it's necessary.", null=True, upload_to='uploads/%Y/%m/%d', verbose_name='Figure')),
                ('content', models.CharField(help_text='Enter the question text that you want displayed', max_length=1000, verbose_name='Question')),
                ('explanation', models.TextField(blank=True, help_text='Explanation to be shown after the question has been answered.', max_length=2000, verbose_name='Explanation')),
                ('choice_order', models.CharField(blank=True, choices=[('content', 'Content'), ('random', 'Random'), ('none', 'None')], help_text='The order in which multi choice choice options are displayed to the user', max_length=30, null=True, verbose_name='Choice Order')),
                ('active', models.BooleanField(default=False)),
                ('quizzes', models.ManyToManyField(related_name='questions', to='exam.quiz')),
            ],
            options={
                'verbose_name': 'Question',
                'verbose_name_plural': 'Questions',
            },
        ),
        migrations.CreateModel(
            name='CustomerResources',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='customer_resource', to='exam.customer')),
                ('resource', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='customer_resource', to='exam.resources')),
            ],
        ),
        migrations.CreateModel(
            name='CourseStructure',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order_number', models.PositiveIntegerField()),
                ('content_type', models.CharField(choices=[('reading', 'Reading Material'), ('video', 'Video'), ('quiz', 'Quiz')], max_length=10)),
                ('content_id', models.PositiveIntegerField()),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='course_structure', to='exam.course')),
            ],
            options={
                'ordering': ['order_number'],
            },
        ),
        migrations.CreateModel(
            name='CourseRegisterRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now=True)),
                ('active', models.BooleanField(default=True)),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='registered_costumer', to='exam.course')),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='registered_courses', to='exam.customer')),
            ],
        ),
        migrations.CreateModel(
            name='CourseEnrollment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('enrolled_at', models.DateTimeField(auto_now=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('active', models.BooleanField(default=True)),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='enrolled_courses', to='exam.course')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='enrollments', to='exam.user')),
            ],
        ),
        migrations.CreateModel(
            name='Choice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('choice', models.CharField(help_text='Enter the choice text that you want displayed', max_length=1000, verbose_name='Content')),
                ('correct', models.BooleanField(default=False, help_text='Is this a correct answer?', verbose_name='Correct')),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='exam.question', verbose_name='Question')),
            ],
            options={
                'verbose_name': 'Choice',
                'verbose_name_plural': 'Choices',
            },
        ),
    ]
