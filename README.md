# Subscription Management System

A SaaS Subscription Management System built with FastAPI and vanilla JavaScript.

## Project Overview

This system provides a complete subscription management solution with two teams:

### Person 1 Responsibilities
- **Authentication** - JWT-based authentication and authorization
- **Products** - Product catalog management
- **Plans** - Subscription plan configuration
- **Discounts** - Discount code and coupon management
- **Dashboard** - Main dashboard and reporting features

### Person 2 Responsibilities
- **Quotations** - Quotation template management
- **Subscriptions** - Subscription lifecycle management
- **Invoices** - Invoice generation and management
- **Payments** - Payment recording and tracking
- **Testing** - Test coverage and documentation

## Tech Stack

- **Backend**: Python 3.14, FastAPI, SQLAlchemy 2.0, SQLite
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Authentication**: JWT tokens, bcrypt password hashing
- **Database**: SQLite with SQLModel ORM

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── api/routes/          # API route definitions
│   │   │   ├── quotations.py    # Quotation templates (Person 2)
│   │   │   ├── subscriptions.py # Subscription management (Person 2)
│   │   │   ├── invoices.py      # Invoice handling (Person 2)
│   │   │   ├── payments.py      # Payment recording (Person 2)
│   │   │   ├── products.py      # Product catalog (Person 1)
│   │   │   ├── plans.py         # Plan definitions (Person 1)
│   │   │   └── users.py         # User management (Person 1)
│   │   ├── models/              # SQLAlchemy ORM models
│   │   ├── services/            # Business logic services
│   │   ├── core/                # Core configuration and dependencies
│   │   └── main.py              # Application entry point
│   └── tests/                   # Backend tests (Person 2)
│
├── frontend/
│   ├── index.html               # Main HTML page
│   └── static/
│       ├── css/styles.css       # Styling
│       └── js/app.js            # Frontend application
│
├── backend/tests/               # Test files
│   ├── test_quotations.py
│   ├── test_subscriptions.py
│   ├── test_invoices.py
│   ├── test_payments.py
│   └── test_subscription_flow.py
│
├── requirements.txt
├── .env.example
└── README.md
```

## Getting Started

### Prerequisites
- Python 3.14+
- pip

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd Subscription-Management-System

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env with your configuration
```

### Running the Application

```bash
# Start the FastAPI server
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000

# Open in browser
http://localhost:8000
```

### Running Tests

```bash
# Run all tests
python -m pytest backend/tests/ -v

# Run specific test file
python -m pytest backend/tests/test_quotations.py -v
```

## API Endpoints

### Person 2 Endpoints (Implemented)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/quotation-templates` | List all quotation templates |
| POST | `/api/v1/quotation-templates` | Create new quotation template |
| PATCH | `/api/v1/quotation-templates/{id}` | Update quotation template |
| DELETE | `/api/v1/quotation-templates/{id}` | Delete quotation template |
| GET | `/api/v1/subscriptions` | List all subscriptions |
| POST | `/api/v1/subscriptions` | Create new subscription |
| GET | `/api/v1/subscriptions/{id}` | Get subscription details |
| PATCH | `/api/v1/subscriptions/{id}/status` | Change subscription status |
| POST | `/api/v1/subscriptions/{id}/pause` | Pause subscription |
| POST | `/api/v1/subscriptions/{id}/resume` | Resume subscription |
| GET | `/api/v1/invoices` | List all invoices |
| POST | `/api/v1/invoices` | Create new invoice |
| POST | `/api/v1/invoices/{id}/confirm` | Confirm invoice |
| POST | `/api/v1/invoices/{id}/cancel` | Cancel invoice |
| GET | `/api/v1/invoices/{id}/outstanding` | Get outstanding amount |
| GET | `/api/v1/payments` | List all payments |
| POST | `/api/v1/payments` | Record new payment |

### Person 1 Endpoints (Dependency)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/plans` | List all plans |
| GET | `/api/v1/products` | List all products |
| GET | `/api/v1/users/customers` | List all customers |

## Subscription Lifecycle

1. **Draft** - Initial subscription state
2. **Quotation** - Sent to customer for review
3. **Confirmed** - Customer has accepted
4. **Active** - Billing has started
5. **Closed** - Subscription ended

## Usage

### Web Interface
1. Navigate to `http://localhost:8000`
2. Use sidebar to navigate between modules
3. The current page is remembered on refresh via URL hash

### API Authentication
The system uses mock authentication for testing. In production, JWT tokens would be required for all operations.

## Testing

### Run All Tests
```bash
python -m pytest backend/tests/ -v
```

### Test Coverage
- Quotation CRUD operations
- Subscription lifecycle and status transitions
- Invoice generation (requires active subscription)
- Payment recording and outstanding balance calculation
- Business rule validation

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PROJECT_NAME` | Application name | "Subscription Management System" |
| `DATABASE_URL` | SQLite database path | `sqlite:///./subscription_system.db` |
| `SECRET_KEY` | JWT secret key | (required in production) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiration | 60 |

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## License

[Add license information]

## Authors

- **Person 1 Team**: Authentication, Products, Plans, Dashboard
- **Person 2 Team**: Quotations, Subscriptions, Invoices, Payments, Testing