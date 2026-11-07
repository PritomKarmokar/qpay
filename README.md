<a name="top"></a>

# QPay — Quick Pay

A digital wallet backend (Mini MFS) built with Django and PostgreSQL, designed around financial integrity, concurrency safety, and idempotent money movement.

## Table of Contents

- [Quick Start](#quick-start)
- [Tech Stack](#tech-stack)
- [Progress](#progress)
- [Architecture and Request Flow](#architecture-and-request-flow)
- [Monetary Representation](#monetary-representation)
- [Directory Structure](#directory-structure)
- [API Documentation](#api-documentation)
- [Testing](#testing)
- [Author](#author)

## Quick Start

`Docker` is required to run the application.

Clone the repository:

```bash
git clone https://github.com/PritomKarmokar/qpay.git && cd qpay
```

Create a `.env` file in the project root:

```env
DEBUG=True
MOCK_RESPONSE=False
SERVICE_NAME=qpay
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=127.0.0.1,0.0.0.0,*,localhost

POSTGRES_DB_NAME=qpay_db
POSTGRES_DB_USER=postgres
POSTGRES_DB_HOST=postgres_db
POSTGRES_DB_PORT=5432
POSTGRES_DB_PASSWORD=postgres
POSTGRES_DB_OPTIONS=sslmode=disable
POSTGRES_DB_TEST_NAME=qpay_db

REQUEST_TIMEOUT=100
LOG_LEVEL=DEBUG
LOGGER_ROOT_NAME=qpay
DEV_MODE=True
```

Run the application:

```bash
docker compose up
```

This builds the image if needed, starts PostgreSQL, and then starts the Django app. The API is available at `http://localhost:8000/`.

### More Commands

```bash
docker compose up --build   # Rebuild images and run
docker compose down         # Stop the application
docker compose down -v      # Stop and remove PostgreSQL data
```

> **Note:** Database data persists in the `postgres_data` Docker volume across restarts.

<a href="#top">Back to Top</a>

## Tech Stack

| Component | Technology |
|---|---|
| Language | Python 3.12 |
| Backend Framework | Django |
| API Framework | Django REST Framework |
| Database | PostgreSQL 17 |
| Database Access | Django ORM |
| Containerization | Docker |

## Progress

✅ Implemented | 🔄 Planned

| Area | Features and Best Practices | Status |
|------|------------------------------|--------|
| Wallet Management | • Create and retrieve wallets<br>• User and phone association<br>• Wallet activation and deactivation | ✅<br>✅<br>✅ |
| Money Operations | • Add money via simulated gateway<br>• Gateway reference validation<br>• Peer-to-peer transfers<br>• Self-transfer and insufficient-balance checks | ✅<br>✅<br>✅<br>✅ |
| Financial Integrity | • Atomic transactions with `transaction.atomic`<br>• Row-level locking with `select_for_update`<br>• Integer arithmetic in Poisha<br>• Database constraints<br>• Immutable transaction ledger | ✅<br>✅<br>✅<br>✅<br>✅ |
| Idempotency | • `Idempotency-Key` header support<br>• Stored response replay<br>• Payload mismatch rejection<br>• Processing and completed state tracking | ✅<br>✅<br>✅<br>✅ |
| Security & Access | • Authentication and authorization<br>• Rate limiting and throttling | 🔄<br>🔄 |
| Payments | • Real payment gateway integration<br>• Refund and reversal workflows | 🔄<br>🔄 |
| Observability & Docs | • Wallet statements and reporting<br>• Structured logging and monitoring<br>• Concurrency and integration tests<br>• OpenAPI / Swagger documentation | 🔄<br>🔄<br>🔄<br>🔄 |

<a href="#top">Back to Top</a>

## Architecture and Request Flow

QPay keeps business logic separate from the API and database layers, and wraps every financial operation in a single database transaction.

### Money Transfer Flow

```text
          Client
            |
     POST /transfers/
            |
            v
     Idempotency Check
            |
            v
    Validate Request
            |
            v
    Database Transaction
            |
       +----+----+
       |         |
       v         v
   Lock Sender  Lock Receiver
       |         |
       +----+----+
            |
            v
   Check Available Balance
            |
            v
      Debit Sender
            |
            v
     Credit Receiver
            |
            v
    Create Ledger Records
            |
            v
   Complete Idempotency Record
            |
            v
       Commit Transaction
            |
            v
      Return Response
```

### Design Principles

| Concern | Approach |
|---|---|
| Partial transfers | `transaction.atomic` |
| Concurrent balance updates | Row-level locking (`select_for_update`) |
| Duplicate requests | Idempotency keys |
| Duplicate gateway callbacks | Gateway reference validation |
| Negative balances | Validation and database constraints |
| Precision errors | Integer arithmetic in Poisha |
| Auditability | Immutable transaction ledger |

<a href="#top">Back to Top</a>

## Monetary Representation

The default currency is BDT. All amounts are stored as integer **Poisha**.

| Amount | Value in Poisha |
|---|---:|
| ৳1 | 100 |
| ৳100 | 10,000 |
| ৳1,000 | 100,000 |

- **Minimum transaction:** 100 Poisha (৳1)
- **Maximum transaction:** 2,500,000 Poisha (৳25,000)

## Directory Structure

```bash
├── applibs/                          # Shared utilities
│   ├── choices.py                    # Enum-style choices (transaction types, statuses)
│   ├── decorator.py                  # Custom decorators
│   ├── helpers.py                    # General helper functions
│   ├── logger.py                     # Logger configuration
│   ├── response.py                   # Standardized API response helpers
│   └── validators.py                 # Reusable validators
├── mini_wallet/                      # Core wallet application
│   ├── admin/
│   │   ├── idempotency.py            # Idempotency record admin
│   │   ├── transaction.py            # Transaction ledger admin
│   │   ├── user_wallet.py            # Wallet admin
│   │   └── wallet_transfer.py        # Transfer admin
│   ├── management/
│   │   └── commands/
│   │       └── seed_admin.py         # Command to seed an admin user
│   ├── migrations/                   # Database schema migrations
│   ├── models/
│   │   ├── idempotency.py            # Idempotency record model
│   │   ├── transaction.py            # Transaction ledger model
│   │   ├── user_wallet.py            # Wallet model
│   │   └── wallet_transfer.py        # Transfer model
│   ├── serializers/
│   │   ├── add_money.py              # Add money request/response serializers
│   │   ├── history.py                # Transaction history serializers
│   │   ├── transfer.py               # Transfer request/response serializers
│   │   └── wallets.py                # Wallet serializers
│   ├── tests/                        # Test suite
│   ├── views/
│   │   ├── add_money.py              # Add money API view
│   │   ├── history.py                # Transaction history API view
│   │   ├── transfer.py               # Money transfer API view
│   │   └── wallets.py                # Wallet API views
│   ├── apps.py                       # App configuration
│   └── urls.py                       # App-level URL routing
├── qpay/                             # Django project configuration
│   ├── asgi.py                       # ASGI entry point
│   ├── settings.py                   # Project settings
│   ├── urls.py                       # Root URL configuration
│   └── wsgi.py                       # WSGI entry point
├── Dockerfile                        # Application image
├── docker-compose.yml                # Django and PostgreSQL services
├── manage.py                         # Django management entry point
├── requirements.txt                  # Python dependencies
└── README.md                         # Project documentation
```
<a href="#top">Back to Top</a>

## API Documentation

Base URL: `http://localhost:8000/api/v1`

### Wallet Endpoints

#### Create Wallet

- **URL**: `/wallets/`
- **Method**: `POST`
- **Description**: Creates a new wallet for a user.
- **Request Body**:
  ```json
  {
    "user_id": "user_001",
    "phone": "017XXXXXXXX"
  }
  ```
- **Success Response**: `201 Created`
- **Error Responses**: `400 Bad Request`, `409 Conflict`, `500 Internal Server Error`

#### Retrieve Wallet

- **URL**: `/wallets/{wallet_id}`
- **Method**: `GET`
- **Description**: Returns wallet details and current balance.
- **Success Response**: `200 OK`
  ```json
  {
    "wallet_id": "01JXXXXXXXXXXXXXXX",
    "phone": "017XXXXXXXX",
    "currency": "BDT",
    "balance": 10000
  }
  ```
- **Error Responses**: `404 Not Found`, `500 Internal Server Error`

### Transfer Endpoints

#### Transfer Money

- **URL**: `/transfers/`
- **Method**: `POST`
- **Description**: Atomically transfers money between two wallets. `amount` is in Poisha.
- **Headers**: `Idempotency-Key: <unique-key>` (required)
- **Request Body**:
  ```json
  {
    "from_wallet_id": "w_aaa",
    "to_wallet_id": "w_bbb",
    "amount": 10000,
    "note": "Lunch"
  }
  ```
- **Success Response**: `201 Created`
  ```json
  {
    "transfer_id": "t_123",
    "from_wallet_id": "w_aaa",
    "to_wallet_id": "w_bbb",
    "amount": 10000,
    "status": "COMPLETED"
  }
  ```
- **Error Responses**: `400 Bad Request`, `404 Not Found`, `409 Conflict`, `422 Unprocessable Entity`, `500 Internal Server Error`

### Transaction History Endpoints

#### List Wallet Transactions

- **URL**: `/wallets/{wallet_id}/transactions/`
- **Method**: `GET`
- **Description**: Returns the ledger entries for a wallet, including type, status, and reference.
- **Success Response**: `200 OK`
- **Error Responses**: `404 Not Found`, `500 Internal Server Error`

<a href="#top">Back to Top</a>

## Testing

```bash
docker compose exec django-web python manage.py test
```

To test a specific app, append its name: `python manage.py test your_app_name`.

[Back to Top](#top)