# Mark's Food Corner Online Ordering System

A web-based restaurant ordering and delivery management system developed for Mark's Food Corner as part of a Software Design / Computer Engineering course project.

The system allows customers to browse food products, add items to cart, verify promo codes, place orders, upload GCash payment proof, and track delivery status. It also provides admin order management, delivery rider dashboard, customer map routing, Cloudinary image storage, and Progressive Web App support for mobile installation.

Theme: Mark's Food Corner Restaurant Ordering and Delivery Theme.

Main purpose: customers can order food online, admins can manage orders and payment verification, and delivery riders can view customer locations and update delivery progress.

## Stack

- Django backend and templates
- Django authentication and role-based access
- SQLite fallback for local development
- PostgreSQL support through `DATABASE_URL`
- Cloudinary for deployed media uploads
- WhiteNoise for static files
- Bootstrap, CSS, and JavaScript frontend
- Leaflet and OpenStreetMap for maps
- OSRM route service for road-based delivery routes
- Progressive Web App support through manifest and service worker
- Render-ready deployment configuration

## Setup

Create and activate a virtual environment.

Install dependencies:

```bash
pip install -r requirements.txt
```

Set environment variables for local or production use:

```env
SECRET_KEY=change-this-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=
DATABASE_URL=
CLOUDINARY_URL=
```

For deployed Cloudinary media storage, use:

```env
CLOUDINARY_URL=cloudinary://API_KEY:API_SECRET@CLOUD_NAME
```

Or use separate Cloudinary variables:

```env
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret
```

Run migrations:

```bash
python manage.py migrate
```

Create an admin account:

```bash
python manage.py createsuperuser
```

Run the development server:

```bash
python manage.py runserver
```

Open the system:

```text
http://127.0.0.1:8000/
```

## User Roles

### Customer

- Register and log in
- Browse food categories
- View featured product carousel
- Add food to cart
- Add special instructions
- Verify promo code before payment
- Select delivery, pickup, or dine-in
- Upload GCash reference and proof
- Track active orders
- View order history
- Install the system as a mobile PWA

### Admin / Staff

- Access Django admin
- Manage food products, categories, images, prices, and availability
- View and update orders
- Verify GCash payment reference and screenshot
- Update payment status
- Upload delivery proof
- Access sales dashboard
- Manage order status workflow

### Delivery Rider

- Access rider delivery dashboard
- View active delivery orders
- View customer contact details
- Open customer map preview
- View road-based route to customer
- Update order status to `On the way`
- Mark delivery as delivered

To give a user delivery rider access, create a Django group named:

```text
Delivery
```

Then add the rider account to that group.

## Features

- Login and registration system
- Registration verification code
- Show password toggle for login and signup
- Food category management
- Food image upload support
- Featured product carousel
- Mobile-friendly menu layout
- Cart and order summary
- In-app checkout confirmation modal
- Promo code verification button
- Automatic discount and total preview
- GCash payment proof upload
- 13-digit GCash reference validation
- Duplicate GCash reference prevention
- Admin payment verification workflow
- Active order tracking
- Customer order history
- Delivery rider dashboard
- Customer map preview
- Road-based delivery route using OSRM
- Cloudinary media storage for deployment
- Progressive Web App install support
- App-style mobile layout
- Order status notification support while the PWA/browser is active
- Render deployment support

## Payment Verification Notes

GCash references are not automatically verified through the official GCash system. The system improves safety by requiring:

- 13-digit GCash reference number
- Payment screenshot upload
- Duplicate reference blocking
- Admin review before marking payment as `Paid`

GCash delivery orders are not shown to riders until the admin marks the payment as paid.

## PWA / Mobile App Notes

The system includes Progressive Web App support.

Android Chrome:

```text
Open website -> Install App
```

iPhone Safari:

```text
Open website -> Share -> Add to Home Screen
```

PWA installation requires HTTPS. Render provides HTTPS by default.

Notification permission is requested when the system is opened as an installed app. Browser rules may require the first user tap before the notification permission prompt appears.

## Deployment Notes

Recommended deployment:

- Render for Django hosting
- PostgreSQL database through Render, Supabase, Railway, or another managed provider
- Cloudinary for uploaded media files
- WhiteNoise for static files

Render environment variables:

```env
SECRET_KEY=your-long-random-secret-key
DEBUG=False
ALLOWED_HOSTS=your-app-name.onrender.com
CSRF_TRUSTED_ORIGINS=https://your-app-name.onrender.com
DATABASE_URL=your-postgres-database-url
CLOUDINARY_URL=cloudinary://API_KEY:API_SECRET@CLOUD_NAME
```

Build command:

```bash
pip install -r requirements.txt && python manage.py migrate && python manage.py collectstatic --noinput
```

Start command:

```bash
gunicorn restaurant.wsgi:application
```

## Important Deployment Reminder

Render uses temporary local storage. Uploaded images saved only in `/media/` can disappear after redeploy or restart.

Use Cloudinary for:

- Food images
- Profile pictures
- Payment proof screenshots
- Delivery proof screenshots

After Cloudinary is configured, re-upload food images through Django admin if old images are broken.

## Common Commands

Check project status:

```bash
git status
```

Commit changes:

```bash
git add .
git commit -m "Update Mark's Food Corner system"
git push
```

Run locally:

```bash
python manage.py runserver
```

Apply migrations:

```bash
python manage.py migrate
```

Collect static files:

```bash
python manage.py collectstatic --noinput
```

## Project Purpose

This project demonstrates practical software design concepts such as role-based access control, database-driven application development, cloud media storage, payment proof validation, delivery tracking, responsive web design, PWA support, and deployment-ready Django configuration.
