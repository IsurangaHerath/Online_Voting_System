# Online Voting System

A secure, transparent, and democratic online voting platform built with Python Flask.

## Features

- **User Registration & Login** - Secure authentication with email verification
- **Password Security** - Bcrypt password hashing
- **JWT Authentication** - Token-based API authentication
- **Role-Based Access** - Admin and Voter roles
- **Vote Encryption** - Votes are encrypted before storage
- **Duplicate Prevention** - One vote per verified voter
- **Admin Panel** - Manage candidates, view voters, view results
- **Voter Panel** - View candidates, cast votes, view confirmation
- **Responsive Design** - Bootstrap-based frontend

## Technology Stack

- **Backend**: Python 3.x, Flask
- **Database**: MySQL
- **Authentication**: JWT, Bcrypt
- **Frontend**: HTML5, CSS3, Bootstrap 5, JavaScript

## Prerequisites

- Python 3.8+
- MySQL Server
- pip (Python package manager)

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd OnlineVotingSystem
```

### 2. Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy `.env.example` to `.env` and update the values:

```bash
# Database
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=online_voting_system

# Flask
FLASK_ENV=development
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret-key

# Email (for verification)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# App
APP_URL=http://localhost:5000
VOTE_ENCRYPTION_KEY=your-encryption-key
```

### 5. Create Database

```bash
# Login to MySQL
mysql -u root -p

# Run the schema
source schema.sql
```

Or create the database manually:

```sql
CREATE DATABASE online_voting_system;
```

### 6. Run the Application

```bash
python app.py
```

The application will start at `http://localhost:5000`

### 7. Default Admin Credentials

- **Username**: admin
- **Password**: Admin@123

## Project Structure

```
OnlineVotingSystem/
├── app.py                 # Main application
├── config.py              # Configuration
├── schema.sql             # Database schema
├── requirements.txt       # Dependencies
├── .env.example          # Environment template
├── routes/               # Route blueprints
│   ├── auth.py          # Authentication routes
│   ├── admin.py         # Admin routes
│   └── voter.py        # Voter routes
├── templates/           # HTML templates
│   ├── base.html       # Base template
│   ├── index.html      # Home page
│   ├── login.html      # Login
│   ├── register.html  # Registration
│   ├── admin/         # Admin templates
│   └── voter/        # Voter templates
└── static/            # Static files
    ├── css/          # Stylesheets
    └── js/           # JavaScript
```

## API Endpoints

### Authentication
- `POST /auth/api/register` - Register new user
- `POST /auth/api/login` - Login and get JWT token
- `GET /auth/api/me` - Get current user info
- `GET /auth/api/protected` - Protected route example

### Admin
- `GET /admin/dashboard` - Admin dashboard
- `GET /admin/add-candidate` - Add candidate form
- `GET /admin/voters` - View all voters
- `GET /admin/results` - View voting results

### Voter
- `GET /voter/dashboard` - Voter dashboard
- `GET /voter/candidates` - View candidates
- `POST /voter/vote/<id>` - Cast vote

## Deployment

### Heroku

See [deployment/heroku.md](deployment/heroku.md) for detailed instructions.

### PythonAnywhere

See [deployment/pythonanywhere.md](deployment/pythonanywhere.md) for detailed instructions.

## Security Features

1. **Password Hashing** - All passwords are hashed using bcrypt
2. **SQL Injection Prevention** - Using SQLAlchemy ORM
3. **CSRF Protection** - Flask-WTF forms include CSRF tokens
4. **Session Management** - Secure session handling
5. **Vote Encryption** - Votes are encrypted using Fernet symmetric encryption
6. **Role-Based Access** - Strict role checking for all routes
7. **Input Validation** - WTForms for form validation

## Usage Flow

### For Voters:
1. Register an account
2. Verify email address
3. Login with credentials
4. View list of candidates
5. Select candidate and cast vote
6. Receive confirmation

### For Admins:
1. Login with admin credentials
2. Add candidates
3. View registered voters
4. Monitor voting results
5. Manage election settings

## License

MIT License

## Contributing

Contributions are welcome! Please read the contributing guidelines first.
