from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from .models import Product, Order, OrderItem
from django.contrib.auth.models import User

# Home page - list of products
def home(request):
    products = Product.objects.all()
    return render(request, 'home.html', {'products': products})

# Product detail page
def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'product.html', {'product': product})

# Add product to cart (session-based)
def add_to_cart(request, product_id):
    cart = request.session.get('cart', {})
    cart[str(product_id)] = cart.get(str(product_id), 0) + 1
    request.session['cart'] = cart
    return redirect('cart')

# View cart
def cart(request):
    cart = request.session.get('cart', {})
    items = []
    total = 0

    for pid, quantity in cart.items():
        product = get_object_or_404(Product, id=pid)
        subtotal = product.price * quantity
        total += subtotal
        items.append({'product': product, 'quantity': quantity, 'subtotal': subtotal})

    return render(request, 'cart.html', {'items': items, 'total': total})

# Checkout - create order
@login_required
def checkout(request):
    cart = request.session.get('cart', {})
    if not cart:
        return redirect('home')

    total = 0
    order = Order.objects.create(user=request.user, total_price=0)

    for pid, quantity in cart.items():
        product = get_object_or_404(Product, id=pid)
        OrderItem.objects.create(order=order, product=product, quantity=quantity)
        total += product.price * quantity

    order.total_price = total
    order.save()
    request.session['cart'] = {}  # clear cart

    return render(request, 'success.html', {'order': order})

# Register new user
def register(request):
    if request.method == 'POST':
        User.objects.create_user(
            username=request.POST['username'],
            password=request.POST['password'],
            email=request.POST.get('email', '')
        )
        return redirect('login')
    return render(request, 'register.html')

# Login
def login_view(request):
    if request.method == 'POST':
        user = authenticate(
            username=request.POST['username'],
            password=request.POST['password']
        )
        if user:
            auth_login(request, user)
            return redirect('home')
        else:
            return render(request, 'login.html', {'error': 'Invalid credentials'})
    return render(request, 'login.html')

# Logout
def logout_view(request):
    auth_logout(request)
    return redirect('home')
