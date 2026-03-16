from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import json
from datetime import datetime, timedelta
import uuid

app = Flask(__name__)
app.secret_key = 'dummy_secret_key'
app.config['SESSION_COOKIE_SECURE'] = False  # Allow http in development
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

import os

# Background selection config
ALLOWED_BACKGROUNDS = ['farm-bg.svg', 'farm-sunset.svg', 'farm-illustration-2.svg', 'login_bg_custom.jpg', 'login_bg_replace.jpg', 'login_bg_new.jpg']
BG_CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'bg_config.json')

# Server-side session store
server_sessions = {}

# Dummy data
farmers = [
    {'id': 1, 'name': 'Farmer A', 'location': 'Village X', 'username': 'farmer1', 'password_env': 'FARMER1_PASS', 'role': 'farmer'},
    {'id': 2, 'name': 'Farmer B', 'location': 'Village Y', 'username': 'farmer2', 'password_env': 'FARMER2_PASS', 'role': 'farmer'},
]

customers = [
    {'id': 1, 'name': 'Customer A', 'username': 'customer1', 'password_env': 'CUSTOMER1_PASS', 'role': 'customer'},
    {'id': 2, 'name': 'Fertilizer Co', 'username': 'fert1', 'password_env': 'CUSTOMER2_PASS', 'role': 'customer'},
]

admins = [
    {'id': 1, 'username': 'admin1', 'password_env': 'ADMIN1_PASS', 'role': 'admin'},
]

crops = [
    {'id': 1, 'farmer_id': 1, 'name': 'Wheat', 'quantity': 200, 'price': 22, 'harvest_date': '2025-12-01', 'image': '/static/images/crops/wheat.jpg'},
    {'id': 2, 'farmer_id': 1, 'name': 'Rice', 'quantity': 150, 'price': 28, 'harvest_date': '2025-11-15', 'image': '/static/images/crops/rice.jpg'},
    {'id': 3, 'farmer_id': 2, 'name': 'Corn', 'quantity': 180, 'price': 26, 'harvest_date': '2025-10-20', 'image': '/static/images/crops/corn.jpg'},
    {'id': 4, 'farmer_id': 2, 'name': 'Sugarcane', 'quantity': 120, 'price': 15, 'harvest_date': '2026-01-10', 'image': '/static/images/crops/sugarcane.jpg'},
    {'id': 5, 'farmer_id': 1, 'name': 'Potato', 'quantity': 300, 'price': 18, 'harvest_date': '2026-01-05', 'image': '/static/images/crops/potato.jpg'},
    {'id': 6, 'farmer_id': 2, 'name': 'Tomato', 'quantity': 250, 'price': 40, 'harvest_date': '2025-12-20', 'image': '/static/images/crops/tomato.jpg'},
    {'id': 7, 'farmer_id': 1, 'name': 'Onion', 'quantity': 200, 'price': 35, 'harvest_date': '2025-12-18', 'image': '/static/images/crops/onion.jpg'},
    {'id': 8, 'farmer_id': 1, 'name': 'Mango', 'quantity': 80, 'price': 120, 'harvest_date': '2026-03-15', 'image': '/static/images/crops/mango.jpg'},
    {'id': 9, 'farmer_id': 2, 'name': 'Banana', 'quantity': 180, 'price': 60, 'harvest_date': '2026-02-01', 'image': '/static/images/crops/banana.jpg'},
    {'id': 10, 'farmer_id': 2, 'name': 'Apple', 'quantity': 90, 'price': 140, 'harvest_date': '2026-02-20', 'image': '/static/images/crops/apple.jpg'},
    {'id': 11, 'farmer_id': 1, 'name': 'Cabbage', 'quantity': 160, 'price': 25, 'harvest_date': '2025-12-30', 'image': '/static/images/crops/cabbage.jpg'},
    {'id': 12, 'farmer_id': 2, 'name': 'Peas', 'quantity': 140, 'price': 55, 'harvest_date': '2025-12-28', 'image': '/static/images/crops/peas.jpg'},
    {'id': 13, 'farmer_id': 1, 'name': 'Soybean', 'quantity': 220, 'price': 32, 'harvest_date': '2026-01-12', 'image': '/static/images/crops/soybean.jpg'},
    {'id': 14, 'farmer_id': 2, 'name': 'Sunflower', 'quantity': 130, 'price': 45, 'harvest_date': '2026-01-25', 'image': '/static/images/crops/sunflower.jpg'},
    {'id': 15, 'farmer_id': 1, 'name': 'Millet', 'quantity': 210, 'price': 38, 'harvest_date': '2026-02-05', 'image': '/static/images/crops/millet.jpg'},
]

