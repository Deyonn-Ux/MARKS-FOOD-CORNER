import re
import secrets
import string
from decimal import Decimal, InvalidOperation
from pathlib import Path

from django.db.models import Q, Sum
from django.conf import settings
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.utils.timezone import localtime
from django.contrib.auth.models import User
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LoginView

from .models import Food, Category, Order, OrderItem, Profile, Review, PromoCode


DELIVERY_FEE = Decimal('50.00')
TRACKABLE_STATUSES = ['Pending', 'Preparing', 'Ready', 'On the way']


def user_is_delivery(user):
    return user.groups.filter(name='Delivery').exists()


def user_can_view_order(user, order):
    return user.is_staff or order.customer_id == user.id or user_is_delivery(user)


class RoleLoginView(LoginView):
    template_name = 'login.html'

    def get_success_url(self):
        redirect_to = self.get_redirect_url()
        if redirect_to:
            return redirect_to
        if self.request.user.is_staff:
            return '/dashboard/'
        if user_is_delivery(self.request.user):
            return '/delivery/'
        return '/'


def service_worker(request):
    service_worker_path = Path(settings.BASE_DIR) / 'static' / 'service-worker.js'
    response = FileResponse(open(service_worker_path, 'rb'), content_type='application/javascript')
    response['Service-Worker-Allowed'] = '/'
    response['Cache-Control'] = 'no-cache'
    return response


def normalize_cart(cart):
    normalized = {}
    for food_id, value in cart.items():
        if isinstance(value, dict):
            normalized[food_id] = {
                'quantity': max(1, min(int(value.get('quantity', 1)), 99)),
                'special_instructions': str(value.get('special_instructions', '')).strip(),
                'flavor_choice': str(value.get('flavor_choice', '')).strip(),
                'unavailable_action': str(value.get('unavailable_action', 'remove')).strip() or 'remove'
            }
        else:
            try:
                quantity = int(value)
            except (TypeError, ValueError):
                quantity = 1
            normalized[food_id] = {
                'quantity': max(1, min(quantity, 99)),
                'special_instructions': '',
                'unavailable_action': 'remove'
            }
    return normalized


# 🏠 HOME
def home(request):
    cart = normalize_cart(request.session.get('cart', {}))
    request.session['cart'] = cart
    cart_count = sum(item['quantity'] for item in cart.values())
    profile = None
    categories = Category.objects.all().prefetch_related('food_set')
    featured_categories = []

    is_delivery = False
    if request.user.is_authenticated:
        profile, created = Profile.objects.get_or_create(user=request.user)
        is_delivery = request.user.groups.filter(name='Delivery').exists()

    featured_limits = {
        'meals': 5,
        'meal': 5,
        'food': 5,
        'foods': 5,
        'drinks': 3,
        'drink': 3,
        'cakes': 2,
        'cake': 2,
        'snacks': 3,
        'snack': 3,
    }

    for category in categories:
        foods = [food for food in category.food_set.all() if food.image]
        if not foods:
            foods = list(category.food_set.all())

        category_name = category.name.lower()
        image_limit = 2
        for key, limit in featured_limits.items():
            if key in category_name:
                image_limit = limit
                break

        featured_foods = foods[:image_limit]

        if featured_foods:
            featured_categories.append({
                'category': category,
                'foods': featured_foods,
            })

    return render(request, 'home.html', {
        'categories': categories,
        'featured_categories': featured_categories,
        'cart_count': cart_count,
        'profile': profile,
        'is_delivery': is_delivery,
    })


# 🔐 REGISTER
def register(request):
    def new_captcha_code():
        alphabet = string.ascii_uppercase + string.digits
        code = ''.join(secrets.choice(alphabet) for _ in range(6))
        request.session['register_captcha'] = code
        return code

    captcha_code = request.session.get('register_captcha') or new_captcha_code()

    if request.method == "POST":
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        password2 = request.POST.get('password2', '')
        captcha_answer = request.POST.get('captcha_answer', '').strip().upper().replace(' ', '')

        if not username or not email or not password or not password2 or not captcha_answer:
            messages.error(request, "⚠ Please fill in all fields.")
            return redirect('register')

        if captcha_answer != captcha_code:
            new_captcha_code()
            messages.error(request, "âš  Verification code is incorrect. Please try again.")
            return redirect('register')

        if len(username) > 150:
            messages.error(request, "⚠ Username must be 150 characters or fewer.")
            return redirect('register')

        if User.objects.filter(username=username).exists():
            messages.error(request, "⚠ Username already exists.")
            return redirect('register')

        if User.objects.filter(email=email).exists():
            messages.error(request, "⚠ An account with that email already exists.")
            return redirect('register')

        if password != password2:
            messages.error(request, "⚠ Passwords do not match. Enter the same password twice.")
            return redirect('register')

        if len(password) < 8:
            messages.error(request, "⚠ Password should be at least 8 characters long.")
            return redirect('register')

        user = User.objects.create_user(username=username, email=email, password=password)
        Profile.objects.create(user=user)
        request.session.pop('register_captcha', None)
        login(request, user)

        messages.success(request, "✅ Account created successfully!")
        return redirect('home')

    return render(request, 'register.html', {
        'captcha_code': captcha_code,
    })


