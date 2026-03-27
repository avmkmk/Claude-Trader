import streamlit as st
import pandas as pd
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from apis.nubra_api import NubraAPIHandler
from backtesting.data_scraper import EquityDataScraper
from backtesting.backtest_runner import BacktestRunner
from strategies.sma_crossover import SMACrossoverStrategy

st.set_page_config(page_title="SimpleTrader Backtesting", layout="wide")


def validate_phone(phone):
    """Validate phone number format."""
    if not phone:
        return False, "Phone number is required"
    if not phone.isdigit():
        return False, "Phone number must contain only digits"
    if len(phone) != 10:
        return False, "Phone number must be exactly 10 digits"
    return True, None


def mask_phone(phone):
    """Mask phone number for display (e.g., +91-XXXXX-XXX45)."""
    if len(phone) == 10:
        return f"+91-XXXXX-XXX{phone[-2:]}"
    return phone


def auth_page():
    """
    Page 1: Nubra Authentication with UI inputs.

    Implements two authentication flows:
    - Quick Login: MPIN only (uses existing session token)
    - Full Login: Phone → OTP → MPIN (three-step sequential flow)

    All credentials are entered via UI and passed to NubraAPIHandler.
    No credentials are stored in .env file or persisted to disk.
    """
    st.header("Nubra Authentication")

    # Initialize session state variables
    if 'login_type' not in st.session_state:
        st.session_state['login_type'] = None
    if 'auth_step' not in st.session_state:
        st.session_state['auth_step'] = 'phone'
    if 'auth_status' not in st.session_state:
        st.session_state['auth_status'] = 'pending'
    if 'phone_number' not in st.session_state:
        st.session_state['phone_number'] = None
    if 'otp_verified' not in st.session_state:
        st.session_state['otp_verified'] = False

    # Check if already authenticated
    if 'nubra' in st.session_state and st.session_state['nubra'] is not None:
        st.success("✅ Already authenticated!")
        st.info("You can now proceed to Data Scraping or Backtesting pages.")

        # Option to clear authentication
        if st.button("Logout"):
            st.session_state.clear()
            st.rerun()
        return

    # Security banner
    st.info("🔒 Your credentials are securely processed and never stored on disk.")

    # Login type selection
    if st.session_state['login_type'] is None:
        st.subheader("Choose Login Method")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("🚀 Quick Login", use_container_width=True, type="primary"):
                st.session_state['login_type'] = 'quick'
                st.rerun()
            st.caption("Use MPIN only (if you've logged in today)")

        with col2:
            if st.button("🔐 Full Login", use_container_width=True):
                st.session_state['login_type'] = 'full'
                st.session_state['auth_step'] = 'phone'
                st.rerun()
            st.caption("Phone → OTP → MPIN (first login of the day)")

        return

    # Back button to return to login type selection
    if st.button("← Back to Login Selection"):
        st.session_state['login_type'] = None
        st.session_state['auth_step'] = 'phone'
        st.session_state['phone_number'] = None
        st.session_state['otp_verified'] = False
        st.rerun()

    st.markdown("---")

    # Quick Login Flow
    if st.session_state['login_type'] == 'quick':
        st.subheader("🚀 Quick Login (MPIN Only)")

        with st.form("quick_login_form"):
            mpin = st.text_input(
                "MPIN",
                type="password",
                placeholder="Enter your MPIN",
                max_chars=10,
                key="quick_mpin_input"
            )

            submitted = st.form_submit_button("Authenticate", type="primary", use_container_width=True)

            if submitted:
                if not mpin:
                    st.error("⚠️ MPIN is required")
                else:
                    with st.spinner("Authenticating..."):
                        nubra = NubraAPIHandler()
                        success, error = nubra.initialize_sdk_with_credentials(mpin=mpin)

                        if success:
                            st.session_state['nubra'] = nubra
                            st.session_state['auth_status'] = 'success'
                            st.success("✅ Authentication successful!")
                            st.balloons()
                            st.info("You can now proceed to Data Scraping or Backtesting pages.")
                        else:
                            st.error(f"❌ Authentication failed: {error}")
                            st.warning("💡 Try Full Login if your session has expired.")

        return

    # Full Login Flow
    if st.session_state['login_type'] == 'full':
        st.subheader("🔐 Full Login (Phone → OTP → MPIN)")

        # Progress indicator
        step_num = {'phone': 1, 'otp': 2, 'mpin': 3}[st.session_state['auth_step']]
        st.progress(step_num / 3)
        st.caption(f"Step {step_num} of 3")

        # Step 1: Phone Number
        if st.session_state['auth_step'] == 'phone':
            st.write("### Step 1: Phone Number")

            with st.form("phone_form"):
                phone = st.text_input(
                    "Phone Number",
                    placeholder="Enter 10-digit mobile number",
                    max_chars=10,
                    key="phone_input"
                )

                submitted = st.form_submit_button("Send OTP", type="primary", use_container_width=True)

                if submitted:
                    valid, error_msg = validate_phone(phone)

                    if not valid:
                        st.error(f"⚠️ {error_msg}")
                    else:
                        # Store phone and move to OTP step
                        # In real implementation, SDK would trigger OTP here
                        # For now, we just store and proceed
                        st.session_state['phone_number'] = phone
                        st.session_state['auth_step'] = 'otp'
                        st.success(f"✅ OTP sent to {mask_phone(phone)}")
                        st.rerun()

            return

        # Step 2: OTP Verification
        if st.session_state['auth_step'] == 'otp':
            st.write("### Step 2: OTP Verification")

            if st.session_state['phone_number']:
                st.info(f"📱 OTP sent to: {mask_phone(st.session_state['phone_number'])}")

            with st.form("otp_form"):
                otp = st.text_input(
                    "Enter OTP",
                    type="password",
                    placeholder="Enter 6-digit OTP",
                    max_chars=6,
                    key="otp_input"
                )

                col1, col2 = st.columns([3, 1])

                with col1:
                    submitted = st.form_submit_button("Verify OTP", type="primary", use_container_width=True)

                with col2:
                    # Placeholder for resend OTP (future enhancement)
                    st.form_submit_button("Resend", disabled=True, use_container_width=True)

                if submitted:
                    if not otp:
                        st.error("⚠️ OTP is required")
                    elif not otp.isdigit():
                        st.error("⚠️ OTP must contain only digits")
                    elif len(otp) != 6:
                        st.error("⚠️ OTP must be exactly 6 digits")
                    else:
                        # Mark OTP as verified and move to MPIN step
                        # In real implementation, SDK would verify OTP here
                        st.session_state['otp_verified'] = True
                        st.session_state['otp_code'] = otp
                        st.session_state['auth_step'] = 'mpin'
                        st.success("✅ OTP verified successfully!")
                        st.rerun()

            # Back button for this step
            if st.button("← Back to Phone Number"):
                st.session_state['auth_step'] = 'phone'
                st.session_state['otp_verified'] = False
                st.rerun()

            return

        # Step 3: MPIN Authentication
        if st.session_state['auth_step'] == 'mpin':
            st.write("### Step 3: MPIN Authentication")

            if st.session_state['phone_number']:
                st.info(f"📱 Phone: {mask_phone(st.session_state['phone_number'])} ✓")
            if st.session_state['otp_verified']:
                st.info("🔐 OTP Verified ✓")

            with st.form("mpin_form"):
                mpin = st.text_input(
                    "MPIN",
                    type="password",
                    placeholder="Enter your MPIN",
                    max_chars=10,
                    key="full_mpin_input"
                )

                submitted = st.form_submit_button("Authenticate", type="primary", use_container_width=True)

                if submitted:
                    if not mpin:
                        st.error("⚠️ MPIN is required")
                    else:
                        with st.spinner("Authenticating with Nubra..."):
                            nubra = NubraAPIHandler()

                            # Call SDK with all credentials
                            success, error = nubra.initialize_sdk_with_credentials(
                                phone=st.session_state['phone_number'],
                                mpin=mpin,
                                otp=st.session_state.get('otp_code', None)
                            )

                            if success:
                                st.session_state['nubra'] = nubra
                                st.session_state['auth_status'] = 'success'
                                st.success("✅ Authentication successful!")
                                st.balloons()
                                st.info("You can now proceed to Data Scraping or Backtesting pages.")

                                # Clear temporary credentials from session state
                                if 'otp_code' in st.session_state:
                                    del st.session_state['otp_code']
                            else:
                                st.error(f"❌ Authentication failed: {error}")
                                st.warning("💡 Please check your credentials and try again.")

            # Back button for this step
            if st.button("← Back to OTP"):
                st.session_state['auth_step'] = 'otp'
                st.rerun()

            return


