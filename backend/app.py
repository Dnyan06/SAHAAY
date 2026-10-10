"""Sahaay backend: Flask + SQLAlchemy. Run with:  python app.py"""
import os, secrets, json, time
from datetime import datetime, timedelta, timezone
from flask import Flask, Blueprint, request, session, jsonify, send_from_directory, abort
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
db_url = os.environ.get('DATABASE_URL', 'sqlite:///' + os.path.join(HERE, 'sahaay.db'))
if db_url.startswith('postgres://'):
    db_url = db_url.replace('postgres://', 'postgresql://', 1)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('COOKIE_SECURE') == '1'   # set COOKIE_SECURE=1 when using HTTPS
if not os.environ.get('SECRET_KEY') and os.environ.get('FLASK_DEBUG') != '1':
    print('WARNING: set the SECRET_KEY environment variable before deploying')
db = SQLAlchemy(app)
S, T, I = db.String, db.Text, db.Integer

# ---------- database tables (models) ----------
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(I, primary_key=True)
    name = db.Column(S(100), nullable=False)
    email = db.Column(S(120), unique=True, nullable=False)
    password_hash = db.Column(S(255), nullable=False)
    role = db.Column(S(20), default='User')
    skills = db.Column(S(200), default='')
    loc = db.Column(S(100), default='')
    dis = db.Column(S(200), default='')      # private accessibility info
    phone = db.Column(S(30), default='')
    education = db.Column(S(100), default='')
    worktype = db.Column(S(30), default='Any')

class Job(db.Model):
    __tablename__ = 'jobs'
    id = db.Column(I, primary_key=True)
    title = db.Column(S(200)); company = db.Column(S(100)); loc = db.Column(S(100))
    type = db.Column(S(30)); pay = db.Column(S(50)); desc = db.Column(T); skills = db.Column(S(200))
    created = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    status = db.Column(S(20), default='approved')      # pending / approved / rejected
    owner_id = db.Column(I, db.ForeignKey('users.id'), nullable=True)

class Doctor(db.Model):
    __tablename__ = 'healthcare_services'
    id = db.Column(I, primary_key=True)
    name = db.Column(S(100)); spec = db.Column(S(60)); city = db.Column(S(60))
    place = db.Column(S(120)); svc = db.Column(T)
    user_id = db.Column(I, db.ForeignKey('users.id'), nullable=True)

class Sign(db.Model):
    __tablename__ = 'lessons'
    id = db.Column(I, primary_key=True)
    t = db.Column(S(60)); cat = db.Column(S(40)); d = db.Column(S(120)); how = db.Column(T)

class Place(db.Model):
    __tablename__ = 'accessibility_locations'
    id = db.Column(I, primary_key=True)
    n = db.Column(S(120)); city = db.Column(S(60)); lat = db.Column(db.Float); lng = db.Column(db.Float)
    s = db.Column(S(10))   # green / yellow / red
    ramp = db.Column(S(10)); lift = db.Column(S(10)); wash = db.Column(S(10))
    sign = db.Column(S(10)); park = db.Column(S(10))

class Post(db.Model):
    __tablename__ = 'community_posts'
    id = db.Column(I, primary_key=True)
    cat = db.Column(S(30)); by = db.Column(S(100)); title = db.Column(S(200)); body = db.Column(T)
    base_likes = db.Column(I, default=0)
    created = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    user_id = db.Column(I, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=True)

class Comment(db.Model):
    __tablename__ = 'post_comments'
    id = db.Column(I, primary_key=True)
    post_id = db.Column(I, db.ForeignKey('community_posts.id', ondelete='CASCADE'))
    user_id = db.Column(I, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=True)
    text = db.Column(T)

class Like(db.Model):
    __tablename__ = 'post_likes'
    post_id = db.Column(I, db.ForeignKey('community_posts.id', ondelete='CASCADE'), primary_key=True)
    user_id = db.Column(I, db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)

class Report(db.Model):
    __tablename__ = 'post_reports'
    id = db.Column(I, primary_key=True)
    post_id = db.Column(I, db.ForeignKey('community_posts.id', ondelete='CASCADE'))
    user_id = db.Column(I, db.ForeignKey('users.id', ondelete='CASCADE'))

