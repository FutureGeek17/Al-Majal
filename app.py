from flask import (
    Flask, render_template, request, redirect, url_for, 
    flash, session, send_file, send_from_directory, g, jsonify
)
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_wtf.csrf import CSRFProtect
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime, date, timedelta, time
import calendar
import pandas as pd
import io
import os
import random
import secrets
import logging
import mimetypes
from config import config
from init_db import init_db
from urllib.parse import urlparse, urljoin
import bcrypt

# Define available facilities
FACILITIES = [
    {'value': 'football', 'name': 'Football Field'},
    {'value': 'basketball', 'name': 'Basketball Court'},
    {'value': 'volleyball', 'name': 'Volleyball Court'},
    {'value': 'tennis', 'name': 'Tennis Court'},
    {'value': 'gym', 'name': 'Gymnasium'}
]

# Configure logging with more detailed output
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log', mode='w')
    ]
)
logger = logging.getLogger(__name__)

# Create the Flask app
app = Flask(__name__, 
           static_folder=config['development'].STATIC_FOLDER,
           template_folder=config['development'].TEMPLATES_FOLDER)

# Load config
app.config.from_object(config['development'])

# Ensure we have a stable secret key
if not os.environ.get('SECRET_KEY'):
    # If no environment variable, use the one from config
    app.secret_key = config['development'].SECRET_KEY
else:
    app.secret_key = os.environ.get('SECRET_KEY')

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

# Initialize CSRF protection
csrf = CSRFProtect(app)
csrf.init_app(app)

# Exempt some routes from CSRF protection if needed
csrf_exempt_routes = ['/webhook']  # Add any routes that need CSRF exemption
for route in csrf_exempt_routes:
    csrf.exempt(route)

# Configure session
app.config['SESSION_COOKIE_SECURE'] = not app.debug  # True in production
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, id, phone, is_admin=False):
        self.id = id
        self.phone = phone
        self.is_admin = bool(is_admin)

    def get_id(self):
        return str(self.id)

@login_manager.user_loader
def load_user(user_id):
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    if user:
        return User(user['id'], user['phone'], user['is_admin'])
    return None

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect('database.db')
        g.db.row_factory = sqlite3.Row
    return g.db

def get_db_with_commit():
    """Get a database connection and ensure changes are committed"""
    db = get_db()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        raise e

@app.teardown_appcontext
def close_db(error):
    db = g.pop('db', None)
    if db is not None:
        db.close()

@app.context_processor
def utility_processor():
    return dict(current_user=current_user)

# Initialize database on startup
try:
    init_db()
    logger.info("Database initialized successfully")
except Exception as e:
    logger.error(f"Error initializing database: {e}")

# Context processor for year
@app.context_processor
def inject_year():
    return {'now': datetime.now()}

# Define route access levels
ROUTE_ACCESS = {
    '/': {'public': True},
    '/login': {'public': True},
    '/register': {'public': True},
    '/about-camp': {'public': True},
    '/about-almajal': {'public': True},
    '/activities': {'public': True},
    '/terms': {'public': True},
    '/privacy': {'public': True},
    '/community-events': {'public': True},
    '/booking': {'requires_auth': True, 'admin_only': False},
    '/admin': {'requires_auth': True, 'admin_only': True},
    '/profile': {'requires_auth': True, 'admin_only': False},
    '/view_bookings': {'requires_auth': True, 'admin_only': False},
    '/submit-booking': {'requires_auth': True, 'admin_only': False},
    '/get-time-slots': {'requires_auth': True, 'admin_only': False},
    '/check-activity-availability': {'requires_auth': True, 'admin_only': False}
}

def get_redirect_target():
    """Get safe redirect target from URL arguments or session"""
    for target in (request.args.get('next'), session.get('next')):
        if target and is_safe_url(target):
            return target

def get_default_redirect():
    """Get default redirect based on user type"""
    if current_user.is_authenticated:
        if current_user.is_admin:
            return url_for('admin_dashboard')
        return url_for('booking')
    return url_for('home')

@app.before_request
def before_request():
    # Skip static files
    if request.path.startswith('/static/'):
        return None

    # Get route configuration
    route_config = ROUTE_ACCESS.get(request.path, {'requires_auth': True, 'admin_only': False})
    
    # Allow public routes
    if route_config.get('public', False):
        return None

    # Handle authentication requirement
    if route_config.get('requires_auth', True):
        if not current_user.is_authenticated:
            # Store current path for post-login redirect
            if request.method == 'GET':
                session['next'] = request.full_path
            return redirect(url_for('login', next=request.full_path))

        # Handle admin-only routes
        if route_config.get('admin_only', False) and not current_user.is_admin:
            flash('You do not have permission to access this page.', 'danger')
            return redirect(get_default_redirect())

    return None

