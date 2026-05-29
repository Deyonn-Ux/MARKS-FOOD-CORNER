from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about_us, name='about_us'),
    path('contact-us/', views.contact_us, name='contact_us'),
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('refund-policy/', views.refund_policy, name='refund_policy'),
    path('add/<int:id>/', views.add, name='add'),
    path('cart/', views.cart, name='cart'),
    path('remove/<int:id>/', views.remove_from_cart, name='remove'),

    # 🔥 RECOMMENDATION
    path('recommend/', views.recommend, name='recommend'),

    # 💳 CHECKOUT FLOW
    path('checkout/', views.checkout, name='checkout'),
    path('checkout/verify-promo/', views.verify_promo_code, name='verify_promo_code'),
    path('receipt/<int:id>/', views.receipt, name='receipt'),
    path('orders/', views.my_orders, name='my_orders'),
    path('track-orders/', views.track_orders, name='track_orders'),
    path('orders/<int:id>/review/', views.review_order, name='review_order'),
    path('orders/<int:id>/cancel/', views.cancel_order, name='cancel_order'),
    path('track/<int:id>/', views.track_order, name='track_order'),
    path('track/<int:id>/status/', views.tracking_api, name='tracking_api'),
    path('delivery/', views.track_orders, name='delivery_dashboard'),
    path('delivery/<int:id>/', views.delivery_order, name='delivery_order'),
    path('delivery/<int:id>/update/', views.delivery_update_order, name='delivery_update_order'),
    path('manage-orders/', views.manage_orders, name='manage_orders'),
    path('manage-orders/<int:id>/update/', views.update_order, name='update_order'),

    # 📊 DASHBOARD
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),

    # 🔐 AUTHENTICATION
    path('login/', views.RoleLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', views.register, name='register'),
]
