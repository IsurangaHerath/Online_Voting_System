# Deployment Guide - PythonAnywhere

This guide explains how to deploy the Online Voting System to PythonAnywhere.

## Prerequisites

- [PythonAnywhere Account](https://www.pythonanywhere.com/)
- Basic knowledge of the PythonAnywhere dashboard

## Step 1: Prepare Your Application

### Create a Zip File

Zip all your project files except:
- `venv/` (virtual environment)
- `__pycache__/`
- `.git/`
- Any `.pyc` files
- `.env` file (you'll set this in PythonAnywhere)

```bash
# Example: Create zip excluding certain folders
zip -r online_voting.zip . -x "venv/*" "__pycache__/*" "*.pyc" ".git/*"
```

## Step 2: Upload to PythonAnywhere

### Upload via Dashboard

1. Log in to PythonAnywhere
2. Go to the **Files** tab
3. Navigate to `/home/yourusername/`
4. Click **Upload a file** and upload your zip file

### Extract the File

Open a **Bash console** and extract:

```bash
cd /home/yourusername/
unzip -o online_voting.zip
```

## Step 3: Set Up Virtual Environment

In the Bash console:

```bash
cd /home/yourusername/online_voting_system

# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Step 4: Configure Database

### Option A: MySQL (Recommended)

1. Go to **Databases** tab in PythonAnywhere
2. Create a new MySQL database
3. Note the database credentials

### Option B: SQLite (For Testing)

SQLite is already supported - just ensure the path is correct.

### Import Database Schema

```bash
# Activate virtual environment
source venv/bin/activate

# Run schema
mysql -u yourusername -p yourdatabase < schema.sql
```

Or use the MySQL client:

```bash
mysql -u yourusername -p
source schema.sql
```

## Step 5: Configure Environment Variables

### Option A: Create a .env File

Create `.env` in your project directory:

```
FLASK_ENV=production
SECRET_KEY=your-random-secret-key
JWT_SECRET_KEY=your-random-jwt-key
VOTE_ENCRYPTION_KEY=your-encryption-key

MYSQL_HOST=yourusername.mysql.pythonanywhere-services.com
MYSQL_PORT=3306
MYSQL_USER=yourusername
MYSQL_PASSWORD=your-mysql-password
MYSQL_DATABASE=yourusername$voting

MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
```

### Option B: Update config.py

Modify `config.py` to handle missing environment variables gracefully:

```python
class ProductionConfig(Config):
    DEBUG = False
    
    # Use PythonAnywhere MySQL settings
    MYSQL_HOST = os.environ.get('MYSQL_HOST') or 'yourusername.mysql.pythonanywhere-services.com'
    MYSQL_USER = os.environ.get('MYSQL_USER') or 'yourusername'
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD') or 'your-password'
    MYSQL_DATABASE = os.environ.get('MYSQL_DATABASE') or 'yourusername$voting'
    
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DATABASE}"
```

## Step 6: Configure Web App

1. Go to **Web** tab
2. Click **Add a new web app**
3. Select **Manual configuration**
4. Select **Python version** (e.g., Python 3.11)

### Update WSGI Configuration

Click on the **WSGI configuration file** link and modify it:

```python
import sys

# Add your project directory to the path
path = '/home/yourusername/online_voting_system'
if path not in sys.path:
    sys.path.insert(0, path)

# Set environment variables
import os
os.environ['FLASK_ENV'] = 'production'
os.environ['SECRET_KEY'] = 'your-secret-key'
os.environ['JWT_SECRET_KEY'] = 'your-jwt-key'
os.environ['VOTE_ENCRYPTION_KEY'] = 'your-encryption-key'
os.environ['MYSQL_HOST'] = 'yourusername.mysql.pythonanywhere-services.com'
os.environ['MYSQL_USER'] = 'yourusername'
os.environ['MYSQL_PASSWORD'] = 'your-password'
os.environ['MYSQL_DATABASE'] = 'yourusername$voting'

# Run the app
from app import app as application
```

### Configure Static Files

In the **Web** tab, scroll to **Static files**:

| URL | Directory |
|-----|-----------|
| `/static/` | `/home/yourusername/online_voting_system/static/` |

## Step 7: Initialize Database

In the Bash console:

```bash
cd /home/yourusername/online_voting_system
source venv/bin/activate

# Initialize database
python -c "from app import app, db; app.app_context().push(); db.create_all()"

# Create admin user
python -c "from app import create_app, db, User; app = create_app(); app.app_context().push(); admin = User(username='admin', email='admin@pythonanywhere.com', role='admin', is_verified=True); admin.set_password('Admin@123'); db.session.add(admin); db.session.commit()"
```

## Step 8: Reload the Application

In the **Web** tab, click the **Reload** button.

## Step 9: Verify

Visit `https://yourusername.pythonanywhere.com`

## Troubleshooting

### Import Errors

Make sure the virtual environment is set up correctly and all packages are installed:

```bash
pip install -r requirements.txt
```

### Database Connection

Verify database credentials in the `.env` file or WSGI configuration.

### Static Files Not Loading

Check the static files configuration in the Web tab.

### Email Issues

For PythonAnywhere, you need to use a custom SMTP server. Gmail may not work due to security restrictions. Consider using:
- SendGrid
- Mailgun
- PythonAnywhere's own email system (for @pythonanywhere.com addresses only)

## Additional Tips

### Using Git on PythonAnywhere

You can clone your repository directly:

```bash
cd /home/yourusername/
git clone https://github.com/yourrepo.git
```

### Updating Your Application

```bash
# Pull latest changes
git pull

# Update dependencies
source venv/bin/activate
pip install -r requirements.txt

# Reload web app
# (Click Reload in the Web tab)
```

### Debugging

Check the **Error log** in the Web tab for any issues.

## Security Notes for Production

1. Change all default secret keys
2. Use strong passwords
3. Enable HTTPS (automatic on PythonAnywhere paid plans)
4. Keep your `.env` file secure
5. Regularly update dependencies