@app.route('/')
def home():
    """Home page is always accessible and shows different navigation options based on auth status"""
    return render_template('index.html')

@app.route('/about-camp')
def about_camp():
    return render_template('about-camp.html')

@app.route('/community-events')
def community_events():
    return render_template('community-events.html')

@app.route('/activities')
def activities():
    return render_template('activities.html')

@app.route('/view_bookings')
@login_required
def view_bookings():
    try:
        conn = get_db()
        # Get user's bookings with activity details
        bookings = conn.execute('''
            SELECT 
                b.*,
                a.name as activity_name,
                a.type as activity_type,
                a.description as activity_description
            FROM bookings b
            JOIN activities a ON b.activity_id = a.id
            WHERE b.user_id = ?
            AND b.date >= DATE('now')
            ORDER BY b.date ASC, b.time ASC
        ''', (current_user.id,)).fetchall()

        # Group bookings by date
        bookings_by_date = {}
        for booking in bookings:
            date_str = booking['date']
            if date_str not in bookings_by_date:
                bookings_by_date[date_str] = []
            bookings_by_date[date_str].append(dict(booking))

        return render_template('view_bookings.html', bookings=bookings_by_date)
    except Exception as e:
        logger.error(f"Error in view_bookings: {e}")
        flash('An error occurred while loading your bookings. Please try again.', 'error')
        return redirect(url_for('home'))

def get_week_number(date_obj):
    """Get ISO week number for a given date."""
    return date_obj.isocalendar()[1]

def get_available_time_slots(activity_id, booking_date):
    """Get available time slots for a given activity and date."""
    time_slots = []
    start_time = time(17, 0)  # 5 PM
    end_time = time(22, 0)  # 10 PM
    
    # Mini golf uses 30-minute slots, others use 1-hour slots
    slot_duration = 30 if activity_id == 'mini-golf' else 60
    
    current_time = start_time
    while current_time < end_time:
        slot_end = (datetime.combine(date.today(), current_time) + 
                   timedelta(minutes=slot_duration)).time()
        
        if slot_end <= end_time:
            slot = {
                'value': current_time.strftime('%H:%M'),
                'label': f"{current_time.strftime('%I:%M %p')} - {slot_end.strftime('%I:%M %p')}",
                'booked': False
            }
            time_slots.append(slot)
        
        current_time = slot_end
    
    # Mark booked slots
    conn = get_db()
    try:
        booked_slots = conn.execute('''
            SELECT time_slot 
            FROM bookings 
            WHERE activity_id = ? AND date = ? AND status != 'cancelled'
        ''', (activity_id, booking_date)).fetchall()
        
        for slot in time_slots:
            if any(slot['value'] == booked['time_slot'] for booked in booked_slots):
                slot['booked'] = True
    finally:
        conn.close()
    
    return time_slots

def check_booking_eligibility(user_id, activity_id, booking_date):
    """
    Check if a user is eligible to book an activity on a given date.
    Returns (is_eligible, message)
    """
    conn = get_db()
    try:
        # Get the week number for the booking date
        booking_week = get_week_number(datetime.strptime(booking_date, '%Y-%m-%d'))
        
        # Get all bookings for this user in the same week
        bookings = conn.execute('''
            SELECT activity_id, COUNT(*) as count 
            FROM bookings 
            WHERE user_id = ? AND week_number = ? AND activity_id = ?
            GROUP BY activity_id
        ''', (user_id, booking_week, activity_id)).fetchone()
        
        # Check activity-specific limits
        if activity_id == 'mini-golf':
            # Mini golf: max 2 bookings per week
            if bookings and bookings['count'] >= 2:
                return False, "You've reached the maximum mini golf bookings (2) for this week"
        else:
            # Other activities: max 1 booking per activity per week
            if bookings and bookings['count'] >= 1:
                return False, f"You've already booked this activity for this week"
        
        # Check if the time slot is available
        existing_booking = conn.execute('''
            SELECT id FROM bookings 
            WHERE activity_id = ? AND date = ? AND time_slot = ?
        ''', (activity_id, booking_date, time_slot)).fetchone()
        
        if existing_booking:
            return False, "This time slot is already booked"
            
        return True, "Eligible for booking"
        
    except Exception as e:
        logger.error(f"Error checking booking eligibility: {str(e)}")
        return False, "An error occurred while checking booking eligibility"

