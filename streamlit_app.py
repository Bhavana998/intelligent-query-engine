# streamlit_app.py
import streamlit as st
import requests
import pandas as pd
import json
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# Page configuration
st.set_page_config(
    page_title="Intelligent Query Engine",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .insight-box {
        background: #f0f2f6;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        margin: 1rem 0;
    }
    .sql-box {
        background: #1e1e1e;
        color: #d4d4d4;
        padding: 1rem;
        border-radius: 10px;
        font-family: monospace;
        font-size: 14px;
        overflow-x: auto;
    }
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.5rem 2rem;
        border-radius: 8px;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        transition: 0.3s;
    }
</style>
""", unsafe_allow_html=True)

# API Configuration
API_BASE_URL = "https://intelligent-query-engine-sjwi.onrender.com"

# Initialize session state
if 'query_history' not in st.session_state:
    st.session_state.query_history = []
if 'current_results' not in st.session_state:
    st.session_state.current_results = None

# Header
st.markdown("""
<div class="main-header">
    <h1 style="color: white; margin: 0;">🔍 Intelligent Query Engine</h1>
    <p style="color: white; margin: 10px 0 0 0;">Ask anything about your finances in plain English</p>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("## 🎮 Controls")
    
    # User selection
    user_id = st.selectbox(
        "Select User",
        options=[1, 2, 3],
        format_func=lambda x: f"User {x} - " + {
            1: "Active (90 days history)",
            2: "Moderate (30 days history)",
            3: "New (14 days history)"
        }[x]
    )
    
    st.markdown("---")
    
    # Example queries
    st.markdown("## 💡 Example Queries")
    example_queries = {
        "🍔 Food Spending": "How much did I spend on food last month?",
        "📊 Top Categories": "What are my top 3 spending categories?",
        "💰 Average Transaction": "What's my average transaction amount?",
        "📅 Weekly Count": "How many transactions did I make last week?",
        "🏪 Top Merchant": "Which merchant do I spend the most at?",
        "📈 Monthly Total": "Show me my total spending this month",
        "💸 Biggest Expense": "What's my biggest expense?",
        "📋 All Transactions": "Show me all my transactions"
    }
    
    for label, query in example_queries.items():
        if st.button(label, use_container_width=True):
            st.session_state.current_query = query
            st.rerun()
    
    st.markdown("---")
    
    # Cache control
    if st.button("🗑️ Clear Cache", use_container_width=True):
        try:
            response = requests.delete(f"{API_BASE_URL}/cache/{user_id}")
            if response.status_code == 200:
                st.success("Cache cleared successfully!")
            else:
                st.error("Failed to clear cache")
        except Exception as e:
            st.error(f"Error: {e}")
    
    st.markdown("---")
    st.markdown("### 📊 Stats")
    st.markdown(f"**API Status:** 🟢 Live")
    st.markdown(f"**Base URL:** `{API_BASE_URL}`")

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("## 📝 Ask a Question")
    
    # Query input
    query_text = st.text_area(
        "Type your question here:",
        value=st.session_state.get('current_query', "How much did I spend on food last month?"),
        height=100,
        placeholder="Example: How much did I spend on food last month?"
    )
    
    # Submit button
    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
    with col_btn1:
        submit = st.button("✨ Ask AI", use_container_width=True)

with col2:
    st.markdown("## 🎯 Quick Tips")
    st.markdown("""
    - Be specific with dates (last month, this week)
    - Ask about categories (food, transport)
    - Compare merchants or time periods
    - Request summaries or totals
    """)

