# Asset Desk

A full-stack asset management platform for tracking shared inventory, booking resources, approving requests, issuing assets, recording returns and viewing operational analytics.

The project is written to be easy to read and run. Folder names are intentionally familiar: `backend`, `frontend`, `database` and `docs`.

## Live Demo

**Application URL:** https://asset-desk.onrender.com/

Use the demo accounts below to explore the platform features.

## Submitted By

| Name | Enrollment Number | Email |
|--------|--------|--------|
| Aric Sukhija | 24113021 | aric_s@ch.iitr.ac.in |
| Vedant Ganesh Halkude | 24112113 | vedant_gh@ch.iitr.ac.in |
| Vatsal Jain | 24126019 | vatsal_j@hre.iitr.ac.in |

## Technology Stack

### Backend
- Python 3 standard library HTTP server
- Signed cookie sessions
- PBKDF2 password hashing
- REST-style JSON API

### Database
- SQLite
- Relational schema with foreign keys
- Seed data for demo users, assets and bookings

### Frontend
- HTML
- CSS
- Vanilla JavaScript
- Responsive single-page dashboard

### Documentation
- README setup guide
- Design document
- Tech stack and deliverables presentation
- Demonstration video

## Project Resources

The design document, presentation, and demonstration video are available at:

https://drive.google.com/drive/folders/1raa9D2YBpfbu47Iu-0vml2tfvdfJX5Mo?usp=sharing

## Mandatory Feature Coverage

- User registration and login
- Role-based access for admins and users
- Secure sessions through signed HTTP-only cookies
- Admin asset create, edit, delete and categorization
- Search and category filtering for assets
- Asset availability display
- Booking requests with date ranges and quantity checks
- Approval and rejection workflow
- Issue and return tracking
- Due date and overdue handling
- Analytics dashboard with summary cards and utilization bars
- Borrowing history for users
- System-wide booking activity for admins

## Demo Accounts

Both demo accounts use the same password:

```text
password123
```

```text
Admin: admin@example.com
User:  riya@example.com
```

## Setup Instructions

1. Make sure Python 3 is installed.
2. Open a terminal in this project folder.
3. Start the backend server:

```bash
python3 backend/app.py
```

4. Open the app in a browser:

```text
http://127.0.0.1:8000
```

The SQLite database is created automatically at `database/asset_manager.db` on first run.

## Running the Application

Use the admin account to:
- Add, edit and delete assets
- Review booking requests
- Approve or reject bookings
- Mark approved bookings as issued
- Mark issued bookings as returned
- View all booking activity

Use the normal user account to:
- Browse and filter assets
- Request assets for specific dates
- Track active bookings
- View borrowing history

## API Overview

| Method | Route | Purpose |
|----------|----------|----------|
| POST | `/api/register` | Create a user account |
| POST | `/api/login` | Log in and create a session |
| POST | `/api/logout` | Clear the session |
| GET | `/api/me` | Get the current user |
| GET | `/api/assets` | List and filter assets |
| POST | `/api/assets` | Create an asset as admin |
| PUT | `/api/assets/:id` | Update an asset as admin |
| DELETE | `/api/assets/:id` | Delete an asset as admin |
| GET | `/api/bookings` | List user or system bookings |
| POST | `/api/bookings` | Create a booking request |
| POST | `/api/bookings/:id/approve` | Approve a request as admin |
| POST | `/api/bookings/:id/reject` | Reject a request as admin |
| POST | `/api/bookings/:id/issue` | Mark assets as issued |
| POST | `/api/bookings/:id/return` | Mark assets as returned |
| GET | `/api/analytics` | Dashboard summary and utilization data |

## Repository Contents

```text
asset-desk/
├── backend/
│   ├── app.py
│   ├── auth.py
│   └── database.py
├── database/
│   ├── schema.sql
│   └── seed_data.sql
├── docs/
│   └── design_document.md
├── frontend/
│   ├── app.js
│   ├── index.html
│   └── styles.css
└── README.md
```

## Notes for Submission

The mandatory deliverables are represented as:

- Working application: source code in this repository
- GitHub repository contents: project folder with source code, database scripts and documentation
- README: this file
- Design document, presentation, and demonstration video: available through the shared drive

## Project Resources

https://drive.google.com/drive/folders/1raa9D2YBpfbu47Iu-0vml2tfvdfJX5Mo?usp=sharing
