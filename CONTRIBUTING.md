# Contributing
Each team member owns separate modules to avoid merge conflicts.
- Student 1: Learn (js/learn.js), Sign-to-Text, Accessibility (js/accessibility.js) and Assistant (js/assistant.js)
- Student 2: Jobs (js/jobs.js) and Map (js/map.js)
- Student 3: Healthcare (js/healthcare.js), Community (js/community.js) and Profile (js/profile.js)

Workflow: one branch per module, pull the latest `main` before editing shared files (index.html, css/style.css, backend/app.py), open a pull request and let a teammate review it before merging. Run `python -m unittest discover tests` before every pull request.