orders = [
    {'id': 1, 'customer_id': 1, 'farmer_id': 1, 'crop_id': 1, 'quantity': 10, 'status': 'delivered'},
    {'id': 2, 'customer_id': 2, 'farmer_id': 1, 'crop_id': 2, 'quantity': 5, 'status': 'pending'},
]

waste_reports = [
    {'id': 1, 'farmer_id': 1, 'crop_type': 'Wheat', 'quantity': 5, 'period': 'today', 'date': '2025-12-22'},
]

# Waste becomes products
waste_products = [
    {'id': 1, 'farmer_id': 1, 'name': 'Organic Waste - Wheat', 'quantity': 5, 'price': 5, 'type': 'waste', 'image': '/static/images/crops/wheat.jpg'},
]

# Tool/equipment/order bookings (farmers can request tools or officers)
tool_bookings = []  # {id, farmer_id, tool_or_service, date, quantity, notes, status, created_at, listing_id, seller_id, seller_name, price}

# Sample dealers and tool listings (multiple sellers can list same tool)
dealers = [
    {'id': 1, 'name': 'AgriTools Pvt Ltd', 'location': 'Town A', 'username': 'dealer1', 'password_env': 'DEALER1_PASS', 'role': 'dealer'},
    {'id': 2, 'name': 'Field Supplies', 'location': 'Town B', 'username': 'dealer2', 'password_env': 'DEALER2_PASS', 'role': 'dealer'},
    {'id': 3, 'name': 'SmartAgri Co', 'location': 'City C', 'username': 'smart1', 'password_env': 'DEALER3_PASS', 'role': 'dealer'},
]

# Marketplace tool listings
tool_listings = [
    {'id': 1, 'seller_id': 1, 'seller_name': 'AgriTools Pvt Ltd', 'name': 'Soil Tester Model A', 'price': 5000.0, 'available': 3, 'image': '/static/images/tools/soil_tester_a.jpg'},
    {'id': 2, 'seller_id': 2, 'seller_name': 'Field Supplies', 'name': 'Soil Tester Model B', 'price': 4500.0, 'available': 5, 'image': '/static/images/tools/soil_tester_b.jpg'},
    {'id': 3, 'seller_id': 1, 'seller_name': 'AgriTools Pvt Ltd', 'name': 'Irrigation Pump X', 'price': 12000.0, 'available': 2, 'image': '/static/images/tools/irrigation_pump_x.jpg'},
    {'id': 4, 'seller_id': 3, 'seller_name': 'SmartAgri Co', 'name': 'Smart Seeder - Model S', 'price': 15000.0, 'available': 5, 'image': '/static/images/tools/smart_seeder_s.jpg'},
]

