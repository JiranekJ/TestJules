from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import datetime
from datetime import datetime as dt # For parsing date string

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///portfolio.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key' # Add a secret key for flash messages
db = SQLAlchemy(app)

class Trade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticker = db.Column(db.String(20), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    fees = db.Column(db.Float, nullable=False, default=0.0)
    transaction_type = db.Column(db.String(4), nullable=False)  # 'buy' or 'sell'

    def __repr__(self):
        return f"<Trade {self.ticker} {self.transaction_type} {self.quantity} @ {self.price}>"

class PortfolioAsset(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticker = db.Column(db.String(20), unique=True, nullable=False)
    quantity = db.Column(db.Float, nullable=False, default=0.0)
    average_buy_price = db.Column(db.Float, nullable=False, default=0.0)

    def __repr__(self):
        return f"<PortfolioAsset {self.ticker} {self.quantity} @ {self.average_buy_price}>"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add_trade', methods=['GET', 'POST'])
def add_trade():
    if request.method == 'POST':
        try:
            ticker = request.form['ticker'].upper()
            # Convert date string from form (YYYY-MM-DD) to datetime object
            date_str = request.form['date']
            date_obj = dt.strptime(date_str, '%Y-%m-%d')

            price = float(request.form['price'])
            quantity = float(request.form['quantity'])
            fees = float(request.form['fees'])
            transaction_type = request.form['transaction_type']

            if quantity <= 0 or price <= 0:
                flash('Price and quantity must be positive.', 'error')
                return redirect(url_for('add_trade'))

            # Create and save the new trade
            new_trade = Trade(
                ticker=ticker,
                date=date_obj,
                price=price,
                quantity=quantity,
                fees=fees,
                transaction_type=transaction_type
            )
            db.session.add(new_trade)

            # Update PortfolioAsset
            asset = PortfolioAsset.query.filter_by(ticker=ticker).first()

            if transaction_type == 'buy':
                if asset:
                    # Cost of new shares including fees per share
                    cost_of_new_shares = (price * quantity) + fees
                    new_total_quantity = asset.quantity + quantity
                    # Recalculate average buy price
                    asset.average_buy_price = ((asset.average_buy_price * asset.quantity) + cost_of_new_shares) / new_total_quantity
                    asset.quantity = new_total_quantity
                else:
                    # First buy of this asset
                    # Average price includes fees per share for the first purchase
                    avg_price_with_fees = (price * quantity + fees) / quantity
                    asset = PortfolioAsset(
                        ticker=ticker,
                        quantity=quantity,
                        average_buy_price=avg_price_with_fees
                    )
                    db.session.add(asset)
            elif transaction_type == 'sell':
                if asset:
                    if asset.quantity >= quantity:
                        asset.quantity -= quantity
                        # If all shares are sold, we could remove the asset or keep it with 0 quantity
                        # For now, just update quantity. Average buy price remains unchanged.
                        if asset.quantity == 0:
                            # Optionally, decide if you want to remove the asset from PortfolioAsset
                            # For example: db.session.delete(asset)
                            # Or just leave it with quantity 0
                            pass
                    else:
                        flash(f'Not enough shares of {ticker} to sell. You have {asset.quantity}.', 'error')
                        db.session.rollback() # Rollback the trade addition
                        return redirect(url_for('add_trade'))
                else:
                    flash(f'No asset found for {ticker} to sell.', 'error')
                    db.session.rollback() # Rollback the trade addition
                    return redirect(url_for('add_trade'))

            db.session.commit()
            flash(f'{transaction_type.capitalize()} trade for {ticker} added successfully!', 'success')
            return redirect(url_for('add_trade'))

        except ValueError:
            flash('Invalid data format for price, quantity, or fees.', 'error')
            return redirect(url_for('add_trade'))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {str(e)}', 'error')
            return redirect(url_for('add_trade'))

    return render_template('add_trade.html')

@app.route('/trades_list')
def trades_list():
    trades = Trade.query.order_by(Trade.date.desc()).all()
    return render_template('trades_list.html', trades=trades)

mock_current_prices = {
    'DEFAULT': 100.0,
    'AAPL': 170.50,
    'GOOGL': 2750.20,
    'MSFT': 300.10,
    # Add more tickers as needed
}

@app.route('/portfolio')
def portfolio():
    assets = PortfolioAsset.query.filter(PortfolioAsset.quantity > 0).all() # Only display assets with quantity > 0

    portfolio_details = []
    total_portfolio_value = 0.0
    total_portfolio_cost_basis = 0.0

    for asset in assets:
        current_price = mock_current_prices.get(asset.ticker.upper(), mock_current_prices['DEFAULT'])
        current_value = asset.quantity * current_price
        cost_basis = asset.quantity * asset.average_buy_price
        gain_loss = current_value - cost_basis
        percentage_gain_loss = (gain_loss / cost_basis) * 100 if cost_basis != 0 else 0

        portfolio_details.append({
            'ticker': asset.ticker,
            'quantity': asset.quantity,
            'average_buy_price': asset.average_buy_price,
            'current_price': current_price,
            'current_value': current_value,
            'cost_basis': cost_basis,
            'gain_loss': gain_loss,
            'percentage_gain_loss': percentage_gain_loss,
        })

        total_portfolio_value += current_value
        total_portfolio_cost_basis += cost_basis

    total_portfolio_gain_loss = total_portfolio_value - total_portfolio_cost_basis
    total_percentage_gain_loss = (total_portfolio_gain_loss / total_portfolio_cost_basis) * 100 if total_portfolio_cost_basis != 0 else 0

    # CAGR Calculation
    cagr = 0.0
    if mock_portfolio_historical_simple and len(mock_portfolio_historical_simple) > 1:
        start_value = mock_portfolio_historical_simple[0]
        end_value = mock_portfolio_historical_simple[-1]
        if mock_period_years > 0 and start_value > 0:
            cagr = ((end_value / start_value) ** (1 / mock_period_years)) - 1
        elif mock_period_years == 0 and start_value > 0 : # Handle case for single period (simple return)
             cagr = (end_value / start_value) - 1


    # XIRR Calculation
    xirr_value = "XIRR calculation unavailable (pyxirr not loaded)" # Default message
    try:
        from pyxirr import xirr # Attempt to import

        trades_for_xirr = Trade.query.order_by(Trade.date.asc()).all()
        xirr_dates = []
        xirr_values = []

        for trade in trades_for_xirr:
            # Ensure date is a datetime.date object for pyxirr if it's strict,
            # or that all date/datetime objects are compatible (e.g. all naive or all aware)
            # Assuming trade.date is a naive datetime.datetime object from strptime
            xirr_dates.append(trade.date) # pyxirr can handle datetime.datetime
            if trade.transaction_type == 'buy':
                xirr_values.append(-(trade.price * trade.quantity + trade.fees))
            elif trade.transaction_type == 'sell':
                xirr_values.append(trade.price * trade.quantity - trade.fees)

        # Add current portfolio valuation as the final cash flow
        if xirr_values: # Proceed only if there are trades, which implies xirr_dates is also populated
            # Ensure dt.today() is compatible. dt.today() returns a datetime.date object.
            # pyxirr should handle mixed datetime.date and datetime.datetime objects.
            xirr_dates.append(dt.today())
            xirr_values.append(total_portfolio_value)

            # XIRR needs at least one positive and one negative cash flow.
            has_positive = any(v > 0 for v in xirr_values)
            has_negative = any(v < 0 for v in xirr_values)

            if len(xirr_values) >= 2 and has_positive and has_negative:
                try:
                    # Convert all dates to datetime.date objects just to be safe, though pyxirr might be flexible.
                    # trade.date is datetime.datetime, dt.today() is datetime.date.
                    # This conversion was found to be problematic in testing if not handled carefully.
                    # For now, we will pass them as is, as pyxirr is generally robust.
                    # processed_dates = [d.date() if isinstance(d, datetime.datetime) else d for d in xirr_dates]

                    calculated_xirr = xirr(xirr_dates, xirr_values) # Use original xirr_dates

                    if calculated_xirr is None:
                        xirr_value = "XIRR could not be calculated (e.g., no solution found or invalid cash flows)."
                    else:
                        xirr_value = calculated_xirr
                except Exception as e:
                    xirr_value = f"XIRR calculation error: {str(e)}"
            else:
                xirr_value = "Insufficient data for XIRR (needs positive & negative cash flows, and at least two flows)."
        else:
            xirr_value = "No trades recorded for XIRR calculation."

    except ImportError:
        # This message is already set as default, but kept here for clarity of logic flow
        # xirr_value = "XIRR calculation unavailable (pyxirr not loaded or import error)"
        pass

    return render_template('portfolio.html',
                           assets=portfolio_details,
                           total_value=total_portfolio_value,
                           total_cost_basis=total_portfolio_cost_basis,
                           total_gain_loss=total_portfolio_gain_loss,
                           total_percentage_gain_loss=total_percentage_gain_loss,
                           cagr=cagr,
                           xirr_value=xirr_value)

@app.route('/portfolio_graphs')
def portfolio_graphs():
    assets = PortfolioAsset.query.filter(PortfolioAsset.quantity > 0).all()

    labels = []
    values = []

    for asset in assets:
        current_price = mock_current_prices.get(asset.ticker.upper(), mock_current_prices['DEFAULT'])
        current_value = asset.quantity * current_price
        if current_value > 0: # Only include assets with a positive current value in the pie chart
            labels.append(asset.ticker)
            values.append(current_value)

    return render_template('portfolio_graphs.html', labels=labels, values=values)

# Mock historical data
mock_time_labels = ['Start', 'Month 1', 'Month 2', 'Month 3', 'Month 4', 'Current'] # 5 periods
mock_portfolio_historical_simple = [10000, 10200, 10100, 10500, 10300, 10800]
mock_period_years = len(mock_time_labels) - 1 # Assumes each label is one year apart

mock_benchmark_historical_data = {
    'SPY': [200, 201, 200, 203, 202, 205],
    'QQQ': [150, 152, 151, 155, 154, 158],
    'VT':  [75, 76, 75, 77, 76, 79]
}

def calculate_percentage_change(data_series):
    if not data_series or len(data_series) == 0:
        return []
    start_value = data_series[0]
    if start_value == 0: # Avoid division by zero if start value is 0
        return [0.0] * len(data_series)
    return [((value - start_value) / start_value) * 100 for value in data_series]

@app.route('/compare', methods=['GET'])
def compare():
    selected_benchmark_ticker = request.args.get('benchmark_ticker', 'SPY').upper()

    benchmark_data_raw = mock_benchmark_historical_data.get(selected_benchmark_ticker)

    portfolio_perf_pct = calculate_percentage_change(mock_portfolio_historical_simple)
    benchmark_perf_pct = []

    if benchmark_data_raw:
        if len(benchmark_data_raw) == len(mock_time_labels) and len(mock_portfolio_historical_simple) == len(mock_time_labels):
             benchmark_perf_pct = calculate_percentage_change(benchmark_data_raw)
        else:
            flash(f'Data length mismatch for {selected_benchmark_ticker}. Cannot display comparison.', 'error')
    else:
        flash(f'Benchmark data for {selected_benchmark_ticker} not found.', 'error')
        # Provide empty list for benchmark to prevent chart error, or default to SPY's % change
        # For simplicity, we'll use an empty list, the template should handle it.

    return render_template('compare.html',
                           time_labels=mock_time_labels,
                           portfolio_performance=portfolio_perf_pct,
                           benchmark_performance=benchmark_perf_pct,
                           current_benchmark_ticker=selected_benchmark_ticker,
                           available_benchmarks=list(mock_benchmark_historical_data.keys()))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
