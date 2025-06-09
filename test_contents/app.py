from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime, date, timedelta
import calendar
import pandas as pd
import io
import os
import random
import secrets

app = Flask(__name__)
# Generate a proper random secret key
app.secret_key = secrets.token_hex(32)
# Set debug to False for production
app.config['DEBUG'] = False

FACILITIES = [
    {'value': 'football', 'name': 'Football Field'},
    {'value': 'basketball', 'name': 'Basketball Court'},
    {'value': 'volleyball', 'name': 'Volleyball Court'},
    {'value': 'tennis', 'name': 'Tennis Court'},
    {'value': 'gym', 'name': 'Gymnasium'}
]

TIME_SLOTS = [
    {'value': '17:00', 'label': '5:00 PM - 6:00 PM'},
    {'value': '18:00', 'label': '6:00 PM - 7:00 PM'},
    {'value': '19:00', 'label': '7:00 PM - 8:00 PM'},
    {'value': '20:00', 'label': '8:00 PM - 9:00 PM'},
    {'value': '21:00', 'label': '9:00 PM - 10:00 PM'}
]

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# Login required decorator with flash message
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Admin required decorator with flash message
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        if not session.get('is_admin'):
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

def has_weekly_booking(user_id, booking_date):
    """
    Check if user has already booked a slot in the same week
    Returns True if user has a booking in the same week, False otherwise
    """
    # Convert booking_date string to datetime
    booking_datetime = datetime.strptime(booking_date, '%Y-%m-%d')
    
    # Calculate the start and end of the week for the booking date
    week_start = booking_datetime - timedelta(days=booking_datetime.weekday())
    week_end = week_start + timedelta(days=6)
    
    conn = get_db_connection()
    try:
        existing_booking = conn.execute('''
            SELECT id FROM bookings 
            WHERE user_id = ? 
            AND date BETWEEN ? AND ?
        ''', (user_id, week_start.strftime('%Y-%m-%d'), week_end.strftime('%Y-%m-%d'))).fetchone()
        
        return existing_booking is not None
    finally:
        conn.close()

def get_available_time_slots(facility, selected_date):
    time_slots = [
        {'value': '17:00', 'label': '5:00 PM - 6:00 PM'},
        {'value': '18:00', 'label': '6:00 PM - 7:00 PM'},
        {'value': '19:00', 'label': '7:00 PM - 8:00 PM'},
        {'value': '20:00', 'label': '8:00 PM - 9:00 PM'},
        {'value': '21:00', 'label': '9:00 PM - 10:00 PM'}
    ]
    
    conn = get_db_connection()
    booked_slots = conn.execute('''
        SELECT time_slot FROM bookings 
        WHERE facility = ? AND date = ?
    ''', (facility, selected_date)).fetchall()
    conn.close()
    
    booked_times = [slot['time_slot'] for slot in booked_slots]
    
    for slot in time_slots:
        slot['booked'] = slot['value'] in booked_times
    
    return time_slots

@app.route('/')
@login_required
def home():
    user_name = session.get('user_name', 'Guest')
    return f'Welcome to Al Majal Camp Activity Booking, {user_name}!'

@app.route('/booking', methods=['GET', 'POST'])
@login_required
def booking():
    if request.method == 'POST':
        facility = request.form['facility']
        booking_date = request.form['date']
        time_slot = request.form['time_slot']
        user_id = session['user_id']
        
        # Check if user has already booked this week
        if has_weekly_booking(user_id, booking_date):
            return render_template('booking.html',
                                error='You already have a booking this week. Only one booking per week is allowed.',
                                time_slots=get_available_time_slots(facility, booking_date),
                                today=date.today().isoformat())
        
        conn = get_db_connection()
        try:
            # Check if slot is already booked
            existing = conn.execute('''
                SELECT id FROM bookings 
                WHERE facility = ? AND date = ? AND time_slot = ?
            ''', (facility, booking_date, time_slot)).fetchone()
            
            if existing:
                return render_template('booking.html', 
                                     error='This time slot is already booked.',
                                     time_slots=get_available_time_slots(facility, booking_date),
                                     today=date.today().isoformat())
            
            # Create new booking
            conn.execute('''
                INSERT INTO bookings (user_id, facility, date, time_slot)
                VALUES (?, ?, ?, ?)
            ''', (user_id, facility, booking_date, time_slot))
            conn.commit()
            
            return render_template('booking.html',
                                 success='Booking confirmed!',
                                 time_slots=get_available_time_slots(facility, booking_date),
                                 today=date.today().isoformat())
        finally:
            conn.close()
    
    # Default time slots for GET request
    today = date.today().isoformat()
    default_facility = request.args.get('facility', 'football')
    time_slots = get_available_time_slots(default_facility, today)
    
    return render_template('booking.html', time_slots=time_slots, today=today)