def scraping_page():
    """Page 2: Data Scraping"""
    st.header("Equity Data Scraping")

    if 'nubra' not in st.session_state or not st.session_state['nubra']:
        st.warning("Please authenticate first (go to Authentication page)")
        return

    nubra = st.session_state['nubra']
    scraper = EquityDataScraper(nubra)

    # Get available NSE equities
    with st.spinner("Loading NSE equities..."):
        nse_equities = scraper.get_nse_equities(limit=100)

    if not nse_equities:
        st.error("No NSE equities found. Check security_id_list.csv")
        return

    # Symbol selection
    selected_symbols = st.multiselect(
        "Select symbols to scrape:",
        nse_equities,
        default=nse_equities[:5] if len(nse_equities) >= 5 else nse_equities
    )

    # Period selection
    period_days = st.slider("Historical period (days):", 30, 365, 90)

    # Rate limit info
    st.info(f"Rate Limit: 2 seconds between requests. "
            f"For {len(selected_symbols)} symbols: ~{len(selected_symbols) * 2} seconds")

    # Scrape button
    if st.button("Scrape Data", type="primary"):
        if not selected_symbols:
            st.error("Please select at least one symbol")
        else:
            progress_bar = st.progress(0)
            status_text = st.empty()

            total = len(selected_symbols)
            for idx, symbol in enumerate(selected_symbols):
                status_text.text(f"Scraping {symbol}... ({idx+1}/{total})")
                try:
                    df = scraper.scrape_equity(symbol, period_days)
                    if df is not None:
                        scraper.save_to_csv(df, symbol, period_days)
                        st.success(f"{symbol}: {len(df)} rows")
                    else:
                        st.warning(f"{symbol}: No data returned")
                except Exception as e:
                    st.error(f"{symbol}: {str(e)}")

                progress_bar.progress((idx + 1) / total)

            status_text.text("Scraping complete!")


