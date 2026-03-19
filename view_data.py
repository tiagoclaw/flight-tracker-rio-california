#!/usr/bin/env python3
"""
View stored flight price data from SQLite database.
"""

import sqlite3
import os
from datetime import datetime
import json

def connect_to_db(db_path='data/flights.db'):
    """Connect to the SQLite database."""
    if not os.path.exists(db_path):
        print(f"❌ Database not found at: {db_path}")
        return None
    
    return sqlite3.connect(db_path)

def show_database_info(db_path='data/flights.db'):
    """Show general database information."""
    
    conn = connect_to_db(db_path)
    if not conn:
        return
    
    cursor = conn.cursor()
    
    print("📊 DATABASE INFORMATION")
    print("=" * 50)
    print(f"📍 Location: {os.path.abspath(db_path)}")
    print(f"📁 Size: {os.path.getsize(db_path) / 1024:.1f} KB")
    print()
    
    # Count total flights
    cursor.execute("SELECT COUNT(*) FROM flights")
    total_flights = cursor.fetchone()[0]
    
    # Count alerts
    cursor.execute("SELECT COUNT(*) FROM price_alerts")
    total_alerts = cursor.fetchone()[0]
    
    print(f"✈️  Total flights stored: {total_flights}")
    print(f"🚨 Total alerts generated: {total_alerts}")
    print()
    
    if total_flights > 0:
        # Date range
        cursor.execute("SELECT MIN(checked_at), MAX(checked_at) FROM flights")
        min_date, max_date = cursor.fetchone()
        print(f"📅 Data range: {min_date} → {max_date}")
        
        # Routes
        cursor.execute("""
            SELECT departure_airport || '-' || arrival_airport as route, COUNT(*) as count
            FROM flights 
            GROUP BY departure_airport, arrival_airport 
            ORDER BY count DESC
        """)
        
        routes = cursor.fetchall()
        print("\n🛫 Routes monitored:")
        for route, count in routes:
            print(f"   {route}: {count} flights")
    
    conn.close()

def show_recent_flights(db_path='data/flights.db', limit=20):
    """Show most recent flights."""
    
    conn = connect_to_db(db_path)
    if not conn:
        return
    
    cursor = conn.cursor()
    
    print(f"\n🕒 RECENT FLIGHTS (Last {limit})")
    print("=" * 70)
    
    cursor.execute("""
        SELECT departure_airport, arrival_airport, departure_date, 
               price, airline, stops, checked_at, source
        FROM flights 
        ORDER BY checked_at DESC 
        LIMIT ?
    """, (limit,))
    
    flights = cursor.fetchall()
    
    if not flights:
        print("No flights found in database.")
        conn.close()
        return
    
    for i, flight in enumerate(flights, 1):
        dep_airport, arr_airport, dep_date, price, airline, stops, checked_at, source = flight
        
        stops_text = "Direct" if stops == 0 else f"{stops} stop{'s' if stops > 1 else ''}"
        
        print(f"{i:2}. {dep_airport}-{arr_airport} | R$ {price:>8,.2f} | {airline}")
        print(f"    📅 {dep_date} | {stops_text} | 🕒 {checked_at} | 📡 {source}")
        print()
    
    conn.close()

def show_price_statistics(db_path='data/flights.db'):
    """Show price statistics by route."""
    
    conn = connect_to_db(db_path)
    if not conn:
        return
    
    cursor = conn.cursor()
    
    print("\n💰 PRICE STATISTICS BY ROUTE")
    print("=" * 50)
    
    cursor.execute("""
        SELECT departure_airport || '-' || arrival_airport as route,
               COUNT(*) as count,
               MIN(price) as min_price,
               MAX(price) as max_price,
               AVG(price) as avg_price,
               MIN(checked_at) as first_check,
               MAX(checked_at) as last_check
        FROM flights 
        GROUP BY departure_airport, arrival_airport 
        ORDER BY route
    """)
    
    stats = cursor.fetchall()
    
    for route, count, min_price, max_price, avg_price, first_check, last_check in stats:
        print(f"\n✈️  Route: {route}")
        print(f"   📊 Records: {count}")
        print(f"   💰 Price range: R$ {min_price:,.2f} - R$ {max_price:,.2f}")
        print(f"   📈 Average: R$ {avg_price:,.2f}")
        print(f"   📅 Period: {first_check} → {last_check}")
    
    conn.close()

