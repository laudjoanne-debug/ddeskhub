import os
import secrets
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, flash, request, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__, template_folder='.', static_folder='static')
app.config['SECRET_KEY'] = 'modern_gold_white_barangay_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///barangay_desk_v4.db'
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'webp'}

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
db = SQLAlchemy(app)

# DATABASE MODELS
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    middle_name = db.Column(db.String(50), default='N/A')
    last_name = db.Column(db.String(50), nullable=False)
    suffix = db.Column(db.String(10), default='')
    dob = db.Column(db.String(15), nullable=False)
    gender = db.Column(db.String(15), nullable=False)
    purok_address = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    email_address = db.Column(db.String(120), unique=True, nullable=False)
    religion = db.Column(db.String(50), nullable=False)
    city_municipality = db.Column(db.String(50), nullable=False)
    state_province = db.Column(db.String(50), nullable=False)
    postal_code = db.Column(db.String(10), nullable=False)
    
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(250), nullable=False)
    
    role = db.Column(db.String(20), default='Resident')
    status = db.Column(db.String(20), default='Pending')
    profile_picture = db.Column(db.String(200), nullable=True)
    valid_id = db.Column(db.String(200), nullable=True)

    # Categories assigned by Admin
    cat_medical = db.Column(db.Boolean, default=False)
    cat_pwd = db.Column(db.Boolean, default=False)
    cat_senior = db.Column(db.Boolean, default=False)
    cat_disaster = db.Column(db.Boolean, default=False)

class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class BeneficiaryAnnouncement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Comma-separated user IDs of included residents
    resident_ids = db.Column(db.Text, nullable=False)

class StateRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    cat_medical = db.Column(db.Boolean, default=False)
    cat_pwd = db.Column(db.Boolean, default=False)
    cat_senior = db.Column(db.Boolean, default=False)
    cat_disaster = db.Column(db.Boolean, default=False)
    evidence_1 = db.Column(db.String(200), nullable=False)
    evidence_2 = db.Column(db.String(200), nullable=True)
    evidence_3 = db.Column(db.String(200), nullable=True)
    status = db.Column(db.String(20), default='Pending') # Pending, Approved, Rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='state_requests')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def save_uploaded_file(file_obj, prefix):
    if file_obj and allowed_file(file_obj.filename):
        filename = secure_filename(f"{prefix}_{secrets.token_hex(4)}_{file_obj.filename}")
        file_obj.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return filename
    return None

