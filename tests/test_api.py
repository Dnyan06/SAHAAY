"""End-to-end API tests. Run from the project folder:  python -m unittest discover tests -v"""
import os, sys, unittest, uuid
os.environ['DATABASE_URL'] = 'sqlite://'          # in-memory database for tests
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
import app as sahaay

def register(c, dis=''):
    email = uuid.uuid4().hex[:8] + '@test.com'
    r = c.post('/api/register', json={'name': 'Test User', 'email': email, 'password': 'secret1', 'dis': dis})
    assert r.status_code == 200, r.get_json()
    return email

class ApiTests(unittest.TestCase):
    def setUp(self):
        self.c = sahaay.app.test_client()

    def test_seed_data(self):
        self.assertEqual(len(self.c.get('/api/jobs').get_json()), 7)
        self.assertEqual(len(self.c.get('/api/doctors').get_json()), 7)
        self.assertEqual(len(self.c.get('/api/places').get_json()), 12)
        self.assertGreater(len(self.c.get('/api/signs').get_json()), 10)

    def test_register_and_login(self):
        self.assertEqual(self.c.post('/api/register', json={'name': 'A', 'email': 'bad', 'password': '1'}).status_code, 400)
        email = register(self.c)
        self.assertEqual(self.c.post('/api/register', json={'name': 'A', 'email': email, 'password': 'secret1'}).status_code, 409)
        self.c.post('/api/logout')
        self.assertEqual(self.c.post('/api/login', json={'email': email, 'password': 'wrong'}).status_code, 401)
        self.assertEqual(self.c.post('/api/login', json={'email': email, 'password': 'secret1'}).status_code, 200)
        self.assertEqual(self.c.post('/api/login', json={'email': 'user@demo.com', 'password': 'user123'}).status_code, 200)

    def test_protected_routes(self):
        for path in ('/api/jobs/1/save', '/api/jobs/1/apply', '/api/doctors/1/book', '/api/posts/1/like'):
            self.assertEqual(self.c.post(path, json={}).status_code, 401, path)
        self.assertEqual(self.c.get('/api/my').status_code, 401)

    def test_jobs_save_apply_and_isolation(self):
        register(self.c)
        self.assertEqual(self.c.post('/api/jobs/1/save').get_json()['mine']['saved'], [1])
        self.assertEqual(self.c.post('/api/jobs/1/save').get_json()['mine']['saved'], [])   # toggles off
        self.c.post('/api/jobs/2/save')
        self.assertEqual(self.c.post('/api/jobs/2/apply').status_code, 200)
        self.assertEqual(self.c.post('/api/jobs/2/apply').status_code, 409)
        other = sahaay.app.test_client(); register(other)
        m = other.get('/api/my').get_json()
        self.assertEqual((m['saved'], m['apps'], m['learned']), ([], [], []))

    def test_booking_and_learning(self):
        register(self.c)
        self.assertEqual(self.c.post('/api/doctors/1/book', json={}).status_code, 400)
        self.assertEqual(self.c.post('/api/doctors/1/book', json={'date': '10/10/2026'}).status_code, 200)
        self.assertEqual(self.c.post('/api/signs/1/learn').get_json()['mine']['learned'], [1])

    def test_community_and_privacy(self):
        register(self.c, dis='secret-info')
        p = self.c.post('/api/posts', json={'title': 'Hi', 'body': 'Hello all', 'cat': 'General'}).get_json()
        self.c.post('/api/posts/%d/like' % p['id'])
        self.c.post('/api/posts/%d/comment' % p['id'], json={'text': 'Nice'})
        self.assertEqual(self.c.post('/api/posts/%d/report' % p['id']).status_code, 200)
        listing = self.c.get('/api/posts').get_data(as_text=True)
        self.assertIn('Hello all', listing)
        self.assertNotIn('secret-info', listing)      # accessibility info stays private

    def test_static_files(self):
        self.assertIn(b'Sahaay', self.c.get('/').data)
        self.assertEqual(self.c.get('/js/jobs.js').status_code, 200)
        self.assertEqual(self.c.get('/backend/app.py').status_code, 404)   # backend code is not exposed

def login(c, email, pw):
    r = c.post('/api/login', json={'email': email, 'password': pw})
    assert r.status_code == 200, r.get_json()