@app.route('/booking')
@login_required
def booking():
    try:
        conn = get_db()
        activities = conn.execute('''
            SELECT 
                a.*,
                CASE 
                    WHEN EXISTS (
                        SELECT 1 FROM bookings b 
                        WHERE b.activity_id = a.id 
                        AND b.date = DATE('now')
                        AND b.status = 'confirmed'
                    ) THEN 'busy'
                    ELSE 'available'
                END as current_status
            FROM activities a
            WHERE a.status = 'active'
            ORDER BY a.type, a.name
        ''').fetchall()

        # Convert to list of dicts and add image paths
        activities_list = []
        for activity in activities:
            activity_dict = dict(activity)
            image_path = f'images/activities/{activity_dict["name"].lower().replace(" ", "-")}.jpg'
            if not os.path.exists(os.path.join('static', image_path)):
                image_path = 'images/activities/default.jpg'
            activity_dict['image'] = image_path
            activities_list.append(activity_dict)

        return render_template('booking.html', activities=activities_list)
    except Exception as e:
        logger.error(f"Error in booking route: {str(e)}")
        flash('An error occurred while loading activities. Please try again.', 'error')
        return redirect(url_for('home'))

@app.route('/booking/create', methods=['POST'])
@login_required
def create_booking():
    try:
        data = request.get_json()
        activity_id = data.get('activity_id')
        booking_date = data.get('date')
        start_time = data.get('time')
        participants = data.get('participants', 1)
        notes = data.get('notes', '')

        if not all([activity_id, booking_date, start_time]):
            return jsonify({'error': 'Missing required fields'}), 400

        # Validate date format
        try:
            booking_date_obj = datetime.strptime(booking_date, '%Y-%m-%d').date()
            if booking_date_obj < date.today():
                return jsonify({'error': 'Cannot book dates in the past'}), 400
        except ValueError:
            return jsonify({'error': 'Invalid date format'}), 400

        # Get activity details
        conn = get_db()
        activity = conn.execute('SELECT * FROM activities WHERE id = ?', (activity_id,)).fetchone()
        
        if not activity:
            return jsonify({'error': 'Activity not found'}), 404

        # Check if time slot is valid
        try:
            datetime.strptime(start_time, '%H:%M')
        except ValueError:
            return jsonify({'error': 'Invalid time format'}), 400

        # Calculate end time based on activity duration
        duration = activity['duration'] or 60  # Default to 60 minutes if not specified
        start_time_obj = datetime.strptime(start_time, '%H:%M')
        end_time_obj = start_time_obj + timedelta(minutes=duration)
        end_time = end_time_obj.strftime('%H:%M')

        # Check if slot is available
        existing_booking = conn.execute('''
            SELECT id FROM bookings 
            WHERE activity_id = ? AND date = ? AND start_time = ? AND status != 'cancelled'
        ''', (activity_id, booking_date, start_time)).fetchone()

        if existing_booking:
            return jsonify({'error': 'This time slot is already booked'}), 400

        # Create booking
        conn.execute('''
            INSERT INTO bookings (
                user_id, activity_id, date, start_time, end_time,
                participants, notes, status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        ''', (
            current_user.id,
            activity_id,
            booking_date,
            start_time,
            end_time,
            participants,
            notes,
            'confirmed'
        ))
        
        conn.commit()
        return jsonify({'success': True})

    except Exception as e:
        logger.error(f"Error submitting booking: {e}")
        return jsonify({'error': 'Failed to create booking'}), 500