# ROUTES
@app.route('/')
def home():
    if 'user_id' in session:
        if session['role'] == 'Admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('resident_hub'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if len(username) < 8:
            flash('Username must be at least 8 characters long.', 'danger')
            return redirect(url_for('register'))
            
        if len(password) < 8:
            flash('Password must be at least 8 characters long.', 'danger')
            return redirect(url_for('register'))
            
        if not password.isalnum():
            flash('Password must contain letters and numbers only.', 'danger')
            return redirect(url_for('register'))
            
        if User.query.filter_by(username=username).first():
            flash('Username already taken.', 'danger')
            return redirect(url_for('register'))
            
        email = request.form.get('email_address')
        if User.query.filter_by(email_address=email).first():
            flash('Email address already registered.', 'danger')
            return redirect(url_for('register'))

        pic_file = request.files.get('profile_picture')
        id_file = request.files.get('valid_id')

        pic_filename = save_uploaded_file(pic_file, 'pic')
        id_filename = save_uploaded_file(id_file, 'id')

        new_resident = User(
            first_name=request.form.get('first_name'),
            middle_name=request.form.get('middle_name') or 'N/A',
            last_name=request.form.get('last_name'),
            suffix=request.form.get('suffix') or '',
            dob=request.form.get('dob'),
            gender=request.form.get('gender'),
            purok_address=request.form.get('purok_address'),
            phone_number=request.form.get('phone_number'),
            email_address=email,
            religion=request.form.get('religion'),
            city_municipality=request.form.get('city_municipality'),
            state_province=request.form.get('state_province'),
            postal_code=request.form.get('postal_code'),
            username=username,
            password_hash=generate_password_hash(password),
            profile_picture=pic_filename,
            valid_id=id_filename
        )
        db.session.add(new_resident)
        db.session.commit()
        flash('Registration submitted! Please wait for Admin verification before logging in.', 'info')
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['role'] = user.role
            session['name'] = f"{user.first_name} {user.last_name}"
            
            if user.role == 'Admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('resident_hub'))
        
        flash('Please proceed to the barangay hall to request a change of your username and password. Please remember to bring a valid ID.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('login'))

@app.route('/resident-hub')
def resident_hub():
    if 'user_id' not in session or session['role'] != 'Resident':
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    announcements = Announcement.query.order_by(Announcement.created_at.desc()).all()
    beneficiary_announcements = BeneficiaryAnnouncement.query.order_by(BeneficiaryAnnouncement.created_at.desc()).all()
    
    # Map beneficiary announcements with names only
    ben_data = []
    for ba in beneficiary_announcements:
        ids = [int(i) for i in ba.resident_ids.split(',') if i.strip().isdigit()]
        beneficiaries = User.query.filter(User.id.in_(ids)).all()
        names = [f"{b.first_name} {b.middle_name} {b.last_name} {b.suffix}".strip() for b in beneficiaries]
        ben_data.append({
            'id': ba.id,
            'title': ba.title,
            'description': ba.description,
            'created_at': ba.created_at,
            'names': names
        })

    my_requests = StateRequest.query.filter_by(user_id=user.id).order_by(StateRequest.created_at.desc()).all()

    return render_template('resident_hub.html', 
                           user=user, 
                           announcements=announcements, 
                           beneficiary_announcements=ben_data,
                           my_requests=my_requests)

@app.route('/resident/submit-state-request', methods=['POST'])
def submit_state_request():
    if 'user_id' not in session or session['role'] != 'Resident':
        return redirect(url_for('login'))

    f1 = request.files.get('evidence_1')
    f2 = request.files.get('evidence_2')
    f3 = request.files.get('evidence_3')

    e1 = save_uploaded_file(f1, 'ev1')
    if not e1:
        flash('At least one primary evidence image is required.', 'danger')
        return redirect(url_for('resident_hub'))

    e2 = save_uploaded_file(f2, 'ev2')
    e3 = save_uploaded_file(f3, 'ev3')

    req = StateRequest(
        user_id=session['user_id'],
        cat_medical=bool(request.form.get('cat_medical')),
        cat_pwd=bool(request.form.get('cat_pwd')),
        cat_senior=bool(request.form.get('cat_senior')),
        cat_disaster=bool(request.form.get('cat_disaster')),
        evidence_1=e1,
        evidence_2=e2,
        evidence_3=e3
    )
    db.session.add(req)
    db.session.commit()
    flash('State request submitted successfully for administrative review.', 'success')
    return redirect(url_for('resident_hub'))

@app.route('/admin-dashboard')
def admin_dashboard():
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))
    
    pending_users = User.query.filter_by(status='Pending', role='Resident').all()
    approved_residents = User.query.filter_by(status='Approved', role='Resident').all()
    all_residents = User.query.filter_by(role='Resident').all()
    
    announcements = Announcement.query.order_by(Announcement.created_at.desc()).all()
    beneficiary_announcements = BeneficiaryAnnouncement.query.order_by(BeneficiaryAnnouncement.created_at.desc()).all()
    
    state_requests = StateRequest.query.filter_by(status='Pending').order_by(StateRequest.created_at.desc()).all()
    admin_user = User.query.get(session['user_id'])
    
    return render_template('admin_dashboard.html', 
                           pending_users=pending_users, 
                           residents=all_residents,
                           approved_residents=approved_residents,
                           announcements=announcements,
                           beneficiary_announcements=beneficiary_announcements,
                           state_requests=state_requests,
                           admin_user=admin_user)

@app.route('/admin/verify/<int:user_id>/<string:action>')
def verify_user(user_id, action):
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))
    
    user = User.query.get_or_404(user_id)
    if action == 'approve':
        user.status = 'Approved'
        flash(f'Account for {user.first_name} {user.last_name} Approved.', 'success')
    elif action == 'reject':
        user.status = 'Rejected'
        flash(f'Account for {user.first_name} {user.last_name} Rejected.', 'warning')
    
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete-resident/<int:user_id>', methods=['POST'])
def delete_resident(user_id):
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))
    
    user = User.query.get_or_404(user_id)
    # Remove associated state requests first
    StateRequest.query.filter_by(user_id=user.id).delete()
    db.session.delete(user)
    db.session.commit()
    flash(f'Resident {user.first_name} {user.last_name} permanently deleted.', 'info')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/change-password/<int:user_id>', methods=['POST'])
