import streamlit as st
import pandas as pd
import yfinance as yf
from backend.scanner import scan_market, rank_opportunities
from backend.signal_engine import generate_signal
from backend.data_fetch import get_stock_data, get_unknown_stock_response
from backend.stock_search import find_stock, get_suggestions, stock_db
from backend.ai_engine import generate_ai_explanation, chat_with_ai
from backend.backtest import backtest_stock
from backend.auth import login, signup
from backend.news_service import get_news, get_sentiment
import plotly.express as px
import io
from backend.auth import login, signup, get_user, update_profile, load_user_chats, save_user_chats
from backend.signal_engine import support_resistance, market_status, role_reversal
from collections import Counter
import plotly.graph_objects as go
import datetime
import time
import requests
from streamlit_autorefresh import st_autorefresh

@st.cache_data(ttl=60)
def get_chart_data(stock: str, period: str) -> pd.DataFrame:
    """Cached chart data fetch."""
    try:
        return yf.Ticker(stock).history(period=period)
    except:
        return pd.DataFrame()

st.set_page_config(page_title="ALPHAHUNT AI", layout="wide")

# Session state
if "page" not in st.session_state:
    st.session_state.page = "home"

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "username" not in st.session_state:
    st.session_state.username = None

# 🏠 HOME PAGE
if st.session_state.page == "home":
    st.title("🚀 ALPHAHUNT AI")
    st.subheader("GenAI Investment Intelligence Platform")

    st.write("Make smarter investment decisions using AI")

    if st.button("Login"):
        st.session_state.page = "login"

    if st.button("Signup"):
        st.session_state.page = "signup"

# 🔐 LOGIN PAGE
elif st.session_state.page == "login":
    st.title("🔐 Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login Now"):
        success = login(username, password)

        if success:
            st.session_state.username = username
            st.session_state.logged_in = True
            st.session_state.messages = load_user_chats(username)
            st.session_state.page = "dashboard"
            st.rerun()
        else:
            st.error("Invalid credentials")

    if st.button("Back"):
        st.session_state.page = "home"

# 📝 SIGNUP PAGE
elif st.session_state.page == "signup":
    st.title("📝 Signup")

    username = st.text_input("Choose Username")
    password = st.text_input("Choose Password", type="password")
    name = st.text_input("Full Name (optional)")
    email = st.text_input("Email (optional)")

    if st.button("Create Account"):
        success, msg = signup(username, password)
        if success:
            profile = {}
            if name:
                profile["name"] = name
            if email:
                profile["email"] = email
            update_profile(username, profile)
            st.success(msg)
        else:
            st.error(msg)

    if st.button("Back"):
        st.session_state.page = "home"

