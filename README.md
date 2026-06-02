# Simple Python Food Ordering App

A lightweight Flask website where customers can browse food items, add them to a cart, and place an order.

## Setup

1. Install Python 3.10+.
2. Create a virtual environment:

   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Run the app:

   ```bash
   python app.py
   ```

5. Open your browser at `http://127.0.0.1:5000`

## Files

- `app.py` — backend server and route logic
- `food.db` — SQLite database created automatically
- `templates/` — HTML templates
- `static/style.css` — simple page styling

## New features

- update and remove items from the cart
- checkout form with name, email and payment type
- order history page showing past orders
- user sign in and sign out
- admin login with menu management
- admin user and order management pages

## Admin login

- default admin password: `adminpass`
- set a new password with the `ADMIN_PASSWORD` environment variable before running the app

Example:

```bash
set ADMIN_PASSWORD=mysecret
python app.py
```

## User orders

- sign in at `/login` to save your name/email in session
- order history shows only your orders when signed in
- admin users see all orders in order history
