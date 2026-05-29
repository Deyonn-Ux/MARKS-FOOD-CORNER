from django.conf import settings
from django.db import models
from django.urls import reverse


# 🍽 CATEGORY
class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


# 🍔 FOOD
class Food(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    image = models.ImageField(upload_to='foods/', null=True, blank=True)
    is_available = models.BooleanField(default=True)
    preparation_minutes = models.PositiveIntegerField(default=15)

    def __str__(self):
        return self.name


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    picture = models.ImageField(upload_to='profiles/', null=True, blank=True)

    def __str__(self):
        return self.user.username


class PromoCode(models.Model):
    code = models.CharField(max_length=30, unique=True)
    discount = models.DecimalField(max_digits=5, decimal_places=2, help_text='Use decimal values like 0.10 for 10%')
    active = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return f"{self.code} ({int(self.discount * 100)}%)"


# 🧾 ORDER
class Order(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Preparing', 'Preparing'),
        ('Ready', 'Ready'),
        ('On the way', 'On the way'),
        ('Delivered', 'Delivered'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    ]

    SERVICE_CHOICES = [
        ('Dine In', 'Dine In'),
        ('Pickup', 'Pickup'),
        ('Delivery', 'Delivery'),
    ]

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders'
    )
    total = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    promo_code = models.CharField(max_length=30, blank=True)
    payment_method = models.CharField(max_length=20)
    service_type = models.CharField(max_length=20, choices=SERVICE_CHOICES, default='Delivery')
    payment_status = models.CharField(
        max_length=20,
        choices=[
            ('Unpaid', 'Unpaid'),
            ('Pending proof', 'Pending proof'),
            ('Paid', 'Paid'),
            ('Failed', 'Failed'),
        ],
        default='Unpaid'
    )
    payment_reference = models.CharField(max_length=80, blank=True)
    payment_proof = models.ImageField(upload_to='payment_proofs/', null=True, blank=True)
    delivery_proof = models.ImageField(upload_to='delivery_proofs/', null=True, blank=True)
    contact_phone = models.CharField(max_length=30, blank=True)
    delivery_address = models.TextField(blank=True)
    customer_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    customer_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    delivery_note = models.CharField(max_length=200, blank=True)
    pickup_time = models.CharField(max_length=80, blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Pending'
    )
    courier_name = models.CharField(max_length=80, default='Restaurant rider')
    location_label = models.CharField(max_length=120, default='Restaurant kitchen')
    rider_latitude = models.DecimalField(max_digits=9, decimal_places=6, default=9.539611)
    rider_longitude = models.DecimalField(max_digits=9, decimal_places=6, default=125.838139)
    estimated_minutes = models.PositiveIntegerField(default=30)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} - {self.status}"

    def get_absolute_url(self):
        return reverse('track_order', args=[self.id])

    @property
    def tracking_percent(self):
        steps = {
            'Pending': 10,
            'Preparing': 35,
            'Ready': 55,
            'On the way': 78,
            'Delivered': 100,
            'Completed': 100,
            'Cancelled': 100,
        }
        return steps.get(self.status, 10)

    @property
    def customer_name(self):
        if not self.customer:
            return 'Guest'
        full_name = self.customer.get_full_name()
        return full_name or self.customer.username


# 📦 ORDER ITEMS
class OrderItem(models.Model):
    FLAVOR_CHOICES = [
        ('Cheese', 'Cheese'),
        ('Sour Cream', 'Sour Cream'),
        ('Salt', 'Salt'),
        ('BBQ', 'BBQ'),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    food = models.ForeignKey(Food, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    flavor_choice = models.CharField(max_length=30, choices=FLAVOR_CHOICES, blank=True)

    def __str__(self):
        flavor_text = f" ({self.flavor_choice})" if self.flavor_choice else ""
        return f"{self.food.name} x {self.quantity}{flavor_text}"

    @property
    def subtotal(self):
        return self.food.price * self.quantity


class Review(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='review')
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(default=5)
    comment = models.TextField(blank=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review for order #{self.order_id} - {self.rating}/5"
