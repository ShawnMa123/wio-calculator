#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, jsonify, send_from_directory, session, redirect, url_for
from flask_cors import CORS
from functools import wraps
import sqlite3
import json
import calendar
from datetime import datetime, date, timedelta
import os
import math
import hashlib

# Try to import chinesecalendar, fallback if not available
try:
    import chinesecalendar as cc
    HAS_CHINESE_CALENDAR = True
except ImportError:
    HAS_CHINESE_CALENDAR = False
    print("Warning: chinesecalendar not available, using basic weekend detection only")

app = Flask(__name__)
CORS(app)

# Secret key for session management
app.secret_key = os.environ.get('SECRET_KEY', 'wio-calculator-secret-key-change-in-production')

DATABASE = os.environ.get('DATABASE', 'wio_data.db')

# Default password (hashed with SHA-256)
# Default password is "wio2025", you can change it via environment variable
DEFAULT_PASSWORD_HASH = os.environ.get('PASSWORD_HASH', hashlib.sha256('wio2025'.encode()).hexdigest())

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def login_required(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def init_database():
    conn = get_db_connection()

    # Create daily_status table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS daily_status (
            date TEXT PRIMARY KEY,
            status TEXT NOT NULL,
            work_hours REAL DEFAULT 1.0
        )
    ''')

    # Add work_hours column if it doesn't exist (for existing databases)
    try:
        conn.execute('ALTER TABLE daily_status ADD COLUMN work_hours REAL DEFAULT 1.0')
    except sqlite3.OperationalError:
        pass  # Column already exists

    # Create custom_holidays table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS custom_holidays (
            date TEXT PRIMARY KEY,
            description TEXT,
            is_workday BOOLEAN DEFAULT 0
        )
    ''')

    # Create settings table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    ''')

    # Insert default WIO target if not exists
    existing_target = conn.execute('SELECT value FROM settings WHERE key = ?', ('wio_target',)).fetchone()
    if not existing_target:
        conn.execute('INSERT INTO settings (key, value) VALUES (?, ?)', ('wio_target', '40'))

    conn.commit()
    conn.close()

def is_workday(target_date):
    """Check if a given date is a workday (not weekend or holiday)"""
    # Check if it's weekend
    if target_date.weekday() >= 5:  # Saturday = 5, Sunday = 6
        return False

    # Check Chinese holidays and workdays if available
    if HAS_CHINESE_CALENDAR and cc.is_holiday(target_date):
        return False

    # Check custom holidays
    conn = get_db_connection()
    custom_holiday = conn.execute(
        'SELECT is_workday FROM custom_holidays WHERE date = ?',
        (target_date.strftime('%Y-%m-%d'),)
    ).fetchone()
    conn.close()

    if custom_holiday:
        return bool(custom_holiday['is_workday'])

    return True

