from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('menu', '0011_order_pickup_time'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='delivery_proof',
            field=models.ImageField(blank=True, null=True, upload_to='delivery_proofs/'),
        ),
    ]
