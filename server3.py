#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import json
import calendar
from datetime import datetime, date, timedelta
import os

# Try to import chinesecalendar, fallback if not available
try:
    import chinesecalendar as cc
    HAS_CHINESE_CALENDAR = True
except ImportError:
    HAS_CHINESE_CALENDAR = False
    print("Warning: chinesecalendar not available, using basic weekend detection only")

app = Flask(__name__)
CORS(app)

DATABASE = 'wio_data.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    conn = get_db_connection()

    # Create daily_status table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS daily_status (
            date TEXT PRIMARY KEY,
            status TEXT NOT NULL
        )
    ''')

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

    # Get daily status data
    conn = get_db_connection()
    status_data = conn.execute(
        'SELECT date, status FROM daily_status WHERE date LIKE ?',
        (f'{year}-{month:02d}-%',)
    ).fetchall()
    conn.close()

    # Convert to dict for easy lookup
    status_dict = {row['date']: row['status'] for row in status_data}

    # Calculate statistics
    total_workdays = 0
    wio_days = 0

    for day in range(1, days_in_month + 1):
        current_date = date(year, month, day)
        date_str = current_date.strftime('%Y-%m-%d')

        if is_workday(current_date):
            total_workdays += 1

            # Check user status for this day
            user_status = status_dict.get(date_str, 'WIO')  # Default to WIO if not set
            if user_status == 'WIO':
                wio_days += 1

    # Calculate WIO percentage
    wio_percentage = (wio_days / total_workdays * 100) if total_workdays > 0 else 0

    return {
        'total_workdays': total_workdays,
        'wio_days': wio_days,
        'wio_percentage': round(wio_percentage, 1),
        'remaining_workdays': total_workdays - wio_days if status_dict else total_workdays
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/month_data')
def get_month_data():
    year = int(request.args.get('year', datetime.now().year))
    month = int(request.args.get('month', datetime.now().month))

    # Get daily status data for the month
    conn = get_db_connection()
    status_data = conn.execute(
        'SELECT date, status FROM daily_status WHERE date LIKE ?',
        (f'{year}-{month:02d}-%',)
    ).fetchall()

    # Get WIO target
    target_row = conn.execute('SELECT value FROM settings WHERE key = ?', ('wio_target',)).fetchone()
    wio_target = float(target_row['value']) if target_row else 40.0

    conn.close()

    # Convert status data to dict
    status_dict = {row['date']: row['status'] for row in status_data}

    # Get calendar data
    _, days_in_month = calendar.monthrange(year, month)
    calendar_data = []

    for day in range(1, days_in_month + 1):
        current_date = date(year, month, day)
        date_str = current_date.strftime('%Y-%m-%d')

        # Determine day type
        if not is_workday(current_date):
            if current_date.weekday() >= 5:
                day_type = 'weekend'
            else:
                day_type = 'holiday'
        else:
            day_type = 'workday'

        calendar_data.append({
            'date': date_str,
            'day': day,
            'weekday': current_date.weekday(),
            'type': day_type,
            'status': status_dict.get(date_str, 'WIO' if day_type == 'workday' else day_type)
        })

    # Calculate statistics
    stats = calculate_wio_stats(year, month)

    # Calculate days needed to reach target
    days_needed = max(0, int((wio_target / 100 * stats['total_workdays']) - stats['wio_days']))

    return jsonify({
        'calendar': calendar_data,
        'stats': {
            **stats,
            'wio_target': wio_target,
            'days_needed': days_needed
        }
    })

@app.route('/api/day_status', methods=['POST'])
def update_day_status():
    data = request.json
    target_date = data['date']
    status = data['status']

    conn = get_db_connection()
    conn.execute(
        'INSERT OR REPLACE INTO daily_status (date, status) VALUES (?, ?)',
        (target_date, status)
    )
    conn.commit()
    conn.close()

    return jsonify({'success': True})

@app.route('/api/settings', methods=['GET'])
def get_settings():
    conn = get_db_connection()
    settings = conn.execute('SELECT key, value FROM settings').fetchall()
    conn.close()

    settings_dict = {row['key']: row['value'] for row in settings}
    return jsonify(settings_dict)

@app.route('/api/settings', methods=['POST'])
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
def delete_holiday():
    target_date = request.args.get('date')

    conn = get_db_connection()
    conn.execute('DELETE FROM custom_holidays WHERE date = ?', (target_date,))
    conn.commit()
    conn.close()

    return jsonify({'success': True})

if __name__ == '__main__':
    init_database()
    app.run(debug=True, host='127.0.0.1', port=8080)