def calculate_wio_stats(year, month):
    """Calculate WIO statistics for given year and month"""
    # Get all days in the month
    _, days_in_month = calendar.monthrange(year, month)

    # Get daily status data with work hours
    conn = get_db_connection()
    status_data = conn.execute(
        'SELECT date, status, COALESCE(work_hours, 1.0) as work_hours FROM daily_status WHERE date LIKE ?',
        (f'{year}-{month:02d}-%',)
    ).fetchall()
    conn.close()

    # Convert to dict for easy lookup
    status_dict = {row['date']: {'status': row['status'], 'work_hours': row['work_hours']} for row in status_data}

    # Calculate statistics
    total_workdays = 0.0
    wio_days = 0.0

    for day in range(1, days_in_month + 1):
        current_date = date(year, month, day)
        date_str = current_date.strftime('%Y-%m-%d')

        if is_workday(current_date):
            day_data = status_dict.get(date_str, {'status': 'WFH', 'work_hours': 1.0})
            work_hours = day_data['work_hours']

            # Add work hours to total workdays
            total_workdays += work_hours

            # Check user status for this day and add WIO hours
            if day_data['status'] == 'WIO':
                wio_days += work_hours

    # Calculate WIO percentage
    wio_percentage = (wio_days / total_workdays * 100) if total_workdays > 0 else 0

    return {
        'total_workdays': total_workdays,
        'wio_days': wio_days,
        'wio_percentage': round(wio_percentage, 1),
        'remaining_workdays': total_workdays - wio_days if status_dict else total_workdays
    }

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page and authentication"""
    if request.method == 'POST':
        password = request.form.get('password', '')
        password_hash = hashlib.sha256(password.encode()).hexdigest()

        if password_hash == DEFAULT_PASSWORD_HASH:
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='密码错误，请重试')

    # If already logged in, redirect to main page
    if session.get('logged_in'):
        return redirect(url_for('index'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout and clear session"""
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/api/month_data')
@login_required
def get_month_data():
    year = int(request.args.get('year', datetime.now().year))
    month = int(request.args.get('month', datetime.now().month))

    # Get daily status data for the month
    conn = get_db_connection()
    status_data = conn.execute(
        'SELECT date, status, COALESCE(work_hours, 1.0) as work_hours FROM daily_status WHERE date LIKE ?',
        (f'{year}-{month:02d}-%',)
    ).fetchall()

    # Get custom holidays for this month
    custom_holidays_data = conn.execute(
        'SELECT date, description FROM custom_holidays WHERE date LIKE ?',
        (f'{year}-{month:02d}-%',)
    ).fetchall()

    # Get WIO target
    target_row = conn.execute('SELECT value FROM settings WHERE key = ?', ('wio_target',)).fetchone()
    wio_target = float(target_row['value']) if target_row else 40.0

    conn.close()

    # Convert status data to dict
    status_dict = {row['date']: {'status': row['status'], 'work_hours': row['work_hours']} for row in status_data}

    # Convert custom holidays to dict
    custom_holidays_dict = {row['date']: row['description'] for row in custom_holidays_data}

    # Get calendar data
    _, days_in_month = calendar.monthrange(year, month)
    calendar_data = []

    for day in range(1, days_in_month + 1):
        current_date = date(year, month, day)
        date_str = current_date.strftime('%Y-%m-%d')

        # Determine day type and holiday information
        is_custom_holiday = date_str in custom_holidays_dict
        is_legal_holiday = HAS_CHINESE_CALENDAR and cc.is_holiday(current_date) and current_date.weekday() < 5

        if not is_workday(current_date):
            if current_date.weekday() >= 5:
                day_type = 'weekend'
                holiday_type = None
            else:
                day_type = 'holiday'
                if is_custom_holiday:
                    holiday_type = 'custom'
                elif is_legal_holiday:
                    holiday_type = 'legal'
                else:
                    holiday_type = 'unknown'
        else:
            day_type = 'workday'
            holiday_type = None

        day_data = status_dict.get(date_str, {'status': 'WFH' if day_type == 'workday' else day_type, 'work_hours': 1.0})

        calendar_data.append({
            'date': date_str,
            'day': day,
            'weekday': current_date.weekday(),
            'type': day_type,
            'status': day_data['status'],
            'work_hours': day_data['work_hours'],
            'holiday_type': holiday_type,
            'holiday_description': custom_holidays_dict.get(date_str)
        })

    # Calculate statistics
    stats = calculate_wio_stats(year, month)

    # Calculate days needed to reach target (using ceiling for fractional days)
    target_wio_days = math.ceil(wio_target / 100 * stats['total_workdays'])
    days_needed = max(0, target_wio_days - stats['wio_days'])

    return jsonify({
        'calendar': calendar_data,
        'stats': {
            **stats,
            'wio_target': wio_target,
            'target_wio_days': target_wio_days,
            'days_needed': days_needed
        }
    })

@app.route('/api/day_status', methods=['POST'])
@login_required
def update_day_status():
    data = request.json
    target_date = data['date']
    status = data['status']
    work_hours = data.get('work_hours', 1.0)  # Default to full day

    conn = get_db_connection()
    conn.execute(
        'INSERT OR REPLACE INTO daily_status (date, status, work_hours) VALUES (?, ?, ?)',
        (target_date, status, work_hours)
    )
    conn.commit()
    conn.close()

    return jsonify({'success': True})

@app.route('/api/day_status', methods=['DELETE'])
@login_required
def delete_day_status():
    """Delete WIO/WFH status for a specific date (used when converting to holiday)"""
    data = request.json
    target_date = data['date']

    conn = get_db_connection()
    conn.execute('DELETE FROM daily_status WHERE date = ?', (target_date,))
    conn.commit()
    conn.close()

    return jsonify({'success': True})

@app.route('/api/settings', methods=['GET'])
@login_required
def get_settings():
    conn = get_db_connection()
    settings = conn.execute('SELECT key, value FROM settings').fetchall()
    conn.close()

    settings_dict = {row['key']: row['value'] for row in settings}
    return jsonify(settings_dict)