@app.route('/booking/check-availability', methods=['POST'])
@login_required
def check_availability():
    try:
        data = request.get_json()
        activity_id = data.get('activity_id')
        date = data.get('date')

        if not all([activity_id, date]):
            return jsonify({'error': 'Missing required fields'}), 400

        conn = get_db()
        
        # Get all bookings for the activity on the selected date
        bookings = conn.execute('''
            SELECT time 
            FROM bookings 
            WHERE activity_id = ? 
            AND date = ? 
            AND status = 'confirmed'
        ''', (activity_id, date)).fetchall()

        booked_slots = [booking['time'] for booking in bookings]
        
        # Get activity details
        activity = conn.execute('SELECT * FROM activities WHERE id = ?', (activity_id,)).fetchone()
        
        # Generate all possible time slots (5 PM to 10 PM)
        all_slots = []
        start_time = datetime.strptime('17:00', '%H:%M')
        end_time = datetime.strptime('22:00', '%H:%M')
        slot_duration = activity['duration']  # in minutes
        
        current_slot = start_time
        while current_slot <= end_time:
            slot_time = current_slot.strftime('%H:%M')
            all_slots.append({
                'time': slot_time,
                'available': slot_time not in booked_slots
            })
            current_slot += timedelta(minutes=slot_duration)

        return jsonify({
            'slots': all_slots,
            'duration': slot_duration
        })

    except Exception as e:
        logger.error(f"Error checking availability: {str(e)}")
        return jsonify({'error': 'Failed to check availability'}), 500

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('You do not have permission to access this page.', 'danger')
            return redirect(get_default_redirect())
        return f(*args, **kwargs)
    return decorated_function

def is_safe_url(target):
    """Check if the URL is safe for redirection"""
    if not target:
        return False
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    # Check if it's a relative path or matches our host
    # Also ensure it's not a static file path
    return (test_url.scheme in ('http', 'https') and
            ref_url.netloc == test_url.netloc and
            not test_url.path.startswith('/static/') and
            not test_url.path.startswith('/css/') and
            not test_url.path.startswith('/js/'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        phone = request.form.get('phone')
        password = request.form.get('password')
        
        logger.debug(f"Login attempt for phone: {phone}")
        
        conn = get_db()
        try:
            user = conn.execute('SELECT * FROM users WHERE phone = ?', (phone,)).fetchone()
            
            if user:
                try:
                    # Get the stored hash and convert password to bytes
                    stored_hash = user['password']
                    password_bytes = password.encode('utf-8')
                    
                    # Verify the password
                    if bcrypt.checkpw(password_bytes, stored_hash.encode('utf-8')):
                        user_obj = User(user['id'], user['phone'], user['is_admin'])
                        login_user(user_obj)
                        flash('Logged in successfully!', 'success')
                        
                        # Get the next page from the session or URL parameters
                        next_page = get_redirect_target()
                        if next_page:
                            return redirect(next_page)
                        
                        # If no next page, redirect based on user type
                        if user['is_admin']:
                            return redirect(url_for('admin_dashboard'))
                        return redirect(url_for('home'))
                    else:
                        logger.warning(f"Invalid password for user: {phone}")
                except Exception as e:
                    logger.error(f"Error verifying password: {str(e)}", exc_info=True)
            else:
                logger.warning(f"No user found with phone: {phone}")
            
            flash('Invalid phone number or password', 'error')
            return redirect(url_for('login'))
            
        except Exception as e:
            logger.error(f"Login error: {str(e)}", exc_info=True)
            flash('An error occurred during login. Please try again.', 'error')
            return redirect(url_for('login'))
        finally:
            conn.close()
        
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        id_number = request.form.get('id_number')
        terms = request.form.get('terms')

        if not all([name, phone, password, confirm_password, id_number, terms]):
            flash('All fields are required, including accepting the terms and conditions.', 'error')
            return redirect(url_for('register'))

        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('register'))

        # Hash the password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        try:
            conn = get_db()
            cursor = conn.cursor()
            
            # Check if phone number already exists
            cursor.execute('SELECT id FROM users WHERE phone = ?', (phone,))
            if cursor.fetchone() is not None:
                flash('Phone number already registered.', 'error')
                return redirect(url_for('register'))
                
            # Check if ID number already exists
            cursor.execute('SELECT id FROM users WHERE id_number = ?', (id_number,))
            if cursor.fetchone() is not None:
                flash('ID number already registered.', 'error')
                return redirect(url_for('register'))

            # Insert the new user
            cursor.execute('''
                INSERT INTO users (name, phone, password, id_number)
                VALUES (?, ?, ?, ?)
            ''', (name, phone, hashed_password, id_number))
            conn.commit()

            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))

        except sqlite3.Error as e:
            flash('An error occurred. Please try again.', 'error')
            return redirect(url_for('register'))

    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