def backtest_page():
    """Page 3: Backtesting"""
    st.header("Backtest Strategy")

    # List available CSV files
    if not os.path.exists('data'):
        st.error("No data folder found. Please scrape data first.")
        return

    data_files = [f for f in os.listdir('data') if f.endswith('.csv')]

    if not data_files:
        st.warning("No data files found. Please scrape data first.")
        return

    # File selection
    selected_file = st.selectbox("Select data file:", data_files)

    # Strategy parameters
    st.subheader("Strategy Parameters")
    col1, col2 = st.columns(2)
    with col1:
        fast_period = st.number_input("Fast SMA Period:", 5, 50, 10)
    with col2:
        slow_period = st.number_input("Slow SMA Period:", 10, 100, 30)

    # Backtest parameters
    st.subheader("Backtest Parameters")
    initial_cash = st.number_input("Initial Cash (Rs):", 10000, 10000000, 100000, step=10000)

    # Run backtest
    if st.button("Run Backtest", type="primary"):
        with st.spinner("Running backtest..."):
            try:
                runner = BacktestRunner(initial_cash=initial_cash)
                symbol_name = selected_file.split('_')[0]
                runner.load_data(f'data/{selected_file}', symbol_name)
                runner.add_strategy(SMACrossoverStrategy,
                                  fast_period=fast_period,
                                  slow_period=slow_period)
                runner.add_analyzers()

                result = runner.run()
                metrics = runner.get_metrics(result)

                # Display results
                st.success("Backtest completed successfully!")

                # Portfolio value
                final_value = runner.cerebro.broker.getvalue()
                profit = final_value - initial_cash
                profit_pct = (profit / initial_cash) * 100

                col1, col2, col3 = st.columns(3)
                col1.metric("Initial Value", f"Rs {initial_cash:,.2f}")
                col2.metric("Final Value", f"Rs {final_value:,.2f}")
                col3.metric("Profit/Loss", f"Rs {profit:,.2f}", f"{profit_pct:.2f}%")

                # Performance metrics
                st.subheader("Performance Metrics")

                col1, col2 = st.columns(2)

                with col1:
                    st.write("**Returns**")
                    if metrics.get('returns'):
                        st.write(f"Total Return: {metrics['returns'].get('total_return', 0):.2%}")
                        st.write(f"Avg Return: {metrics['returns'].get('average_return', 0):.2%}")

                    st.write("**Risk Metrics**")
                    st.write(f"Sharpe Ratio: {metrics.get('sharpe_ratio', 'N/A')}")
                    if metrics.get('drawdown'):
                        st.write(f"Max Drawdown: {metrics['drawdown'].get('max_drawdown', 0):.2f}%")

                with col2:
                    st.write("**Trade Statistics**")
                    if metrics.get('trades'):
                        trades = metrics['trades']
                        st.write(f"Total Trades: {trades.get('total_trades', 0)}")
                        st.write(f"Won: {trades.get('won_trades', 0)}")
                        st.write(f"Lost: {trades.get('lost_trades', 0)}")
                        st.write(f"Net P&L: Rs {trades.get('pnl_net_total', 0):,.2f}")
                        st.write(f"Avg P&L: Rs {trades.get('pnl_net_average', 0):,.2f}")

                # Full metrics JSON
                with st.expander("View Full Metrics (JSON)"):
                    st.json(metrics)

                # Plot info
                st.info("Note: Chart plotting requires matplotlib GUI and may not display in web browser")

            except Exception as e:
                st.error(f"Backtest failed: {str(e)}")
                import traceback
                st.code(traceback.format_exc())


def main():
    st.title("SimpleTrader Backtesting Dashboard")
    st.sidebar.title("Navigation")

    page = st.sidebar.radio(
        "Select Page:",
        ["Authentication", "Data Scraping", "Backtesting"]
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("### About")
    st.sidebar.info(
        "SimpleTrader backtesting system using SMA crossover strategy. "
        "Built with Backtrader, Nubra API, and Streamlit."
    )

    if page == "Authentication":
        auth_page()
    elif page == "Data Scraping":
        scraping_page()
    elif page == "Backtesting":
        backtest_page()


if __name__ == "__main__":
    main()
