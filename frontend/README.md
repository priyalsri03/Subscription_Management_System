# SaaS Subscription Management Dashboard - Frontend

A professional, modern SaaS dashboard built with HTML, CSS, and JavaScript that connects to the FastAPI backend.

## Tech Stack
- **HTML5** - Semantic markup
- **CSS3** - Modern design with CSS variables, flexbox, and grid
- **Vanilla JavaScript** - No frameworks, direct API integration
- **FastAPI** - Backend API (Person 2 modules)

## Features

### 1. Overview Dashboard
- Total subscriptions counter
- Active subscriptions counter
- Total invoices counter
- Pending payments indicator
- Overdue invoices counter
- Total revenue display
- Recent invoices table
- Recent payments table

### 2. Quotation Management
- View all quotation templates
- Create new quotation templates
- Select plan for quotation
- Set validity period (days)
- Edit/Delete quotations

### 3. Subscription Management
- List all subscriptions
- Create new subscriptions
- View subscription details
- Pause/Resume subscriptions
- Close subscriptions
- Status badges (draft, quotation, confirmed, active, closed)

### 4. Invoice Management
- List all invoices
- Generate new invoices
- View invoice details with line items
- Confirm invoices
- Cancel invoices
- Print invoices (placeholder)
- Status tracking (draft, confirmed, paid, cancelled)

### 5. Payment Management
- Record payments
- Select payment method (Bank Transfer, Credit Card, PayPal, Cash, Check)
- Map payments to invoices
- View payment history
- Update invoice status to "paid" when fully paid

## Page Structure

```
frontend/
├── index.html          # Main HTML template
├── static/
│   ├── css/
│   │   └── styles.css  # All styling
│   └── js/
│       └── app.js      # Main JavaScript application
└── README.md           # This file
```

## API Endpoints Used

### Person 2 Endpoints (Implemented):
- `GET  /api/v1/quotation-templates` - List quotations
- `POST /api/v1/quotation-templates` - Create quotation
- `DELETE /api/v1/quotation-templates/{id}` - Delete quotation
- `GET  /api/v1/subscriptions` - List subscriptions
- `POST /api/v1/subscriptions` - Create subscription
- `GET  /api/v1/subscriptions/{id}` - Get subscription
- `POST /api/v1/subscriptions/{id}/pause` - Pause subscription
- `POST /api/v1/subscriptions/{id}/resume` - Resume subscription
- `POST /api/v1/subscriptions/{id}/status` - Change status
- `GET  /api/v1/invoices` - List invoices
- `POST /api/v1/invoices` - Create invoice
- `GET  /api/v1/invoices/{id}` - Get invoice
- `POST /api/v1/invoices/{id}/confirm` - Confirm invoice
- `POST /api/v1/invoices/{id}/cancel` - Cancel invoice
- `GET  /api/v1/invoices/{id}/outstanding` - Get outstanding amount
- `GET  /api/v1/payments` - List payments
- `POST /api/v1/payments` - Create payment

### Person 1 Endpoints (Needed but NOT implemented - owned by Person 1):
- `GET  /api/v1/plans` - List plans
- `GET  /api/v1/products` - List products
- `GET  /api/v1/users/customers` - List customers

## Features Dependent on Person 1's Missing Modules

The following features require Person 1's endpoints that are not yet implemented:

1. **Customer Selection** - The subscription creation form needs `/api/v1/users/customers` to populate customer dropdown
2. **Plan Selection** - The quotation and subscription forms need `/api/v1/plans` to populate plan options
3. **Product Information** - Some features would benefit from `/api/v1/products` for product descriptions

**Note:** These endpoints have been added to `backend/app/api/plans.py` and `backend/app/api/products.py` but are read-only (Person 1 owns the CRUD operations).

## Design Features

- **Modern Sidebar Navigation** - Collapsible, responsive design
- **Dashboard Cards** - Visual stat tiles with icons
- **Data Tables** - Clean tables with status badges
- **Modal Dialogs** - Form overlays for create/edit actions
- **Responsive Layout** - Works on mobile and desktop
- **Status Badges** - Color-coded status indicators
- **Clean Typography** - Inter font family
- **Consistent Spacing** - CSS variables for design tokens

## Color Scheme

- Primary: `#6366f1` (indigo-500)
- Success: `#10b981` (green-500)
- Warning: `#f59e0b` (amber-500)
- Danger: `#ef4444` (red-500)
- Info: `#3b82f6` (blue-500)

## Usage

1. Start the FastAPI backend:
   ```bash
   uvicorn backend.app.main:app --reload
   ```

2. Open `http://localhost:8000` in your browser

3. The frontend will automatically load and connect to the API

## Authentication

The frontend currently uses mock authentication for staff users. The actual JWT authentication is handled by Person 1's `auth.py` endpoint (not yet implemented).

## Notes

- All monetary values are displayed in INR (₹)
- Status badges use consistent colors across all views
- Empty states are handled gracefully with helpful messages
- Error handling provides user-friendly alerts
- The frontend caches reference data (plans, products) for performance