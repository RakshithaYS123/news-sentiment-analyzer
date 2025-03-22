# News Summarization and Text-to-Speech Application

This application extracts key details from multiple news articles related to a given company, performs sentiment analysis, conducts comparative analysis, and generates a text-to-speech (TTS) output in Hindi.

## Features

- **News Extraction**: Extracts title, summary, and metadata from news articles related to a company
- **Sentiment Analysis**: Analyzes sentiment (positive, negative, neutral) of article content
- **Comparative Analysis**: Compares sentiment across articles to provide insights
- **Text-to-Speech**: Converts summarized content to Hindi speech
- **User Interface**: Simple web-based interface using Streamlit
- **API Development**: Communication between frontend and backend via FastAPI

## Project Structure

```
project/
├── app.py           # Streamlit frontend
├── api.py           # FastAPI backend
├── utils.py         # Utility functions
├── requirements.txt # Dependencies
└── README.md        # Documentation
```

## Installation and Setup

1. Clone the repository:

   ```
   git clone https://github.com/yourusername/news-summarizer.git
   cd news-summarizer
   ```

2. Install dependencies:

   ```
   pip install -r requirements.txt
   ```

3. Run the API server:

   ```
   uvicorn api:app --reload --host 0.0.0.0 --port 8000
   ```

4. In a separate terminal, run the Streamlit app:

   ```
   streamlit run app.py
   ```

5. Open your browser and go to `http://localhost:8501` to access the application.

## API Documentation

The application exposes the following API endpoints:

### POST /analyze

Analyzes news articles for a specified company.

**Request Body:**

```json
{
  "company_name": "Tesla"
}
```

**Response:**

```json
{
  "Company": "Tesla",
  "Articles": [
    {
      "Title": "Article Title",
      "Summary": "Article Summary",
      "Sentiment": "Positive",
      "Topics": ["Topic1", "Topic2"]
    }
  ],
  "Comparative Sentiment Score": {
    "Sentiment Distribution": {
      "Positive": 1,
      "Negative": 0,
      "Neutral": 0
    },
    "Coverage Differences": [...],
    "Topic Overlap": {...}
  },
  "Final Sentiment Analysis": "Summary text",
  "Audio": "base64-encoded audio data"
}
```

## Models Used

1. **Sentiment Analysis**: DistilBERT model fine-tuned on SST-2 dataset
2. **Text-to-Speech**: Google Text-to-Speech (gTTS) for Hindi speech generation
3. **Topic Extraction**: Keyword-based approach for demo purposes

## Assumptions & Limitations

- **Web Scraping**: The application assumes access to non-JavaScript websites that can be scraped using BeautifulSoup.
- **Sentiment Analysis**: Uses a pre-trained model which may not be domain-specific to financial news.
- **Topic Extraction**: Uses a simplified keyword-based approach rather than a sophisticated topic modeling technique.
- **Hindi Translation**: Uses a mock implementation for demo purposes. In production, this would use a proper translation API.
- **Failover Mechanism**: If web scraping fails, the system generates mock data for demonstration.

## Deployment

The application is deployed on Hugging Face Spaces and can be accessed at: [https://huggingface.co/spaces/yourusername/news-summarizer](https://huggingface.co/spaces/yourusername/news-summarizer)

## Future Improvements

- Implement more sophisticated web scraping with JavaScript support
- Use domain-specific sentiment analysis model for financial news
- Implement proper topic modeling using LDA or similar techniques
- Add caching for frequently searched companies
- Improve error handling and user feedback

## License

MIT
