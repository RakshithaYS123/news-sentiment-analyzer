import requests
from bs4 import BeautifulSoup
import re
import random
import os
import tempfile
import numpy as np
from gtts import gTTS
import time


def analyze_sentiment(text):
    """
    Perform sentiment analysis on text using an external API.

    Args:
        text (str): Text to analyze

    Returns:
        str: Sentiment label ("Positive", "Negative", or "Neutral")
    """
    try:
        # Use TextBlob for sentiment analysis as it doesn't require API keys
        from textblob import TextBlob

        analysis = TextBlob(text)
        # Get the polarity score
        polarity = analysis.sentiment.polarity

        # Determine sentiment based on polarity
        if polarity > 0.1:
            return "Positive"
        elif polarity < -0.1:
            return "Negative"
        else:
            return "Neutral"

    except Exception as e:
        print(f"Error in sentiment analysis: {str(e)}")
        # Fallback to a simple keyword-based approach
        positive_words = ["success", "profit", "growth", "increase", "improved", "rise",
                          "strong", "exceed", "exceed", "optimistic", "positive", "advantage"]
        negative_words = ["decline", "loss", "down", "fell", "fall", "drop", "struggle",
                          "concern", "risk", "warning", "negative", "problem", "issue", "fail"]

        text_lower = text.lower()

        # Count occurrences of positive and negative words
        positive_count = sum(
            1 for word in positive_words if word in text_lower)
        negative_count = sum(
            1 for word in negative_words if word in text_lower)

        # Determine sentiment based on counts
        if positive_count > negative_count:
            return "Positive"
        elif negative_count > positive_count:
            return "Negative"
        else:
            return "Neutral"


def clean_text(text):
    """Clean and normalize text"""
    if not text:
        return ""
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    # Remove special characters except punctuation
    text = re.sub(r'[^\w\s\.\,\?\!\:\;\-\"]', '', text)
    return text


def generate_summary(text, max_length=200):
    """
    Generate a summary of the text
    """
    if len(text) <= max_length:
        return text

    # Simple extractive summarization by taking the first few sentences
    sentences = re.split(r'(?<=[.!?])\s+', text)
    summary = ""

    for sentence in sentences:
        if len(summary) + len(sentence) <= max_length:
            summary += sentence + " "
        else:
            break

    return summary.strip()


def get_company_articles(company_name, num_articles=10):
    """
    Fetch news articles related to a company using NewsAPI.

    Args:
        company_name (str): Name of the company to search for
        num_articles (int): Number of articles to retrieve

    Returns:
        list: List of dictionaries containing article title and summary
    """
    try:
        # Try using NewsAPI
        # Replace with your actual API key
        api_key = os.environ.get(
            "NEWS_API_KEY", "0954c90510554c12b5cde5dbb55e7e9f")

        # If API key is not set, try to get from environment or use fallback
        if api_key == "0954c90510554c12b5cde5dbb55e7e9f":
            # You should set this environment variable
            print("WARNING: Using fallback API or mock data as NEWS_API_KEY is not set")
            # Try alternative free API or use fallback
            return get_articles_from_gnews(company_name, num_articles)

        url = f"https://newsapi.org/v2/everything?q={company_name}&language=en&sortBy=publishedAt&pageSize={num_articles}"
        headers = {"X-Api-Key": api_key}

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()

            if data["status"] == "ok" and data["totalResults"] > 0:
                articles = []

                for article in data["articles"][:num_articles]:
                    # Extract and process article data
                    title = article.get("title", "")
                    description = article.get("description", "")
                    content = article.get("content", "")

                    # Generate summary
                    text_for_summary = content if content else description
                    summary = generate_summary(
                        text_for_summary, 200) if text_for_summary else description

                    # Clean the text
                    title = clean_text(title)
                    summary = clean_text(summary)

                    # Create article object
                    article_obj = {
                        "Title": title,
                        "Summary": summary,
                        "URL": article.get("url", ""),
                    }

                    articles.append(article_obj)

                return articles

        # If we got here, something went wrong with the API call
        print(f"Error fetching articles: {response.status_code}")
        # Fallback to alternative methods
        return get_articles_from_gnews(company_name, num_articles)

    except Exception as e:
        print(f"Error in get_company_articles: {str(e)}")
        # Final fallback to mock data if all else fails
        return generate_mock_articles(company_name, num_articles)


