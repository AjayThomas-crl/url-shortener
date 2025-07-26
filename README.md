# URL Shortener

A modern URL shortening service built with FastAPI and SQLAlchemy.

## Features

- Shorten long URLs to easy-to-share links
- Create custom short codes
- Set expiration times for links
- One-time use links that self-delete after access
- QR code generation for shortened URLs
- Admin dashboard to track link usage

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/url-shortener.git
   cd url-shortener
   ```

2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure your database in `config.ini`

5. Run the application:
   ```bash
   uvicorn app.main:app --reload
   ```

6. Visit http://localhost:8000 in your browser

## Usage

- Enter a URL in the input field and click "Shorten"
- Optionally set a custom code, expiration time, or one-time use flag
- The shortened URL will be displayed along with a QR code
- Visit the admin dashboard at http://localhost:8000/admin to see statistics

## Technologies

- FastAPI
- SQLAlchemy
- SQL Server
- Jinja2 Templates
- QR Code Generation

## License

MIT