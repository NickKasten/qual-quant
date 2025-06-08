import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification, AutoModelForCausalLM, BitsAndBytesConfig
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import logging
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import requests
import json
from concurrent.futures import ThreadPoolExecutor

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class NewsProcessor:
    def __init__(self):
        self.tokenizer = AutoTokenizer.from_pretrained("finbert-sentiment")
        self.model = AutoModelForSequenceClassification.from_pretrained("finbert-sentiment")
        
        # API Keys
        self.finnhub_key = os.getenv('FINNHUB_API_KEY')
        self.trading_economics_key = os.getenv('TRADING_ECONOMICS_API_KEY')
        
        if not self.finnhub_key or not self.trading_economics_key:
            raise ValueError("Missing API keys. Please set FINNHUB_API_KEY and TRADING_ECONOMICS_API_KEY in .env file")
        
        # API endpoints
        self.finnhub_base_url = "https://finnhub.io/api/v1"
        self.trading_economics_base_url = "https://api.tradingeconomics.com/news"
        
    def _fetch_finnhub_news(self, ticker: str, from_date: datetime, to_date: datetime) -> List[Dict]:
        """Fetch news from Finnhub API."""
        try:
            url = f"{self.finnhub_base_url}/news"
            params = {
                'category': 'general',
                'token': self.finnhub_key,
                'minId': int(from_date.timestamp()),
                'maxId': int(to_date.timestamp())
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            news_items = response.json()
            # Filter news items that mention the ticker
            return [item for item in news_items if ticker.lower() in item['headline'].lower() or ticker.lower() in item['summary'].lower()]
            
        except Exception as e:
            logger.error(f"Error fetching Finnhub news: {e}")
            return []
            
    def _fetch_trading_economics_news(self, ticker: str, from_date: datetime, to_date: datetime) -> List[Dict]:
        """Fetch news from Trading Economics API."""
        try:
            url = f"{self.trading_economics_base_url}/symbol/{ticker}"
            headers = {
                'Authorization': f'Bearer {self.trading_economics_key}'
            }
            params = {
                'from': from_date.strftime('%Y-%m-%d'),
                'to': to_date.strftime('%Y-%m-%d')
            }
            
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Error fetching Trading Economics news: {e}")
            return []
            
    def _combine_news_data(self, finnhub_news: List[Dict], trading_economics_news: List[Dict]) -> str:
        """Combine and format news data from both sources."""
        combined_news = []
        
        for news in finnhub_news:
            combined_news.append({
                'source': 'Finnhub',
                'title': news['headline'],
                'content': news['summary'],
                'date': datetime.fromtimestamp(news['datetime'])
            })
            
        for news in trading_economics_news:
            combined_news.append({
                'source': 'Trading Economics',
                'title': news['title'],
                'content': news['description'],
                'date': datetime.strptime(news['date'], '%Y-%m-%dT%H:%M:%S')
            })
            
        # Sort by date
        combined_news.sort(key=lambda x: x['date'], reverse=True)
        
        # Format the news into a single string
        formatted_news = []
        for news in combined_news:
            formatted_news.append(
                f"[{news['source']}] {news['date'].strftime('%Y-%m-%d %H:%M')}\n"
                f"Title: {news['title']}\n"
                f"Content: {news['content']}\n"
            )
            
        return "\n".join(formatted_news)
        
    def get_news_data(self, ticker: str, from_date: datetime, to_date: datetime) -> str:
        """Fetch and combine news data from both APIs."""
        with ThreadPoolExecutor(max_workers=2) as executor:
            finnhub_future = executor.submit(self._fetch_finnhub_news, ticker, from_date, to_date)
            trading_economics_future = executor.submit(self._fetch_trading_economics_news, ticker, from_date, to_date)
            
            finnhub_news = finnhub_future.result()
            trading_economics_news = trading_economics_future.result()
            
        return self._combine_news_data(finnhub_news, trading_economics_news)
        
    def process_news(self, news_text: str) -> float:
        """Process news text and return sentiment score."""
        inputs = self.tokenizer(news_text, return_tensors="pt", truncation=True, max_length=512)
        outputs = self.model(**inputs)
        sentiment_scores = torch.softmax(outputs.logits, dim=1)
        return sentiment_scores[0][1].item()  # Return positive sentiment score

class LLMValidator:
    def __init__(self, model_name: str = "Qwen/Qwen-3-7B"):
        self.news_processor = NewsProcessor()
        self.model_name = model_name
        
        # Configure 4-bit quantization
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True
        )
        
        self.tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            trust_remote_code=True,
            quantization_config=quantization_config,
            device_map="auto"
        )
        
    def get_news_context(self, ticker: str, date: datetime) -> str:
        """Get relevant news context for a given ticker and date."""
        # Get news from the last 7 days up to the current date
        from_date = date - timedelta(days=7)
        to_date = date
        
        # Fetch news data
        news_data = self.news_processor.get_news_data(ticker, from_date, to_date)
        
        if not news_data:
            return f"No recent news found for {ticker} between {from_date.strftime('%Y-%m-%d')} and {to_date.strftime('%Y-%m-%d')}"
            
        return news_data
        
    def validate_decision(self, 
                         sac_decision: np.ndarray,
                         tickers: List[str],
                         current_date: datetime,
                         market_data: Dict[str, pd.DataFrame]) -> np.ndarray:
        """Validate SAC decision using LLM and news context."""
        validated_decision = np.zeros_like(sac_decision)
        
        for i, ticker in enumerate(tickers):
            try:
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
                
                # Save validation history
                self.save_validation_history(
                    ticker=ticker,
                    date=current_date,
                    sac_decision=sac_decision[i],
                    validated_decision=validated_decision[i],
                    validation=validation
                )
                
            except Exception as e:
                logger.error(f"Error validating decision for {ticker}: {e}")
                validated_decision[i] = sac_decision[i]  # Fallback to original decision
                
        return validated_decision
        
    def _get_market_context(self, 
                           ticker: str, 
                           current_date: datetime,
                           market_data: Dict[str, pd.DataFrame]) -> str:
        """Get relevant market context for decision validation."""
        try:
            df = market_data[ticker]
            current_idx = df.index.get_loc(current_date)
            
            # Get recent price action (last 5 days)
            recent_prices = df.iloc[current_idx-5:current_idx+1]['close'].values
            price_change = (recent_prices[-1] - recent_prices[0]) / recent_prices[0]
            
            # Get volume trend
            recent_volumes = df.iloc[current_idx-5:current_idx+1]['volume'].values
            volume_trend = np.mean(recent_volumes[-3:]) / np.mean(recent_volumes[:3])
            
            # Get volatility
            returns = df.iloc[current_idx-20:current_idx+1]['close'].pct_change().dropna()
            volatility = returns.std() * np.sqrt(252)  # Annualized volatility
            
            # Get moving averages
            ma20 = df.iloc[current_idx-20:current_idx+1]['close'].mean()
            ma50 = df.iloc[current_idx-50:current_idx+1]['close'].mean() if current_idx >= 50 else None
            
            context = [
                f"Recent price change: {price_change:.2%}",
                f"Volume trend: {volume_trend:.2f}x",
                f"Volatility: {volatility:.2%}",
                f"20-day MA: {ma20:.2f}"
            ]
            
            if ma50 is not None:
                context.append(f"50-day MA: {ma50:.2f}")
                
            return "\n".join(context)
            
        except Exception as e:
            logger.error(f"Error getting market context for {ticker}: {e}")
            return "Market data unavailable"
        
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