@login_required
def profile(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    password_form = PasswordChangeForm(request.user)

    if request.method == "POST":
        form_type = request.POST.get("form_type")

        if form_type == "profile":
            request.user.first_name = request.POST.get("first_name", "").strip()
            request.user.last_name = request.POST.get("last_name", "").strip()
            request.user.email = request.POST.get("email", "").strip()

            if request.FILES.get("picture"):
                profile.picture = request.FILES["picture"]

            request.user.save()
            profile.save()
            messages.success(request, "Profile updated successfully!")
            return redirect("profile")

        if form_type == "password":
            password_form = PasswordChangeForm(request.user, request.POST)

            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, "Password changed successfully!")
                return redirect("profile")

            messages.error(request, "Please check your password fields.")

    return render(request, 'profile.html', {
        'profile': profile,
        'password_form': password_form
    })


# ➕ ADD TO CART
def add(request, id):
    food = get_object_or_404(Food, id=id)
    if not food.is_available:
        messages.warning(request, "This item is currently sold out.")
        return redirect('/')

    cart = normalize_cart(request.session.get('cart', {}))

    try:
        quantity = int(request.POST.get('quantity') or request.GET.get('quantity') or 1)
    except ValueError:
        quantity = 1
    quantity = max(1, min(quantity, 99))
    special_instructions = request.POST.get('special_instructions', '').strip()
    flavor_choice_values = request.POST.getlist('flavor_choice')
    flavor_choice = ', '.join([value.strip() for value in flavor_choice_values if value.strip()])
    unavailable_action = request.POST.get('unavailable_action', 'remove').strip() or 'remove'

    if food.name.strip().lower() == 'french fries' and not flavor_choice:
        messages.error(request, "Please choose at least one flavor for French Fries.")
        return redirect('/')

    existing = cart.get(str(id), {'quantity': 0, 'special_instructions': '', 'flavor_choice': '', 'unavailable_action': 'remove'})
    cart[str(id)] = {
        'quantity': existing['quantity'] + quantity,
        'special_instructions': special_instructions,
        'flavor_choice': flavor_choice,
        'unavailable_action': unavailable_action,
    }

    request.session['cart'] = cart

    messages.success(request, "✅ Item added to order!")

    next_page = request.GET.get('next')

    if next_page == 'payment':
        return redirect('/checkout/')

    if next_page == 'cart':
        return redirect('/cart/')

    return redirect('/')


# ❌ REMOVE FROM CART
def remove_from_cart(request, id):
    cart = normalize_cart(request.session.get('cart', {}))

    if str(id) in cart:
        if cart[str(id)]['quantity'] > 1:
            cart[str(id)]['quantity'] -= 1
        else:
            del cart[str(id)]

        messages.warning(request, "❌ Item removed from order")

    request.session['cart'] = cart
    return redirect('/cart/')


# 🛒 CART PAGE
def cart(request):
    cart = normalize_cart(request.session.get('cart', {}))
    request.session['cart'] = cart

    foods = Food.objects.filter(id__in=cart.keys(), is_available=True)
    available_ids = {str(food.id) for food in foods}
    for food_id in set(cart.keys()) - available_ids:
        cart.pop(food_id, None)
    request.session['cart'] = cart

    cart_items = []
    total = 0

    for f in foods:
        item = cart[str(f.id)]
        quantity = item.get('quantity', 1)
        subtotal = f.price * quantity
        total += subtotal

        cart_items.append({
            'food': f,
            'quantity': quantity,
            'subtotal': subtotal,
            'special_instructions': item.get('special_instructions', ''),
            'flavor_choice': item.get('flavor_choice', ''),
            'unavailable_action': item.get('unavailable_action', 'remove'),
        })

    delivery_fee = DELIVERY_FEE if total else Decimal('0.00')
    grand_total = total + delivery_fee

    return render(request, 'cart.html', {
        'cart_items': cart_items,
        'total': total,
        'delivery_fee': delivery_fee,
        'grand_total': grand_total,
    })


