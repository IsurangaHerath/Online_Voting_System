# Deployment Guide - Heroku

This guide explains how to deploy the Online Voting System to Heroku.

## Prerequisites

- [Heroku Account](https://signup.heroku.com)
- [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli) installed
- Git installed

## Step 1: Prepare Your Application

### Update config.py for Production

Make sure your `config.py` uses environment variables properly:

```python
class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_ECHO = False
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
```

### Create Procfile

Create a `Procfile` in the project root:

```
web: gunicorn app:app
```

### Create runtime.txt

Create a `runtime.txt` file to specify Python version:

```
python-3.11.4
```

### Update requirements.txt

Ensure these are in your requirements.txt:

```
gunicorn==21.2.0
```

## Step 2: Set Up Heroku

### Login to Heroku

```bash
heroku login
```

### Create Heroku App

```bash
heroku create your-app-name
```

### Add MySQL Database (ClearDB)

```bash
heroku addons:create cleardb:ignite
```

Get the database URL:

```bash
heroku config:get CLEARDB_DATABASE_URL
```

### Set Environment Variables

```bash
# Database
heroku config:set MYSQL_HOST=your-host
heroku config:set MYSQL_PORT=3306
heroku config:set MYSQL_USER=your-user
heroku config:set MYSQL_PASSWORD=your-password
heroku config:set MYSQL_DATABASE=your-database

# Flask
heroku config:set FLASK_ENV=production
heroku config:set SECRET_KEY=your-random-secret-key
heroku config:set JWT_SECRET_KEY=your-random-jwt-key
heroku config:set VOTE_ENCRYPTION_KEY=your-encryption-key

# Email (optional)
heroku config:set MAIL_SERVER=smtp.gmail.com
heroku config:set MAIL_PORT=587
heroku config:set MAIL_USERNAME=your-email
heroku config:set MAIL_PASSWORD=your-app-password
```

## Step 3: Deploy

### Initialize Git (if not already)

```bash
git init
git add .
git commit -m "Initial commit"
```

### Connect to Heroku

```bash
heroku git:remote -a your-app-name
```

### Push to Heroku

```bash
git push heroku main
```

### Run Database Migrations

```bash
heroku run python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

### Create Default Admin

```bash
heroku run python -c "from app import create_app, db, User; app = create_app(); app.app_context().push(); admin = User(username='admin', email='admin@example.com', role='admin', is_verified=True); admin.set_password('Admin@123'); db.session.add(admin); db.session.commit()"
```

## Step 4: Verify Deployment

```bash
heroku open
```

Check logs if there are issues:

```bash
heroku logs --tail
```

## Troubleshooting

### Database Connection Issues

Ensure your ClearDB credentials are correct:

```bash
heroku config
```

### Static Files Not Loading

Make sure you're using the correct static file configuration. For Heroku, consider using a CDN like Cloudinary for static files.

### Email Not Working

For production, consider using SendGrid or Mailgun instead of Gmail.

## Additional Resources

- [Heroku Python Deployment](https://devcenter.heroku.com/articles/getting-started-with-python)
- [ClearDB Documentation](https://devcenter.heroku.com/articles/cleardb)
- [Flask on Heroku](https://devcenter.heroku.com/articles/python-gunicorn)