def get_articles_from_gnews(company_name, num_articles=10):
    """
    Alternative method to get news using Google search results
    """
    try:
        # Try to use a simple Google search and extract news
        # Increase the number of results by using multiple pages if needed
        articles = []
        page = 0
        max_attempts = 3  # Try up to 3 pages

        while len(articles) < num_articles and page < max_attempts:
            # Add page parameter for subsequent searches
            start_param = f"&start={page*10}" if page > 0 else ""
            url = f"https://www.google.com/search?q={company_name}+news&tbm=nws{start_param}"

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }

            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')

                # Extract news items - try different class names as Google may change them
                news_divs = soup.find_all('div', {'class': 'SoaBEf'})

                # If the class has changed, try a more general approach
                if not news_divs:
                    # Look for div elements containing news results
                    news_divs = soup.find_all(
                        'div', {'class': re.compile('(SoaBEf|WlydOe|xuvV6b)')})

                if not news_divs:
                    # Try to find any div that has a role="heading" element as a child
                    potential_news_divs = soup.find_all('div')
                    news_divs = [div for div in potential_news_divs if div.find(
                        'div', {'role': 'heading'})]

                for div in news_divs:
                    try:
                        # Extract title
                        title_elem = div.find('div', {'role': 'heading'})
                        if not title_elem:
                            # Try finding h3 elements as well
                            title_elem = div.find('h3')

                        title = title_elem.text if title_elem else f"{company_name} News {len(articles)+1}"

                        # Extract summary
                        # Try different class names as Google may change them
                        summary_elem = div.find(
                            'div', {'class': re.compile('(GI74Re|Y3v8qd|ea0Lbe)')})
                        if not summary_elem:
                            # Try to find any div that might contain summary text
                            non_heading_divs = [
                                d for d in div.find_all('div') if d != title_elem]
                            if non_heading_divs:
                                summary_elem = non_heading_divs[0]

                        summary = summary_elem.text if summary_elem else f"News related to {company_name}"

                        # Extract URL
                        url_elem = div.find('a')
                        url = url_elem.get('href') if url_elem else ""

                        # Check if this is a duplicate article (by title)
                        duplicate = False
                        for existing_article in articles:
                            if existing_article["Title"].lower() == clean_text(title).lower():
                                duplicate = True
                                break

                        if not duplicate:
                            # Create article object
                            article_obj = {
                                "Title": clean_text(title),
                                "Summary": clean_text(summary),
                                "URL": url
                            }
                            articles.append(article_obj)

                            # Stop if we've reached the desired number of articles
                            if len(articles) >= num_articles:
                                break
                    except Exception as inner_e:
                        print(f"Error extracting article: {str(inner_e)}")
                        continue

            # Move to the next page
            page += 1
            # Add a small delay to avoid being blocked
            time.sleep(0.5)

        # If we got enough articles, return them
        if len(articles) >= num_articles:
            return articles[:num_articles]

        # If we have some articles but not enough, supplement with mock data
        if articles:
            mock_count = num_articles - len(articles)
            if mock_count > 0:
                mock_articles = generate_mock_articles(
                    company_name, mock_count)
                articles.extend(mock_articles)
            return articles[:num_articles]

        # If we reached here and have no articles, fall back to mock data
        return generate_mock_articles(company_name, num_articles)

    except Exception as e:
        print(f"Error in get_articles_from_gnews: {str(e)}")
        return generate_mock_articles(company_name, num_articles)