def generate_captcha():
    """Generate a simple math CAPTCHA"""
    num1 = random.randint(1, 10)
    num2 = random.randint(1, 10)
    operator = random.choice(['+', '-', '*'])
    
    if operator == '+':
        answer = num1 + num2
    elif operator == '-':
        answer = num1 - num2
    else:  # multiplication
        answer = num1 * num2
    
    question = f"{num1} {operator} {num2}"
    return question, str(answer)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        id_number = request.form['id_number']
        phone = request.form['phone']
        password = request.form['password']
        captcha_answer = request.form.get('captcha_answer')
        correct_answer = session.get('captcha_answer')
        
        # Validate CAPTCHA
        if not captcha_answer or captcha_answer != correct_answer:
            captcha_question, answer = generate_captcha()
            session['captcha_answer'] = answer
            return render_template('register.html', 
                                error='Incorrect CAPTCHA answer. Please try again.',
                                captcha_question=captcha_question)
        
        # Validate password length
        if len(password) < 6:
            captcha_question, answer = generate_captcha()
            session['captcha_answer'] = answer
            return render_template('register.html',
                                error='Password must be at least 6 characters long.',
                                captcha_question=captcha_question)
        
        # Generate a secure password hash with salt
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)
        
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO users (name, id_number, phone, password) VALUES (?, ?, ?, ?)',
                        (name, id_number, phone, hashed_password))
            conn.commit()
            session.pop('captcha_answer', None)
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            captcha_question, answer = generate_captcha()
            session['captcha_answer'] = answer
            return render_template('register.html', 
                                error='Phone number or ID number already exists.',
                                captcha_question=captcha_question)
        finally:
            conn.close()
    
    captcha_question, answer = generate_captcha()
    session['captcha_answer'] = answer
    return render_template('register.html', captcha_question=captcha_question)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        phone = request.form['phone']
        password = request.form['password']
        
        conn = get_db_connection()
        try:
            user = conn.execute('SELECT * FROM users WHERE phone = ?', (phone,)).fetchone()
            
            if user and check_password_hash(user['password'], password):
                session['user_id'] = user['id']
                session['user_name'] = user['name']
                session['is_admin'] = user['is_admin']
                
                flash('Welcome back!', 'success')
                if session['is_admin']:
                    return redirect(url_for('admin_dashboard'))
                return redirect(url_for('home'))
            else:
                flash('Invalid phone number or password', 'danger')
                return render_template('login.html')
        finally:
            conn.close()
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    # Clear the session
    session.clear()
    return redirect(url_for('login'))

@app.route('/admin')
@admin_required
def admin_dashboard():
    # Get the week start date from query parameters or use current date
    week_start_str = request.args.get('week_start')
    if week_start_str:
        week_start = datetime.strptime(week_start_str, '%Y-%m-%d').date()
    else:
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
    
    # Calculate week dates
    week_dates = [week_start + timedelta(days=i) for i in range(7)]
    
    conn = get_db_connection()
    
    # Get all users with their booking counts
    users = conn.execute('''
        SELECT u.*, COUNT(b.id) as total_bookings 
        FROM users u 
        LEFT JOIN bookings b ON u.id = b.user_id 
        GROUP BY u.id
    ''').fetchall()
    
    # Get all bookings for the week
    bookings_data = conn.execute('''
        SELECT b.*, u.name as user_name, u.phone as user_phone
        FROM bookings b
        JOIN users u ON b.user_id = u.id
        WHERE b.date BETWEEN ? AND ?
    ''', (week_start.isoformat(), week_dates[-1].isoformat())).fetchall()
    
    conn.close()
    
    # Organize bookings by facility
    facilities_bookings = []
    for facility in FACILITIES:
        facility_data = {
            'name': facility['name'],
            'value': facility['value'],
            'dates': week_dates,
            'time_slots': TIME_SLOTS,
            'bookings': {date.isoformat(): {} for date in week_dates}
        }
        
        # Fill in bookings
        for booking in bookings_data:
            if booking['facility'] == facility['value']:
                if booking['date'] not in facility_data['bookings']:
                    facility_data['bookings'][booking['date']] = {}
                
                facility_data['bookings'][booking['date']][booking['time_slot']] = {
                    'user_name': booking['user_name'],
                    'phone': booking['user_phone']
                }
        
        facilities_bookings.append(facility_data)
    
    return render_template('admin_dashboard.html',
                         users=users,
                         bookings=facilities_bookings,
                         week_start=week_start.isoformat())

