# Portfolio Tracker

## Description
Portfolio Tracker is a web application designed to help users track their investments in stocks, cryptocurrencies, and other assets. It allows users to record trades, view their current portfolio valuation, analyze performance metrics like CAGR and XIRR, and visualize asset allocation and performance against benchmarks.

## Features
- **Trade Management:** Add and list buy/sell trades for various assets.
- **Portfolio Overview:**
    - View current quantity, average buy price, and cost basis for each asset.
    - Track current market value (using mock prices for now) and overall portfolio value.
    - Calculate and display absolute and percentage gain/loss for each asset and the total portfolio.
- **Performance Metrics:**
    - **CAGR (Compound Annual Growth Rate):** Calculated based on mock historical portfolio values over a defined period.
    - **XIRR (Extended Internal Rate of Return):** Calculated based on actual trade dates, amounts, and current portfolio valuation, providing a money-weighted rate of return.
- **Visualizations:**
    - **Asset Allocation:** Pie chart showing the current value distribution across different assets in the portfolio.
    - **Performance Comparison:** Line chart comparing mock historical portfolio performance (percentage change) against selectable benchmarks (e.g., SPY, QQQ) over time.
- **Data Storage:** Uses an SQLite database (`portfolio.db`) to store trade and portfolio asset information.

## Getting Started / Installation

### Prerequisites
- Python 3.7+
- pip (Python package installer)

### Setup Steps
1.  **Clone the repository** (or download the project files):
    ```bash
    git clone https://github.com/JiranekJ/TestJules.git
    ```
    (Replace the URL with the actual repository URL if available.)

2.  **Navigate to the project directory:**
    ```bash
    cd portfolio-tracker
    ```

3.  **Create a virtual environment:**
    ```bash
    python -m venv venv
    ```

4.  **Activate the virtual environment:**
    -   On Windows:
        ```bash
        venv\Scripts\activate
        ```
    -   On macOS and Linux:
        ```bash
        source venv/bin/activate
        ```

5.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

6.  **Run the application:**
    ```bash
    python portfolio_tracker/app.py
    ```
    The application will start, and the database (`portfolio.db`) will be created in the `portfolio_tracker` directory if it doesn't exist. Tables for trades and portfolio assets will also be initialized.

7.  **Open your web browser** and go to:
    ```
    http://127.0.0.1:5000
    ```

## Technologies Used
- **Backend:**
    - Flask (Web framework)
    - SQLAlchemy (ORM for database interaction)
- **Database:**
    - SQLite (File-based database)
- **Frontend:**
    - HTML / Jinja2 (Templating)
    - CSS
    - JavaScript
- **Charting:**
    - Chart.js (JavaScript library for data visualization)
- **Financial Calculations:**
    - pyxirr (Python library for XIRR calculation)