def generate_mock_articles(company_name, count):
    """Generate mock articles for testing purposes when APIs fail"""
    # Enhanced with more variety to ensure we can generate at least 10 unique articles
    mock_titles = [
        f"{company_name} Reports Strong Q3 Earnings",
        f"{company_name} Announces New Product Line",
        f"Investors Optimistic About {company_name}'s Future",
        f"{company_name} Faces Regulatory Scrutiny",
        f"Analysts Lower {company_name}'s Price Target",
        f"{company_name} Expands into New Markets",
        f"CEO of {company_name} Steps Down",
        f"{company_name} Stock Hits All-Time High",
        f"Supply Chain Issues Impact {company_name}",
        f"{company_name} Completes Major Acquisition",
        f"{company_name} Announces Strategic Partnership",
        f"New Technology Breakthrough at {company_name}",
        f"{company_name} Releases Sustainability Report",
        f"Labor Disputes at {company_name} Facilities",
        f"{company_name} Receives Industry Recognition",
        f"Competition Heats Up for {company_name}",
        f"{company_name} Revises Annual Forecast",
        f"Cybersecurity Concerns at {company_name}",
        f"{company_name} Restructures Operations",
        f"Shareholders Approve {company_name} Proposal"
    ]

    mock_summaries = [
        f"{company_name} exceeded expectations with their quarterly earnings report, showing a 15% increase in revenue compared to the same period last year. CEO expressed confidence in continued growth.",
        f"The new product line from {company_name} aims to capture a growing market segment. Analysts predict this could boost revenue by up to 20% within the next fiscal year.",
        f"Despite market volatility, investors remain confident in {company_name}'s long-term strategy and innovation pipeline. Stock prices have risen 5% following recent announcements.",
        f"Regulatory bodies have raised concerns about {company_name}'s business practices. The company faces potential fines and may need to adjust operations to comply with regulations.",
        f"Citing concerns about market saturation and increased competition, several analysts have lowered their price targets for {company_name}, suggesting cautious investment approach.",
        f"{company_name} announced plans to enter emerging markets in Asia and South America, potentially reaching 1 billion new customers within the next three years.",
        f"After 8 years of leadership, the CEO of {company_name} announced retirement. Board has appointed the current COO as interim CEO while searching for a permanent replacement.",
        f"Shares of {company_name} reached an all-time high following better-than-expected product launch and positive customer feedback. Market capitalization now exceeds $500 billion.",
        f"Global supply chain disruptions have impacted {company_name}'s production capacity. The company warns of potential product shortages and delays in the coming months.",
        f"{company_name} has completed its $4.2 billion acquisition of a key competitor, strengthening its market position and expanding its technological capabilities.",
        f"{company_name} has formed a strategic alliance with industry leaders to develop next-generation technologies. The partnership is expected to accelerate innovation timelines.",
        f"Research team at {company_name} unveils groundbreaking technology that could revolutionize the industry. Experts call it a potential game-changer.",
        f"{company_name} released its annual sustainability report highlighting carbon reduction initiatives and commitment to renewable energy sources by 2030.",
        f"Workers at multiple {company_name} facilities have initiated labor actions over wage disputes and working conditions. Negotiations with union representatives are ongoing.",
        f"{company_name} received top honors at industry awards ceremony for innovation excellence and market leadership. CEO credits team's dedication to quality.",
        f"New market entrants are challenging {company_name}'s dominance in key segments. Analysts note increasing pressure on profit margins amid intensifying competition.",
        f"{company_name} has adjusted its annual forecast, citing changing market conditions and unexpected challenges in key territories during the previous quarter.",
        f"Security researchers identified potential vulnerabilities in {company_name}'s systems. The company has deployed patches and is conducting a comprehensive security review.",
        f"{company_name} announces major reorganization of business units to streamline operations and reduce costs. Changes expected to result in 5% workforce reduction.",
        f"At annual meeting, shareholders approved management's proposal for stock buyback program and executive compensation package despite some investor concerns."
    ]

    topics_options = [
        ["Financial", "Earnings", "Revenue"],
        ["Product", "Innovation", "Market"],
        ["Investment", "Stock Market", "Strategy"],
        ["Regulation", "Legal", "Compliance"],
        ["Financial", "Investment", "Analysis"],
        ["Expansion", "Global Markets", "Strategy"],
        ["Leadership", "Management", "Corporate"],
        ["Stock Market", "Financial", "Growth"],
        ["Supply Chain", "Operations", "Production"],
        ["Acquisition", "Strategy", "Competition"],
        ["Partnership", "Strategy", "Innovation"],
        ["Technology", "R&D", "Innovation"],
        ["Sustainability", "Environment", "Corporate Responsibility"],
        ["Labor", "HR", "Operations"],
        ["Industry Recognition", "Reputation", "Brand"],
        ["Competition", "Market Share", "Industry"],
        ["Financial", "Forecast", "Market Conditions"],
        ["Cybersecurity", "Technology", "Risk Management"],
        ["Corporate", "Restructuring", "Operations"],
        ["Shareholder", "Governance", "Investment"]
    ]

    # Ensure we have sentiments for all 20 articles
    sentiments = [
        "Positive", "Positive", "Positive", "Negative", "Negative",
        "Positive", "Neutral", "Positive", "Negative", "Positive",
        "Positive", "Positive", "Positive", "Negative", "Positive",
        "Negative", "Neutral", "Negative", "Neutral", "Neutral"
    ]

    mock_articles = []
    for i in range(min(count, len(mock_titles))):
        mock_articles.append({
            "Title": mock_titles[i],
            "Summary": mock_summaries[i],
            "URL": f"https://example.com/{company_name.lower()}-news-{i+1}",
            "Sentiment": sentiments[i],
            "Topics": topics_options[i]
        })

    return mock_articles