@app.route('/profile')
@login_required
def profile():
    conn = get_db()
    try:
        # Get user's booking history
        bookings = conn.execute('''
            SELECT b.*, a.name as activity_name,
                   date(b.date) as formatted_date,
                   time(b.time) as formatted_time,
                   CASE 
                       WHEN b.date > date('now') OR (b.date = date('now') AND b.time > time('now')) 
                       THEN 'upcoming'
                       ELSE 'past'
                   END as booking_status
            FROM bookings b
            JOIN activities a ON b.activity_id = a.id
            WHERE b.user_id = ?
            ORDER BY b.date DESC, b.time DESC
            LIMIT 5
        ''', (current_user.id,)).fetchall()
        
        # Get user's favorite activities (most booked)
        favorite_activities = conn.execute('''
            SELECT a.name, COUNT(*) as booking_count
            FROM bookings b
            JOIN activities a ON b.activity_id = a.id
            WHERE b.user_id = ?
            GROUP BY a.id
            ORDER BY booking_count DESC
            LIMIT 3
        ''', (current_user.id,)).fetchall()
        
        return render_template('profile.html', 
                             bookings=bookings,
                             favorite_activities=favorite_activities)
    finally:
        conn.close()

@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    logger.debug(f"Admin dashboard accessed by user {current_user.id}, is_admin: {current_user.is_admin}")
    
    conn = get_db()
    try:
        # Get all bookings with user information
        bookings = conn.execute('''
            SELECT b.*, u.name as user_name, u.phone as user_phone,
                   date(b.date) as formatted_date,
                   time(b.time_slot) as formatted_time,
                   CASE 
                       WHEN b.date > date('now') OR (b.date = date('now') AND b.time_slot > time('now')) 
                       THEN 'upcoming'
                       ELSE 'past'
                   END as booking_status
            FROM bookings b
            JOIN users u ON b.user_id = u.id
            ORDER BY b.date DESC, b.time_slot DESC
        ''').fetchall()
        
        # Convert the results to a list of dictionaries
        bookings_list = []
        for booking in bookings:
            booking_dict = dict(booking)
            bookings_list.append(booking_dict)
        
        logger.debug("Rendering admin template")
        return render_template('admin.html', bookings=bookings_list)
    except Exception as e:
        logger.error(f"Error in admin dashboard: {str(e)}")
        flash('An error occurred while loading the dashboard.', 'danger')
        return redirect(url_for('home'))
    finally:
        conn.close()

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/submit-booking', methods=['POST'])
@login_required
def submit_booking():
    try:
        data = request.get_json()
        
        if not all(key in data for key in ['activity_id', 'date', 'time', 'participants']):
            return jsonify({'error': 'Missing required fields'}), 400

        conn = get_db()
        
        # Verify activity exists and is active
        activity = conn.execute(
            'SELECT * FROM activities WHERE id = ? AND is_active = 1',
            (data['activity_id'],)
        ).fetchone()
        
        if not activity:
            return jsonify({'error': 'Activity not found or inactive'}), 404

        # Check if slot is available
        booked = conn.execute('''
            SELECT COUNT(*) as count
            FROM bookings
            WHERE activity_id = ? 
            AND date = ?
            AND time = ?
            AND status = 'confirmed'
        ''', (data['activity_id'], data['date'], data['time'])).fetchone()['count']

        if booked >= activity['capacity']:
            return jsonify({'error': 'Time slot is fully booked'}), 400

        # Create booking
        conn.execute('''
            INSERT INTO bookings (
                user_id, activity_id, date, time, 
                participants, notes, status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
        ''', (
            current_user.id,
            data['activity_id'],
            data['date'],
            data['time'],
            data['participants'],
            data.get('notes', ''),
            'confirmed'
        ))
        
        conn.commit()
        return jsonify({'success': True})

    except Exception as e:
        logger.error(f"Error submitting booking: {e}")
        return jsonify({'error': 'Failed to create booking'}), 500