class RoleTests(unittest.TestCase):
    def setUp(self):
        sahaay.FAILS.clear()

    def test_employer_admin_user_flow(self):
        emp = sahaay.app.test_client()
        emp.post('/api/register', json={'name': 'Emp', 'email': 'e%s@t.com' % uuid.uuid4().hex[:6], 'password': 'secret1', 'role': 'Employer'})
        job = emp.post('/api/employer/jobs', json={'title': 'Test Role', 'company': 'TestCo'}).get_json()
        self.assertEqual(job['status'], 'pending')
        self.assertNotIn('Test Role', emp.get('/api/jobs').get_data(as_text=True))      # hidden until approved
        adm = sahaay.app.test_client(); login(adm, 'admin@sahaay.dev', 'admin123')
        self.assertEqual(adm.post('/api/admin/jobs/%d/approve' % job['id']).status_code, 200)
        self.assertIn('Test Role', emp.get('/api/jobs').get_data(as_text=True))
        usr = sahaay.app.test_client(); register(usr)
        self.assertEqual(usr.post('/api/jobs/%d/apply' % job['id']).status_code, 200)
        apps = emp.get('/api/employer/applications').get_json()
        self.assertEqual(apps[0]['job'], 'Test Role'); self.assertNotIn('dis', apps[0])
        uid = apps[0]['user_id']
        self.assertEqual(emp.put('/api/employer/applications/%d/%d' % (job['id'], uid), json={'status': 'Shortlisted'}).status_code, 200)
        self.assertEqual(usr.get('/api/my').get_json()['apps'][0]['status'], 'Shortlisted')

    def test_role_limits(self):
        usr = sahaay.app.test_client(); register(usr)
        self.assertEqual(usr.get('/api/employer/jobs').status_code, 403)
        self.assertEqual(usr.get('/api/admin/stats').status_code, 403)
        self.assertEqual(usr.get('/api/doctor/me').status_code, 403)
        emp = sahaay.app.test_client(); login(emp, 'employer@demo.com', 'employer123')
        self.assertEqual(emp.post('/api/jobs/1/save').status_code, 403)

    def test_doctor_flow(self):
        doc = sahaay.app.test_client()
        doc.post('/api/register', json={'name': 'Dr Test', 'email': 'd%s@t.com' % uuid.uuid4().hex[:6], 'password': 'secret1', 'role': 'Doctor'})
        self.assertNotIn('Dr Test', sahaay.app.test_client().get('/api/doctors').get_data(as_text=True))
        doc.put('/api/doctor/me', json={'spec': 'Audiology', 'city': 'Pune', 'place': 'Test Clinic', 'svc': 'Hearing tests'})
        listing = sahaay.app.test_client().get('/api/doctors').get_json()
        did = [d['id'] for d in listing if d['name'] == 'Dr Test'][0]
        usr = sahaay.app.test_client(); register(usr)
        self.assertEqual(usr.post('/api/doctors/%d/book' % did, json={'date': '1/1/2027'}).status_code, 200)
        appt = doc.get('/api/doctor/me').get_json()['appointments'][0]
        self.assertEqual(doc.put('/api/doctor/appointments/%d' % appt['id'], json={'status': 'Confirmed'}).status_code, 200)
        self.assertEqual(usr.get('/api/my').get_json()['appts'][0]['status'], 'Confirmed')

    def test_admin_stats_and_reports(self):
        adm = sahaay.app.test_client(); login(adm, 'admin@sahaay.dev', 'admin123')
        stats = adm.get('/api/admin/stats').get_json()
        self.assertGreaterEqual(stats['jobs'], 7)
        self.assertEqual(adm.get('/api/admin/users').status_code, 200)

    def test_learning_progress(self):
        usr = sahaay.app.test_client(); register(usr)
        self.assertEqual(usr.post('/api/chapters/u1c1/complete', json={'score': 'x'}).status_code, 400)
        m = usr.post('/api/chapters/u1c1/complete', json={'score': 80}).get_json()['mine']
        self.assertEqual(m['chapters']['u1c1']['stars'], 4)
        self.assertEqual(m['streak'], 1)
        m = usr.post('/api/chapters/u1c1/complete', json={'score': 40}).get_json()['mine']
        self.assertEqual(m['chapters']['u1c1']['score'], 80)       # best score is kept

if __name__ == '__main__':
    unittest.main()