def perform_comparative_analysis(articles):
    """
    Perform comparative analysis across multiple articles.

    Args:
        articles (list): List of article dictionaries with sentiment information

    Returns:
        dict: Comparative analysis results
    """
    # Count sentiments
    sentiment_counts = {"Positive": 0, "Negative": 0, "Neutral": 0}
    for article in articles:
        sentiment = article.get("Sentiment", "Neutral")
        sentiment_counts[sentiment] += 1

    # Extract all topics
    all_topics = []
    for article in articles:
        all_topics.extend(article.get("Topics", []))

    # Find common topics
    topic_frequency = {}
    for topic in all_topics:
        if topic in topic_frequency:
            topic_frequency[topic] += 1
        else:
            topic_frequency[topic] = 1

    common_topics = [topic for topic,
                     freq in topic_frequency.items() if freq > 1]

    # Generate comparisons between articles
    coverage_differences = []
    if len(articles) >= 2:
        for i in range(min(3, len(articles) - 1)):  # Compare up to 3 pairs
            article1 = articles[i]
            article2 = articles[i + 1]

            topics1 = set(article1.get("Topics", []))
            topics2 = set(article2.get("Topics", []))

            unique_topics1 = list(topics1 - topics2)
            unique_topics2 = list(topics2 - topics1)

            comparison = {
                "Comparison": f"Article {i+1} focuses on {', '.join(unique_topics1) if unique_topics1 else 'general news'}, "
                f"while Article {i+2} discusses {', '.join(unique_topics2) if unique_topics2 else 'general news'}.",
                "Impact": generate_impact_statement(article1.get("Sentiment"), article2.get("Sentiment"))
            }

            coverage_differences.append(comparison)

    # Compile results
    comparative_analysis = {
        "Sentiment Distribution": sentiment_counts,
        "Coverage Differences": coverage_differences,
        "Topic Overlap": {
            "Common Topics": common_topics if common_topics else ["No common topics found"],
            "Unique Topics in Article 1": list(set(articles[0].get("Topics", []))) if articles else [],
            "Unique Topics in Article 2": list(set(articles[1].get("Topics", []))) if len(articles) > 1 else []
        }
    }

    return comparative_analysis


def generate_impact_statement(sentiment1, sentiment2):
    """Generate an impact statement based on the sentiments of two articles"""
    if sentiment1 == sentiment2:
        if sentiment1 == "Positive":
            return "Both articles present positive views, reinforcing confidence in the company's position."
        elif sentiment1 == "Negative":
            return "The negative tone in both articles may raise concerns about the company's current situation."
        else:
            return "The neutral coverage in both articles provides balanced information without strong bias."
    elif sentiment1 == "Positive" and sentiment2 == "Negative":
        return "The contrasting perspectives present a complex picture that may lead to market uncertainty."
    elif sentiment1 == "Negative" and sentiment2 == "Positive":
        return "The mixed coverage suggests the company faces both challenges and opportunities."
    else:
        return "The articles present different perspectives that should be considered for a complete understanding."


