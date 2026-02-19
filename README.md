# EcomClean

EcomClean is a Django-based e-commerce web application. It provides a clean, modular structure for building and customizing online stores.

## Features
- Product listing and detail pages
- Shopping cart functionality
- Order checkout and success pages
- Admin management for products and orders
- Static and media file handling
- Modular app structure for easy extension

## Project Structure
- `devloom/` - Main Django app with models, views, templates, static files, and management commands
- `Website/` - Django project configuration (settings, URLs, WSGI/ASGI)
- `db.sqlite3` - SQLite database (development only)
- `env/` - Python virtual environment (not included in version control)

## Setup Instructions
1. Clone the repository:
   ```bash
   git clone <your-repo-url>
   cd EcomClean
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv env
   source env/bin/activate  # On Windows: env\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run migrations:
   ```bash
   python manage.py migrate
   ```
5. Start the development server:
   ```bash
   python manage.py runserver
   ```

## License
MIT License
