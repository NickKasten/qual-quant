import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import logging
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class NewsProcessor:
    def __init__(self):
        self.tokenizer = AutoTokenizer.from_pretrained("finbert-sentiment")
        self.model = AutoModelForSequenceClassification.from_pretrained("finbert-sentiment")
        
    def process_news(self, news_text: str) -> float:
        """Process news text and return sentiment score."""
        inputs = self.tokenizer(news_text, return_tensors="pt", truncation=True, max_length=512)
        outputs = self.model(**inputs)
        sentiment_scores = torch.softmax(outputs.logits, dim=1)
        return sentiment_scores[0][1].item()  # Return positive sentiment score

class LLMValidator:
    def __init__(self, model_name: str = "gpt-3.5-turbo"):
        self.news_processor = NewsProcessor()
        self.model_name = model_name
        
    def get_news_context(self, ticker: str, date: datetime) -> str:
        """Get relevant news context for a given ticker and date."""
        # This would typically involve querying a news API or database
        # For now, we'll return a placeholder
        return f"News context for {ticker} on {date.strftime('%Y-%m-%d')}"
        
    def validate_decision(self, 
                         sac_decision: np.ndarray,
                         tickers: List[str],
                         current_date: datetime,
                         market_data: Dict[str, pd.DataFrame]) -> np.ndarray:
        """Validate SAC decision using LLM and news context."""
        validated_decision = np.zeros_like(sac_decision)
        
        for i, ticker in enumerate(tickers):
            # Get news context
            news_context = self.get_news_context(ticker, current_date)
            
            # Process news sentiment
            sentiment_score = self.news_processor.process_news(news_context)
            
            # Get market context
            market_context = self._get_market_context(ticker, current_date, market_data)
            
            # Create prompt for LLM
            prompt = self._create_validation_prompt(
                ticker=ticker,
                sac_decision=sac_decision[i],
                news_context=news_context,
                sentiment_score=sentiment_score,
                market_context=market_context
            )
            
            # Get LLM validation
            validation = self._get_llm_validation(prompt)
            
            # Adjust decision based on validation
            validated_decision[i] = self._adjust_decision(sac_decision[i], validation)
            
        return validated_decision
        
    def _get_market_context(self, 
                           ticker: str, 
                           current_date: datetime,
                           market_data: Dict[str, pd.DataFrame]) -> str:
        """Get relevant market context for decision validation."""
        df = market_data[ticker]
        current_idx = df.index.get_loc(current_date)
        
        # Get recent price action
        recent_prices = df.iloc[current_idx-5:current_idx+1]['close'].values
        price_change = (recent_prices[-1] - recent_prices[0]) / recent_prices[0]
        
        # Get volume trend
        recent_volumes = df.iloc[current_idx-5:current_idx+1]['volume'].values
        volume_trend = np.mean(recent_volumes[-3:]) / np.mean(recent_volumes[:3])
        
        return f"Recent price change: {price_change:.2%}, Volume trend: {volume_trend:.2f}x"
        
    def _create_validation_prompt(self,
                                ticker: str,
                                sac_decision: float,
                                news_context: str,
                                sentiment_score: float,
                                market_context: str) -> str:
        """Create prompt for LLM validation."""
        return f"""As a trading expert, validate the following trading decision:

Ticker: {ticker}
SAC Model Decision: {sac_decision:.2f} (positive means buy, negative means sell)
News Context: {news_context}
News Sentiment Score: {sentiment_score:.2f}
Market Context: {market_context}

Please provide your validation in the following format:
1. Confidence in SAC decision (0-1)
2. Suggested adjustment to SAC decision (-1 to 1)
3. Reasoning for your validation

Your response:"""
        
    def _get_llm_validation(self, prompt: str) -> Dict:
        """Get validation from LLM."""
        # This would typically involve calling an LLM API
        # For now, we'll return a placeholder response
        return {
            'confidence': 0.8,
            'adjustment': 0.1,
            'reasoning': "SAC decision aligns with market sentiment and news context"
        }
        
    def _adjust_decision(self, sac_decision: float, validation: Dict) -> float:
        """Adjust SAC decision based on LLM validation."""
        # Combine SAC decision with LLM validation
        adjusted_decision = sac_decision * validation['confidence'] + validation['adjustment']
        
        # Ensure decision stays within bounds
        return np.clip(adjusted_decision, -1.0, 1.0)
        
    def save_validation_history(self, 
                              ticker: str,
                              date: datetime,
                              sac_decision: float,
                              validated_decision: float,
                              validation: Dict,
                              path: str = "data/validation_history"):
        """Save validation history for analysis."""
        os.makedirs(path, exist_ok=True)
        
        history = {
            'ticker': ticker,
            'date': date,
            'sac_decision': sac_decision,
            'validated_decision': validated_decision,
            'confidence': validation['confidence'],
            'adjustment': validation['adjustment'],
            'reasoning': validation['reasoning']
        }
        
        df = pd.DataFrame([history])
        file_path = os.path.join(path, f"{ticker}_validation_history.csv")
        
        if os.path.exists(file_path):
            df.to_csv(file_path, mode='a', header=False, index=False)
        else:
            df.to_csv(file_path, index=False) 