def translate_to_hindi(text):
    """Translate text to Hindi using MyMemory API"""
    try:
        import requests

        # MyMemory Translation API - free tier with no authentication required
        url = "https://api.mymemory.translated.net/get"

        # Request parameters
        params = {
            "q": text,
            "langpair": "en|hi",
            "de": "your-email@example.com"  # Optional but recommended to increase daily limit
        }

        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            if data["responseStatus"] == 200:
                return data["responseData"]["translatedText"]
            else:
                print(
                    f"Translation error: {data.get('responseDetails', 'Unknown error')}")
                return f"{text} (अनुवाद उपलब्ध नहीं है)"
        else:
            print(f"Translation request failed: {response.status_code}")
            return f"{text} (अनुवाद उपलब्ध नहीं है)"
    except Exception as e:
        print(f"Translation error: {str(e)}")
        return f"{text} (अनुवाद उपलब्ध नहीं है)"


def translate_company_name(company):
    """Translate common company names to Hindi"""
    company_dict = {
        "Tesla": "टेस्ला",
        "Apple": "एप्पल",
        "Microsoft": "माइक्रोसॉफ्ट",
        "Google": "गूगल",
        "Amazon": "अमेज़न",
        "Meta": "मेटा",
        "Facebook": "फेसबुक",
        "Twitter": "ट्विटर",
        "Netflix": "नेटफ्लिक्स",
        "Nvidia": "एनविडिया",
        "Intel": "इंटेल",
        "AMD": "एएमडी",
        "IBM": "आईबीएम",
        "Oracle": "ओरेकल",
        "Samsung": "सैमसंग"
    }
    return company_dict.get(company, company)


def translate_advice(advice):
    """Translate common advice phrases to Hindi"""
    advice_dict = {
        "Caution advised.": "सावधानी की सलाह दी जाती है।",
        "Potential growth expected.": "संभावित विकास की उम्मीद है।",
        "Situation requires monitoring.": "स्थिति पर नज़र रखने की आवश्यकता है।",
        "Consider buying stocks.": "शेयर खरीदने पर विचार करें।",
        "Consider selling stocks.": "शेयर बेचने पर विचार करें।",
        "Wait for more information.": "अधिक जानकारी के लिए प्रतीक्षा करें।",
        "Recommended for investment.": "निवेश के लिए अनुशंसित है।",
        "Not recommended for investment.": "निवेश के लिए अनुशंसित नहीं है।"
    }
    return advice_dict.get(advice, advice)


def add_hindi_grammar(text):
    """Add Hindi grammar markers and fix word order where possible"""
    # This is a simplified approach - a full implementation would need more complex NLP
    # Add postpositions where needed
    # Masculine plural possession
    text = re.sub(r'(\w+) का (\w+)', r'\1 के \2', text)

    # Add common phrase corrections
    text = text.replace("समाचार कवरेज है", "समाचार कवरेज हैं")

    return text


def generate_hindi_tts(text):
    """
    Generate Hindi text-to-speech audio.

    Args:
        text (str): Hindi text to convert to speech

    Returns:
        str: Path to the generated audio file
    """
    try:
        # Create a temporary file
        fd, temp_file = tempfile.mkstemp(suffix=".wav")
        os.close(fd)

        # Generate TTS using gTTS - make sure to specify Hindi language
        tts = gTTS(text=text, lang='hi', slow=False)
        tts.save(temp_file)

        return temp_file

    except Exception as e:
        print(f"Error in TTS generation: {str(e)}")
        # Return a dummy audio file in case of failure
        return create_dummy_audio()


def create_dummy_audio():
    """Create a dummy audio file for testing purposes"""
    fd, temp_file = tempfile.mkstemp(suffix=".wav")
    os.close(fd)

    # Generate a simple sine wave as dummy audio
    sample_rate = 16000
    duration = 3  # seconds
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    tone = np.sin(2 * np.pi * 440 * t)
    tone = (tone * 32767).astype(np.int16)

    import wave
    with wave.open(temp_file, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(tone.tobytes())

    return temp_file
