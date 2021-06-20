from django.contrib import admin
from .models import Products, Prices, InstockNagornaya


class ShoesAdmin(admin.ModelAdmin):
    list_display = ('code', 'model', 'year', 'use', 'rating')
    list_display_links = ('model',)
    search_fields = ('code', 'model')


class PricesAdmin(admin.ModelAdmin):
    list_display = ('code', 'price', 'timestamp', 'rating')
    list_display_links = ('code',)
    search_fields = ('code', 'price', 'timestamp')


class InstockNagornayaAdmin(admin.ModelAdmin):
    list_display = ('code', 'size', 'count', 'timestamp', 'rating')
    list_display_links = ('code',)
    search_fields = ('code', 'size', 'count', 'timestamp')


admin.site.register(Products, ShoesAdmin)
admin.site.register(Prices, PricesAdmin)
admin.site.register(InstockNagornaya, InstockNagornayaAdmin)