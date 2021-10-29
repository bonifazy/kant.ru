from django.db import models


class Products(models.Model):
    code = models.IntegerField(null=False, primary_key=True, unique=True, verbose_name='Код товара')
    brand = models.CharField(max_length=20, verbose_name='Бренд')
    model = models.CharField(max_length=50, verbose_name='Модель')
    url = models.URLField(null=False, blank=False, unique=True, max_length=100, verbose_name='Ссылка')
    img = models.URLField(max_length=150, verbose_name='Картинка')
    age = models.CharField(max_length=20, verbose_name='Возраст')
    gender = models.CharField(max_length=20, verbose_name='Пол')
    year = models.IntegerField(blank=True, verbose_name='Год')
    use = models.CharField(max_length=20, verbose_name='Использование')
    pronation = models.CharField(max_length=30, verbose_name='Пронация')
    article = models.CharField(max_length=30, verbose_name='Артикул')
    season = models.CharField(max_length=30, verbose_name='Сезон')
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='Обновлено')
    rating = models.PositiveSmallIntegerField(default=0, verbose_name='Рейтинг')

    def __str__(self):
        return '{}: {}'.format(self.code, self.model)

    class Meta:
        db_table = 'products'
        verbose_name_plural = 'Кроссовки'
        verbose_name = 'Товар'
        ordering = ['-rating']


class Prices(models.Model):
    code = models.ForeignKey(Products, on_delete=models.CASCADE, verbose_name='Код товара')
    price = models.PositiveSmallIntegerField(null=False, verbose_name='Стоимость')
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='Обновлено')
    rating = models.PositiveSmallIntegerField(default=0, verbose_name='Популярность')

    def __str__(self):
        return '{}'.format(self.code)

    class Meta:
        db_table = 'prices'
        verbose_name_plural = 'Цены'
        verbose_name = 'Товар'
        ordering = ['-rating', '-timestamp']


class Kant(models.Model):
    code = models.ForeignKey(Products, on_delete=models.CASCADE, verbose_name='Код товара')
    size = models.DecimalField(max_digits=3, decimal_places=1, verbose_name='размер')
    count = models.PositiveSmallIntegerField(verbose_name='Количество')
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='Обновлено')
    rating = models.PositiveSmallIntegerField(default=0, verbose_name='Популярность')

    def __str__(self):
        return '{}'.format(self.code)

    class Meta:
        abstract = True


class InstockNagornaya(Kant):

    class Meta(Kant.Meta):
        db_table = 'instock_nagornaya'
        verbose_name_plural = 'Склад Нагорная'
        verbose_name = 'Размеры'
        ordering = ['-rating', '-timestamp']


class InstockTimiryazevskaya(Kant):

    class Meta(Kant.Meta):
        db_table = 'instock_timiryazevskaya'
        verbose_name_plural = 'Склад Тимирязевская'
        verbose_name = 'Размеры'
        ordering = ['-rating', '-timestamp']


class InstockAltufevo(Kant):

    class Meta(Kant.Meta):
        db_table = 'instock_altufevo'
        verbose_name_plural = 'Склад Алтуфьево'
        verbose_name = 'Размеры'
        ordering = ['-rating', '-timestamp']


class InstockTeplyStan(Kant):

    class Meta(Kant.Meta):
        db_table = 'instock_teply_stan'
        verbose_name_plural = 'Склад Тёплый Стан'
        verbose_name = 'Размеры'
        ordering = ['-rating', '-timestamp']
