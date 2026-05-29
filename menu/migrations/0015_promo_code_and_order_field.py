# Generated manually to add promo code support

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('menu', '0014_order_customer_latitude_order_customer_longitude'),
    ]

    operations = [
        migrations.CreateModel(
            name='PromoCode',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=30, unique=True)),
                ('discount', models.DecimalField(decimal_places=2, help_text='Use decimal values like 0.10 for 10%', max_digits=5)),
                ('active', models.BooleanField(default=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['-created'],
            },
        ),
        migrations.AddField(
            model_name='order',
            name='promo_code',
            field=models.CharField(blank=True, max_length=30),
        ),
    ]