Recent News:
{news_context}

News Sentiment Score: {sentiment_score:.2f} (0-1, higher means more positive)

Market Context:
{market_context}

Please analyze the above information and provide your validation in the following format:
1. Confidence in SAC decision (0-1)
2. Suggested adjustment to SAC decision (-1 to 1)
3. Detailed reasoning for your validation, considering:
   - News sentiment and recent developments
   - Market trends and technical indicators
   - Potential risks and opportunities
   - Any conflicting signals between news and market data

Your response:"""
        
    def _get_llm_validation(self, prompt: str) -> Dict:
        """Get validation from Qwen-3 model."""
        inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=2048)
        if torch.cuda.is_available():
            inputs = {k: v.cuda() for k, v in inputs.items()}
            
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=512,
                temperature=0.7,
                top_p=0.9,
                do_sample=True
            )
            
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Parse the response to extract confidence, adjustment, and reasoning
        try:
            # Extract the response after "Your response:"
            response_text = response.split("Your response:")[-1].strip()
            
            # Parse the response format
            lines = response_text.split('\n')
            confidence = float(lines[0].split(':')[-1].strip())
            adjustment = float(lines[1].split(':')[-1].strip())
            reasoning = '\n'.join(lines[2:]).strip()
            
            return {
                'confidence': confidence,
                'adjustment': adjustment,
                'reasoning': reasoning
            }
        except Exception as e:
            logger.error(f"Error parsing Qwen-3 response: {e}")
            return {
                'confidence': 0.5,
                'adjustment': 0.0,
                'reasoning': "Error in parsing model response"
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