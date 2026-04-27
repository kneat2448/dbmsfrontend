# Transport Office DBMS Frontend

A modern, Flask-based web application for managing a Transport Office database. This project provides a user-friendly interface to perform CRUD (Create, Read, Update, Delete) operations on various transport-related records.

## Features

- **Dashboard**: Real-time statistics showing the number of records in each table and query execution times.
- **Comprehensive Data Management**: Full support for 9 core tables:
  - **Citizen**: Manage personal details of citizens.
  - **Driving License**: Track license issue and expiry dates.
  - **Vehicles**: Register and manage vehicle information.
  - **Vehicle Registrations**: Handle registration records.
  - **Violations**: Log traffic violations and fine amounts.
  - **Tax**: Manage vehicle tax records and due dates.
  - **Payment Info**: Record payments and payment modes.
  - **Liability**: Link violations/taxes to specific vehicles.
  - **Paid Using**: Track which payments cover which liabilities.
- **Modular Architecture**: Built using Flask Blueprints for a clean and scalable codebase.
- **Responsive UI**: Sleek design with a focus on usability.

## Tech Stack

- **Backend**: Python 3.x, Flask
- **Database**: MySQL 8.0
- **Frontend**: HTML5, CSS3 (Vanilla), JavaScript
- **Libraries**: `mysql-connector-python`, `python-dotenv`

## Prerequisites

- Python 3.7+
- MySQL Server 8.0+
- Pip (Python package installer)

## Setup & Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd dbmsfrontend
```

### 2. Set Up Virtual Environment (Recommended)
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Database Setup
1. Log in to your MySQL server.
2. Create the database:
   ```sql
   CREATE DATABASE transport_office;
   ```
3. Import the schema:
   ```bash
   mysql -u your_username -p transport_office < schema.sql
   ```

### 5. Environment Variables
Create a `.env` file in the root directory and configure your database credentials:
```env
SECRET_KEY=your_secret_key
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=your_username
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=transport_office
```

## Running the Application

Start the Flask development server:
```bash
python app.py
```
Open your browser and navigate to `http://127.0.0.1:5000`.

## Project Structure

```text
dbmsfrontend/
├── blueprints/        # Modular route handlers for each table
├── static/            # CSS, JS, and image assets
├── templates/         # HTML templates
├── app.py             # Main application entry point
├── config.py          # Configuration and env variable loading
├── db.py              # Database connection and utility functions
├── requirements.txt   # Project dependencies
└── schema.sql         # Database schema definition
```


