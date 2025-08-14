# database.py
import sqlite3
import json
from datetime import datetime
import logging
import os

DB_NAME = 'queries.sqlite3'

def init_db():
    """Initializes the database and creates the 'queries' table if it doesn't exist."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # Create table with better structure
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS queries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                case_type TEXT NOT NULL,
                case_number TEXT NOT NULL,
                case_year TEXT NOT NULL,
                was_successful BOOLEAN NOT NULL,
                error_message TEXT,
                parsed_data_json TEXT,
                raw_response_html TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create index for better query performance
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_case_lookup 
            ON queries(case_type, case_number, case_year)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_timestamp 
            ON queries(timestamp)
        ''')
        
        conn.commit()
        conn.close()
        print("✅ Database initialized successfully.")
        print(f"📁 Database file: {os.path.abspath(DB_NAME)}")
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        raise

def log_query(case_type, case_number, case_year, result):
    """Logs a query and its result to the database."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        timestamp = datetime.now().isoformat()
        was_successful = result.get('error') is None and result.get('data') is not None
        error_message = result.get('error') if not was_successful else None
        
        # Enhanced data handling
        parsed_data_json = None
        if was_successful and result.get('data'):
            try:
                # Ensure data is serializable
                parsed_data_json = json.dumps(result['data'], ensure_ascii=False, indent=2)
            except (TypeError, ValueError) as e:
                print(f"⚠️  JSON serialization error: {e}")
                parsed_data_json = json.dumps({"error": f"Serialization failed: {str(e)}"})
        
        raw_html = result.get('raw_html', '')
        
        # Insert with proper error handling
        cursor.execute('''
            INSERT INTO queries (
                timestamp, case_type, case_number, case_year, 
                was_successful, error_message, parsed_data_json, raw_response_html
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            timestamp, case_type, case_number, case_year, 
            was_successful, error_message, parsed_data_json, raw_html
        ))

        query_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Enhanced logging output
        status = "✅ SUCCESS" if was_successful else "❌ FAILED"
        print(f"📝 Query logged to database:")
        print(f"   ID: {query_id}")
        print(f"   Case: {case_type} {case_number}/{case_year}")
        print(f"   Status: {status}")
        print(f"   Timestamp: {timestamp}")
        
        if was_successful:
            data = result.get('data', {})
            print(f"   Petitioner: {data.get('petitioner', 'N/A')}")
            print(f"   Respondent: {data.get('respondent', 'N/A')}")
            print(f"   Orders: {len(data.get('orders', []))}")
        else:
            print(f"   Error: {error_message}")
        
        return query_id
        
    except Exception as e:
        print(f"❌ Failed to log query to database: {e}")
        raise

def get_query_by_id(query_id):
    """Retrieve a specific query by ID"""
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row  # This allows dict-like access
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM queries WHERE id = ?', (query_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            result = dict(row)
            # Parse JSON data back to dict
            if result['parsed_data_json']:
                try:
                    result['parsed_data'] = json.loads(result['parsed_data_json'])
                except json.JSONDecodeError:
                    result['parsed_data'] = None
            return result
        return None
        
    except Exception as e:
        print(f"❌ Failed to retrieve query {query_id}: {e}")
        return None

def get_recent_queries(limit=10):
    """Get recent queries for dashboard display"""
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, timestamp, case_type, case_number, case_year, 
                   was_successful, error_message
            FROM queries 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
        
    except Exception as e:
        print(f"❌ Failed to get recent queries: {e}")
        return []

def search_cases(case_type=None, case_number=None, case_year=None):
    """Search for existing cases in database"""
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Build dynamic query
        where_conditions = []
        params = []
        
        if case_type:
            where_conditions.append("case_type = ?")
            params.append(case_type)
        if case_number:
            where_conditions.append("case_number = ?")
            params.append(case_number)
        if case_year:
            where_conditions.append("case_year = ?")
            params.append(case_year)
        
        where_clause = " WHERE " + " AND ".join(where_conditions) if where_conditions else ""
        
        query = f'''
            SELECT * FROM queries 
            {where_clause}
            ORDER BY timestamp DESC
        '''
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        results = []
        for row in rows:
            result = dict(row)
            if result['parsed_data_json']:
                try:
                    result['parsed_data'] = json.loads(result['parsed_data_json'])
                except json.JSONDecodeError:
                    result['parsed_data'] = None
            results.append(result)
        
        return results
        
    except Exception as e:
        print(f"❌ Failed to search cases: {e}")
        return []

def get_database_stats():
    """Get database statistics"""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # Total queries
        cursor.execute('SELECT COUNT(*) FROM queries')
        total = cursor.fetchone()[0]
        
        # Successful queries
        cursor.execute('SELECT COUNT(*) FROM queries WHERE was_successful = 1')
        successful = cursor.fetchone()[0]
        
        # Failed queries
        cursor.execute('SELECT COUNT(*) FROM queries WHERE was_successful = 0')
        failed = cursor.fetchone()[0]
        
        # Most recent query
        cursor.execute('SELECT timestamp FROM queries ORDER BY timestamp DESC LIMIT 1')
        latest_row = cursor.fetchone()
        latest = latest_row[0] if latest_row else None
        
        conn.close()
        
        success_rate = (successful / total * 100) if total > 0 else 0
        
        return {
            'total_queries': total,
            'successful_queries': successful,
            'failed_queries': failed,
            'success_rate': round(success_rate, 2),
            'latest_query': latest
        }
        
    except Exception as e:
        print(f"❌ Failed to get database stats: {e}")
        return {}

def display_database_contents():
    """Display all database contents for debugging"""
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM queries ORDER BY timestamp DESC')
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            print("📊 Database is empty - no queries logged yet.")
            return
        
        print(f"📊 Database Contents ({len(rows)} entries):")
        print("=" * 80)
        
        for row in rows:
            print(f"ID: {row['id']}")
            print(f"Case: {row['case_type']} {row['case_number']}/{row['case_year']}")
            print(f"Time: {row['timestamp']}")
            print(f"Success: {'✅' if row['was_successful'] else '❌'}")
            
            if row['was_successful'] and row['parsed_data_json']:
                try:
                    data = json.loads(row['parsed_data_json'])
                    print(f"Petitioner: {data.get('petitioner', 'N/A')}")
                    print(f"Respondent: {data.get('respondent', 'N/A')}")
                except:
                    print("Parsed data: Error reading JSON")
            elif row['error_message']:
                print(f"Error: {row['error_message']}")
            
            print("-" * 40)
        
    except Exception as e:
        print(f"❌ Failed to display database contents: {e}")

# Test function to verify database works
def test_database():
    """Test database functionality"""
    print("🧪 Testing database functionality...")
    
    # Initialize database
    init_db()
    
    # Test data
    test_result = {
        'data': {
            'petitioner': 'TEST PETITIONER',
            'respondent': 'TEST RESPONDENT',
            'case_status': 'PENDING',
            'filing_date': '01/01/2025',
            'next_hearing_date': '15/01/2025',
            'orders': [
                {
                    'description': 'Test Order',
                    'pdf_link': 'https://example.com/test.pdf',
                    'date': '01/01/2025'
                }
            ]
        },
        'raw_html': '<html>Test HTML</html>',
        'error': None
    }
    
    # Log test query
    query_id = log_query("W.P.(C)", "TEST", "2025", test_result)
    
    # Retrieve and verify
    retrieved = get_query_by_id(query_id)
    if retrieved:
        print("✅ Database test successful!")
        print(f"Retrieved data: {retrieved['parsed_data']['petitioner']}")
    else:
        print("❌ Database test failed!")
    
    # Show stats
    stats = get_database_stats()
    print(f"📊 Database stats: {stats}")

if __name__ == "__main__":
    # Run tests when file is executed directly
    test_database()
