from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from .models import Product, Order, OrderItem
from django.contrib.auth.models import User
from django.contrib import messages
from django.db import transaction

# -------------------------
# Home & Product Views
# -------------------------
def home(request):
    products = Product.objects.all()
    return render(request, 'home.html', {'products': products})

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'product.html', {'product': product})

def product_list(request):
    products = Product.objects.all()
    return render(request, 'products.html', {'products': products})

# -------------------------
# Cart Views
# -------------------------
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = request.session.get('cart', {})
    
    current_qty = cart.get(str(product_id), 0)
    if product.stock > current_qty:
        cart[str(product_id)] = current_qty + 1
        request.session['cart'] = cart
        # Optional: message can be added here
    else:
        messages.error(request, f"Insufficient stock for {product.name}. Only {product.stock} available.")
        
    return redirect('cart')

def decrease_cart(request, product_id):
    cart = request.session.get('cart', {})
    if str(product_id) in cart:
        if cart[str(product_id)] > 1:
            cart[str(product_id)] -= 1
        else:
            del cart[str(product_id)]
        request.session['cart'] = cart
    return redirect('cart')

def remove_from_cart(request, product_id):
    cart = request.session.get('cart', {})
    if str(product_id) in cart:
        del cart[str(product_id)]
        request.session['cart'] = cart
    return redirect('cart')

def cart(request):
    cart = request.session.get('cart', {})
    items = []
    total_amount = 0

    for pid, quantity in cart.items():
        product = get_object_or_404(Product, id=pid)
        subtotal = product.price * quantity
        total_amount += subtotal
        items.append({'product': product, 'quantity': quantity, 'subtotal': subtotal})

    return render(request, 'cart.html', {'items': items, 'total_amount': total_amount})

# -------------------------
# Checkout & Success Views
# -------------------------
@login_required
def checkout(request):
    cart = request.session.get('cart', {})
    if not cart:
        return redirect('home')

    items = []
    total_amount = 0
    for pid, quantity in cart.items():
        product = get_object_or_404(Product, id=pid)
        subtotal = product.price * quantity
        total_amount += subtotal
        items.append({'product': product, 'quantity': quantity, 'subtotal': subtotal})

    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')
        
        with transaction.atomic():
            # Final stock check
            for item in items:
                product = Product.objects.select_for_update().get(id=item['product'].id)
                if product.stock < item['quantity']:
                    messages.error(request, f"Sorry, {product.name} just went out of stock.")
                    return redirect('cart')

            # Create Order
            order = Order.objects.create(
                user=request.user,
                total_price=total_amount,
                payment_method=payment_method,
                payment_status='Paid'
            )

            # Create OrderItems and deduct stock
            for item in items:
                p = item['product']
                qty = item['quantity']
                
                OrderItem.objects.create(
                    order=order,
                    product=p,
                    quantity=qty,
                    price=p.price
                )
                
                # Update stock
                p.stock -= qty
                p.save()

        request.session['cart'] = {}  # clear cart
        return redirect('checkout_success', order_id=order.id)

    return render(request, 'checkout.html', {'items': items, 'total_amount': total_amount})

@login_required
def checkout_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'success.html', {'order': order})

# -------------------------
# Authentication Views
# -------------------------
def register(request):
    if request.method == 'POST':
        User.objects.create_user(
            username=request.POST['username'],
            password=request.POST['password'],
            email=request.POST.get('email', '')
        )
        return redirect('login')
    return render(request, 'register.html')

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

@login_required
def logout_view(request):
    auth_logout(request)
    return redirect('home')