# Process query
if submit and query_text:
    with st.spinner("🤔 Analyzing your question..."):
        try:
            # Make API request
            response = requests.post(
                f"{API_BASE_URL}/query",
                json={"user_id": user_id, "question": query_text},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                st.session_state.current_results = data
                
                # Add to history
                st.session_state.query_history.insert(0, {
                    "timestamp": datetime.now(),
                    "user_id": user_id,
                    "question": query_text,
                    "execution_time": data['execution_time_ms'],
                    "result_count": data['result_count']
                })
                
                # Keep only last 10 history items
                st.session_state.query_history = st.session_state.query_history[:10]
                
            else:
                st.error(f"Error: {response.status_code} - {response.text}")
                
        except requests.exceptions.Timeout:
            st.error("Request timeout. Please try again.")
        except Exception as e:
            st.error(f"Error: {e}")

# Display results
if st.session_state.current_results:
    data = st.session_state.current_results
    
    # Success metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3>⏱️ {data['execution_time_ms']:.0f}ms</h3>
            <p>Execution Time</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        cache_status = "✅ Hit" if data['from_cache'] else "❌ Miss"
        st.markdown(f"""
        <div class="metric-card">
            <h3>{cache_status}</h3>
            <p>Cache Status</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h3>{data['result_count']}</h3>
            <p>Results Found</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <h3>🔍</h3>
            <p>Query Processed</p>
        </div>
        """, unsafe_allow_html=True)
    
    # AI Insights
    st.markdown("## 🧠 AI Insights")
    st.markdown(f"""
    <div class="insight-box">
        <p style="font-size: 18px; margin: 0;">{data['insights']}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Results display
    st.markdown("## 📊 Query Results")
    if data['results'] and len(data['results']) > 0:
        df = pd.DataFrame(data['results'])
        st.dataframe(df, use_container_width=True)
        
        # Add download button
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Download Results as CSV",
            data=csv,
            file_name=f"query_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
        
        # Visualization for numeric data
        st.markdown("## 📈 Data Visualization")
        
        # Check if there are numeric columns for visualization
        numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns.tolist()
        
        if len(numeric_cols) > 0 and len(df) > 1:
            # Bar chart for top results
            fig = px.bar(
                df.head(10),
                x=df.columns[0] if len(df.columns) > 0 else numeric_cols[0],
                y=numeric_cols[0],
                title=f"Top Results by {numeric_cols[0]}",
                color_discrete_sequence=['#667eea']
            )
            st.plotly_chart(fig, use_container_width=True)
        
    else:
        st.info("No results found for your query. Try adjusting your question.")
    
    # SQL query display
    with st.expander("🔍 View Generated SQL"):
        st.markdown(f"""
        <div class="sql-box">
            {data['sql']}
        </div>
        """, unsafe_allow_html=True)
        
        # Copy SQL button
        st.code(data['sql'], language='sql')

# Query History
if st.session_state.query_history:
    st.markdown("## 📜 Recent Queries")
    
    history_df = pd.DataFrame(st.session_state.query_history)
    history_df['timestamp'] = history_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
    history_df.columns = ['Time', 'User', 'Question', 'Execution (ms)', 'Results']
    
    st.dataframe(history_df[['Time', 'User', 'Question', 'Execution (ms)', 'Results']], 
                 use_container_width=True)

# Analytics Dashboard (Bonus)
st.markdown("## 📊 Analytics Dashboard")

try:
    # Get analytics for current user
    response = requests.get(f"{API_BASE_URL}/analytics/{user_id}")
    if response.status_code == 200:
        analytics = response.json()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Queries", analytics.get('total_queries', 0))
        with col2:
            st.metric("Avg Execution Time", f"{analytics.get('average_execution_time_ms', 0):.0f}ms")
        with col3:
            st.metric("Avg Results/Query", f"{analytics.get('average_results_per_query', 0):.1f}")
        
        # Most frequent queries
        if analytics.get('most_frequent_queries'):
            st.markdown("### Most Common Questions")
            freq_df = pd.DataFrame(analytics['most_frequent_queries'])
            st.dataframe(freq_df, use_container_width=True)
            
except Exception as e:
    st.info("Analytics data will appear after more queries")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 20px;">
    <p>Powered by OpenRouter AI &amp; FastAPI | Intelligent Query Engine v2.0</p>
</div>
""", unsafe_allow_html=True)