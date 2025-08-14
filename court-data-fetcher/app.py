# app.py - Complete Court Data Fetcher Flask Application
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
import asyncio
import json
import os
import logging
from datetime import datetime
from scraper import fetch_case_data
from database import init_db, log_query, get_recent_queries, search_cases, get_database_stats, get_query_by_id

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, 
            static_folder='static',
            static_url_path='/static',
            template_folder='templates')

# Secret key for session management and flash messages
app.secret_key = 'court_data_fetcher_secret_key_2025_change_in_production'

# Enable debug mode for development
app.config['DEBUG'] = True

# Updated case types specifically for Delhi High Court
CASE_TYPES = [
    ("W.P.(C)", "Writ Petition (Civil)"),
    ("W.P.(CRL)", "Writ Petition (Criminal)"),
    ("CRL.A.", "Criminal Appeal"),
    ("CRL.M.C.", "Criminal Miscellaneous Case"),
    ("CRL.REV.P.", "Criminal Revision Petition"),
    ("C.M.", "Civil Miscellaneous"),
    ("C.S.(OS)", "Civil Suit (Original Side)"),
    ("C.S.(COMM)", "Civil Suit (Commercial)"),
    ("FAO(OS)", "First Appeal from Original Side"),
    ("FAO(COMM)", "First Appeal (Commercial)"),
    ("RFA", "Regular First Appeal"),
    ("ARB.A.", "Arbitration Appeal"),
    ("ARB.P.", "Arbitration Petition"),
    ("COMP.CAS(IB)", "Company Case (Insolvency & Bankruptcy)"),
    ("C.P.", "Company Petition"),
    ("MAT.APP.", "Mat Appeal"),
    ("L.P.A.", "Letters Patent Appeal"),
    ("C.O.", "Contempt of Court"),
    ("BAIL APPLN.", "Bail Application"),
    ("EA", "Execution Application"),
    ("EC", "Execution Case"),
    ("EP", "Election Petition"),
    ("EXE", "Execution"),
    ("GA", "General Application"),
    ("MA", "Miscellaneous Application"),
    ("O", "Original"),
    ("P", "Petition"),
    ("SA", "Second Appeal"),
    ("U", "Under")
]

@app.route('/')
def index():
    """Renders the main page with the search form and recent queries."""
    try:
        logger.info("Loading home page")
        
        # Get recent queries for dashboard
        recent_queries = get_recent_queries(10)
        
        # Get database statistics
        stats = get_database_stats()
        
        logger.info(f"Loaded {len(recent_queries)} recent queries and stats: {stats}")
        
        return render_template('index.html', 
                             case_types=CASE_TYPES, 
                             recent_queries=recent_queries,
                             stats=stats)
    except Exception as e:
        logger.error(f"Error loading index page: {e}")
        return render_template('index.html', 
                             case_types=CASE_TYPES, 
                             recent_queries=[],
                             stats={})

