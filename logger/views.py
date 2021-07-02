from django.shortcuts import render
from .models import Products, Prices, InstockNagornaya


def index(request):
    shoes = Products.objects.all()[:50]
    # add props
    for shoe in shoes:
        price_obj = Prices.objects.get(code_id=shoe.code)
        shoe.price, shoe.price_time, shoe.price_rate = price_obj.price, price_obj.timestamp, price_obj.rating
        nag = InstockNagornaya.objects.all().order_by('-rating')
        shoe.size, shoe.count, shoe.nag_time, shoe.nag_rate = nag.count, nag.timestamp, nag.rating
    templates = 'display/index.html'
    context = {
        'shoes': shoes,
    }

    return render(request, templates, context)
