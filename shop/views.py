from decimal import Decimal
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from django.http import JsonResponse

from .forms import CheckoutForm, RegisterForm
from .models import Product, Order, OrderItem

def _get_cart(session):
    return session.setdefault('cart', {})


def _cart_products(cart):
    product_ids = cart.keys()
    products = Product.objects.filter(id__in=product_ids)
    items = []
    total = Decimal('0.00')

    for product in products:
        quantity = cart[str(product.id)]
        subtotal = product.price * quantity
        total += subtotal
        items.append({
            'product': product,
            'quantity': quantity,
            'subtotal': subtotal,
        })

    return items, total


def home(request):
    products = Product.objects.all()
    return render(request, 'shop/home.html', {'products': products})


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    return render(request, 'shop/product_detail.html', {'product': product})


def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = _get_cart(request.session)
    product_key = str(product.id)

    if product.stock < 1:
        messages.error(request, 'This product is out of stock.')
        return redirect('product_detail', slug=product.slug)

    cart[product_key] = cart.get(product_key, 0) + 1
    request.session.modified = True
    messages.success(request, f'{product.name} added to cart.')
    return redirect('cart')


def update_cart(request, product_id):
    cart = _get_cart(request.session)
    product = get_object_or_404(Product, id=product_id)
    quantity = int(request.POST.get('quantity', 1))

    if quantity <= 0:
        cart.pop(str(product.id), None)
    else:
        cart[str(product.id)] = min(quantity, product.stock)

    request.session.modified = True
    return redirect('cart')


def remove_from_cart(request, product_id):
    cart = _get_cart(request.session)
    cart.pop(str(product_id), None)
    request.session.modified = True
    messages.info(request, 'Item removed from cart.')
    return redirect('cart')


def cart_view(request):
    cart = request.session.get('cart', {})
    items, total = _cart_products(cart)
    return render(request, 'shop/cart.html', {'items': items, 'total': total})


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully.')
            return redirect('home')
    else:
        form = RegisterForm()
    return render(request, 'registration/register.html', {'form': form})


def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            return redirect('home')

    return render(request, 'registration/login.html')

@login_required
def checkout(request):
    print("USER:", request.user)
    print("AUTH:", request.user.is_authenticated)
    
    cart = request.session.get('cart', {})
    items, total = _cart_products(cart)

    if not items:
        messages.warning(request, 'Your cart is empty.')
        return redirect('home')

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            order = Order.objects.create(
                user=request.user,
                full_name=form.cleaned_data['full_name'],
                email=form.cleaned_data['email'],
                address=form.cleaned_data['address'],
                city=form.cleaned_data['city'],
                postal_code=form.cleaned_data['postal_code'],
                paid=True,
                total_amount=total,
            )
            
            print("ORDER ID CREATED:", order.id)
            print("ORDER USER:", order.user) 

            for item in items:
                product = item['product']
                quantity = item['quantity']
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity,
                    price=product.price,
                )
                product.stock = max(product.stock - quantity, 0)
                product.save()

            request.session['cart'] = {}
            request.session.modified = True
            messages.success(request, 'Order placed successfully.')
            return redirect('order_success', order_id=order.id)
    else:
        initial = {}
        if request.user.is_authenticated:
            initial['email'] = request.user.email
            initial['full_name'] = request.user.username
        form = CheckoutForm(initial=initial)

    return render(request, 'shop/checkout.html', {'form': form, 'items': items, 'total': total})

@login_required
def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'shop/order_success.html', {'order': order})

@login_required
def orders(request):
    orders = Order.objects.all().order_by('-id')
    return render(request, 'shop/orders.html', {'orders': orders})