# Curated Smart Inventions (videos and images) for farmer education
smart_inventions = [
    {
        'id': 1,
        'type': 'video',
        'category': 'Overview',
        'title': 'Smart Tools Overview',
        'url': 'https://www.youtube.com/embed/0KvovFmiu6c',
        'thumbnail': 'https://img.youtube.com/vi/0KvovFmiu6c/hqdefault.jpg',
        'description': 'Overview of modern tools and safe usage',
        'related_listing_id': 4
    },
    {
        'id': 2,
        'type': 'video',
        'category': 'Drones',
        'title': 'Drone Spraying Example',
        'url': 'https://www.youtube.com/embed/Mnxh85xaRbI',
        'thumbnail': 'https://img.youtube.com/vi/Mnxh85xaRbI/hqdefault.jpg',
        'description': 'Drone-assisted spraying demo (video)',
        'related_listing_id': None
    },
    {
        'id': 3,
        'type': 'video',
        'category': 'Planting',
        'title': 'Potato Planting Techniques',
        'url': 'https://www.youtube.com/embed/P9y_DDCHsK4',
        'thumbnail': 'https://img.youtube.com/vi/P9y_DDCHsK4/hqdefault.jpg',
        'description': 'Best practices for potato planting and spacing',
        'related_listing_id': None
    },
    {
        'id': 4,
        'type': 'image',
        'category': 'Sensors',
        'title': 'Soil Sensor Overview',
        'url': 'https://frankever.com/wp-content/uploads/2023/10/S92f6e1ad245749c79f9d84c94994a21aI.jpg',
        'thumbnail': 'https://frankever.com/wp-content/uploads/2023/10/S92f6e1ad245749c79f9d84c94994a21aI.jpg',
        'description': 'Soil moisture sensor and data interpretation (image)',
        'related_listing_id': 1
    },
]

def get_user_from_session(sid):
    """Get user from server-side session"""
    if not sid or sid not in server_sessions:
        return None
    return server_sessions[sid]

@app.route("/")
def login():
    # Allow preview via ?bg=filename (must be one of allowed backgrounds)
    bg_name = request.args.get('bg')
    if bg_name and bg_name in ALLOWED_BACKGROUNDS:
        bg_url = '/static/images/' + bg_name
    else:
        # read from config (if any)
        try:
            if os.path.exists(BG_CONFIG_PATH):
                cfg = json.load(open(BG_CONFIG_PATH))
                bg = cfg.get('bg')
                if bg in ALLOWED_BACKGROUNDS:
                    bg_url = '/static/images/' + bg
                else:
                    bg_url = '/static/images/farm-bg.svg'
            else:
                bg_url = '/static/images/farm-bg.svg'
        except Exception:
            bg_url = '/static/images/farm-bg.svg'
    return render_template("login.html", bg_url=bg_url)

@app.route('/preview-backgrounds')
def preview_backgrounds():
    current = None
    try:
        if os.path.exists(BG_CONFIG_PATH):
            cfg = json.load(open(BG_CONFIG_PATH))
            if cfg.get('bg') in ALLOWED_BACKGROUNDS:
                current = cfg.get('bg')
    except Exception:
        current = None
    images = [{'filename': n, 'url': '/static/images/' + n, 'selected': (n == current)} for n in ALLOWED_BACKGROUNDS]
    return render_template('preview_backgrounds.html', images=images)

@app.route('/set-background', methods=['POST'])
def set_background():
    bg = request.form.get('bg')
    if not bg or bg not in ALLOWED_BACKGROUNDS:
        return "Invalid background", 400
    try:
        with open(BG_CONFIG_PATH, 'w') as f:
            json.dump({'bg': bg}, f)
    except Exception as e:
        return f"Failed to save: {e}", 500
    return redirect(url_for('preview_backgrounds'))

