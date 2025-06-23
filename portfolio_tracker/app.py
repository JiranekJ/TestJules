from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import datetime
from datetime import datetime as dt, date as Date
# Corrected absolute import:
from portfolio_tracker.api_client import get_current_price, get_historical_data

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

# mock_current_prices is now removed / commented out
# mock_current_prices = {
#     'DEFAULT': 100.0,
#     'AAPL': 170.50,
#     'GOOGL': 2750.20,
#     'MSFT': 300.10,
# }

@app.route('/portfolio')
def portfolio():
    assets = PortfolioAsset.query.filter(PortfolioAsset.quantity > 0).all()

    portfolio_details = []
    total_portfolio_value = 0.0
    total_portfolio_cost_basis = 0.0

    for asset in assets:
        api_price = get_current_price(asset.ticker)

        current_price_for_display = "N/A"
        current_price_for_calculation = asset.average_buy_price # Fallback

        if api_price is not None:
            current_price_for_display = api_price
            current_price_for_calculation = api_price

        current_value = asset.quantity * current_price_for_calculation
        cost_basis = asset.quantity * asset.average_buy_price
        gain_loss = current_value - cost_basis
        percentage_gain_loss = (gain_loss / cost_basis) * 100 if cost_basis != 0 else 0

        portfolio_details.append({
            'ticker': asset.ticker,
            'quantity': asset.quantity,
            'average_buy_price': asset.average_buy_price,
            'current_price_display': current_price_for_display, # For template
            'current_value': current_value,
            'cost_basis': cost_basis,
            'gain_loss': gain_loss,
            'percentage_gain_loss': percentage_gain_loss,
        })

        total_portfolio_value += current_value
        total_portfolio_cost_basis += cost_basis # Cost basis remains the same regardless of current price

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
            xirr_dates.append(trade.date)
            if trade.transaction_type == 'buy':
                xirr_values.append(-(trade.price * trade.quantity + trade.fees))
            elif trade.transaction_type == 'sell':
                xirr_values.append(trade.price * trade.quantity - trade.fees)

        if xirr_values:
            xirr_dates.append(Date.today()) # Use datetime.date.today()
            xirr_values.append(total_portfolio_value)

            has_positive = any(v > 0 for v in xirr_values)
            has_negative = any(v < 0 for v in xirr_values)

            if len(xirr_values) >= 2 and has_positive and has_negative:
                try:
                    calculated_xirr = xirr(xirr_dates, xirr_values)
                    if calculated_xirr is None:
                        xirr_value = "XIRR could not be calculated (e.g., no solution found)."
                    else:
                        xirr_value = calculated_xirr
                except Exception as e:
                    xirr_value = f"XIRR calculation error: {str(e)}"
            else:
                xirr_value = "Insufficient data for XIRR."
        else:
            xirr_value = "No trades for XIRR."
    except ImportError:
        pass # xirr_value remains "XIRR calculation unavailable..."

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
        # For pie chart, using live prices is better if available
        price_for_chart = get_current_price(asset.ticker)
        if price_for_chart is None: # Fallback for pie chart value if live price fails
            price_for_chart = asset.average_buy_price
            # Or, one might choose to skip assets where live price isn't available for allocation chart
            # For now, using average_buy_price as a fallback to ensure it's part of the chart.

        current_value = asset.quantity * price_for_chart
        if current_value > 0:
            labels.append(asset.ticker)
            values.append(current_value)

    return render_template('portfolio_graphs.html', labels=labels, values=values)

# Mock historical data for portfolio (CAGR calculation still uses it)
# mock_time_labels is removed as it's now derived from benchmark data or a fallback.
mock_portfolio_historical_simple = [10000, 10200, 10100, 10500, 10300, 10800] # Stays for now
mock_period_years = 5 # Fixed for CAGR, or make dynamic if portfolio history becomes dynamic

# mock_benchmark_historical_data is removed.
# Available benchmarks for the dropdown can be a predefined list.
available_benchmarks_list = ['SPY', 'QQQ', 'VT', 'AGG'] # Example list

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

    time_labels = []
    benchmark_perf_pct = []
    portfolio_perf_pct = [] # Renamed from portfolio_perf_pct for clarity

    benchmark_hist_df = get_historical_data(selected_benchmark_ticker, period="1y", interval="1d")

    if benchmark_hist_df is not None and not benchmark_hist_df.empty:
        benchmark_raw_values = benchmark_hist_df['Close'].tolist()
        # Ensure time_labels are strings, yfinance index can be DatetimeIndex
        time_labels = benchmark_hist_df.index.strftime('%Y-%m-%d').tolist()

        num_points = len(benchmark_raw_values)

        # Align mock portfolio data
        # Using a copy to avoid modifying the global mock list if it were to be used elsewhere unmodified
        portfolio_raw_values_for_comparison = list(mock_portfolio_historical_simple)

        if len(portfolio_raw_values_for_comparison) >= num_points:
            portfolio_to_compare = portfolio_raw_values_for_comparison[:num_points]
        else: # Portfolio history is shorter than benchmark history
            portfolio_to_compare = portfolio_raw_values_for_comparison
            # Benchmark data and time_labels should also be sliced to match the shorter portfolio history
            benchmark_raw_values = benchmark_raw_values[:len(portfolio_to_compare)]
            time_labels = time_labels[:len(portfolio_to_compare)]

        # Recalculate num_points if benchmark was sliced
        num_points = len(portfolio_to_compare) # This is now the effective number of points for both series

        # Calculate percentage change if there are points to compare
        if num_points > 0:
            benchmark_perf_pct = calculate_percentage_change(benchmark_raw_values)
            portfolio_perf_pct = calculate_percentage_change(portfolio_to_compare)
        else: # Should not happen if benchmark_hist_df was not empty, but as a safeguard
            flash('No data points available for comparison after alignment.', 'warning')
            # time_labels will be from benchmark, potentially non-empty but benchmark_perf_pct will be empty.
            # portfolio_perf_pct will also be empty.

    else:
        flash(f'Could not fetch historical data for benchmark {selected_benchmark_ticker}. Displaying only portfolio mock data if available.', 'error')
        # Fallback for portfolio data if benchmark fails
        if mock_portfolio_historical_simple:
             portfolio_perf_pct = calculate_percentage_change(mock_portfolio_historical_simple)
             # Create simple time labels for the portfolio data
             time_labels = [f"P{i+1}" for i in range(len(mock_portfolio_historical_simple))]
        else:
            portfolio_perf_pct = []
            time_labels = []


    return render_template('compare.html',
                           time_labels=time_labels,
                           portfolio_performance=portfolio_perf_pct,
                           benchmark_performance=benchmark_perf_pct,
                           current_benchmark_ticker=selected_benchmark_ticker,
                           available_benchmarks=available_benchmarks_list) # Use predefined list

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