# 🍔 RECOMMENDATION
def recommend(request):
    recommends = Food.objects.filter(is_available=True).order_by('?')[:3]

    return render(request, 'recommend.html', {
        'recommends': recommends
    })


# 💳 CHECKOUT (PROTECTED 🔐)
@login_required
def checkout(request):
    if request.user.is_staff:
        messages.warning(request, "Admin users cannot place orders.")
        return redirect('home')

    cart = normalize_cart(request.session.get('cart', {}))
    request.session['cart'] = cart
    available_food_ids = {
        str(food_id)
        for food_id in Food.objects.filter(id__in=cart.keys(), is_available=True).values_list('id', flat=True)
    }
    unavailable_ids = set(cart.keys()) - available_food_ids
    for food_id in unavailable_ids:
        cart.pop(food_id, None)
    request.session['cart'] = cart
    foods = Food.objects.filter(id__in=cart.keys(), is_available=True)

    subtotal = sum(f.price * cart[str(f.id)]['quantity'] for f in foods)
    delivery_fee = DELIVERY_FEE
    discount = Decimal('0.00')
    total = subtotal + delivery_fee

    # 🚫 prevent empty checkout
    if not cart:
        messages.warning(request, "⚠ No items in cart!")
        return redirect('home')

    if request.method == "POST":
        payment = request.POST.get("payment")
        service_type = request.POST.get("service_type", "Delivery")
        phone = request.POST.get("contact_phone", "").strip()
        address = request.POST.get("delivery_address", "").strip()
        special_instructions = request.POST.get("special_instructions", "").strip()
        pickup_time = request.POST.get("pickup_time", "").strip()
        payment_reference = request.POST.get("payment_reference", "").strip()
        promo_code = request.POST.get("promo_code", "").strip().upper()

        delivery_fee = DELIVERY_FEE if service_type == 'Delivery' else Decimal('0.00')
        total = subtotal + delivery_fee

        if promo_code:
            code = PromoCode.objects.filter(code__iexact=promo_code, active=True).first()
            if code:
                discount = (subtotal * code.discount).quantize(Decimal('0.01'))
                total = subtotal + delivery_fee - discount
            else:
                messages.error(request, "Invalid promo code.")
                return redirect('checkout')

        if not payment or not phone or (service_type == 'Delivery' and not address):
            messages.error(request, "Please complete payment, contact number, and delivery address for delivery orders.")
            return redirect('checkout')

        if service_type == 'Pickup' and not pickup_time:
            messages.error(request, "Please choose a pickup time for pickup orders.")
            return redirect('checkout')

        payment_status = 'Unpaid'
        customer_latitude = request.POST.get("customer_latitude", "").strip()
        customer_longitude = request.POST.get("customer_longitude", "").strip()

        if payment == 'GCash':
            payment_status = 'Pending proof'
            payment_reference = re.sub(r'\D', '', payment_reference)
            payment_proof = request.FILES.get("payment_proof")

            if not payment_reference or not payment_proof:
                messages.error(request, "For GCash, please enter the reference number and upload the payment screenshot.")
                return redirect('checkout')

            if not re.fullmatch(r'\d{13}', payment_reference):
                messages.error(request, "Please enter the 13-digit GCash reference number from your receipt.")
                return redirect('checkout')

            if Order.objects.filter(payment_method='GCash', payment_reference=payment_reference).exclude(payment_status='Failed').exists():
                messages.error(request, "This GCash reference number was already used. Please check your receipt or contact support.")
                return redirect('checkout')

        if service_type == 'Delivery':
            if not customer_latitude or not customer_longitude:
                messages.error(request, "Please share your delivery location so the rider can track your order accurately.")
                return redirect('checkout')
            try:
                customer_lat = Decimal(customer_latitude)
                customer_lon = Decimal(customer_longitude)
            except InvalidOperation:
                messages.error(request, "Could not read your location. Please try again.")
                return redirect('checkout')
        else:
            customer_lat = None
            customer_lon = None
            address = ''

        order = Order.objects.create(
            customer=request.user,
            total=total,
            subtotal=subtotal,
            delivery_fee=delivery_fee,
            discount=discount,
            promo_code=promo_code,
            payment_method=payment,
            service_type=service_type,
            payment_status=payment_status,
            payment_reference=payment_reference,
            contact_phone=phone,
            delivery_address=address,
            customer_latitude=customer_lat,
            customer_longitude=customer_lon,
            delivery_note=special_instructions,
            pickup_time=pickup_time,
            payment_proof=request.FILES.get("payment_proof"),
        )

        for f in foods:
            OrderItem.objects.create(
                order=order,
                food=f,
                quantity=cart[str(f.id)]['quantity'],
                flavor_choice=cart[str(f.id)].get('flavor_choice', ''),
            )

        request.session['cart'] = {}

        messages.success(request, "🎉 Order placed successfully!")
        return redirect('track_order', order.id)

    return render(request, 'checkout.html', {
        'subtotal': subtotal,
        'delivery_fee': delivery_fee,
        'discount': discount,
        'total': total,
    })