@app.route("/login", methods=['POST'])
def do_login():
    username = request.form['username']
    password = request.form['password']
    role = request.form['role']
    
    print(f"Login attempt - Username: {username}, Role: {role}")
    
    user = None
    if role == 'farmer':
        user = next((f for f in farmers if f['username'] == username), None)
    elif role == 'customer':
        user = next((c for c in customers if c['username'] == username), None)
    elif role == 'admin':
        user = next((a for a in admins if a['username'] == username), None)

    # Verify password from environment variable referenced by the user record
    if user:
        pwd_env = user.get('password_env')
        expected = os.environ.get(pwd_env) if pwd_env else None
        if expected:
            if password != expected:
                print(f"Invalid password for user {username}")
                user = None
        else:
            # No password configured in env. Allow fallback only if explicitly enabled via ALLOW_DEV_INSECURE
            if os.environ.get('ALLOW_DEV_INSECURE') == '1':
                if password != 'pass':
                    print(f"Invalid fallback password for user {username}")
                    user = None
                else:
                    print(f"Warning: Using insecure fallback password for {username} (dev only)")
            else:
                print(f"Login disabled for {username}: no password env var ({pwd_env}) set")
                user = None

    # Bypass authentication for development convenience when ALLOW_ANY_LOGIN=1 or when running in debug mode
    if not user and (os.environ.get('ALLOW_ANY_LOGIN') == '1' or app.debug):
        print(f"Bypassing auth for {username} (ALLOW_ANY_LOGIN or debug mode active)")
        # create a lightweight synthetic user for the session
        synthetic_id = 100000 + len(server_sessions)
        user = {'id': synthetic_id, 'username': username, 'name': username, 'role': role}
        if role == 'farmer':
            user['location'] = 'Unknown'
    
    if user:
        print(f"User found: {user}")
        # Create a server-side session
        session_id = str(uuid.uuid4())
        server_sessions[session_id] = user
        print(f"Server session created: {session_id}")
        
        if role == 'farmer':
            return redirect(url_for('farmer_dashboard', sid=session_id))
        elif role == 'customer':
            return redirect(url_for('customer_browse', sid=session_id))
        elif role == 'admin':
            return redirect(url_for('admin_analytics', sid=session_id))
    else:
        print(f"User not found for username: {username}")
    return redirect(url_for('login'))

@app.route("/logout")
def logout():
    sid = request.args.get('sid')
    if sid and sid in server_sessions:
        del server_sessions[sid]
        print(f"Session {sid} deleted")
    return redirect(url_for('login'))

@app.route("/farmer")
def farmer_dashboard():
    sid = request.args.get('sid')
    farmer = get_user_from_session(sid)
    if not farmer or farmer['role'] != 'farmer':
        return redirect(url_for('login'))
    
    farmer_crops = [c for c in crops if c['farmer_id'] == farmer['id']]
    farmer_orders = [o for o in orders if o['farmer_id'] == farmer['id']]
    # Dummy visualizations data
    crop_sales = {'Wheat': 200, 'Rice': 150, 'Corn': 100}
    monthly_income = {'Jan': 500, 'Feb': 600, 'Mar': 700}
    profit_per_crop = {'Wheat': 50, 'Rice': 75, 'Corn': 60}
    # collect related products referenced by smart inventions
    related_ids = set([s.get('related_listing_id') for s in smart_inventions if s.get('related_listing_id')])
    related_products = [l for l in tool_listings if l['id'] in related_ids]
    return render_template("farmer/dashboard.html", farmer=farmer, crops=farmer_crops, orders=farmer_orders, crop_sales=crop_sales, monthly_income=monthly_income, profit_per_crop=profit_per_crop, sid=sid, smart_inventions=smart_inventions, related_products=related_products, tool_listings=tool_listings)

