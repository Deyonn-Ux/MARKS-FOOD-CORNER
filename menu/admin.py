from django.contrib import admin

from .models import Category, Food, Order, OrderItem, Profile, Review, PromoCode


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)


@admin.register(Food)
class FoodAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'is_available', 'preparation_minutes')
    search_fields = ('name', 'description')
    list_filter = ('category', 'is_available')


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ('food', 'quantity', 'flavor_choice')
    readonly_fields = ('food', 'quantity')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'customer',
        'total',
        'payment_status',
        'payment_method',
        'status',
        'location_label',
        'estimated_minutes',
        'created',
    )
    list_filter = ('status', 'payment_status', 'payment_method', 'created')
    search_fields = ('id', 'customer__username', 'contact_phone', 'delivery_address')
    readonly_fields = ('created', 'updated', 'delivery_proof')
    inlines = (OrderItemInline,)
    actions = ['mark_preparing', 'mark_ready', 'mark_on_the_way', 'mark_completed']
    fieldsets = (
        ('Customer', {'fields': ('customer', 'contact_phone', 'delivery_address', 'customer_latitude', 'customer_longitude', 'delivery_note')}),
        ('Order', {'fields': ('service_type', 'pickup_time')}),
        ('Payment', {'fields': ('subtotal', 'delivery_fee', 'discount', 'promo_code', 'total', 'payment_method', 'payment_status', 'payment_reference', 'payment_proof', 'delivery_proof')}),
        ('Tracking', {'fields': ('status', 'courier_name', 'location_label', 'rider_latitude', 'rider_longitude', 'estimated_minutes')}),
        ('Dates', {'fields': ('created', 'updated')}),
    )

    def mark_preparing(self, request, queryset):
        queryset.update(status='Preparing', location_label='Restaurant kitchen', estimated_minutes=25)
    mark_preparing.short_description = 'Mark as Preparing'

    def mark_ready(self, request, queryset):
        queryset.update(status='Ready', location_label='Ready for pickup by rider', estimated_minutes=20)
    mark_ready.short_description = 'Mark as Ready'

    def mark_on_the_way(self, request, queryset):
        queryset.update(status='On the way', location_label='On the way to customer', estimated_minutes=15)
    mark_on_the_way.short_description = 'Mark as On the way'

    def mark_delivered(self, request, queryset):
        queryset.update(status='Delivered', location_label='Delivered to customer', estimated_minutes=0)
    mark_delivered.short_description = 'Mark as Delivered'

    def mark_completed(self, request, queryset):
        queryset.update(status='Completed', location_label='Order completed', estimated_minutes=0)
    mark_completed.short_description = 'Mark as Completed'


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'food', 'quantity', 'flavor_choice')
    search_fields = ('order__id', 'food__name')


@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount', 'active', 'created', 'updated')
    search_fields = ('code',)
    list_filter = ('active',)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'picture')
    search_fields = ('user__username',)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('order', 'customer', 'rating', 'created')
    search_fields = ('order__id', 'customer__username', 'comment')
    list_filter = ('rating', 'created')