@login_required
def verify_promo_code(request):
    if request.user.is_staff:
        return JsonResponse({'valid': False, 'message': 'Admin users cannot place orders.'}, status=403)

    cart = normalize_cart(request.session.get('cart', {}))
    foods = Food.objects.filter(id__in=cart.keys(), is_available=True)
    subtotal = sum(f.price * cart[str(f.id)]['quantity'] for f in foods)
    service_type = request.GET.get('service_type', 'Delivery')
    delivery_fee = DELIVERY_FEE if service_type == 'Delivery' else Decimal('0.00')
    code_text = request.GET.get('code', '').strip().upper()

    if not cart or subtotal <= 0:
        return JsonResponse({'valid': False, 'message': 'Your cart is empty.'})

    if not code_text:
        total = subtotal + delivery_fee
        return JsonResponse({
            'valid': False,
            'message': 'Please enter a promo code.',
            'subtotal': float(subtotal),
            'delivery_fee': float(delivery_fee),
            'discount': 0.0,
            'total': float(total),
        })

    promo = PromoCode.objects.filter(code__iexact=code_text, active=True).first()
    if not promo:
        total = subtotal + delivery_fee
        return JsonResponse({
            'valid': False,
            'message': 'Invalid or inactive promo code.',
            'subtotal': float(subtotal),
            'delivery_fee': float(delivery_fee),
            'discount': 0.0,
            'total': float(total),
        })

    discount = (subtotal * promo.discount).quantize(Decimal('0.01'))
    total = subtotal + delivery_fee - discount
    return JsonResponse({
        'valid': True,
        'message': f'Promo {promo.code} applied.',
        'code': promo.code,
        'subtotal': float(subtotal),
        'delivery_fee': float(delivery_fee),
        'discount': float(discount),
        'total': float(total),
    })


# 🧾 RECEIPT
@login_required
def receipt(request, id):
    order = get_object_or_404(Order, id=id)
    if not user_can_view_order(request.user, order):
        raise Http404

    items = OrderItem.objects.filter(order=order)

    new_items = []
    for i in items:
        subtotal = i.food.price * i.quantity
        new_items.append({
            'food': i.food,
            'quantity': i.quantity,
            'subtotal': subtotal
        })

    return render(request, 'receipt.html', {
        'order': order,
        'items': new_items
    })


# Dashboard redirects users to the right role-specific view.
@login_required
def dashboard(request):
    if user_is_delivery(request.user) and not request.user.is_staff:
        return redirect('delivery_dashboard')
    if not request.user.is_staff:
        return redirect('home')

    total_sales = Order.objects.aggregate(Sum('total'))['total__sum'] or 0
    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(status='Pending').count()
    active_deliveries = Order.objects.filter(status='On the way').count()
    paid_orders = Order.objects.filter(payment_status='Paid').count()

    orders = Order.objects.all().order_by('-created')[:5]

    labels = [o.created.strftime("%H:%M") for o in orders]
    data = [float(o.total) for o in orders]

    return render(request, 'dashboard.html', {
        'sales': total_sales,
        'orders': total_orders,
        'pending_orders': pending_orders,
        'active_deliveries': active_deliveries,
        'paid_orders': paid_orders,
        'labels': labels,
        'data': data
    })