@app.route('/api/settings', methods=['POST'])
@login_required
def update_settings():
    data = request.json

    conn = get_db_connection()
    for key, value in data.items():
        conn.execute(
            'INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)',
            (key, str(value))
        )
    conn.commit()
    conn.close()

    return jsonify({'success': True})

@app.route('/api/holidays')
@login_required
def get_holidays():
    year = int(request.args.get('year', datetime.now().year))

    # Get custom holidays
    conn = get_db_connection()
    custom_holidays = conn.execute(
        'SELECT date, description, is_workday FROM custom_holidays WHERE date LIKE ?',
        (f'{year}-%',)
    ).fetchall()
    conn.close()

    holidays_list = []

    # Add custom holidays
    for holiday in custom_holidays:
        holidays_list.append({
            'date': holiday['date'],
            'description': holiday['description'],
            'is_workday': bool(holiday['is_workday']),
            'type': 'custom'
        })

    # Add Chinese holidays for current year if available
    if HAS_CHINESE_CALENDAR:
        for month in range(1, 13):
            _, days_in_month = calendar.monthrange(year, month)
            for day in range(1, days_in_month + 1):
                current_date = date(year, month, day)
                if cc.is_holiday(current_date) and current_date.weekday() < 5:  # Weekday holidays
                    date_str = current_date.strftime('%Y-%m-%d')
                    # Don't add if already in custom holidays
                    if not any(h['date'] == date_str for h in holidays_list):
                        holidays_list.append({
                            'date': date_str,
                            'description': '法定节假日',
                            'is_workday': False,
                            'type': 'legal'
                        })

    return jsonify(holidays_list)

@app.route('/api/holidays', methods=['POST'])
@login_required
def add_holiday():
    data = request.json

    conn = get_db_connection()
    conn.execute(
        'INSERT OR REPLACE INTO custom_holidays (date, description, is_workday) VALUES (?, ?, ?)',
        (data['date'], data['description'], data.get('is_workday', False))
    )
    conn.commit()
    conn.close()

    return jsonify({'success': True})

@app.route('/api/holidays', methods=['DELETE'])
@login_required
def delete_holiday():
    target_date = request.args.get('date')

    conn = get_db_connection()
    conn.execute('DELETE FROM custom_holidays WHERE date = ?', (target_date,))
    conn.commit()
    conn.close()

    return jsonify({'success': True})

@app.route('/api/export')
@login_required
def export_data():
    """Export all data as JSON"""
    conn = get_db_connection()

    # Get all daily status records
    daily_status = conn.execute('SELECT * FROM daily_status ORDER BY date').fetchall()

    # Get all custom holidays
    custom_holidays = conn.execute('SELECT * FROM custom_holidays ORDER BY date').fetchall()

    # Get all settings
    settings = conn.execute('SELECT * FROM settings').fetchall()

    conn.close()

    # Convert to dicts
    export_data = {
        'daily_status': [dict(row) for row in daily_status],
        'custom_holidays': [dict(row) for row in custom_holidays],
        'settings': {row['key']: row['value'] for row in settings},
        'export_date': datetime.now().isoformat(),
        'version': '1.0'
    }

    return jsonify(export_data)

@app.route('/api/import', methods=['POST'])
@login_required
def import_data():
    """Import data from JSON"""
    data = request.json

    if not data or 'version' not in data:
        return jsonify({'success': False, 'error': '无效的导入数据格式'}), 400

    try:
        conn = get_db_connection()

        # Import daily status
        if 'daily_status' in data:
            for record in data['daily_status']:
                conn.execute(
                    'INSERT OR REPLACE INTO daily_status (date, status, work_hours) VALUES (?, ?, ?)',
                    (record['date'], record['status'], record.get('work_hours', 1.0))
                )

        # Import custom holidays
        if 'custom_holidays' in data:
            for holiday in data['custom_holidays']:
                conn.execute(
                    'INSERT OR REPLACE INTO custom_holidays (date, description, is_workday) VALUES (?, ?, ?)',
                    (holiday['date'], holiday['description'], holiday.get('is_workday', 0))
                )

        # Import settings
        if 'settings' in data:
            for key, value in data['settings'].items():
                conn.execute(
                    'INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)',
                    (key, value)
                )

        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': '数据导入成功'})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    init_database()
    app.run(debug=True, host='0.0.0.0', port=8080)