def admin_change_password(user_id):
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))
    
    new_password = request.form.get('new_password')
    user = User.query.get_or_404(user_id)
    
    user.password_hash = generate_password_hash(new_password)
    db.session.commit()
    flash(f'Password updated for {user.first_name} {user.last_name}.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/post-announcement', methods=['POST'])
def post_announcement():
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))
    
    title = request.form.get('title')
    category = request.form.get('category')
    content = request.form.get('content')

    new_ann = Announcement(title=title, category=category, content=content)
    db.session.add(new_ann)
    db.session.commit()
    flash('Announcement published!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete-announcement/<int:ann_id>', methods=['POST'])
def delete_announcement(ann_id):
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))
    
    ann = Announcement.query.get_or_404(ann_id)
    db.session.delete(ann)
    db.session.commit()
    flash('Announcement deleted.', 'info')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/post-beneficiary-announcement', methods=['POST'])
def post_beneficiary_announcement():
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))

    title = request.form.get('title')
    description = request.form.get('description')
    selected_ids = request.form.getlist('selected_residents')

    if not selected_ids:
        flash('Please select at least one resident beneficiary.', 'warning')
        return redirect(url_for('admin_dashboard'))

    ba = BeneficiaryAnnouncement(
        title=title,
        description=description,
        resident_ids=','.join(selected_ids)
    )
    db.session.add(ba)
    db.session.commit()
    flash('Beneficiary notice published successfully.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete-beneficiary-announcement/<int:ba_id>', methods=['POST'])
def delete_beneficiary_announcement(ba_id):
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))

    ba = BeneficiaryAnnouncement.query.get_or_404(ba_id)
    db.session.delete(ba)
    db.session.commit()
    flash('Beneficiary notice removed.', 'info')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/process-state-request/<int:req_id>/<string:action>', methods=['POST'])
def process_state_request(req_id, action):
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))

    req = StateRequest.query.get_or_404(req_id)
    user = User.query.get(req.user_id)

    if action == 'approve':
        req.status = 'Approved'
        # Apply selected categories from admin form input
        user.cat_medical = bool(request.form.get('cat_medical'))
        user.cat_pwd = bool(request.form.get('cat_pwd'))
        user.cat_senior = bool(request.form.get('cat_senior'))
        user.cat_disaster = bool(request.form.get('cat_disaster'))
        flash(f'State Request Approved for {user.first_name} {user.last_name}. Resident categorized.', 'success')
    else:
        req.status = 'Rejected'
        flash(f'State Request Disapproved for {user.first_name} {user.last_name}.', 'warning')

    db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/update-resident-categories/<int:user_id>', methods=['POST'])
def update_resident_categories(user_id):
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))

    user = User.query.get_or_404(user_id)
    user.cat_medical = bool(request.form.get('cat_medical'))
    user.cat_pwd = bool(request.form.get('cat_pwd'))
    user.cat_senior = bool(request.form.get('cat_senior'))
    user.cat_disaster = bool(request.form.get('cat_disaster'))
    
    db.session.commit()
    flash(f'Categories updated for {user.first_name} {user.last_name}.', 'info')
    return redirect(url_for('admin_dashboard'))

# DEFAULT ADMIN CREATION
with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='adminaccount').first():
        admin = User(
            first_name='System',
            middle_name='N/A',
            last_name='Admin',
            suffix='',
            dob='01/01/1990',
            gender='Other',
            purok_address='Central Hall',
            phone_number='09123456789',
            email_address='admin@barangay.gov.ph',
            religion='N/A',
            city_municipality='Valencia',
            state_province='Bukidnon',
            postal_code='8709',
            username='adminaccount',
            password_hash=generate_password_hash('adminpass123'),
            role='Admin',
            status='Approved'
        )
        db.session.add(admin)
        db.session.commit()

if __name__ == '__main__':
    app.run(debug=True)