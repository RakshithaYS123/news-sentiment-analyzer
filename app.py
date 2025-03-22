import streamlit as st
import requests
import base64
import io
import json
import time
import pandas as pd
import matplotlib.pyplot as plt
import os
import subprocess
import threading

# Function to start the API in a separate thread


def start_api():
    subprocess.Popen(["uvicorn", "api:app", "--host",
                     "0.0.0.0", "--port", "8000"])


# Start the API when the app loads
threading.Thread(target=start_api, daemon=True).start()
time.sleep(2)  # Give the API time to start

st.set_page_config(
    page_title="News Summarizer & Sentiment Analyzer",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #424242;
    }
    .info-box {
        background-color: #E3F2FD;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .sentiment-positive {
        color: #2E7D32;
        font-weight: bold;
    }
    .sentiment-negative {
        color: #C62828;
        font-weight: bold;
    }
    .sentiment-neutral {
        color: #757575;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar for API configuration
with st.sidebar:
    st.title("⚙️ Configuration")
    api_endpoint = "http://localhost:8000/analyze"  # Hardcode to local API
    article_count = st.slider("Number of articles to analyze", 3, 15, 10)

    st.subheader("About")
    st.info(
        "This application extracts news articles about a company, "
        "analyzes their sentiment, performs comparative analysis, "
        "and provides a summary in Hindi with text-to-speech."
    )

# Main content
st.markdown('<p class="main-header">📰 News Summarization and Sentiment Analysis</p>',
            unsafe_allow_html=True)
st.markdown('<p class="sub-header">Extract insights from news articles with AI-powered analysis</p>',
            unsafe_allow_html=True)

# Company selection
company_list = ["Tesla", "Apple", "Microsoft",
                "Google", "Amazon", "Meta", "Netflix", "Nvidia"]
col1, col2 = st.columns([3, 1])

with col1:
    company_selection = st.radio("Choose company selection method:", [
                                 "From list", "Custom entry"])
    if company_selection == "From list":
        company_name = st.selectbox("Select a company", company_list)
    else:
        company_name = st.text_input("Enter company name", "")

with col2:
    st.markdown('<div class="info-box">', unsafe_allow_html=True)
    st.markdown("### How it works")
    st.markdown("1. Select or enter a company name")
    st.markdown("2. Click 'Analyze News' to start")
    st.markdown("3. Review sentiment analysis and insights")
    st.markdown("4. Listen to the Hindi summary")
    st.markdown('</div>', unsafe_allow_html=True)

if not company_name and company_selection == "Custom entry":
    st.warning("Please enter a company name to analyze")

# Button to trigger analysis
analyze_button = st.button(
    "🔍 Analyze News", type="primary", disabled=not company_name)

# Create placeholder for results
results_placeholder = st.empty()

if analyze_button:
    # Display progress
    progress_bar = st.progress(0)
    status_text = st.empty()

    status_text.text("Fetching news articles...")
    progress_bar.progress(10)
    time.sleep(0.5)

    try:
        # Call the API endpoint
        response = requests.post(
            api_endpoint,
            json={"company_name": company_name,
                  "article_count": article_count},
            timeout=30
        )

        progress_bar.progress(50)
        status_text.text("Analyzing sentiment and generating insights...")
        time.sleep(0.5)

        if response.status_code == 200:
            data = response.json()

            progress_bar.progress(80)
            status_text.text("Preparing results...")
            time.sleep(0.5)

            # Clear progress indicators
            progress_bar.progress(100)
            status_text.empty()
            progress_bar.empty()

            # Display results in a visually appealing format
            with results_placeholder.container():
                st.header(f"📊 Analysis Results for {data['Company']}")

                # Summary of findings
                st.subheader("Summary")
                st.info(data["Final Sentiment Analysis"])

                # Create tabs for different sections
                tab1, tab2, tab3, tab4 = st.tabs(
                    ["News Articles", "Sentiment Analysis", "Topic Analysis", "Hindi Summary"])

                with tab1:
                    # Articles in a more structured format
                    st.subheader("News Articles Analysis")

                    # Create a DataFrame for better visualization
                    articles_data = []
                    for i, article in enumerate(data["Articles"]):
                        articles_data.append({
                            "Index": i+1,
                            "Title": article["Title"],
                            "Sentiment": article["Sentiment"],
                            "Topics": ", ".join(article["Topics"]) if "Topics" in article else "N/A"
                        })

                    # Convert to DataFrame and display as a table
                    df_articles = pd.DataFrame(articles_data)
                    st.dataframe(df_articles, use_container_width=True)

                    # Display a few articles in detail
                    st.subheader("Article Details")
                    # Show only first 3 articles
                    for i, article in enumerate(data["Articles"][:3]):
                        with st.expander(f"Article {i+1}: {article['Title']}"):
                            # Apply sentiment-based styling
                            sentiment_class = ""
                            if article["Sentiment"] == "Positive":
                                sentiment_class = "sentiment-positive"
                            elif article["Sentiment"] == "Negative":
                                sentiment_class = "sentiment-negative"
                            else:
                                sentiment_class = "sentiment-neutral"

                            st.markdown(f"**Summary:** {article['Summary']}")
                            st.markdown(
                                f"**Sentiment:** <span class='{sentiment_class}'>{article['Sentiment']}</span>", unsafe_allow_html=True)
                            st.markdown(
                                f"**Topics:** {', '.join(article['Topics']) if 'Topics' in article else 'N/A'}")
                            if "URL" in article and article["URL"]:
                                st.markdown(
                                    f"[Read full article]({article['URL']})")

                with tab2:
                    # Sentiment analysis visualization
                    st.subheader("Sentiment Distribution")

                    # Get sentiment distribution
                    sentiment_dist = data["Comparative Sentiment Score"]["Sentiment Distribution"]

                    # Create DataFrame for visualization
                    df_sentiment = pd.DataFrame({
                        "Sentiment": list(sentiment_dist.keys()),
                        "Count": list(sentiment_dist.values())
                    })

                    # Create a bar chart
                    fig, ax = plt.subplots(figsize=(8, 5))
                    bars = ax.bar(
                        df_sentiment["Sentiment"],
                        df_sentiment["Count"],
                        color=["#2E7D32", "#C62828", "#757575"]
                    )

                    # Add labels and title
                    ax.set_title(
                        f"Sentiment Distribution for {data['Company']}", fontsize=14)
                    ax.set_xlabel("Sentiment", fontsize=12)
                    ax.set_ylabel("Number of Articles", fontsize=12)

                    # Add values on top of bars
                    for bar in bars:
                        height = bar.get_height()
                        ax.annotate(f"{height}",
                                    xy=(bar.get_x() + bar.get_width() / 2, height),
                                    xytext=(0, 3),
                                    textcoords="offset points",
                                    ha="center", va="bottom", fontsize=12)

                    st.pyplot(fig)

                    # Show sentiment comparisons
                    st.subheader("Comparative Analysis")

                    for i, comparison in enumerate(data["Comparative Sentiment Score"]["Coverage Differences"]):
                        st.markdown(
                            f"**Comparison {i+1}:** {comparison['Comparison']}")
                        st.markdown(f"**Impact:** {comparison['Impact']}")

                with tab3:
                    # Topic analysis
                    st.subheader("Topic Distribution")

                    # Extract all topics
                    all_topics = []
                    for article in data["Articles"]:
                        if "Topics" in article:
                            all_topics.extend(article["Topics"])

                    # Count topic frequencies
                    topic_counts = {}
                    for topic in all_topics:
                        if topic in topic_counts:
                            topic_counts[topic] += 1
                        else:
                            topic_counts[topic] = 1

                    # Convert to DataFrame
                    df_topics = pd.DataFrame({
                        "Topic": list(topic_counts.keys()),
                        "Frequency": list(topic_counts.values())
                    }).sort_values(by="Frequency", ascending=False)

                    # Plot horizontal bar chart for topics
                    fig, ax = plt.subplots(figsize=(10, 6))
                    bars = ax.barh(
                        df_topics["Topic"], df_topics["Frequency"], color="#1E88E5")

                    # Add labels and title
                    ax.set_title(
                        f"Topic Distribution in {data['Company']} News", fontsize=14)
                    ax.set_xlabel("Number of Articles", fontsize=12)
                    ax.set_ylabel("Topics", fontsize=12)

                    # Add values to the right of bars
                    for bar in bars:
                        width = bar.get_width()
                        ax.annotate(f"{width}",
                                    xy=(width, bar.get_y() +
                                        bar.get_height() / 2),
                                    xytext=(3, 0),
                                    textcoords="offset points",
                                    ha="left", va="center", fontsize=10)

                    st.pyplot(fig)

                    # Show common topics
                    st.subheader("Topic Overlap Analysis")

                    common_topics = data["Comparative Sentiment Score"]["Topic Overlap"]["Common Topics"]

                    if common_topics and common_topics[0] != "No common topics found":
                        st.markdown("**Common Topics Across Articles:**")
                        for topic in common_topics:
                            st.markdown(f"- {topic}")
                    else:
                        st.markdown(
                            "No common topics were found across articles.")

                with tab4:
                    # Hindi summary and audio
                    st.subheader("Summary in Hindi")

                    # Display Hindi text
                    st.markdown(f"**Hindi Summary:**")
                    st.info(data["Hindi Summary"])

                    # Display audio player
                    st.markdown("**Listen to Summary:**")

                    # Decode base64 audio data
                    audio_data = base64.b64decode(data["Audio"])

                    # Create a bytes buffer
                    audio_bytes = io.BytesIO(audio_data)

                    # Create an audio player
                    st.audio(audio_bytes, format="audio/wav")

                    # Add download button for audio
                    st.download_button(
                        label="Download Audio",
                        data=audio_data,
                        file_name=f"{data['Company']}_hindi_summary.wav",
                        mime="audio/wav"
                    )

    except requests.exceptions.ConnectionError:
        progress_bar.empty()
        status_text.empty()
        st.error(
            "❌ Unable to connect to the API. Please check if the API server is running and the endpoint is correct.")

    except Exception as e:
        progress_bar.empty()
        status_text.empty()
        st.error(f"❌ An error occurred: {str(e)}")

# Footer
st.markdown("---")
st.markdown("Made with ❤️ using Streamlit, FastAPI, and AI-powered analysis")
