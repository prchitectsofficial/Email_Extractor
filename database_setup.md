# MySQL Database Setup Guide

## Prerequisites

1. MySQL Server installed and running
2. Python 3.11 or higher
3. MySQL connector library installed

## Installation Steps

### 1. Install MySQL Server

**Windows:**
- Download MySQL Installer from https://dev.mysql.com/downloads/installer/
- Run the installer and follow the setup wizard
- Remember your root password

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install mysql-server
sudo mysql_secure_installation
```

**macOS:**
```bash
brew install mysql
brew services start mysql
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3. Create Database and User (Optional but Recommended)

Connect to MySQL:
```bash
mysql -u root -p
```

Run these commands:
```sql
CREATE DATABASE email_extractor;
CREATE USER 'email_user'@'localhost' IDENTIFIED BY 'your_secure_password';
GRANT ALL PRIVILEGES ON email_extractor.* TO 'email_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### 4. Configure Database Connection

You have three options:

#### Option A: Environment Variables (Recommended for Production)

Create a `.env` file or set environment variables:
```bash
export DB_HOST=localhost
export DB_NAME=email_extractor
export DB_USER=email_user
export DB_PASSWORD=your_secure_password
export DB_PORT=3306
```

#### Option B: Modify history_manager.py

Edit the `__init__` method in `history_manager.py`:
```python
def __init__(self, 
             host='localhost',
             database='email_extractor',
             user='root',
             password='your_password',
             port=3306):
```

#### Option C: Pass Parameters When Initializing

In `app.py`, modify the HistoryManager initialization:
```python
history_manager = HistoryManager(
    host='localhost',
    database='email_extractor',
    user='root',
    password='your_password',
    port=3306
)
```

### 5. Run the Application

The database tables will be created automatically when you run the app:
```bash
streamlit run app.py
```

## Database Schema

### Table: `extractions`
- Stores main extraction metadata
- Keeps latest 15 entries automatically

### Table: `extraction_results`
- Stores individual website results
- Linked to extractions via foreign key
- Automatically deleted when extraction is deleted (CASCADE)

## Migration from JSON

If you have existing data in `extraction_history.json`, you can migrate it:

1. The app will automatically create tables on first run
2. Old JSON data won't be automatically migrated
3. New extractions will be stored in MySQL
4. You can manually import old data if needed

## Troubleshooting

### Connection Error
- Check MySQL is running: `sudo systemctl status mysql` (Linux) or check Services (Windows)
- Verify credentials are correct
- Check firewall settings

### Permission Denied
- Ensure database user has proper privileges
- Try using root user for testing

### Table Creation Error
- Check MySQL user has CREATE TABLE permission
- Verify database exists

## Security Notes

- Never commit database passwords to version control
- Use environment variables for production
- Create a dedicated database user (not root)
- Use strong passwords
- Consider using SSL for remote connections
