-- Sahaay database schema (PostgreSQL). Generated from the SQLAlchemy models in backend/app.py

CREATE TABLE accessibility_locations (
	id SERIAL NOT NULL, 
	n VARCHAR(120), 
	city VARCHAR(60), 
	lat FLOAT, 
	lng FLOAT, 
	s VARCHAR(10), 
	ramp VARCHAR(10), 
	lift VARCHAR(10), 
	wash VARCHAR(10), 
	sign VARCHAR(10), 
	park VARCHAR(10), 
	PRIMARY KEY (id)
);

CREATE TABLE lessons (
	id SERIAL NOT NULL, 
	t VARCHAR(60), 
	cat VARCHAR(40), 
	d VARCHAR(120), 
	how TEXT, 
	PRIMARY KEY (id)
);

CREATE TABLE users (
	id SERIAL NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	email VARCHAR(120) NOT NULL, 
	password_hash VARCHAR(255) NOT NULL, 
	role VARCHAR(20), 
	skills VARCHAR(200), 
	loc VARCHAR(100), 
	dis VARCHAR(200), 
	phone VARCHAR(30), 
	education VARCHAR(100), 
	worktype VARCHAR(30), 
	PRIMARY KEY (id), 
	UNIQUE (email)
);

CREATE TABLE chapter_progress (
	user_id INTEGER NOT NULL, 
	chapter VARCHAR(30) NOT NULL, 
	score INTEGER, 
	stars INTEGER, 
	PRIMARY KEY (user_id, chapter), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE TABLE community_posts (
	id SERIAL NOT NULL, 
	cat VARCHAR(30), 
	by VARCHAR(100), 
	title VARCHAR(200), 
	body TEXT, 
	base_likes INTEGER, 
	created TIMESTAMP WITHOUT TIME ZONE, 
	user_id INTEGER, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE TABLE healthcare_services (
	id SERIAL NOT NULL, 
	name VARCHAR(100), 
	spec VARCHAR(60), 
	city VARCHAR(60), 
	place VARCHAR(120), 
	svc TEXT, 
	user_id INTEGER, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE TABLE jobs (
	id SERIAL NOT NULL, 
	title VARCHAR(200), 
	company VARCHAR(100), 
	loc VARCHAR(100), 
	type VARCHAR(30), 
	pay VARCHAR(50), 
	"desc" TEXT, 
	skills VARCHAR(200), 
	created TIMESTAMP WITHOUT TIME ZONE, 
	status VARCHAR(20), 
	owner_id INTEGER, 
	PRIMARY KEY (id), 
	FOREIGN KEY(owner_id) REFERENCES users (id)
);

CREATE TABLE study_days (
	user_id INTEGER NOT NULL, 
	day VARCHAR(10) NOT NULL, 
	PRIMARY KEY (user_id, day), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE TABLE user_progress (
	user_id INTEGER NOT NULL, 
	sign_id INTEGER NOT NULL, 
	PRIMARY KEY (user_id, sign_id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
	FOREIGN KEY(sign_id) REFERENCES lessons (id) ON DELETE CASCADE
);

CREATE TABLE appointments (
	id SERIAL NOT NULL, 
	user_id INTEGER, 
	doctor_id INTEGER, 
	date VARCHAR(30), 
	status VARCHAR(20), 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
	FOREIGN KEY(doctor_id) REFERENCES healthcare_services (id) ON DELETE CASCADE
);

CREATE TABLE job_applications (
	user_id INTEGER NOT NULL, 
	job_id INTEGER NOT NULL, 
	status VARCHAR(20), 
	PRIMARY KEY (user_id, job_id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
	FOREIGN KEY(job_id) REFERENCES jobs (id) ON DELETE CASCADE
);

CREATE TABLE post_comments (
	id SERIAL NOT NULL, 
	post_id INTEGER, 
	user_id INTEGER, 
	text TEXT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(post_id) REFERENCES community_posts (id) ON DELETE CASCADE, 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE TABLE post_likes (
	post_id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	PRIMARY KEY (post_id, user_id), 
	FOREIGN KEY(post_id) REFERENCES community_posts (id) ON DELETE CASCADE, 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE TABLE post_reports (
	id SERIAL NOT NULL, 
	post_id INTEGER, 
	user_id INTEGER, 
	PRIMARY KEY (id), 
	FOREIGN KEY(post_id) REFERENCES community_posts (id) ON DELETE CASCADE, 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE TABLE saved_jobs (
	user_id INTEGER NOT NULL, 
	job_id INTEGER NOT NULL, 
	PRIMARY KEY (user_id, job_id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
	FOREIGN KEY(job_id) REFERENCES jobs (id) ON DELETE CASCADE
);