@app.route("/farmer/add-crop", methods=['GET', 'POST'])
def add_crop():
    sid = request.args.get('sid') if request.method == 'GET' else request.form.get('sid')
    farmer = get_user_from_session(sid)
    if not farmer or farmer['role'] != 'farmer':
        return redirect(url_for('login'))
    if request.method == 'POST':
        name = request.form['name']
        quantity = int(request.form['quantity'])
        price = float(request.form['price'])
        # image selection: prefer selected static image, fallback to pasted URL, else try to find existing crop image
        image_choice = (request.form.get('image_choice') or '').strip()
        image_url = (request.form.get('image_url') or '').strip()
        if image_choice:
            image = image_choice
        elif image_url:
            image = image_url
        else:
            existing = next((c for c in crops if c['name'].lower() == name.lower()), None)
            image = existing['image'] if existing and existing.get('image') else '/static/images/crops/millet.svg'
        new_crop = {'id': len(crops)+1, 'farmer_id': farmer['id'], 'name': name, 'quantity': quantity, 'price': price, 'harvest_date': datetime.now().strftime('%Y-%m-%d'), 'image': image}
        crops.append(new_crop)
        return redirect(url_for('farmer_dashboard', sid=sid))
    # GET: enumerate available static images in crops folder for selection
    try:
        img_dir = os.path.join(os.path.dirname(__file__), 'static', 'images', 'crops')
        images_list = [n for n in os.listdir(img_dir) if os.path.splitext(n)[1].lower() in ['.jpg','.jpeg','.png','.svg']]
        images_list.sort()
        available_images = ['/static/images/crops/' + n for n in images_list]
    except Exception:
        available_images = []
    return render_template("farmer/add_crop.html", sid=sid, available_images=available_images)

@app.route("/farmer/waste-alert", methods=['GET', 'POST'])
def waste_alert():
    sid = request.args.get('sid') if request.method == 'GET' else request.form.get('sid')
    farmer = get_user_from_session(sid)
    if not farmer or farmer['role'] != 'farmer':
        return redirect(url_for('login'))
    if request.method == 'POST':
        crop_type = request.form['crop_type']
        quantity = int(request.form['quantity'])
        period = request.form['period']
        # determine image for this waste: prefer existing crop image if available
        match = next((c for c in crops if c['name'].lower() == crop_type.lower()), None)
        image_for_waste = match['image'] if match and match.get('image') else '/static/images/crops/millet.svg'
        new_waste = {'id': len(waste_reports)+1, 'farmer_id': farmer['id'], 'crop_type': crop_type, 'quantity': quantity, 'period': period, 'date': datetime.now().strftime('%Y-%m-%d'), 'image': image_for_waste}
        waste_reports.append(new_waste)
        # Add to waste products with same image for consistent display
        waste_products.append({'id': len(waste_products)+1, 'farmer_id': farmer['id'], 'name': f'Organic Waste - {crop_type}', 'quantity': quantity, 'price': 5, 'type': 'waste', 'image': image_for_waste})
        return redirect(url_for('farmer_dashboard', sid=sid))
    return render_template("farmer/waste_alert.html", sid=sid)

@app.route('/farmer/book-tool', methods=['GET','POST'])
def book_tool():
    sid = request.args.get('sid') if request.method == 'GET' else request.form.get('sid')
    farmer = get_user_from_session(sid)
    if not farmer or farmer['role'] != 'farmer':
        return redirect(url_for('login'))
    if request.method == 'POST':
        tool_or_service = request.form.get('tool_or_service')
        date = request.form.get('date') or None
        quantity = int(request.form.get('quantity') or 1)
        notes = request.form.get('notes') or ''
        listing_id = request.form.get('listing_id')
        seller_id = None
        seller_name = None
        price = None
        if listing_id:
            try:
                lid = int(listing_id)
                listing = next((l for l in tool_listings if l['id'] == lid), None)
                if listing:
                    seller_id = listing.get('seller_id')
                    seller_name = listing.get('seller_name')
                    price = listing.get('price')
            except ValueError:
                pass
        new_booking = {
            'id': len(tool_bookings) + 1,
            'farmer_id': farmer['id'],
            'tool_or_service': tool_or_service,
            'date': date,
            'quantity': quantity,
            'notes': notes,
            'listing_id': listing_id,
            'seller_id': seller_id,
            'seller_name': seller_name,
            'price': price,
            'status': 'pending',
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M')
        }
        tool_bookings.append(new_booking)
        return redirect(url_for('farmer_dashboard', sid=sid))
    # GET: support preselecting a listing via query param
    selected = None
    listing_id = request.args.get('listing_id')
    if listing_id:
        try:
            lid = int(listing_id)
            selected = next((l for l in tool_listings if l['id'] == lid), None)
        except ValueError:
            selected = None
    return render_template('farmer/book_tool.html', sid=sid, selected_listing=selected)


