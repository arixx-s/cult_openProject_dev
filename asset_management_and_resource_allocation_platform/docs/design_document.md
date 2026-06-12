# Smart Asset Management and Resource Allocation Platform

## Problem Understanding

Organizations such as the Cultural Council of IIT Roorkee manage shared assets across many events and sections. When inventory is tracked through informal messages, spreadsheets and registers, teams face double bookings, unclear availability, delayed returns and weak accountability.

This platform centralizes asset records, booking requests, approval decisions, issue and return tracking, borrowing history and operational analytics. The system supports two roles: administrators who manage inventory and approvals, and users who discover assets and request them for event durations.

## System Architecture

The application follows a simple full-stack architecture:

1. Browser frontend served as static files.
2. Python backend exposing REST-style JSON endpoints.
3. SQLite database storing users, assets and bookings.
4. Signed HTTP-only cookies maintaining secure sessions.

```text
Browser UI
   |
   | HTTP + JSON
   v
Python API Server
   |
   | SQL queries
   v
SQLite Database
```

## Database Schema

### users

Stores login identity, password hash and role.

| Field | Type | Notes |
| --- | --- | --- |
| id | integer | Primary key |
| name | text | Display name |
| email | text | Unique login email |
| password_hash | text | Salted PBKDF2 hash |
| role | text | `admin` or `user` |
| created_at | text | Creation timestamp |

### assets

Stores inventory records.

| Field | Type | Notes |
| --- | --- | --- |
| id | integer | Primary key |
| asset_name | text | Human-readable asset name |
| category | text | Camera, Audio, Lighting, etc. |
| description | text | Asset details |
| quantity_total | integer | Total owned quantity |
| status | text | Operational status label |
| created_at | text | Creation timestamp |

### bookings

Stores lifecycle records for requests, approvals, issue and returns.

| Field | Type | Notes |
| --- | --- | --- |
| id | integer | Primary key |
| asset_id | integer | Foreign key to assets |
| user_id | integer | Foreign key to users |
| quantity_requested | integer | Requested units |
| start_date | text | Booking start date |
| end_date | text | Booking due date |
| purpose | text | Event or usage reason |
| status | text | pending, approved, rejected, issued, returned, overdue |
| returned_at | text | Return date |
| created_at | text | Request timestamp |

## Entity Relationship Diagram

```text
users 1 -------- * bookings * -------- 1 assets

users.id      -> bookings.user_id
assets.id     -> bookings.asset_id
```

## API Overview

Authentication:
- `POST /api/register`
- `POST /api/login`
- `POST /api/logout`
- `GET /api/me`

Inventory:
- `GET /api/assets`
- `POST /api/assets`
- `PUT /api/assets/:id`
- `DELETE /api/assets/:id`

Booking workflow:
- `GET /api/bookings`
- `POST /api/bookings`
- `POST /api/bookings/:id/approve`
- `POST /api/bookings/:id/reject`
- `POST /api/bookings/:id/issue`
- `POST /api/bookings/:id/return`

Analytics:
- `GET /api/analytics`

## Design Decisions

The project uses Python, SQLite and vanilla frontend technologies to keep the application reproducible without external service setup. The backend is split into small files for routing, authentication and database access. The database keeps source-of-truth quantities in the `assets` table while availability is calculated from approved, issued and overdue bookings that overlap the requested date range.

Role-based access is enforced on the backend. Admin-only routes reject normal users even if frontend controls are hidden. Passwords are salted and hashed using PBKDF2. Sessions are signed and stored in HTTP-only cookies to reduce accidental exposure in browser JavaScript.

The frontend is a responsive single-page interface because the workflow benefits from quick movement between assets, bookings, history and analytics. Admins see management actions, while users see request and history actions.

## Mandatory Deliverables Mapping

| Deliverable | Implementation |
| --- | --- |
| Working application | Python backend, SQLite database, HTML/CSS/JS frontend |
| Design document | This document exported as PDF |
| Public GitHub repository | Folder contains source, config, scripts and documentation |
| README | Setup, stack, routes and feature list included |
| Demonstration video | Can be recorded from the seeded demo workflow |

## Scalability Considerations

The schema separates users, assets and bookings, which allows future growth into sections, events, notifications, audit logs or maintenance records. The API boundaries are clear enough to replace SQLite with PostgreSQL if concurrent usage increases. Availability logic is centralized in the backend so inventory integrity remains consistent across UI screens.
