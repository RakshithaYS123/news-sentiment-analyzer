from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import tempfile
from utils import get_company_articles, analyze_sentiment, perform_comparative_analysis, generate_hindi_tts, translate_to_hindi
import base64
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="News Analysis API", 
              description="API for fetching and analyzing news articles",
              version="1.0.0")

# Enable CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, specify the actual origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CompanyRequest(BaseModel):
    company_name: str
    article_count: int = 10

@app.get("/")
async def root():
    return {"message": "Welcome to the News Analysis API", 
            "endpoints": ["/analyze (POST)"],
            "documentation": "/docs or /redoc"}

@app.post("/analyze")
async def analyze_company(request: CompanyRequest):
    logger.info(f"Received analysis request for company: {request.company_name}")
    
    try:
        # Get news articles
        articles = get_company_articles(request.company_name, request.article_count)
        
        if not articles:
            raise HTTPException(status_code=404, detail=f"Could not find news articles for {request.company_name}")
        
        logger.info(f"Found {len(articles)} articles for {request.company_name}")
        
        # Perform sentiment analysis for each article
        for article in articles:
            article["Sentiment"] = analyze_sentiment(article["Summary"])
            # Extract topics from summary
            article["Topics"] = extract_topics(article["Summary"])
        
        # Perform comparative analysis
        comparative_analysis = perform_comparative_analysis(articles)
        
        # Generate final sentiment summary
        final_sentiment = generate_final_sentiment(comparative_analysis, request.company_name)
        
        # Convert to Hindi and generate TTS
        hindi_summary = translate_to_hindi(final_sentiment)
        logger.info(f"Translated to Hindi: {hindi_summary}")
        
        audio_file = generate_hindi_tts(hindi_summary)
        
        # Convert audio file to base64 for transmission
        with open(audio_file, "rb") as f:
            audio_data = base64.b64encode(f.read()).decode("utf-8")
        
        # Clean up temporary file
        os.remove(audio_file)
        
        # Construct response
        response = {
            "Company": request.company_name,
            "Articles": articles,
            "Comparative Sentiment Score": comparative_analysis,
            "Final Sentiment Analysis": final_sentiment,
            "Hindi Summary": hindi_summary,
            "Audio": audio_data
        }
        
        return response
    
    except Exception as e:
        logger.error(f"Error during analysis: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

def extract_topics(text):
    """Extract key topics from text"""
    topics = []
    keywords = {
        "stock": "Stock Market",
        "revenue": "Financial",
        "profit": "Financial",
        "sales": "Sales",
        "product": "Product",
        "innovation": "Innovation",
        "tech": "Technology",
        "regulation": "Regulation",
        "legal": "Legal",
        "expansion": "Expansion",
        "growth": "Growth",
        "market": "Market",
        "customer": "Customer Relations",
        "launch": "Product Launch",
        "research": "Research & Development",
        "invest": "Investment",
        "competition": "Competition",
        "partnership": "Partnership",
        "acquisition": "Acquisition",
        "merger": "Merger",
        "fiscal": "Financial",
        "quarterly": "Quarterly Report",
        "annual": "Annual Report"
    }
    
    for keyword, topic in keywords.items():
        if keyword.lower() in text.lower() and topic not in topics:
            topics.append(topic)
    
    # Add default topic if none found
    if not topics:
        topics = ["Business News"]
    
    return topics[:3]  # Limit to top 3 topics

def generate_final_sentiment(comparative_analysis, company_name):
    """Generate a final sentiment summary based on the comparative analysis"""
    sentiment_dist = comparative_analysis["Sentiment Distribution"]
    
    # Calculate total articles for percentage
    total_articles = sum(sentiment_dist.values())
    
    # Determine overall sentiment with percentages
    positive_percent = (sentiment_dist["Positive"] / total_articles * 100) if total_articles > 0 else 0
    negative_percent = (sentiment_dist["Negative"] / total_articles * 100) if total_articles > 0 else 0
    
    if positive_percent > 60:
        overall = "strongly positive"
        outlook = "Strong growth potential indicated."
    elif positive_percent > negative_percent:
        overall = "mostly positive"
        outlook = "Potential growth expected."
    elif negative_percent > 60:
        overall = "strongly negative"
        outlook = "Significant challenges ahead."
    elif negative_percent > positive_percent:
        overall = "mostly negative"
        outlook = "Caution advised."
    else:
        overall = "mixed"
        outlook = "Situation requires monitoring."
    
    return f"{company_name}'s latest news coverage is {overall} ({sentiment_dist['Positive']} positive, {sentiment_dist['Negative']} negative, {sentiment_dist['Neutral']} neutral articles). {outlook}"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)