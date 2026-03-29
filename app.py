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
from backend.auth import login, signup, get_user, update_profile, load_user_chats, save_user_chats
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
    show_support = st.sidebar.toggle("🟢 Show Support Lines (Green)", value=True)
    show_resistance = st.sidebar.toggle("🔴 Show Resistance Lines (Red)", value=True)
    apply_role_reversal = st.sidebar.toggle("🔄 Role Reversal", value=False, disabled=not (show_support and show_resistance))

    # Cache key for dashboard results
    stocks_tuple = tuple(st.session_state.selected_stocks)
    settings_hash = hash((stocks_tuple, show_support, show_resistance))

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

                    if r.get('support'):
                        fig.add_hline(y=r['support'], line_dash="dash", line_color="green", annotation_text="Support")
                    if r.get('resistance'):
                        fig.add_hline(y=r['resistance'], line_dash="dash", line_color="red", annotation_text="Resistance")
                    fig.update_layout(
                        title=f'{stock_id} Chart ({selected_period}) | S:{len(r.get("supports",[]))} R:{len(r.get("resistances",[]))}' + (' + S/R Lines' if show_support or show_resistance else ''),
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

        portfolio_input = st.text_input("Enter stocks (comma separated)", "tcs,sbin")

        if st.button("Analyze Portfolio"):
            raw_stocks = [s.strip() for s in portfolio_input.split(",")]            
            
            # Refactored to be more efficient and clear for static analysis.
            # This avoids calling normalize_stock twice and makes it explicit
            # that the 'stocks' list will not contain None values.
            stocks = []
            for s_raw in raw_stocks:
                normalized = find_stock(s_raw)
                if normalized:
                    stocks.append(normalized)
            sectors = []

            for s in stocks:
                sector = st.session_state.sector_map.get(s, "Unknown")
                # Dynamically fetch sector if not in hardcoded map
                if sector == "Unknown":
                    try:
                        ticker = yf.Ticker(s)
                        info = ticker.info
                        if 'sector' in info and info['sector']:
                            sector = info['sector']
                            st.session_state.sector_map[s] = sector  # Update session state map
                        elif 'industry' in info and info['industry']:  # Fallback to industry if sector is not available
                            sector = info['industry']
                            st.session_state.sector_map[s] = sector  # Update session state map
                    except Exception:
                        sector = "Unknown (API Error)"
                sectors.append(sector)

            # Clean summary display (no spam)
            if stocks:
                df_display = pd.DataFrame({
                    "Stock": stocks,
                    "Sector": sectors
                })
                st.dataframe(df_display, use_container_width=True, hide_index=True)
            else:
                st.warning("No valid stocks entered.")

            sector_count = Counter(sectors)

            st.subheader("⚠️ Risk Analysis")

            for sec, count in sector_count.items():
                if count > 1:
                    st.warning(f"High exposure in {sec} sector ({count} stocks)")

            st.subheader("📊 Portfolio Risk Score")

            risk_score = 0

            # 1. Sector concentration
            for sec, count in sector_count.items():
                if count > 1:
                    risk_score += count * 2

            # 2. Too few sectors = risky
            if len(sector_count) <= 2:
                risk_score += 3

            # 3. Number of stocks (more = more complex risk)
            risk_score += len(stocks) * 0.5

            # Normalize (0–10)
            risk_score = min(risk_score, 10)

            st.metric("Risk Score", f"{risk_score}/10")

            if risk_score <= 3:
                st.success("Low Risk Portfolio")
            elif risk_score <= 6:
                st.warning("Moderate Risk Portfolio")
            else:
                st.error("High Risk Portfolio")

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
        
        col1, col2 = st.columns(2)
        stock = col1.selectbox("Stock", st.session_state.selected_stocks)
        period = col2.selectbox("Period", ["3mo", "6mo", "1y"])
        
        if st.button("🚀 Run Backtest", key="run_backtest"):
            with st.spinner(f"Backtesting {stock} ({period})..."):
                result = backtest_stock(stock, period)
            
            st.success("✅ Backtest Complete!")
            
            col1, col2, col3 = st.columns(3)
            buy_acc = result.get('buy_accuracy', 0)
            sell_acc = result.get('sell_accuracy', 0)
            col1.metric("🟢 BUY Win Rate", f"{buy_acc:.1f}%")
            col2.metric("🔴 SELL Win Rate", f"{sell_acc:.1f}%")
            col3.metric("Total Signals", result.get('total_buy', 0) + result.get('total_sell', 0))
            
            signal_counts = result.get('signal_counts', {})
            st.caption(f"BUY: {result.get('wins_buy', 0)}/{result.get('total_buy', 0)} | SELL: {result.get('wins_sell', 0)}/{result.get('total_sell', 0)}")
            st.json(signal_counts)
            
            if buy_acc > 60:
                st.balloons()
                st.balloons()
                st.success("🎉 EXCELLENT - Profitable!")
            elif buy_acc > 50:
                st.success("✅ Good performance")
            else:
                st.warning("⚠️ Review strategy")
        else:
            if stock:
                st.info(f"👆 Click 'Run Backtest' for {stock}")
            else:
                st.info("👆 Select stock first")
    
    # ============== TAB 5: LIVE MARKET ==============
    with tab5: # type: ignore
        st.subheader("📡 Live Market Analysis")
        
        live_stock = st.text_input("Enter ticker for live analysis (e.g. AAPL, RELIANCE.NS)", key="live_input")
        
        if live_stock:
            with st.spinner(f"Analyzing {live_stock} live..."):
                # Get live data
                live_hist = get_chart_data(live_stock, "1d")
                data_result = get_stock_data(live_stock)
                
                if not live_hist.empty:
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=live_hist.index, y=live_hist['Close'], mode='lines', name='Live Price'))
                    fig.update_layout(title=f"{live_stock} Live Chart", height=400)
                    st.plotly_chart(fig, use_container_width=True)
                    
                    latest_price = live_hist['Close'].iloc[-1]
                    st.metric("Current Price", latest_price)
                else:
                    st.warning("No live data available")
                
                # Signal analysis
                if isinstance(data_result, pd.DataFrame):
                    signal = generate_signal(data_result)
                    st.markdown(f"""
### 📊 Signal: {signal['signal']}
Reason: {signal['reason']}  
Confidence: {signal['confidence']}  

RSI: {signal['rsi']}  
Support: {signal['support']}  
Resistance: {signal['resistance']}  
""")
                    
                    # News & AI reasoning
                    headlines = get_news(live_stock, 3)
                    sentiment = get_sentiment(headlines)
                    st.caption(f"News Sentiment: {sentiment}")
                    
                    ai_reason = generate_ai_explanation({**signal, 'stock': live_stock, 'news_sentiment': sentiment})
                    with st.expander("🤖 AI Reasoning"):
                        st.markdown(ai_reason)
                else:
                    st.error("Could not analyze - invalid ticker?")
        else:
            st.info("👆 Enter a ticker to get live analysis")