@app.route('/admin/export/users')
@admin_required
def export_users():
    conn = get_db_connection()
    
    # Get users with booking counts
    users_data = conn.execute('''
        SELECT u.id, u.name, u.id_number, u.phone, COUNT(b.id) as total_bookings 
        FROM users u 
        LEFT JOIN bookings b ON u.id = b.user_id 
        WHERE u.is_admin = 0
        GROUP BY u.id
    ''').fetchall()
    
    conn.close()
    
    # Convert to DataFrame
    df = pd.DataFrame([dict(row) for row in users_data])
    
    # Create Excel file in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Users', index=False)
    
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'users_export_{date.today().isoformat()}.xlsx'
    )

@app.route('/admin/export/bookings')
@admin_required
def export_bookings():
    week_start_str = request.args.get('week_start')
    if week_start_str:
        week_start = datetime.strptime(week_start_str, '%Y-%m-%d').date()
    else:
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
    
    week_end = week_start + timedelta(days=6)
    
    conn = get_db_connection()
    
    # Get bookings with user details
    bookings_data = conn.execute('''
        SELECT 
            b.id,
            u.name as user_name,
            u.phone as user_phone,
            b.facility,
            b.date,
            b.time_slot,
            b.created_at
        FROM bookings b
        JOIN users u ON b.user_id = u.id
        WHERE b.date BETWEEN ? AND ?
        ORDER BY b.date, b.time_slot
    ''', (week_start.isoformat(), week_end.isoformat())).fetchall()
    
    conn.close()
    
    # Convert to DataFrame
    df = pd.DataFrame([dict(row) for row in bookings_data])
    
    if not df.empty:
        # Add facility name
        facility_names = {f['value']: f['name'] for f in FACILITIES}
        df['facility'] = df['facility'].map(facility_names)
        
        # Format time slots
        time_slot_labels = {t['value']: t['label'] for t in TIME_SLOTS}
        df['time_slot'] = df['time_slot'].map(time_slot_labels)
        
        # Rename columns
        df = df.rename(columns={
            'user_name': 'User Name',
            'user_phone': 'Phone',
            'facility': 'Facility',
            'date': 'Date',
            'time_slot': 'Time Slot',
            'created_at': 'Booking Time'
        })
    
    # Create Excel file in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        if df.empty:
            pd.DataFrame().to_excel(writer, sheet_name='No Bookings')
        else:
            df.to_excel(writer, sheet_name='Bookings', index=False)
    
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'bookings_export_{week_start.isoformat()}_to_{week_end.isoformat()}.xlsx'
    )

@app.route('/profile')
@login_required
def profile():
    conn = get_db_connection()
    
    # Get user information
    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    
    # Get user's bookings with facility names and time slot labels
    bookings_data = conn.execute('''
        SELECT b.*, u.name as user_name
        FROM bookings b
        JOIN users u ON b.user_id = u.id
        WHERE b.user_id = ?
        ORDER BY b.date DESC, b.time_slot
    ''', (session['user_id'],)).fetchall()
    
    conn.close()
    
    # Process bookings data
    bookings = []
    for booking in bookings_data:
        # Get facility name
        facility_name = next(f['name'] for f in FACILITIES if f['value'] == booking['facility'])
        
        # Get time slot label
        time_slot_label = next(t['label'] for t in TIME_SLOTS if t['value'] == booking['time_slot'])
        
        # Check if booking is in the past
        booking_date = datetime.strptime(booking['date'], '%Y-%m-%d').date()
        is_past = booking_date < date.today()
        
        bookings.append({
            'facility_name': facility_name,
            'date': booking['date'],
            'time_slot_label': time_slot_label,
            'is_past': is_past
        })
    
    return render_template('profile.html', user=user, bookings=bookings)

if __name__ == '__main__':
    # Make the app accessible from any device on the network
    # 0.0.0.0 means listen on all available network interfaces
    app.run(host='0.0.0.0', port=5000, debug=False) 