@app.route('/tools/search')
def tools_search():
    q = request.args.get('q', '').strip().lower()
    # If no query provided, return all listings (for browsing)
    source = tool_listings if not q else [t for t in tool_listings if q in t['name'].lower()]
    matches = [
        {
            'id': t['id'],
            'name': t['name'],
            'price': t['price'],
            'available': t['available'],
            'seller_id': t['seller_id'],
            'seller_name': t['seller_name'],
            'image': t.get('image')
        }
        for t in source
    ]
    return jsonify(matches)

@app.route('/admin/tool-bookings')
def admin_tool_bookings():
    sid = request.args.get('sid')
    admin = get_user_from_session(sid)
    if not admin or admin['role'] != 'admin':
        return redirect(url_for('login'))
    return render_template('admin/tool_bookings.html', bookings=tool_bookings, sid=sid)

@app.route('/admin/tool-bookings/<int:booking_id>/update', methods=['POST'])
def admin_update_booking(booking_id):
    sid = request.form.get('sid')
    admin = get_user_from_session(sid)
    if not admin or admin['role'] != 'admin':
        return redirect(url_for('login'))
    status = request.form.get('status')
    b = next((t for t in tool_bookings if t['id'] == booking_id), None)
    if b and status in ['pending','confirmed','completed','cancelled']:
        b['status'] = status
    return redirect(url_for('admin_tool_bookings', sid=sid))

@app.route("/customer")
def customer_browse():
    sid = request.args.get('sid')
    customer = get_user_from_session(sid)
    if not customer or customer['role'] != 'customer':
        return redirect(url_for('login'))
    all_crops = crops + waste_products
    q = request.args.get('q', '').strip()
    if q:
        q_lower = q.lower()
        filtered = [c for c in all_crops if q_lower in c.get('name', '').lower()]
    else:
        filtered = all_crops

    # Build display list where each crop includes farmer info and a trust score
    display_crops = []
    for c in filtered:
        cp = dict(c)  # shallow copy to avoid mutating global state
        farmer = next((f for f in farmers if f['id'] == c.get('farmer_id')), None)
        if farmer:
            cp['farmer_name'] = farmer.get('name')
            cp['farmer_location'] = farmer.get('location')
            # Compute trust score based on farmer's completed deliveries if available
            farmer_orders = [o for o in orders if o['farmer_id'] == farmer['id']]
            if farmer_orders:
                delivered = len([o for o in farmer_orders if o['status'] == 'delivered'])
                total = len(farmer_orders)
                completion_rate = int((delivered / total) * 100)
                # Use completion_rate clamped between 40 and 95
                ts = max(40, min(95, completion_rate))
                cp['trust_score'] = ts
            else:
                # deterministic fallback score for farmers without orders
                ts = 70 + (farmer['id'] * 11) % 21  # between 70 and 90
                cp['trust_score'] = ts
            # human readable label
            cp['trust_label'] = 'High' if cp['trust_score'] >= 80 else 'Medium' if cp['trust_score'] >= 60 else 'Low'
        else:
            cp['farmer_name'] = 'Unknown'
            cp['farmer_location'] = 'Unknown'
            cp['trust_score'] = 65
            cp['trust_label'] = 'Medium'
        display_crops.append(cp)

    return render_template("customer/browse.html", crops=display_crops, farmers=farmers, sid=sid, q=q)

