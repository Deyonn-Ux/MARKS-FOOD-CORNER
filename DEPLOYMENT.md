# Deployment Checklist

## Local setup

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Render or Railway settings

Set these environment variables on the hosting dashboard:

```bash
PYTHON_VERSION=3.12.13
SECRET_KEY=your-long-random-secret-key
DEBUG=False
ALLOWED_HOSTS=your-app-domain.onrender.com
CSRF_TRUSTED_ORIGINS=https://your-app-domain.onrender.com
DATABASE_URL=your-postgres-database-url
CLOUDINARY_URL=cloudinary://your-api-key:your-api-secret@your-cloud-name
```

For `DATABASE_URL` on Render, use the database **Internal Database URL** when the web service and database are in the same Render region. If you use the **External Database URL**, make sure it ends with `?sslmode=require`.

You can use `CLOUDINARY_URL` by itself. If you do not use `CLOUDINARY_URL`, set all three variables instead:

```bash
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret
```

Uploads made through Django admin are stored in Cloudinary. Render does not keep local uploaded files permanently, so do not rely on `/media/` local storage in production.

Build command:

```bash
pip install -r requirements.txt && python manage.py collectstatic --noinput
```

Pre-deploy command:

```bash
python manage.py migrate
```

Start command:

```bash
gunicorn restaurant.wsgi:application
```

## Order tracking

Customers can open `/orders/` to see their orders, then open `/track/<order_id>/` for live status and location updates.

Admins update the order in `/admin/` by changing:

- Status
- Location label
- Rider latitude and longitude
- Estimated minutes

The customer tracking page refreshes every 5 seconds.