@login_required
def track_order(request, id):
    order = get_object_or_404(Order, id=id)
    if not user_can_view_order(request.user, order):
        raise Http404

    if order.status not in TRACKABLE_STATUSES:
        messages.warning(request, "This order is no longer trackable. Please use My Orders for order history.")
        return redirect('my_orders')

    items = OrderItem.objects.filter(order=order).select_related('food')
    return render(request, 'track_order.html', {
        'order': order,
        'items': items
    })


@login_required
def tracking_api(request, id):
    order = get_object_or_404(Order, id=id)
    if not user_can_view_order(request.user, order):
        raise Http404

    return JsonResponse({
        'id': order.id,
        'status': order.status,
        'location': order.location_label,
        'courier': order.courier_name,
        'latitude': float(order.rider_latitude),
        'longitude': float(order.rider_longitude),
        'customer_latitude': float(order.customer_latitude) if order.customer_latitude is not None else None,
        'customer_longitude': float(order.customer_longitude) if order.customer_longitude is not None else None,
        'estimated_minutes': order.estimated_minutes,
        'payment_status': order.payment_status,
        'progress': order.tracking_percent,
        'updated': localtime(order.updated).strftime('%b %d, %Y %I:%M %p'),
    })


@login_required
def order_status_feed(request):
    if request.user.is_staff or user_is_delivery(request.user):
        return JsonResponse({'orders': []})

    orders = (
        Order.objects
        .filter(customer=request.user)
        .exclude(status__in=['Completed', 'Cancelled'])
        .order_by('-created')[:10]
    )
    return JsonResponse({
        'orders': [
            {
                'id': order.id,
                'status': order.status,
                'payment_status': order.payment_status,
                'updated': order.updated.isoformat(),
            }
            for order in orders
        ]
    })


@login_required
def my_orders(request):
    orders = Order.objects.filter(customer=request.user).order_by('-created')
    return render(request, 'my_orders.html', {
        'order_history': orders,
        'trackable_statuses': TRACKABLE_STATUSES,
    })


@login_required
def track_orders(request):
    if request.user.is_staff:
        return redirect('manage_orders')
    if user_is_delivery(request.user):
        current_orders = (
            Order.objects
            .filter(service_type='Delivery')
            .filter(Q(payment_method='Cash') | Q(payment_status='Paid'))
            .exclude(status__in=['Delivered', 'Completed', 'Cancelled'])
            .order_by('-created')
        )
        history_orders = (
            Order.objects
            .filter(service_type='Delivery', status__in=['Delivered', 'Completed'])
            .order_by('-updated')[:20]
        )
        return render(request, 'delivery_dashboard.html', {
            'orders': current_orders,
            'history_orders': history_orders,
        })
    orders = Order.objects.filter(customer=request.user, status__in=TRACKABLE_STATUSES).order_by('-created')
    return render(request, 'track_orders.html', {
        'current_orders': orders,
    })


@login_required
@user_passes_test(user_is_delivery)
def delivery_order(request, id):
    order = get_object_or_404(Order, id=id, service_type='Delivery')
    items = OrderItem.objects.filter(order=order).select_related('food')
    return render(request, 'delivery_order.html', {
        'order': order,
        'items': items,
    })


@login_required
@user_passes_test(user_is_delivery)
def delivery_update_order(request, id):
    order = get_object_or_404(Order, id=id, service_type='Delivery')
    if request.method != 'POST':
        return redirect('delivery_order', id=order.id)

    status = request.POST.get('status')
    if status in dict(Order.STATUS_CHOICES):
        if status == 'Delivered' and not order.delivery_proof:
            messages.error(request, f"Order #{order.id} needs rider delivery proof before it can be marked Delivered.")
            return redirect('manage_orders')
        order.status = status

    order.location_label = request.POST.get('location_label', order.location_label).strip() or order.location_label
    order.courier_name = request.POST.get('courier_name', order.courier_name).strip() or order.courier_name
    try:
        order.estimated_minutes = max(0, int(request.POST.get('estimated_minutes', order.estimated_minutes)))
    except (ValueError, TypeError):
        pass

    latitude = request.POST.get('rider_latitude', '').strip()
    longitude = request.POST.get('rider_longitude', '').strip()
    if latitude:
        order.rider_latitude = latitude
    if longitude:
        order.rider_longitude = longitude

    delivery_proof = request.FILES.get('delivery_proof')
    wants_delivered = request.POST.get('mark_delivered') or order.status == 'Delivered'

    if wants_delivered:
        if not delivery_proof and not order.delivery_proof:
            messages.error(request, f"Please upload delivery proof before marking order #{order.id} as delivered.")
            if request.POST.get('next') == 'dashboard':
                return redirect('delivery_dashboard')
            return redirect('delivery_order', id=order.id)
        order.status = 'Delivered'

    if delivery_proof:
        order.delivery_proof = delivery_proof

    order.save()

    messages.success(request, f"Order #{order.id} updated.")
    if request.POST.get('next') == 'dashboard':
        return redirect('delivery_dashboard')
    return redirect('delivery_order', id=order.id)


