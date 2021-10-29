# Generated by Django 3.2.4 on 2021-10-26 19:26

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('logger', '0002_auto_20210625_1940'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='instocknagornaya',
            options={'ordering': ['-rating', '-timestamp'], 'verbose_name': 'Размеры', 'verbose_name_plural': 'Склад Нагорная'},
        ),
        migrations.CreateModel(
            name='InstockTimiryazevskaya',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('size', models.DecimalField(decimal_places=1, max_digits=3, verbose_name='размер')),
                ('count', models.PositiveSmallIntegerField(verbose_name='Количество')),
                ('timestamp', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='Обновлено')),
                ('rating', models.PositiveSmallIntegerField(default=0, verbose_name='Популярность')),
                ('code', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='logger.products', verbose_name='Код товара')),
            ],
            options={
                'verbose_name': 'Размеры',
                'verbose_name_plural': 'Склад Тимирязевская',
                'db_table': 'instock_timiryazevskaya',
                'ordering': ['-rating', '-timestamp'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='InstockTeplyStan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('size', models.DecimalField(decimal_places=1, max_digits=3, verbose_name='размер')),
                ('count', models.PositiveSmallIntegerField(verbose_name='Количество')),
                ('timestamp', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='Обновлено')),
                ('rating', models.PositiveSmallIntegerField(default=0, verbose_name='Популярность')),
                ('code', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='logger.products', verbose_name='Код товара')),
            ],
            options={
                'verbose_name': 'Размеры',
                'verbose_name_plural': 'Склад Тёплый Стан',
                'db_table': 'instock_teply_stan',
                'ordering': ['-rating', '-timestamp'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='InstockAltufevo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('size', models.DecimalField(decimal_places=1, max_digits=3, verbose_name='размер')),
                ('count', models.PositiveSmallIntegerField(verbose_name='Количество')),
                ('timestamp', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='Обновлено')),
                ('rating', models.PositiveSmallIntegerField(default=0, verbose_name='Популярность')),
                ('code', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='logger.products', verbose_name='Код товара')),
            ],
            options={
                'verbose_name': 'Размеры',
                'verbose_name_plural': 'Склад Алтуфьево',
                'db_table': 'instock_altufevo',
                'ordering': ['-rating', '-timestamp'],
                'abstract': False,
            },
        ),
    ]