@app.route('/search', methods=['POST'])
def search():
    """Handles the form submission, runs the scraper, and shows results."""
    try:
        # Get form data
        case_type = request.form.get('case_type')
        case_number = request.form.get('case_number')
        case_year = request.form.get('case_year')

        logger.info(f"🔍 Received search request for: {case_type} {case_number}/{case_year}")
        print(f"🔍 Received search request for: {case_type} {case_number}/{case_year}")

        # Enhanced validation
        if not all([case_type, case_number, case_year]):
            flash("All fields are required.", "error")
            return redirect(url_for('index'))
        
        # Validate case number (basic)
        if not case_number.isdigit():
            flash("Case number must contain only digits.", "error")
            return redirect(url_for('index'))
        
        # Validate year
        current_year = datetime.now().year
        try:
            year_int = int(case_year)
            if year_int < 1947 or year_int > current_year + 1:
                flash("Please enter a valid year.", "error")
                return redirect(url_for('index'))
        except ValueError:
            flash("Year must be a valid number.", "error")
            return redirect(url_for('index'))

        # Check if case already exists in database
        logger.info("🔍 Checking database for existing case...")
        try:
            existing_cases = search_cases(case_type, case_number, case_year)
            if existing_cases and existing_cases[0]['was_successful']:
                logger.info(f"📋 Found existing case in database (ID: {existing_cases[0]['id']})")
                
                # Parse the stored data
                try:
                    existing_data = json.loads(existing_cases[0]['parsed_data_json'])
                    flash(f"Case found in database (queried on {existing_cases[0]['timestamp'][:19]})", "info")
                    
                    case_info = {
                        'case_type': case_type,
                        'case_number': case_number,
                        'case_year': case_year,
                        'query_id': existing_cases[0]['id'],
                        'source': 'database',
                        'timestamp': existing_cases[0]['timestamp']
                    }
                    
                    return render_template('results.html', 
                                         data=existing_data,
                                         case_info=case_info)
                except (json.JSONDecodeError, KeyError) as e:
                    logger.warning(f"⚠️  Stored data is corrupted: {e}, re-scraping...")
        except Exception as e:
            logger.warning(f"⚠️  Error checking database: {e}")

        # Run the scraper for new data
        logger.info("🚀 Starting web scraper...")
        print("🚀 Starting web scraper...")
        
        try:
            # Run the async scraper function
            result = asyncio.run(fetch_case_data(case_type, case_number, case_year))
            logger.info(f"✅ Scraper completed. Success: {result.get('error') is None}")
            print(f"✅ Scraper completed. Success: {result.get('error') is None}")
            
        except Exception as e:
            logger.error(f"❌ Scraper error: {e}")
            print(f"❌ Scraper error: {e}")
            result = {
                "data": None, 
                "raw_html": None, 
                "error": f"Scraper failed: {str(e)}"
            }

        # Log the attempt to the database
        try:
            query_id = log_query(case_type, case_number, case_year, result)
            logger.info(f"📝 Logged query to database with ID: {query_id}")
            print(f"📝 Logged query to database with ID: {query_id}")
        except Exception as e:
            logger.error(f"❌ Database logging failed: {e}")
            print(f"❌ Database logging failed: {e}")
            query_id = None

        # Handle results
        if result.get('error'):
            # If the scraper returned an error, show it to the user
            error_msg = result['error']
            logger.error(f"❌ Showing error to user: {error_msg}")
            print(f"❌ Showing error to user: {error_msg}")
            flash(f"Could not retrieve case data: {error_msg}", "error")
            return redirect(url_for('index'))

        # Check if we got meaningful data
        data = result.get('data', {})
        if not data or (not data.get('petitioner') and not data.get('respondent')):
            logger.warning("⚠️  No meaningful data extracted")
            flash("No case details found. Please verify the case number exists and try again.", "warning")
            return redirect(url_for('index'))

        # Success - render results
        logger.info(f"✅ Displaying results for case {case_type} {case_number}/{case_year}")
        print(f"✅ Displaying results for case {case_type} {case_number}/{case_year}")
        flash(f"Successfully retrieved case data for {case_type} {case_number}/{case_year}", "success")
        
        case_info = {
            'case_type': case_type,
            'case_number': case_number,
            'case_year': case_year,
            'query_id': query_id,
            'source': 'scraped',
            'timestamp': datetime.now().isoformat()
        }
        
        return render_template('results.html', 
                             data=data,
                             case_info=case_info)
    
    except Exception as e:
        logger.error(f"❌ Critical error in search route: {e}")
        print(f"❌ Critical error in search route: {e}")
        flash(f"An unexpected error occurred: {str(e)}", "error")
        return redirect(url_for('index'))