@app.route('/get-time-slots')
@login_required
def get_time_slots():
    try:
        activity_id = request.args.get('activity_id')
        date_str = request.args.get('date')
        
        if not activity_id or not date_str:
            return jsonify({'error': 'Missing required parameters'}), 400
            
        # Convert date string to date object
        try:
            booking_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format'}), 400
            
        # Check if date is in the past
        if booking_date < date.today():
            return jsonify({'error': 'Cannot book dates in the past'}), 400
            
        # Get activity details
        conn = get_db()
        activity = conn.execute('SELECT * FROM activities WHERE id = ?', (activity_id,)).fetchone()
        
        if not activity:
            return jsonify({'error': 'Activity not found'}), 404
            
        # Define time slots based on activity duration
        duration = activity['duration'] or 60  # Default to 60 minutes if not specified
        start_time = time(17, 0)  # 5:00 PM
        end_time = time(22, 0)   # 10:00 PM
        
        # Generate all possible time slots
        time_slots = []
        current_time = start_time
        while current_time < end_time:  # Changed from <= to < to avoid going past end time
            slot_end = datetime.combine(date.today(), current_time) + timedelta(minutes=duration)
            if slot_end.time() <= end_time:
                time_slots.append({
                    'start_time': current_time.strftime('%H:%M'),
                    'end_time': slot_end.time().strftime('%H:%M'),
                    'available': True
                })
            current_time = slot_end.time()
            
        # Get existing bookings for this activity and date
        bookings = conn.execute('''
            SELECT start_time 
            FROM bookings 
            WHERE activity_id = ? AND date = ? AND status != 'cancelled'
        ''', (activity_id, date_str)).fetchall()
        
        # Mark booked slots as unavailable
        booked_times = [booking['start_time'] for booking in bookings]
        for slot in time_slots:
            if slot['start_time'] in booked_times:
                slot['available'] = False
                
        # Check if user has already booked this activity for this date
        user_booking = conn.execute('''
            SELECT id 
            FROM bookings 
            WHERE user_id = ? AND activity_id = ? AND date = ?
        ''', (current_user.id, activity_id, date_str)).fetchone()
        
        if user_booking:
            return jsonify({'error': 'You already have a booking for this activity on this date'}), 400
            
        return jsonify(time_slots)
        
    except Exception as e:
        logger.error(f"Error in get_time_slots: {e}")
        return jsonify({'error': 'An error occurred while fetching time slots'}), 500

@app.route('/check-activity-availability')
@login_required
def check_activity_availability():
    activity_id = request.args.get('activity_id')
    if not activity_id:
        return jsonify({'error': 'Activity ID is required'}), 400

    try:
        conn = get_db()
        # Get current date
        today = date.today()
        
        # Check if activity exists and is active
        activity = conn.execute(
            'SELECT * FROM activities WHERE id = ?',
            (activity_id,)
        ).fetchone()
        
        if not activity:
            return jsonify({
                'available': False,
                'message': 'Activity not found'
            })

        # Get bookings for today
        bookings = conn.execute('''
            SELECT COUNT(*) as count 
            FROM bookings 
            WHERE activity_id = ? 
            AND date = ? 
            AND status = 'confirmed'
        ''', (activity_id, today)).fetchone()

        # Check availability based on capacity
        is_available = bookings['count'] < activity['capacity']
        
        return jsonify({
            'available': is_available,
            'message': 'Available' if is_available else 'Fully booked for today'
        })

    except Exception as e:
        logger.error(f"Error checking activity availability: {e}")
        return jsonify({
            'error': 'Failed to check availability'
        }), 500

@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@app.route('/booking/<int:booking_id>/cancel', methods=['POST'])
@login_required
def cancel_booking(booking_id):
    try:
        conn = get_db()
        
        # Verify booking belongs to user
        booking = conn.execute('''
            SELECT * FROM bookings 
            WHERE id = ? AND user_id = ?
        ''', (booking_id, current_user.id)).fetchone()
        
        if not booking:
            return jsonify({'error': 'Booking not found'}), 404

        # Cancel booking
        conn.execute('''
            UPDATE bookings 
            SET status = 'cancelled' 
            WHERE id = ?
        ''', (booking_id,))
        
        conn.commit()
        return jsonify({'success': True})

    except Exception as e:
        logger.error(f"Error cancelling booking: {e}")
        return jsonify({'error': 'Failed to cancel booking'}), 500

@app.route('/debug/users')
def debug_users():
    if not app.debug:
        return "Not available in production", 404
        
    conn = get_db()
    try:
        users = conn.execute('SELECT id, name, phone, id_number, is_admin FROM users').fetchall()
        return '<br>'.join([f"ID: {u['id']}, Name: {u['name']}, Phone: {u['phone']}, ID#: {u['id_number']}, Admin: {u['is_admin']}" for u in users])
    finally:
        conn.close()

if __name__ == '__main__':
    # Get port from environment variable or use default
    port = int(os.environ.get('PORT', 10000))
    
    # Use 0.0.0.0 to make the server publicly accessible
    host = os.environ.get('HOST', '0.0.0.0')
    
    app.run(host=host, port=port, debug=False) 