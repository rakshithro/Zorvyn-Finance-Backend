# Finance Dashboard API

Finance Dashboard — built with FastAPI. Supports multiple user roles for financial records, transaction tracking, and spending summaries.


## Features

- User login and registration with JWT tokens
- Three roles: viewer, analyst and admin
- Track all income and expense transactions
- Dashboard with totals, trends, and category breakdowns
- Rate limiting to prevent abuse
- Audit log that records every change


## Setup

# Create a virtual environment and install packages
python -m venv venv
pip install -r requirements.txt

# Copy the example env file 
cp .env.example .env

# Start the server
uvicorn main:app --reload

When the server starts, it creates a default admin account:

- Email:admin@finance.com
- Password:admin123


## Seeding test data

python seed.py - run this on terminal   (it is a script that fills the database with sample data for testing purposes) 

This creates 6 users (1 admin, 2 analysts, 3 viewers) and around 60 transactions spread over the last 6 months — useful for testing the dashboard.



## API docs

when server is running, open one of the link:

- http://localhost:8000/docs — Swagger ui
- http://localhost:8000/redoc — ReDoc



## Roles

| Role | What they can do |
| viewer | See their own transactions and dashboard |
| analyst | See all transactions, create/edit/delete their own |
| admin | Everything — manage users, all transactions, audit logs |

New users register as viewers. Admins can promote them.


## Main endpoints

### Auth — `/api/v1/auth`

| POST | `/register` | Create a new account |
| POST | `/login` | Get a JWT token |
| GET | `/me` | See your own profile |
| POST | `/change-password` | Update your password |

### Transactions — `/api/v1/transactions`

| GET | `/` | List transactions (with filters) | viewer |
| GET | `/{id}` | Get one transaction | viewer |
| POST | `/` | Create a transaction | analyst |
| PATCH | `/{id}` | Edit a transaction | analyst |
| DELETE | `/{id}` | Delete | analyst |

You can filter transactions by type, category, and date range as given

----------------------------------------------------------------------------------------------------------