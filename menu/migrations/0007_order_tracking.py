from decimal import Decimal

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('menu', '0006_profile'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='contact_phone',
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AddField(
            model_name='order',
            name='courier_name',
            field=models.CharField(default='Restaurant rider', max_length=80),
        ),
        migrations.AddField(
            model_name='order',
            name='customer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='orders', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='order',
            name='delivery_address',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='order',
            name='delivery_note',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name='order',
            name='estimated_minutes',
            field=models.PositiveIntegerField(default=30),
        ),
        migrations.AddField(
            model_name='order',
            name='location_label',
            field=models.CharField(default='Restaurant kitchen', max_length=120),
        ),
        migrations.AddField(
            model_name='order',
            name='rider_latitude',
            field=models.DecimalField(decimal_places=6, default=Decimal('14.599512'), max_digits=9),
        ),
        migrations.AddField(
            model_name='order',
            name='rider_longitude',
            field=models.DecimalField(decimal_places=6, default=Decimal('120.984222'), max_digits=9),
        ),
        migrations.AddField(
            model_name='order',
            name='updated',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[('Pending', 'Pending'), ('Preparing', 'Preparing'), ('Ready', 'Ready'), ('On the way', 'On the way'), ('Delivered', 'Delivered'), ('Completed', 'Completed'), ('Cancelled', 'Cancelled')], default='Pending', max_length=20),
        ),
    ]