# 📊 DASHBOARD PAGE
elif st.session_state.page == "dashboard":
    # 🔥 STEP 3.1 — ADD HEADER (TOP BRANDING)
    st.markdown("""
        <h1 style='text-align: center; color: #00FFAA;'>
            🚀 ALPHAHUNT AI
        </h1>
        <p style='text-align: center;'>
            GenAI-Powered Investment Intelligence Platform
        </p>
    """, unsafe_allow_html=True)

    if st.session_state.username:
        user_profile = get_user(st.session_state.username)
        name = user_profile['profile'].get('name', st.session_state.username) if user_profile else st.session_state.username
        st.success(f"Hi, {name}! 👋")

    if st.button("Logout"):
        if st.session_state.username:
            save_user_chats(st.session_state.username, st.session_state.get('messages', []))
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.messages = []
        st.session_state.page = "home"
        st.rerun()

    # Initialize sector_map in session state if not already present
    if "sector_map" not in st.session_state:
        st.session_state.sector_map = {
            "RELIANCE.NS": "Energy",
            "TCS.NS": "IT",
            "INFY.NS": "IT",
            "HDFCBANK.NS": "Banking",
            "ICICIBANK.NS": "Banking"
        }

    # 📊 STEP 1.1 — DEFINE DEFAULT STOCKS
    DEFAULT_STOCKS = [
        "RELIANCE.NS",
        "TCS.NS",
        "INFY.NS",
        "HDFCBANK.NS",
        "ICICIBANK.NS"
    ]

    # 📄 STEP 1.2 — SESSION STATE FOR USER STOCKS
    if "selected_stocks" not in st.session_state:
        st.session_state.selected_stocks = DEFAULT_STOCKS.copy()

    # Existing dashboard code starts here
    st.subheader("GenAI Opportunity Radar for Indian Investors")

    # 🔥 STEP 3.6 — SIDEBAR POLISH
    st.sidebar.title("⚙️ Control Panel")
    st.sidebar.markdown("Manage stocks & portfolio")

    # 📄 STEP 1.3 — ADD STOCK INPUT (SIDEBAR)
    st.sidebar.subheader("➕ Add Stock")

    new_stock = st.sidebar.text_input("Enter stock name/ticker (e.g. reliance, AAPL)")

    # --- Refactored Smart Search UI ---
    suggestions = []
    if new_stock:
        suggestions = get_suggestions(new_stock, n=5)

    # The selectbox will contain the user's input and any suggestions
    options = []
    if new_stock:
        options.append(new_stock)
    options.extend(suggestions)
    # Remove duplicates while preserving order
    options = list(dict.fromkeys(options))

    selected_to_add = st.sidebar.selectbox("Select or type stock to add", options=options, key="stock_add_selection")

    if st.sidebar.button("Add Stock"):
        if selected_to_add:
            ticker_to_add = find_stock(selected_to_add)
            if ticker_to_add and ticker_to_add not in st.session_state.selected_stocks:
                st.session_state.selected_stocks.append(ticker_to_add)
                st.sidebar.success(f"Added: {ticker_to_add}")
                st.rerun()
            elif ticker_to_add in st.session_state.selected_stocks:
                st.sidebar.warning(f"{ticker_to_add} is already in the list.")
            else:
                st.sidebar.error(f"Could not find a match for '{selected_to_add}'.")

    # 📄 STEP 1.4 — REMOVE STOCK OPTION
    st.sidebar.subheader("❌ Remove Stock")

    if st.session_state.selected_stocks:
        remove_stock = st.sidebar.selectbox("Select stock to remove", st.session_state.selected_stocks)
        if st.sidebar.button("Remove"):
            st.session_state.selected_stocks.remove(remove_stock)
            st.rerun()

    st.sidebar.title("📊 S/R Lines")
    show_sr = st.sidebar.toggle("Show Support/Resistance", value=True)
    apply_role_reversal = st.sidebar.toggle("🔄 Role Reversal", value=False, disabled=not show_sr)

    # Cache key for dashboard results
    stocks_tuple = tuple(st.session_state.selected_stocks)
    settings_hash = hash((stocks_tuple, show_sr, apply_role_reversal))

    # Old refresh button removed - enhanced version added in header

    if "results_cache" not in st.session_state:
        st.session_state.results_cache = {}

    if settings_hash not in st.session_state.results_cache:
        # 🔥 STEP 3.7 — LOADING EXPERIENCE
        with st.spinner("🔍 AI analyzing market (first load or refresh)..."):
            results = []

            for stock in st.session_state.selected_stocks:
                stock_key = stock
                
                data_result = get_stock_data(stock_key)
                
                if isinstance(data_result, dict) and data_result.get('status') == 'error':
                    signal = get_unknown_stock_response(data_result)
                    signal['sector'] = "Unknown"
                elif data_result is None or not isinstance(data_result, pd.DataFrame):
                    signal = get_unknown_stock_response({'status': 'error', 'message': 'Invalid data format', 'symbol': stock_key})
                    signal['sector'] = "Unknown"
                else:
                    signal = generate_signal(data_result)
                    sector = st.session_state.sector_map.get(stock_key, "Unknown")
                    if sector == "Unknown":
                        try:
                            ticker_obj = yf.Ticker(stock_key)
                            info = ticker_obj.info
                            if 'sector' in info and info['sector']:
                                sector = info['sector']
                                st.session_state.sector_map[stock_key] = sector
                            elif 'industry' in info and info['industry']:
                                sector = info['industry']
                                st.session_state.sector_map[stock_key] = sector
                        except Exception:
                            sector = "Unknown"
                    signal['sector'] = sector

                signal['stock'] = stock_key
                signal['apply_role_reversal'] = str(apply_role_reversal)

                headlines = get_news(stock_key)
                sentiment = get_sentiment(headlines)
                signal['news_sentiment'] = sentiment
                signal['ai_explanation'] = generate_ai_explanation(signal)

                results.append(signal)

        ranked = rank_opportunities(results)
        st.session_state.results_cache[settings_hash] = ranked

        st.success("Scan Complete & Cached ✅ - Use Refresh to update")
    else:
        ranked = st.session_state.results_cache[settings_hash]
        st.success("Using Cached Results ✅ - Fast!")


    # 🔥 STEP 3.2 — TOP METRICS BAR
    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Stocks Tracked", len(st.session_state.selected_stocks))
    col2.metric("Top Signal", ranked[0]['signal'] if ranked else "-")
    col3.metric("Best Confidence", ranked[0].get('confidence', '-') if ranked else "-")
    col4.metric("AI Status", "Active")

    # Enhanced Manual Refresh Button
    if st.button("🔄 Manual Refresh (Force Update)", type="primary", help="Clears cache and refreshes analysis"):
        if "results_cache" in st.session_state:
            st.session_state.results_cache.clear()
        st.success("🔄 Refreshing analysis...")
        st.rerun()

    st_autorefresh(interval=1200000, key="dashboard")  # Updated to 20 minutes

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Dashboard", "💼 Portfolio", "🤖 AI Assistant", "📈 Backtesting", "📡 Live Market"])

    # ============== TAB 1: DASHBOARD ==============
    with tab1: # type: ignore

        st.subheader("🚨 Alerts")

        alerts = []

        for r in ranked:
            stock_id = r.get("stock")
            if not stock_id:
                continue # Skip entries with no stock ID

            if r['signal'] == "BUY" and r['confidence'] == "High":
                alerts.append(f"🔥 Strong BUY signal: {stock_id}")

            if r['signal'] == "SELL":
                alerts.append(f"⚠️ SELL warning: {stock_id}")

        if len(alerts) == 0:
            st.info("No critical alerts")
        else:
            for alert in alerts:
                st.warning(alert)

        st.subheader("📊 Market Opportunities")

        for r in ranked:
            stock_id = r.get("stock")
            if not stock_id:
                st.warning("Skipping an entry with a missing stock ID.")
                continue

            # 🔥 STEP 3.3 — CARD STYLE STOCK DISPLAY
            st.markdown(f"""
<div style='
    padding:15px;
    border-radius:12px;
    background-color:#1e1e1e;
    margin-bottom:15px;
'>
<h3>{stock_id}</h3>
""", unsafe_allow_html=True)

            # 🔥 STEP 3.4 — COLOR SIGNAL TAGS
            if r['signal'] == "BUY":
                st.success("🟢 BUY SIGNAL")
            elif r['signal'] == "SELL":
                st.error("🔴 SELL SIGNAL")
            elif r['signal'] in ["ERROR", "UNKNOWN"]:
                st.error(f"🚨 {r['signal']}")
            else:
                st.warning("🟡 HOLD")

            st.markdown(f"""
<p><b>Confidence:</b> {r.get('confidence', 'Medium')} | <b>RSI:</b> {r.get('rsi', 'N/A')} | <b>S:</b> {r.get('support', 'N/A')} <b>R:</b> {r.get('resistance', 'N/A')}</p>
<p><b>Reason:</b> {r['reason']}</p>
<p><b>AI Insight:</b> {r['ai_explanation'][:200]}...</p>
</div>
""", unsafe_allow_html=True)

            st.info(f"📡 Event Signal: {r.get('event_signal', 'Neutral')}")

            # AI Detailed Reasoning Section
            with st.expander("🤖 Full AI Detailed Analysis & Reasoning", expanded=False):
                st.markdown(r['ai_explanation'])

            # 🔥 STEP 3.5 — SECTION DIVIDERS
            st.markdown("---")

            # Time period selector
            period_options = ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "max"]
            selected_period = st.selectbox("Select Time Period", period_options, index=1, key=f"period_{stock_id}")


            try:
                data_chart = get_chart_data(stock_id, selected_period)
                if not data_chart.empty:
                    fig = go.Figure()

                    fig.add_trace(go.Scatter(x=data_chart.index, y=data_chart['Close'], mode='lines', name='Close Price', line=dict(color='blue')))

                    if show_sr:
                        if r.get('support'):
                            fig.add_hline(y=r['support'], line_dash="dash", line_color="green", annotation_text="Support")
                        if r.get('resistance'):
                            fig.add_hline(y=r['resistance'], line_dash="dash", line_color="red", annotation_text="Resistance")
                    fig.update_layout(
                        title=f'{stock_id} Chart ({selected_period}) | S:{len(r.get("supports",[]))} R:{len(r.get("resistances",[]))}' + (' + S/R Lines' if show_sr else ''),
                        xaxis_title='Date',
                        yaxis_title='Price',
                        showlegend=True
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    print(f"No chart data for {stock_id} ({selected_period}): empty dataframe") 
                    st.warning(f"Unable to fetch chart data for {stock_id}")
            except Exception as e:
                st.error(f"Error fetching chart for {stock_id}: {str(e)}")

            if r.get('volume_spike'):
                st.success("📊 Volume Spike Detected")

            st.markdown("---")



    # ============== TAB 2: PORTFOLIO ==============
    with tab2: # type: ignore
        st.subheader("💼 Portfolio Analysis")

        portfolio_input = st.text_input("Enter stocks (comma separated): e.g. RELIANCE.NS,AAPL", "tcs,sbin")

        if st.button("🚀 Analyze Multi-Stock Portfolio & Signals"):
            raw_stocks = [s.strip() for s in portfolio_input.split(",")]
            
            stocks = []
            for s_raw in raw_stocks:
                normalized = find_stock(s_raw)
                if normalized:
                    stocks.append(normalized)
            
            if not stocks:
                st.warning("No valid stocks found.")
                sector_count = Counter()
            else:
                sector_count = Counter()
                
                # Enhanced multi-stock display (Fix #7)
                for stock in stocks:
                    with st.expander(f"📊 {stock}"):
                        df = get_stock_data(stock)
                        if df is None or isinstance(df, dict) or (hasattr(df, 'empty') and df.empty):
                            st.error(f"{stock}: No live data")
                            continue
                        
                        st.write(f"**Price:** {df['Close'].iloc[-1]:.2f}")
                        
                        status = market_status(stock)
                        st.write(f"**Market:** {status}")
                        
                        signal = generate_signal(df)
                        st.success(f"Signal: {signal['signal']} | Reason: {signal['reason']}")
                        
                        support, resistance = support_resistance(df)
                        st.write(f"**Support:** {support:.2f} | **Resistance:** {resistance:.2f}")
                        
                        reversal = role_reversal(df['Close'].iloc[-1], support, resistance)
                        st.write(f"**Role Reversal:** {reversal}")
                    
                    # Update sector map for risk analysis
                    sector = st.session_state.sector_map.get(stock, "Unknown")
                    if sector == "Unknown":
                        try:
                            ticker_obj = yf.Ticker(stock)
                            info = ticker_obj.info
                            sector = info.get('sector') or info.get('industry') or "Unknown"
                            st.session_state.sector_map[stock] = sector
                        except:
                            sector = "Unknown"
                    sector_count[sector] += 1

                # Portfolio table
                sectors_list = [st.session_state.sector_map.get(s, "Unknown") for s in stocks]
                df_display = pd.DataFrame({"Stock": stocks, "Sector": sectors_list})
                st.dataframe(df_display, use_container_width=True, hide_index=True)

                st.subheader("⚠️ Risk Analysis")
                for sec, count in sector_count.items():
                    if count > 1:
                        st.warning(f"High exposure: {sec} ({count})")

                risk_score = min(10, len(stocks)*0.5 + (sum(c*2 for c in list(sector_count.values()) if c>1) if isinstance(sector_count, dict) else 0) + (3 if len(sector_count)<=2 else 0))
                st.metric("Risk Score", f"{risk_score:.1f}/10")

                st.subheader("💡 AI Suggestions")
                suggestions = []
                if "Banking" in sector_count and sector_count["Banking"] > 1:
                    suggestions.append("Reduce exposure to Banking sector")
                if "IT" not in sector_count:
                    suggestions.append("Consider adding IT sector for diversification")
                if len(sector_count) <= 2:
                    suggestions.append("Diversify across more sectors")
                if len(suggestions) == 0:
                    st.success("Portfolio looks well balanced")
                else:
                    for s in suggestions:
                        st.info(f"👉 {s}")

            st.subheader("🤖 Pro AI Advice")

            portfolio_context = f"Sectors: {dict(sector_count)}, Stocks: {stocks}"
            ai_messages = [{"role": "system", "content": "You are a portfolio advisor."}, {"role": "user", "content": f"Improve portfolio: {portfolio_context}." }]
            ai_advice = chat_with_ai(ai_messages, temperature=0.7, max_tokens=500, context_data=portfolio_context)

            st.markdown("### 🤖 AI Assistant Response")
            
            # The original code had redundant rendering which caused the duplication issue.
            # The logic is now simplified to show the AI advice only once,
            # using a summary and an expander for better UI organization.
            if '\n' in ai_advice:
                summary = ai_advice.split('\n')[0].strip()
                st.success(f"💡 AI Summary: {summary}")
                
                with st.expander("📊 View Full AI Advice"):
                    styled_advice = f"""
<div style='
    background-color:#1e1e1e;
    padding:15px;
    border-radius:10px;
    line-height:1.6;
'>
{ai_advice}
</div>
"""
                    st.markdown(styled_advice, unsafe_allow_html=True)
            else:
                # If the advice is short, just display it directly in a styled box.
                styled_advice = f"""
<div style='
    background-color:#1e1e1e;
    padding:15px;
    border-radius:10px;
    line-height:1.6;
'>
{ai_advice}
</div>
"""
                st.markdown(styled_advice, unsafe_allow_html=True)

    # ============== TAB 3: AI ASSISTANT ==============
    with tab3: # type: ignore
        st.subheader("🤖 AI Assistant")

        # Moved chat preferences from sidebar to the tab
        with st.expander("⚙️ Chat Preferences"):
            col1, col2 = st.columns(2)
            temperature = col1.slider("Temperature", 0.0, 1.0, 0.7, 0.1, help="Controls randomness: 0.0 = deterministic, 1.0 = very random")
            max_tokens = col2.slider("Max Tokens", 100, 2000, 500, 50, help="Maximum length of AI response")
            if st.button("Clear Chat History"):
                st.session_state.messages = []
                st.rerun()

        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Display chat messages from history on app rerun
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                if "timestamp" in message:
                    st.caption(f"{message['timestamp']}")
                styled_content = f"""
<div style='
    background-color:#1e1e1e;
    padding:12px;
    border-radius:8px;
    {'border-left: 4px solid #00FFAA;' if message["role"] == "assistant" else ''}
'>
{message["content"]}
</div>
"""
                st.markdown(styled_content, unsafe_allow_html=True)

        # Build portfolio context
        context_data = ""
        for r in ranked:
            context_data += f"""
Stock: {r['stock']}
Signal: {r['signal']}
Score: {r['score']}
Confidence: {r['confidence']}
Reason: {r['reason']}
            """

        # Accept user input
        if prompt := st.chat_input("Ask me anything about stocks (e.g. tesla, andhra bank)..."):
            normalized_prompt = find_stock(prompt) or prompt
            # Add user message to chat history
            st.session_state.messages.append({
                "role": "user",
                "content": normalized_prompt,
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

            # Display user message in chat message container
            with st.chat_message("user"):
                st.caption(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                st.markdown(normalized_prompt)

            # Generate AI response
            clean_messages = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
            response = chat_with_ai(clean_messages, temperature=temperature, max_tokens=max_tokens, context_data=context_data)

            # Add assistant response to chat history
            st.session_state.messages.append({
                "role": "assistant", 
                "content": response,
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

            if st.session_state.username:
                save_user_chats(st.session_state.username, st.session_state.messages)

            # Display assistant response in chat message container
            with st.chat_message("assistant"):
                st.caption(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                styled_response = f"""
<div style='
    background-color:#1e1e1e;
    padding:12px;
    border-radius:8px;
    border-left: 4px solid #00FFAA;
'>
{response}
</div>
"""
                st.markdown(styled_response, unsafe_allow_html=True)

    # ============== TAB 4: BACKTESTING ==============
    with tab4: # type: ignore
        st.subheader("📈 Backtesting")
        
        stock = st.selectbox("Select stock", st.session_state.selected_stocks, key="backtest_stock")
        
        col1, col2, col3, col4 = st.columns(4)
        stock = col1.selectbox("Stock", st.session_state.selected_stocks)
        period = col2.selectbox("Period", ["3mo", "6mo", "1y"])
        lookforward_days = col3.slider("Lookforward Days", 5, 20, 10, key="lf_days")
        win_threshold_pct = col4.slider("Win Threshold %", 0.5, 3.0, 1.5, 0.1, key="win_thresh")
        
        if st.button("🚀 Run Enhanced Backtest", key="run_backtest"):
            with st.spinner(f"Backtesting {stock} ({period})..."):
                result = backtest_stock(stock, period, lookforward_days, win_threshold_pct)
            
            st.success("✅ Enhanced Backtest Complete!")
            
            # 1. KEY METRICS EXPANDED
            col1, col2, col3, col4, col5, col6 = st.columns(6)
            buy_acc = result.get('buy_accuracy', 0)
            sell_acc = result.get('sell_accuracy', 0)
            hold_acc = result.get('hold_accuracy', 100)
            col1.metric("🟢 BUY Win Rate", f"{buy_acc:.1f}%")
            col2.metric("🔴 SELL Win Rate", f"{sell_acc:.1f}%")
            col3.metric("🟡 HOLD Win Rate", f"{hold_acc:.1f}%")
            col4.metric("📈 Total Return", f"{result.get('total_return_pct', 0):.1f}%")
            col5.metric("⚡ Sharpe Ratio", f"{result.get('sharpe_ratio', 0):.2f}")
            col6.metric("📉 Max Drawdown", f"{result.get('max_drawdown_pct', 0):.1f}%")
            
            # 2. EQUITY CURVE
            fig_curve = go.Figure()
            equity_curve = result.get('equity_curve', [10000])
            safe_len_curve = len(equity_curve) if isinstance(equity_curve, (list, tuple)) else 1
            x_range = list(range(safe_len_curve))
            fig_curve.add_trace(go.Scatter(x=x_range, y=equity_curve, mode='lines', name='Strategy Equity', line=dict(color='#00FFAA', width=3)))
            
# Buy-hold benchmark - FULL type safe
            signals_data = result.get('signals_df', [])
            if isinstance(signals_data, list) and len(signals_data) > 0:
                first_entry = signals_data[0]
                if isinstance(first_entry, dict):
                    entry_price = first_entry.get('entry_price', 1.0)
                    bh_prices = [10000 * (entry_price / (p.get('entry_price', 1.0) or 1.0)) for p in signals_data if isinstance(p, dict)]
                else:
                    bh_prices = [10000]
            else:
                bh_prices = [10000]
            safe_len_curve = len(equity_curve) if isinstance(equity_curve, (list, tuple)) else 1
            bh_prices = [10000.0] * safe_len_curve
            fig_curve.add_trace(go.Scatter(x=x_range, y=bh_prices, mode='lines', name='Buy & Hold', line=dict(color='orange', width=2)))
            
            fig_curve.update_layout(title="📈 Equity Curve vs Buy & Hold", xaxis_title="Trades", yaxis_title="$ Equity", height=400)
            st.plotly_chart(fig_curve, use_container_width=True)
            
            # 3. SIGNAL DISTRIBUTION PIE - FIXED syntax + type safety
            signal_counts = result.get('signal_counts', {}) or {}
            if isinstance(signal_counts, dict) and signal_counts:
                pie_df = pd.DataFrame(list(signal_counts.items()), columns=['Signal', 'Count'])
                fig_pie = px.pie(pie_df, names='Signal', values='Count', title="Signal Distribution")
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("No signal distribution data available.")
            
            # 4. PERFORMANCE TABLE - FIXED type safety
            total_signals = sum(signal_counts.values()) if isinstance(signal_counts, dict) else 0
            perf_data = {
                'Metric': ['BUY Win Rate', 'SELL Win Rate', 'HOLD Win Rate', 'Total Signals', 'Total Return', 'Sharpe', 'Max DD', 'Profit Factor'],
                'Value': [f"{buy_acc:.1f}%", f"{sell_acc:.1f}%", f"{hold_acc:.1f}%", 
                         total_signals, f"{result.get("total_return_pct", 0):.1f}%",
                         f"{result.get("sharpe_ratio", 0):.2f}", f"{result.get("max_drawdown_pct", 0):.1f}%", "N/A"]
            }
            st.dataframe(pd.DataFrame(perf_data), use_container_width=True)
            
            # 5. TOP SIGNALS TABLE - FIXED column validation
            signals_data = result.get('signals_df', [])
            if isinstance(signals_data, list):
                signals_df = pd.DataFrame(signals_data)
            else:
                signals_df = pd.DataFrame()
            if not signals_df.empty and 'return_pct' in signals_df.columns and 'timestamp' in signals_df.columns:
                signals_df['datetime'] = pd.to_datetime(signals_df['timestamp'])
                top_signals = signals_df.nlargest(10, 'return_pct')[['datetime', 'signal', 'entry_price', 'return_pct', 'win']]
                st.data_editor(top_signals.rename(columns={'datetime': 'Date', 'entry_price': 'Entry $', 'return_pct': 'Return %', 'win': 'Win'}), 
                              use_container_width=True, hide_index=False)
            else:
                st.info("No valid signals data available for table.")
            
            # 6. CSV EXPORT - FIXED empty handling
            if not signals_df.empty:
                csv_buffer = io.StringIO()
                signals_df.to_csv(csv_buffer, index=False)
                st.download_button("📥 Download Signals CSV", csv_buffer.getvalue(), f"{stock}_backtest.csv", "text/csv")
            else:
                st.info("No signals data to export.")
            
            # Performance Rating
            if buy_acc > 60 or result.get('total_return_pct', 0) > 10:
                st.balloons()
                st.success("🎉 STRATEGY EXCELLENT - Deploy Live!")
            elif buy_acc > 50:
                st.success("✅ Good - Fine-tune params")
            else:
                st.info("⚠️ Needs strategy review")
    
    # ============== TAB 5: LIVE MARKET ==============
    with tab5: # type: ignore
        st.subheader("📡 Live Market Analysis - FIXED MULTI-TICKER")
        
        live_input = st.text_input("Enter tickers (comma sep): e.g. RELIANCE.NS,AAPL", value="RELIANCE.NS", key="live_input")
        
        if live_input:
            tickers = [t.strip() for t in live_input.split(",")]
            
            for ticker in tickers:
                with st.expander(f"📈 {ticker}"):
                    with st.spinner(f"Analyzing {ticker}..."):
                        df = get_stock_data(ticker)
                        
                        if df is None or isinstance(df, dict) or (hasattr(df, 'empty') and df.empty):
                            st.error(f"{ticker}: No data available")
                            continue
                        
                        st.write(f"**Price:** {df['Close'].iloc[-1]:.2f}")
                        
                        signal = generate_signal(df)
                        st.success(f"**Signal:** {signal['signal']} ({signal['confidence']})")
                        st.write(f"**Reason:** {signal['reason']}")
                        
                        support, resistance = support_resistance(df)
                        st.write(f"**Support:** {support:.2f}")
                        st.write(f"**Resistance:** {resistance:.2f}")
                        
                        price = df['Close'].iloc[-1]
                        reversal = role_reversal(price, support, resistance)
                        st.write(f"**Role Reversal:** {reversal}")
                        
                        status = market_status(ticker)
                        st.write(f"**Market Status:** {status}")
                        
                        # Chart
                        chart_data = get_chart_data(ticker, "5d")
                        if not chart_data.empty:
                            fig = go.Figure()
                            fig.add_trace(go.Scatter(x=chart_data.index, y=chart_data['Close'], mode='lines', name='Close'))
                            fig.add_hline(y=support, line_dash="dash", line_color="green", annotation_text="Support")
                            fig.add_hline(y=resistance, line_dash="dash", line_color="red", annotation_text="Resistance")
                            fig.update_layout(title=f"{ticker} Chart", height=300)
                            st.plotly_chart(fig, use_container_width=True)
                        
                        st.markdown("---")