@login_required
def review_order(request, id):
    order = get_object_or_404(Order, id=id, customer=request.user)
    if order.status not in ['Delivered', 'Completed']:
        messages.warning(request, "You can review your order after it is delivered.")
        return redirect('track_order', id=order.id)

    if hasattr(order, 'review'):
        messages.info(request, "You already reviewed this order.")
        return redirect('my_orders')

    if request.method == 'POST':
        try:
            rating = int(request.POST.get('rating', 5))
        except ValueError:
            rating = 5
        rating = max(1, min(rating, 5))
        Review.objects.create(
            order=order,
            customer=request.user,
            rating=rating,
            comment=request.POST.get('comment', '').strip()
        )
        messages.success(request, "Thank you for your review!")
        return redirect('my_orders')

    return render(request, 'review_order.html', {'order': order})


@login_required
def cancel_order(request, id):
    order = get_object_or_404(Order, id=id, customer=request.user)
    if request.method != 'POST':
        return redirect('track_order', id=order.id)

    if order.status in ['Delivered', 'Completed', 'Cancelled']:
        messages.warning(request, "This order cannot be cancelled.")
        return redirect('track_order', id=order.id)

    order.status = 'Cancelled'
    order.save()
    messages.success(request, f"Order #{order.id} has been cancelled.")

    next_page = request.POST.get('next', 'my_orders')
    if next_page == 'track':
        return redirect('track_order', id=order.id)
    return redirect('my_orders')


@login_required
@user_passes_test(lambda user: user.is_staff)
def manage_orders(request):
    status = request.GET.get('status', '')
    orders = Order.objects.select_related('customer').order_by('-created')
    if status:
        orders = orders.filter(status=status)

    counts = {
        key: Order.objects.filter(status=key).count()
        for key, label in Order.STATUS_CHOICES
    }

    return render(request, 'manage_orders.html', {
        'orders': orders,
        'counts': counts,
        'status': status,
        'status_choices': Order.STATUS_CHOICES,
    })


@login_required
@user_passes_test(lambda user: user.is_staff)
def update_order(request, id):
    order = get_object_or_404(Order, id=id)
    if request.method != 'POST':
        return redirect('manage_orders')

    status = request.POST.get('status')
    if status in dict(Order.STATUS_CHOICES):
        order.status = status

    order.location_label = request.POST.get('location_label', order.location_label).strip() or order.location_label
    order.courier_name = request.POST.get('courier_name', order.courier_name).strip() or order.courier_name
    order.payment_status = request.POST.get('payment_status', order.payment_status)

    try:
        order.estimated_minutes = max(0, int(request.POST.get('estimated_minutes', order.estimated_minutes)))
    except ValueError:
        pass

    latitude = request.POST.get('rider_latitude', '').strip()
    longitude = request.POST.get('rider_longitude', '').strip()
    if latitude:
        order.rider_latitude = latitude
    if longitude:
        order.rider_longitude = longitude

    order.save()
    messages.success(request, f"Order #{order.id} updated.")
    return redirect('manage_orders')

def about_us(request):
    food_images = [
        food.image.url
        for food in Food.objects.filter(image__isnull=False).exclude(image='').order_by('id')[:12]
    ]
    if not food_images:
        food_images = [
            '/media/foods/FOOD_1.webp',
            '/media/foods/FOOD_2.webp',
            '/media/foods/FOOD_3.webp',
            '/media/foods/HALOHALO.jfif',
            '/media/foods/DRINKS_1.webp',
        ]
    return render(request, 'about.html', {'food_images': food_images})


def privacy_policy(request):
    return render(request, 'privacy_policy.html')


def refund_policy(request):
    return render(request, 'refund_policy.html')


def contact_us(request):
    return render(request, 'contact_us.html')