class SavedJob(db.Model):
    __tablename__ = 'saved_jobs'
    user_id = db.Column(I, db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    job_id = db.Column(I, db.ForeignKey('jobs.id', ondelete='CASCADE'), primary_key=True)

class Application(db.Model):
    __tablename__ = 'job_applications'
    user_id = db.Column(I, db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    job_id = db.Column(I, db.ForeignKey('jobs.id', ondelete='CASCADE'), primary_key=True)
    status = db.Column(S(20), default='Submitted')

class Appointment(db.Model):
    __tablename__ = 'appointments'
    id = db.Column(I, primary_key=True)
    user_id = db.Column(I, db.ForeignKey('users.id', ondelete='CASCADE'))
    doctor_id = db.Column(I, db.ForeignKey('healthcare_services.id', ondelete='CASCADE'))
    date = db.Column(S(30))
    status = db.Column(S(20), default='Requested')

class Progress(db.Model):
    __tablename__ = 'user_progress'
    user_id = db.Column(I, db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    sign_id = db.Column(I, db.ForeignKey('lessons.id', ondelete='CASCADE'), primary_key=True)

class ChapterProgress(db.Model):
    __tablename__ = 'chapter_progress'
    user_id = db.Column(I, db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    chapter = db.Column(S(30), primary_key=True)
    score = db.Column(I, default=0); stars = db.Column(I, default=0)

class StudyDay(db.Model):
    __tablename__ = 'study_days'
    user_id = db.Column(I, db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    day = db.Column(S(10), primary_key=True)

# ---------- helpers ----------
def row(o):
    return {c.name: getattr(o, c.name) for c in o.__table__.columns}

def pub(o, *hide):   # row without private columns
    return {k: v for k, v in row(o).items() if k not in hide}

def me():
    return db.session.get(User, session['uid']) if 'uid' in session else None

def need():
    u = me()
    if not u:
        abort(401, 'Please log in first.')
    return u

def user_json(u):
    return dict(id=u.id, name=u.name, email=u.email, role=u.role, skills=u.skills, loc=u.loc, dis=u.dis,
                phone=u.phone, education=u.education, worktype=u.worktype)

def ist_day(offset=0):   # today's date in Indian time
    return (datetime.now(timezone.utc) + timedelta(hours=5, minutes=30) - timedelta(days=offset)).strftime('%Y-%m-%d')

def mine(u):
    days = [s.day for s in StudyDay.query.filter_by(user_id=u.id)]
    streak, k = 0, (0 if ist_day() in days else 1)
    while ist_day(k) in days:
        streak += 1; k += 1
    return dict(saved=[s.job_id for s in SavedJob.query.filter_by(user_id=u.id)],
                apps=[dict(job_id=a.job_id, status=a.status) for a in Application.query.filter_by(user_id=u.id)],
                learned=[p.sign_id for p in Progress.query.filter_by(user_id=u.id)],
                chapters={c.chapter: dict(score=c.score, stars=c.stars) for c in ChapterProgress.query.filter_by(user_id=u.id)},
                appts=[dict(doctor=db.session.get(Doctor, x.doctor_id).name, date=x.date, status=x.status)
                       for x in Appointment.query.filter_by(user_id=u.id)],
                days=days, streak=streak, today=ist_day())

def post_json(p):   # never includes private user data
    return dict(id=p.id, cat=p.cat, by=p.by, created=p.created.strftime('%Y-%m-%d'), title=p.title, body=p.body,
                likes=p.base_likes + Like.query.filter_by(post_id=p.id).count(),
                comments=[c.text for c in Comment.query.filter_by(post_id=p.id).order_by(Comment.id)])

@app.errorhandler(400)
@app.errorhandler(401)
@app.errorhandler(404)
@app.errorhandler(403)
@app.errorhandler(409)
@app.errorhandler(429)
def handle_error(e):
    return jsonify(error=e.description), e.code

# ---------- blueprints ----------
auth = Blueprint('auth', __name__, url_prefix='/api')
jobs = Blueprint('jobs', __name__, url_prefix='/api')
health = Blueprint('health', __name__, url_prefix='/api')
comm = Blueprint('comm', __name__, url_prefix='/api')
learn = Blueprint('learn', __name__, url_prefix='/api')
places = Blueprint('places', __name__, url_prefix='/api')

@auth.post('/register')
def register():
    d = request.get_json() or {}
    name, email, pw = (d.get('name') or '').strip(), (d.get('email') or '').strip().lower(), d.get('password') or ''
    if not name or '@' not in email or len(pw) < 6:
        abort(400, 'Enter your name, a valid email and a password of at least 6 characters.')
    if User.query.filter_by(email=email).first():
        abort(409, 'This email is already registered.')
    role = d.get('role') if d.get('role') in ('User', 'Employer', 'Doctor') else 'User'
    u = User(name=name, email=email, password_hash=generate_password_hash(pw), role=role,
             skills=d.get('skills', ''), loc=d.get('loc', ''), dis=d.get('dis', ''),
             phone=d.get('phone', ''), education=d.get('education', ''), worktype=d.get('worktype', 'Any'))
    db.session.add(u); db.session.commit()
    if role == 'Doctor':   # a doctor account gets a clinic profile to fill in
        db.session.add(Doctor(name=name, spec='General Medicine', city=u.loc or '', place='', svc='', user_id=u.id)); db.session.commit()
    session['uid'] = u.id
    return jsonify(user=user_json(u))

FAILS = {}   # simple login rate limit: 10 wrong tries per 5 minutes per address

@auth.post('/login')
def login():
    d = request.get_json() or {}
    ip = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()
    n, t0 = FAILS.get(ip, (0, 0))
    if n >= 10 and time.time() - t0 < 300:
        abort(429, 'Too many wrong attempts. Please try again in a few minutes.')
    u = User.query.filter_by(email=(d.get('email') or '').strip().lower()).first()
    if not u or not check_password_hash(u.password_hash, d.get('password') or ''):
        FAILS[ip] = (n + 1 if time.time() - t0 < 300 else 1, time.time())
        abort(401, 'Wrong email or password.')
    FAILS.pop(ip, None)
    session['uid'] = u.id
    return jsonify(user=user_json(u))

@auth.post('/logout')
def logout():
    session.clear()
    return jsonify(ok=True)

@auth.get('/me')
def whoami():
    u = me()
    return jsonify(user=user_json(u) if u else None)

@auth.get('/my')
def my_data():
    return jsonify(mine(need()))

@jobs.get('/jobs')
def list_jobs():
    return jsonify([pub(j, 'owner_id') for j in Job.query.filter_by(status='approved').order_by(Job.id)])

@jobs.post('/jobs/<int:jid>/save')
def save_job(jid):
    u = need_role('User'); db.get_or_404(Job, jid)
    s = db.session.get(SavedJob, (u.id, jid))
    if s: db.session.delete(s)
    else: db.session.add(SavedJob(user_id=u.id, job_id=jid))
    db.session.commit()
    return jsonify(mine=mine(u))

@jobs.post('/jobs/<int:jid>/apply')
def apply_job(jid):
    u = need_role('User'); db.get_or_404(Job, jid)
    if db.session.get(Application, (u.id, jid)):
        abort(409, 'You already applied to this job.')
    db.session.add(Application(user_id=u.id, job_id=jid)); db.session.commit()
    return jsonify(mine=mine(u))

@health.get('/doctors')
def list_doctors():
    return jsonify([pub(d, 'user_id') for d in Doctor.query.filter(Doctor.svc != '').order_by(Doctor.id)])

@health.post('/doctors/<int:did>/book')
def book(did):
    u = need_role('User'); db.get_or_404(Doctor, did)
    date = ((request.get_json() or {}).get('date') or '').strip()
    if not date: abort(400, 'Please enter a date.')
    db.session.add(Appointment(user_id=u.id, doctor_id=did, date=date)); db.session.commit()
    return jsonify(ok=True)

@comm.get('/posts')
def list_posts():
    return jsonify([post_json(p) for p in Post.query.order_by(Post.id.desc())])

@comm.post('/posts')
def new_post():
    u = need(); d = request.get_json() or {}
    if not (d.get('title') or '').strip() or not (d.get('body') or '').strip():
        abort(400, 'A post needs a title and some text.')
    p = Post(cat=d.get('cat', 'General'), by=u.name, title=d['title'], body=d['body'], user_id=u.id)
    db.session.add(p); db.session.commit()
    return jsonify(post_json(p))

@comm.post('/posts/<int:pid>/like')
def like(pid):
    u = need(); db.get_or_404(Post, pid)
    l = db.session.get(Like, (pid, u.id))
    if l: db.session.delete(l)
    else: db.session.add(Like(post_id=pid, user_id=u.id))
    db.session.commit()
    return jsonify(ok=True)

@comm.post('/posts/<int:pid>/comment')
def comment(pid):
    u = need(); db.get_or_404(Post, pid)
    text = ((request.get_json() or {}).get('text') or '').strip()
    if not text: abort(400, 'Comment cannot be empty.')
    db.session.add(Comment(post_id=pid, user_id=u.id, text=text)); db.session.commit()
    return jsonify(ok=True)

@comm.post('/posts/<int:pid>/report')
def report(pid):
    u = need(); db.get_or_404(Post, pid)
    db.session.add(Report(post_id=pid, user_id=u.id)); db.session.commit()
    return jsonify(ok=True)

@learn.get('/signs')
def list_signs():
    return jsonify([row(s) for s in Sign.query.order_by(Sign.id)])

@learn.post('/signs/<int:sid>/learn')
def learn_sign(sid):
    u = need(); db.get_or_404(Sign, sid)
    if not db.session.get(Progress, (u.id, sid)):
        db.session.add(Progress(user_id=u.id, sign_id=sid)); db.session.commit()
    return jsonify(mine=mine(u))

@places.get('/places')
def list_places():
    return jsonify([row(p) for p in Place.query.order_by(Place.id)])

dash = Blueprint('dash', __name__, url_prefix='/api')
STATUSES = ('Submitted', 'Under review', 'Shortlisted', 'Selected', 'Rejected')
LIMITS = {'phone': 30, 'skills': 200, 'loc': 100, 'education': 100, 'worktype': 30, 'dis': 200}

def need_role(*roles):
    u = need()
    if u.role not in roles:
        abort(403, 'This page is not available for your account type.')
    return u

@dash.put('/me')
def update_me():
    u = need(); d = request.get_json() or {}
    if (d.get('name') or '').strip():
        u.name = d['name'].strip()[:100]
    for f, n in LIMITS.items():
        if f in d:
            setattr(u, f, (d[f] or '').strip()[:n])
    db.session.commit()
    return jsonify(user=user_json(u))

# ----- employer -----
@dash.post('/employer/jobs')
def post_job():
    u = need_role('Employer', 'Admin'); d = request.get_json() or {}
    if not (d.get('title') or '').strip() or not (d.get('company') or '').strip():
        abort(400, 'A job needs a title and a company.')
    j = Job(title=d['title'].strip()[:200], company=d['company'].strip()[:100], loc=(d.get('loc') or 'Remote')[:100],
            type=d['type'] if d.get('type') in ('Full-Time', 'Part-Time', 'Remote', 'Hybrid') else 'Full-Time',
            pay=(d.get('pay') or '')[:50], desc=(d.get('desc') or '')[:2000], skills=(d.get('skills') or '')[:200],
            owner_id=u.id, status='approved' if u.role == 'Admin' else 'pending')
    db.session.add(j); db.session.commit()
    return jsonify(pub(j, 'owner_id'))

@dash.get('/employer/jobs')
def my_jobs():
    u = need_role('Employer', 'Admin'); out = []
    for j in Job.query.filter_by(owner_id=u.id).order_by(Job.id.desc()):
        r = pub(j, 'owner_id'); r['applicants'] = Application.query.filter_by(job_id=j.id).count(); out.append(r)
    return jsonify(out)

@dash.get('/employer/applications')
def applications():
    u = need_role('Employer', 'Admin'); out = []   # applicant details shown to employers never include private accessibility info
    for a in Application.query.join(Job, Job.id == Application.job_id).filter(Job.owner_id == u.id):
        p = db.session.get(User, a.user_id); j = db.session.get(Job, a.job_id)
        out.append(dict(job_id=j.id, user_id=p.id, job=j.title, name=p.name, email=p.email,
                        skills=p.skills, loc=p.loc, education=p.education, status=a.status))
    return jsonify(out)

@dash.put('/employer/applications/<int:jid>/<int:uid>')
def set_app_status(jid, uid):
    u = need_role('Employer', 'Admin'); j = db.get_or_404(Job, jid)
    if j.owner_id != u.id and u.role != 'Admin':
        abort(403, 'This is not your job posting.')
    a = db.get_or_404(Application, (uid, jid))
    st = (request.get_json() or {}).get('status')
    if st not in STATUSES: abort(400, 'Unknown status.')
    a.status = st; db.session.commit()
    return jsonify(ok=True)

# ----- doctor -----
def my_doctor(u):
    d = Doctor.query.filter_by(user_id=u.id).first()
    if not d:
        d = Doctor(name=u.name, spec='General Medicine', city=u.loc or '', place='', svc='', user_id=u.id)
        db.session.add(d); db.session.commit()
    return d

@dash.get('/doctor/me')
def doctor_me():
    d = my_doctor(need_role('Doctor'))
    appts = [dict(id=a.id, patient=db.session.get(User, a.user_id).name, date=a.date, status=a.status)
             for a in Appointment.query.filter_by(doctor_id=d.id).order_by(Appointment.id.desc())]
    return jsonify(doctor=pub(d, 'user_id'), appointments=appts)

@dash.put('/doctor/me')
def doctor_update():
    d = my_doctor(need_role('Doctor')); b = request.get_json() or {}
    for f, n in (('name', 100), ('spec', 60), ('city', 60), ('place', 120), ('svc', 1000)):
        if f in b: setattr(d, f, (b[f] or '').strip()[:n])
    db.session.commit()
    return jsonify(doctor=pub(d, 'user_id'))

@dash.put('/doctor/appointments/<int:aid>')
def appt_status(aid):
    d = my_doctor(need_role('Doctor')); a = db.get_or_404(Appointment, aid)
    if a.doctor_id != d.id: abort(403, 'This is not your appointment.')
    st = (request.get_json() or {}).get('status')
    if st not in ('Confirmed', 'Declined'): abort(400, 'Unknown status.')
    a.status = st; db.session.commit()
    return jsonify(ok=True)

# ----- admin -----
@dash.get('/admin/stats')
def admin_stats():
    need_role('Admin')
    return jsonify(users=User.query.filter_by(role='User').count(), employers=User.query.filter_by(role='Employer').count(),
                   doctors=Doctor.query.count(), jobs=Job.query.filter_by(status='approved').count(),
                   pending=Job.query.filter_by(status='pending').count(), posts=Post.query.count(),
                   reports=Report.query.count(), applications=Application.query.count(), appointments=Appointment.query.count())

@dash.get('/admin/users')
def admin_users():
    need_role('Admin')
    return jsonify([dict(id=u.id, name=u.name, email=u.email, role=u.role) for u in User.query.order_by(User.id)])

@dash.get('/admin/pending')
def admin_pending():
    need_role('Admin')
    return jsonify([dict(pub(j, 'owner_id'), by=(db.session.get(User, j.owner_id).name if j.owner_id else '')) for j in Job.query.filter_by(status='pending')])

@dash.post('/admin/jobs/<int:jid>/<action>')
def admin_job(jid, action):
    need_role('Admin'); j = db.get_or_404(Job, jid)
    if action not in ('approve', 'reject'): abort(400, 'Unknown action.')
    j.status = 'approved' if action == 'approve' else 'rejected'; db.session.commit()
    return jsonify(ok=True)

@dash.get('/admin/reports')
def admin_reports():
    need_role('Admin'); out = []
    for pid, n in db.session.query(Report.post_id, db.func.count()).group_by(Report.post_id):
        p = db.session.get(Post, pid)
        if p: out.append(dict(id=p.id, title=p.title, by=p.by, body=p.body, reports=n))
    return jsonify(out)

@dash.delete('/admin/posts/<int:pid>')
def admin_delete_post(pid):
    need_role('Admin'); p = db.get_or_404(Post, pid)
    for m in (Comment, Like, Report):
        m.query.filter_by(post_id=pid).delete()
    db.session.delete(p); db.session.commit()
    return jsonify(ok=True)

# ----- learning progress -----
@learn.post('/chapters/<cid>/complete')
def complete_chapter(cid):
    u = need(); d = request.get_json() or {}
    try: score = max(0, min(100, int(d.get('score'))))
    except (TypeError, ValueError): abort(400, 'A score is needed.')
    stars = min(5, (score + 19) // 20) if score else 0
    cp = db.session.get(ChapterProgress, (u.id, cid[:30]))
    if not cp:
        cp = ChapterProgress(user_id=u.id, chapter=cid[:30], score=0, stars=0); db.session.add(cp)
    cp.score, cp.stars = max(cp.score, score), max(cp.stars, stars)
    if not db.session.get(StudyDay, (u.id, ist_day())):
        db.session.add(StudyDay(user_id=u.id, day=ist_day()))
    for sid in d.get('signs') or []:
        if isinstance(sid, int) and db.session.get(Sign, sid) and not db.session.get(Progress, (u.id, sid)):
            db.session.add(Progress(user_id=u.id, sign_id=sid))
    db.session.commit()
    return jsonify(mine=mine(u))

for bp in (auth, jobs, health, comm, learn, places, dash):
    app.register_blueprint(bp)

# ---------- serve the front end (only index.html, css/ and js/) ----------
@app.route('/')
def index():
    return send_from_directory(ROOT, 'index.html')

@app.route('/<d>/<path:f>')
def assets(d, f):
    if d not in ('css', 'js', 'assets'):
        abort(404, 'Not found.')
    return send_from_directory(os.path.join(ROOT, d), f)

# ---------- sample data ----------
def seed():
    if Job.query.first():
        return
    data = json.load(open(os.path.join(HERE, 'seed.json'), encoding='utf-8'))
    day = datetime(2026, 9, 3)
    if os.environ.get('SEED_DEMO_USERS', '1') == '1':      # set SEED_DEMO_USERS=0 on a public server
        for name, email, pw, role in [('Demo User', 'user@demo.com', 'user123', 'User'),
                                      ('Demo Employer', 'employer@demo.com', 'employer123', 'Employer'),
                                      ('Demo Doctor', 'doctor@demo.com', 'doctor123', 'Doctor'),
                                      ('Admin', 'admin@sahaay.dev', 'admin123', 'Admin')]:
            db.session.add(User(name=name, email=email, password_hash=generate_password_hash(pw), role=role))
    for j in data['jobs']: db.session.add(Job(created=day, **j))
    for d in data['doctors']: db.session.add(Doctor(**d))
    for s in data['signs']: db.session.add(Sign(**s))
    for p in data['places']: db.session.add(Place(**p))
    for p in data['posts']:
        db.session.add(Post(id=p['id'], cat=p['cat'], by=p['by'], title=p['title'], body=p['body'], base_likes=p['likes'], created=day))
        db.session.flush()
        for c in p['comments']: db.session.add(Comment(post_id=p['id'], text=c))
    db.session.commit()
    emp, doc, usr = (User.query.filter_by(email=e).first() for e in ('employer@demo.com', 'doctor@demo.com', 'user@demo.com'))
    if emp and doc and usr:   # link the demo accounts so every dashboard has something to show
        for j in Job.query.filter(Job.id.in_([1, 3, 4])): j.owner_id = emp.id
        first = Doctor.query.order_by(Doctor.id).first(); first.user_id = doc.id
        db.session.add(Application(user_id=usr.id, job_id=1, status='Under review'))
        db.session.add(Appointment(user_id=usr.id, doctor_id=first.id, date='10/10/2026'))
        db.session.commit()

with app.app_context():
    db.create_all()
    seed()

if __name__ == '__main__':
    app.run(port=5000, debug=os.environ.get('FLASK_DEBUG') == '1')