@app.route('/case/<int:query_id>')
def view_case(query_id):
    """View a specific case by query ID"""
    try:
        logger.info(f"Loading case with query ID: {query_id}")
        case_data = get_query_by_id(query_id)
        
        if not case_data:
            flash("Case not found.", "error")
            return redirect(url_for('index'))
        
        if case_data['was_successful'] and case_data.get('parsed_data'):
            case_info = {
                'case_type': case_data['case_type'],
                'case_number': case_data['case_number'],
                'case_year': case_data['case_year'],
                'query_id': query_id,
                'source': 'database',
                'timestamp': case_data['timestamp']
            }
            
            return render_template('results.html',
                                 data=case_data['parsed_data'],
                                 case_info=case_info)
        else:
            flash(f"Case query failed: {case_data.get('error_message', 'Unknown error')}", "error")
            return redirect(url_for('index'))
            
    except Exception as e:
        logger.error(f"Error loading case {query_id}: {e}")
        flash(f"Error loading case: {str(e)}", "error")
        return redirect(url_for('index'))

@app.route('/about')
def about():
    """About page with system information"""
    return render_template('about.html')

@app.route('/api/stats')
def api_stats():
    """API endpoint for database statistics"""
    try:
        stats = get_database_stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/recent')
def api_recent():
    """API endpoint for recent queries"""
    try:
        limit = request.args.get('limit', 10, type=int)
        recent = get_recent_queries(limit)
        return jsonify(recent)
    except Exception as e:
        logger.error(f"Error getting recent queries: {e}")
        return jsonify({'error': str(e)}), 500

# Static file serving (for development)
@app.route('/static/<path:filename>')
def static_files(filename):
    """Serve static files in development mode"""
    return send_from_directory(app.static_folder, filename)

# Error handlers
@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {error}")
    return render_template('500.html'), 500

# Template filters for better display
@app.template_filter('datetime')
def datetime_filter(value):
    """Format datetime for display"""
    if not value:
        return 'N/A'
    try:
        # Parse ISO format datetime
        dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
        return dt.strftime('%d/%m/%Y %H:%M')
    except:
        return value

@app.template_filter('truncate_html')
def truncate_html_filter(value, length=100):
    """Truncate HTML content for display"""
    if not value:
        return 'N/A'
    if len(value) <= length:
        return value
    return value[:length] + '...'

# Application startup
def create_app():
    """Create and configure the Flask application"""
    
    # Initialize the database when the app starts
    try:
        init_db()
        logger.info("✅ Database initialized successfully")
        print("✅ Database initialized successfully")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        print(f"❌ Database initialization failed: {e}")
        raise
    
    # Check if templates directory exists
    templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
    if not os.path.exists(templates_dir):
        logger.warning(f"⚠️  Templates directory not found: {templates_dir}")
        print(f"⚠️  Templates directory not found: {templates_dir}")
        print("📁 Creating templates directory...")
        os.makedirs(templates_dir)
    
    # Check if static directory exists
    static_dir = os.path.join(os.path.dirname(__file__), 'static')
    if not os.path.exists(static_dir):
        logger.warning(f"⚠️  Static directory not found: {static_dir}")
        print(f"⚠️  Static directory not found: {static_dir}")
        print("📁 Creating static directory...")
        os.makedirs(static_dir, exist_ok=True)
        os.makedirs(os.path.join(static_dir, 'css'), exist_ok=True)
        os.makedirs(os.path.join(static_dir, 'js'), exist_ok=True)
        os.makedirs(os.path.join(static_dir, 'img'), exist_ok=True)
    
    return app

if __name__ == '__main__':
    print("🚀 Starting Court Data Fetcher Web Application")
    print("=" * 60)
    
    # Create the app
    app = create_app()
    
    print("🌐 Starting Flask web server...")
    print("📍 Access the application at: http://localhost:5000")
    print("=" * 60)
    
    # Run the Flask app
    try:
        app.run(debug=True, host='127.0.0.1', port=5000, threaded=True)
    except Exception as e:
        print(f"❌ Failed to start web server: {e}")
        logger.error(f"Failed to start web server: {e}")