@app.route('/farmer/summary/<int:farmer_id>')
def farmer_summary(farmer_id):
    sid = request.args.get('sid')
    customer = get_user_from_session(sid)
    if not customer or customer['role'] != 'customer':
        return jsonify({'error': 'login_required'}), 401
    farmer = next((f for f in farmers if f['id'] == farmer_id), None)
    if not farmer:
        return jsonify({'error': 'not_found'}), 404
    farmer_orders = [o for o in orders if o['farmer_id'] == farmer_id]
    delivered_count = len([o for o in farmer_orders if o['status'] == 'delivered'])
    total_orders = len(farmer_orders)
    completion_rate = int((delivered_count / total_orders) * 100) if total_orders else 0
    if total_orders:
        trust_score = max(40, min(95, completion_rate))
    else:
        trust_score = 70 + (farmer_id * 11) % 21
    trust_label = 'High' if trust_score >= 80 else 'Medium' if trust_score >= 60 else 'Low'
    return jsonify({
        'id': farmer_id,
        'name': farmer.get('name'),
        'location': farmer.get('location'),
        'trust_score': trust_score,
        'trust_label': trust_label,
        'delivered_count': delivered_count,
        'total_orders': total_orders,
        'completion_rate': completion_rate
    })

@app.route("/customer/farmer_profile/<int:farmer_id>")
def farmer_profile(farmer_id):
    sid = request.args.get('sid')
    customer = get_user_from_session(sid)
    if not customer or customer['role'] != 'customer':
        return redirect(url_for('login'))
    farmer = next((f for f in farmers if f['id'] == farmer_id), None)
    if not farmer:
        return "Farmer not found"
    farmer_crops = [c for c in crops if c['farmer_id'] == farmer_id]
    farmer_orders = [o for o in orders if o['farmer_id'] == farmer_id]
    total_sales = sum(o['quantity'] * next((c['price'] for c in crops if c['id'] == o['crop_id']), 0) for o in farmer_orders if o['status'] == 'delivered')
    # Compute delivered / total and trust score
    delivered_count = len([o for o in farmer_orders if o['status'] == 'delivered'])
    total_orders = len(farmer_orders)
    completion_rate = int((delivered_count / total_orders) * 100) if total_orders else 0
    if total_orders:
        trust_score = max(40, min(95, completion_rate))
    else:
        trust_score = 70 + (farmer_id * 11) % 21
    trust_label = 'High' if trust_score >= 80 else 'Medium' if trust_score >= 60 else 'Low'
    return render_template("customer/farmer_profile.html", farmer=farmer, crops=farmer_crops, total_sales=total_sales, completion_rate=completion_rate, trust_indicator=trust_label, trust_score=trust_score, trust_label=trust_label, delivered_count=delivered_count, total_orders=total_orders, sid=sid)

@app.route("/customer/order/<int:crop_id>", methods=['POST'])
def place_order(crop_id):
    sid = request.form.get('sid')
    customer = get_user_from_session(sid)
    if not customer or customer['role'] != 'customer':
        return redirect(url_for('login'))
    quantity = int(request.form['quantity'])
    crop = next((c for c in crops + waste_products if c['id'] == crop_id), None)
    if crop:
        new_order = {'id': len(orders)+1, 'customer_id': customer['id'], 'farmer_id': crop['farmer_id'], 'crop_id': crop_id, 'quantity': quantity, 'status': 'pending'}
        orders.append(new_order)
    return redirect(url_for('customer_browse', sid=sid))

@app.route("/admin")
def admin_analytics():
    sid = request.args.get('sid')
    admin = get_user_from_session(sid)
    if not admin or admin['role'] != 'admin':
        return redirect(url_for('login'))
    # Dummy data for charts
    price_transparency = {'farmer_price': [20, 30, 25], 'market_price': [22, 32, 27]}
    sales_trends = {'months': ['Jan', 'Feb', 'Mar'], 'sales': [100, 150, 200]}
    farmer_income = {'farmers': ['A', 'B'], 'income': [1200, 800]}
    waste_trends = {'months': ['Jan', 'Feb', 'Mar'], 'waste': [10, 15, 20]}
    sustainability = {'compost_generated': 50, 'waste_reduction': 30}
    return render_template("admin/analytics.html", price_transparency=price_transparency, sales_trends=sales_trends, farmer_income=farmer_income, waste_trends=waste_trends, sustainability=sustainability, sid=sid)

if __name__ == "__main__":
    app.run(debug=True)
