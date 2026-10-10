# Sahaay - Access for everyone
An accessibility platform for jobs, healthcare, sign-language learning and community. BCA final-year project (Project Based Learning BCA30050), MIT WPU. Group 04: Harsha Dhage, Zaara Anam, Hussain Mohammad. Mentor: Prof. Suryakant Karande.

## Run on your computer
    pip install -r requirements.txt
    python backend/app.py
Open http://localhost:5000. The SQLite database is created and filled with sample data on the first run. Open the site through this address, not by double-clicking index.html.

Demo logins: user@demo.com / user123, employer@demo.com / employer123, doctor@demo.com / doctor123, admin@sahaay.dev / admin123

## Put it on GitHub
    git init
    git add .
    git commit -m "Sahaay project"
    git branch -M main
    git remote add origin https://github.com/YOUR-NAME/Sahaay-Website.git
    git push -u origin main

## Deploy (Render, free plan)
1. Push the project to GitHub.
2. On render.com choose New > Blueprint and select your repository. `render.yaml` creates the web service and a PostgreSQL database and sets SECRET_KEY, DATABASE_URL and COOKIE_SECURE for you.
3. When the build finishes, open the URL Render gives you.
Any other host that runs Python works too: start command `gunicorn --chdir backend app:app`, and set the variables from `.env.example`.

For a public site set SEED_DEMO_USERS=0 so the demo accounts are not created. Free Render databases expire after a while, so re-create it for the demo day if needed.

## Updating from an older copy
The database tables changed (new columns and tables). Delete `backend/sahaay.db` once before running, or it will fail with a "no such column" error. On Render a fresh database is created for you.

## What each account type sees (Profile page)
- User: applications with status, saved jobs, appointments, learning streak
- Employer: post jobs (an admin approves them), see applicants, change each applicant's status
- Doctor: edit the clinic profile shown in the directory, confirm or decline appointment requests
- Admin: statistics, approve or reject jobs, delete reported posts, see all users

## Sign Language Centre
Four tabs: Learning path (units, chapters and stars with lessons and quizzes built from the videos), Practice (flashcards and a daily quiz), Dictionary and Achievements (daily streak and badges). Videos are in `assets/signs/`. Alphabet videos carry the ISLRTC watermark: give credit and check the licence before publishing.

## Tests
    python -m unittest discover tests -v

## Folders
    index.html, css/, js/   front end (one JavaScript file per module)
    backend/app.py          Flask app: tables, 6 blueprints, sample data (backend/seed.json)
    backend/schema.sql      PostgreSQL tables
    tests/test_api.py       API tests
    Procfile, render.yaml, requirements.txt, .env.example   deployment
    VIVA.md                 viva notes