def show_alerts_history(db_path='data/flights.db'):
    """Show price alerts history."""
    
    conn = connect_to_db(db_path)
    if not conn:
        return
    
    cursor = conn.cursor()
    
    print("\n🚨 PRICE ALERTS HISTORY")
    print("=" * 50)
    
    cursor.execute("""
        SELECT route, price, drop_percentage, alert_sent_at
        FROM price_alerts 
        ORDER BY alert_sent_at DESC
        LIMIT 20
    """)
    
    alerts = cursor.fetchall()
    
    if not alerts:
        print("No alerts found in database.")
        conn.close()
        return
    
    for i, (route, price, drop_pct, sent_at) in enumerate(alerts, 1):
        print(f"{i:2}. {route} | R$ {price:,.2f} | 📉 {drop_pct:.1f}% drop | 🕒 {sent_at}")
    
    conn.close()

def export_data_json(db_path='data/flights.db', output_file='flight_data.json'):
    """Export all data to JSON."""
    
    conn = connect_to_db(db_path)
    if not conn:
        return
    
    cursor = conn.cursor()
    
    # Get flights
    cursor.execute("""
        SELECT id, departure_airport, arrival_airport, departure_date, return_date,
               price, airline, source, stops, checked_at
        FROM flights ORDER BY checked_at DESC
    """)
    
    flights = []
    for row in cursor.fetchall():
        flights.append({
            'id': row[0],
            'departure_airport': row[1],
            'arrival_airport': row[2], 
            'departure_date': row[3],
            'return_date': row[4],
            'price': row[5],
            'airline': row[6],
            'source': row[7],
            'stops': row[8],
            'checked_at': row[9]
        })
    
    # Get alerts
    cursor.execute("""
        SELECT id, route, price, drop_percentage, alert_sent_at
        FROM price_alerts ORDER BY alert_sent_at DESC
    """)
    
    alerts = []
    for row in cursor.fetchall():
        alerts.append({
            'id': row[0],
            'route': row[1],
            'price': row[2],
            'drop_percentage': row[3],
            'alert_sent_at': row[4]
        })
    
    data = {
        'export_time': datetime.now().isoformat(),
        'database_path': db_path,
        'flights': flights,
        'alerts': alerts,
        'summary': {
            'total_flights': len(flights),
            'total_alerts': len(alerts)
        }
    }
    
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    
    print(f"✅ Data exported to: {output_file}")
    print(f"📊 Exported {len(flights)} flights and {len(alerts)} alerts")
    
    conn.close()

def main():
    """Main function to view all data."""
    
    print("🛫 FLIGHT TRACKER DATA VIEWER")
    print("=" * 60)
    
    db_path = 'data/flights.db'
    
    # Check if database exists
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        print("🔍 Looking for alternative locations...")
        
        # Try Railway path
        railway_path = '/app/data/flights.db'
        if os.path.exists(railway_path):
            db_path = railway_path
            print(f"✅ Found database at: {railway_path}")
        else:
            print("❌ No database found. Run the monitoring system first.")
            return
    
    # Show all information
    show_database_info(db_path)
    show_recent_flights(db_path, 15)
    show_price_statistics(db_path)
    show_alerts_history(db_path)
    
    # Export option
    print(f"\n💾 Export data to JSON:")
    export_data_json(db_path, 'flight_data_export.json')

if __name__ == "__main__":
    main()