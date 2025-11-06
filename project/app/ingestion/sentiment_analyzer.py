"""
Financial sentiment analysis module.

Provides comprehensive sentiment analysis using FinBERT, TextBlob, and VADER
for financial text including earnings calls, MD&A sections, and news articles.
"""

import re
from typing import Any, Dict, List, Optional

from app.utils.logger import get_logger

logger = get_logger(__name__)

# Try to import optional dependencies
try:
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.warning("transformers library not available. FinBERT will be disabled.")

try:
    from textblob import TextBlob

    TEXTBLOB_AVAILABLE = True
except ImportError:
    TEXTBLOB_AVAILABLE = False
    logger.warning(
        "textblob library not available. TextBlob sentiment will be disabled."
    )

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

    VADER_AVAILABLE = True
except ImportError:
    VADER_AVAILABLE = False
    logger.warning(
        "vaderSentiment library not available. VADER sentiment will be disabled."
    )


class SentimentAnalyzerError(Exception):
    """Custom exception for sentiment analyzer errors."""

    pass


class SentimentAnalyzer:
    """
    Financial sentiment analyzer.

    Supports multiple sentiment analysis models:
    - FinBERT: Financial domain-specific BERT model
    - TextBlob: Rule-based sentiment scoring
    - VADER: Financial text-optimized sentiment analyzer
    """

    # FinBERT model name (financial domain-specific)
    FINBERT_MODEL = "ProsusAI/finbert"

    # Forward guidance keywords for extraction
    FORWARD_GUIDANCE_KEYWORDS = [
        "guidance",
        "outlook",
        "forecast",
        "expect",
        "anticipate",
        "project",
        "target",
        "estimate",
        "believe",
        "plan",
        "intend",
        "should",
        "will",
        "may",
        "could",
        "fiscal year",
        "quarter",
        "revenue",
        "earnings",
        "growth",
        "margin",
        "profit",
    ]

    # Risk factor keywords
    RISK_KEYWORDS = [
        "risk",
        "uncertainty",
        "volatility",
        "challenge",
        "concern",
        "threat",
        "adverse",
        "negative",
        "decline",
        "decrease",
        "loss",
        "failure",
        "litigation",
        "regulation",
        "competition",
        "market conditions",
    ]

    def __init__(
        self,
        use_finbert: bool = True,
        use_textblob: bool = True,
        use_vader: bool = True,
        device: Optional[str] = None,
    ):
        """
        Initialize sentiment analyzer.

        Args:
            use_finbert: Whether to use FinBERT model (default: True)
            use_textblob: Whether to use TextBlob (default: True)
            use_vader: Whether to use VADER (default: True)
            device: Device for FinBERT ('cpu', 'cuda', or None for auto)
        """
        self.use_finbert = use_finbert and TRANSFORMERS_AVAILABLE
        self.use_textblob = use_textblob and TEXTBLOB_AVAILABLE
        self.use_vader = use_vader and VADER_AVAILABLE

        # Initialize FinBERT
        self.finbert_model = None
        self.finbert_tokenizer = None
        if self.use_finbert:
            try:
                logger.info("Loading FinBERT model...")
                self.finbert_tokenizer = AutoTokenizer.from_pretrained(
                    self.FINBERT_MODEL
                )
                self.finbert_model = AutoModelForSequenceClassification.from_pretrained(
                    self.FINBERT_MODEL
                )

                # Set device
                if device is None:
                    device = "cuda" if torch.cuda.is_available() else "cpu"
                self.device = device
                self.finbert_model.to(self.device)
                self.finbert_model.eval()

                logger.info(f"FinBERT model loaded on {self.device}")
            except Exception as e:
                logger.error(f"Failed to load FinBERT model: {str(e)}")
                self.use_finbert = False
                self.finbert_model = None
                self.finbert_tokenizer = None

        # Initialize TextBlob (no initialization needed)
        if self.use_textblob:
            logger.info("TextBlob sentiment analyzer ready")

        # Initialize VADER
        self.vader_analyzer = None
        if self.use_vader:
            try:
                self.vader_analyzer = SentimentIntensityAnalyzer()
                logger.info("VADER sentiment analyzer ready")
            except Exception as e:
                logger.error(f"Failed to initialize VADER: {str(e)}")
                self.use_vader = False
                self.vader_analyzer = None

        # Compile regex patterns for forward guidance and risk extraction
        self.forward_guidance_pattern = re.compile(
            r"\b(" + "|".join(self.FORWARD_GUIDANCE_KEYWORDS) + r")\b",
            re.IGNORECASE,
        )
        self.risk_pattern = re.compile(
            r"\b(" + "|".join(self.RISK_KEYWORDS) + r")\b",
            re.IGNORECASE,
        )

    def analyze_sentiment(
        self, text: str, model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze sentiment of text using specified or all available models.

        Args:
            text: Text to analyze
            model: Specific model to use
                ('finbert', 'textblob', 'vader', or None for all)

        Returns:
            Dictionary with sentiment scores and labels from all enabled models

        Raises:
            SentimentAnalyzerError: If analysis fails
        """
        if not text or not text.strip():
            return {
                "finbert": None,
                "textblob": None,
                "vader": None,
                "overall_sentiment": "neutral",
                "overall_score": 0.0,
            }

        results: Dict[str, Any] = {
            "finbert": None,
            "textblob": None,
            "vader": None,
        }

        # Analyze with FinBERT
        if (model is None or model == "finbert") and self.use_finbert:
            try:
                finbert_result = self._analyze_finbert(text)
                results["finbert"] = finbert_result
            except Exception as e:
                logger.warning(f"FinBERT analysis failed: {str(e)}")
                results["finbert"] = None

        # Analyze with TextBlob
        if (model is None or model == "textblob") and self.use_textblob:
            try:
                textblob_result = self._analyze_textblob(text)
                results["textblob"] = textblob_result
            except Exception as e:
                logger.warning(f"TextBlob analysis failed: {str(e)}")
                results["textblob"] = None

        # Analyze with VADER
        if (model is None or model == "vader") and self.use_vader:
            try:
                vader_result = self._analyze_vader(text)
                results["vader"] = vader_result
            except Exception as e:
                logger.warning(f"VADER analysis failed: {str(e)}")
                results["vader"] = None

        # Calculate overall sentiment
        # (prefer FinBERT if available, else VADER, else TextBlob)
        overall = self._calculate_overall_sentiment(results)
        results["overall_sentiment"] = overall["sentiment"]
        results["overall_score"] = overall["score"]

        return results

    def _analyze_finbert(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment using FinBERT.

        Args:
            text: Text to analyze

        Returns:
            Dictionary with FinBERT sentiment results
        """
        if self.finbert_model is None or self.finbert_tokenizer is None:
            raise SentimentAnalyzerError("FinBERT model not initialized")

        # Tokenize and truncate if necessary (max 512 tokens)
        inputs = self.finbert_tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True,
        ).to(self.device)

        # Get predictions
        with torch.no_grad():
            outputs = self.finbert_model(**inputs)
            logits = outputs.logits
            probabilities = torch.softmax(logits, dim=-1)

        # Get predicted class
        predicted_class_id = torch.argmax(logits, dim=-1).item()
        predicted_label = self.finbert_model.config.id2label[predicted_class_id]

        # Get probabilities for all classes
        probs = probabilities[0].cpu().tolist()
        label_probs = {
            self.finbert_model.config.id2label[i]: probs[i] for i in range(len(probs))
        }

        # Map FinBERT labels to standard sentiment
        sentiment_map = {
            "positive": "positive",
            "negative": "negative",
            "neutral": "neutral",
        }
        sentiment = sentiment_map.get(predicted_label.lower(), "neutral")

        # Calculate score (positive - negative)
        positive_prob = label_probs.get("positive", 0.0)
        negative_prob = label_probs.get("negative", 0.0)
        score = positive_prob - negative_prob

        return {
            "label": predicted_label,
            "sentiment": sentiment,
            "score": float(score),
            "probabilities": label_probs,
            "confidence": float(max(probs)),
        }

    def _analyze_textblob(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment using TextBlob.

        Args:
            text: Text to analyze

        Returns:
            Dictionary with TextBlob sentiment results
        """
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity
        subjectivity = blob.sentiment.subjectivity

        # Map polarity to sentiment
        if polarity > 0.1:
            sentiment = "positive"
        elif polarity < -0.1:
            sentiment = "negative"
        else:
            sentiment = "neutral"

        return {
            "polarity": float(polarity),
            "subjectivity": float(subjectivity),
            "sentiment": sentiment,
            "score": float(polarity),
        }

    def _analyze_vader(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment using VADER.

        Args:
            text: Text to analyze

        Returns:
            Dictionary with VADER sentiment results
        """
        if self.vader_analyzer is None:
            raise SentimentAnalyzerError("VADER analyzer not initialized")

        scores = self.vader_analyzer.polarity_scores(text)

        # Determine sentiment from compound score
        compound = scores["compound"]
        if compound >= 0.05:
            sentiment = "positive"
        elif compound <= -0.05:
            sentiment = "negative"
        else:
            sentiment = "neutral"

        return {
            "compound": float(compound),
            "positive": float(scores["pos"]),
            "neutral": float(scores["neu"]),
            "negative": float(scores["neg"]),
            "sentiment": sentiment,
            "score": float(compound),
        }

    def _calculate_overall_sentiment(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate overall sentiment from multiple model results.

        Args:
            results: Dictionary with results from different models

        Returns:
            Dictionary with overall sentiment and score
        """
        # Prefer FinBERT if available, else VADER, else TextBlob
        if results.get("finbert") is not None:
            finbert = results["finbert"]
            return {
                "sentiment": finbert["sentiment"],
                "score": finbert["score"],
                "model": "finbert",
            }
        elif results.get("vader") is not None:
            vader = results["vader"]
            return {
                "sentiment": vader["sentiment"],
                "score": vader["score"],
                "model": "vader",
            }
        elif results.get("textblob") is not None:
            textblob = results["textblob"]
            return {
                "sentiment": textblob["sentiment"],
                "score": textblob["score"],
                "model": "textblob",
            }
        else:
            return {"sentiment": "neutral", "score": 0.0, "model": None}

    def extract_forward_guidance(self, text: str) -> List[str]:
        """
        Extract forward guidance statements from text.

        Args:
            text: Text to analyze

        Returns:
            List of forward guidance sentences
        """
        if not text:
            return []

        # Split into sentences
        sentences = re.split(r"[.!?]+", text)

        # Find sentences with forward guidance keywords
        guidance_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            # Check if sentence contains forward guidance keywords
            if self.forward_guidance_pattern.search(sentence):
                guidance_sentences.append(sentence)

        return guidance_sentences

    def extract_risk_factors(self, text: str) -> List[str]:
        """
        Extract risk factor statements from text.

        Args:
            text: Text to analyze

        Returns:
            List of risk factor sentences
        """
        if not text:
            return []

        # Split into sentences
        sentences = re.split(r"[.!?]+", text)

        # Find sentences with risk keywords
        risk_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            # Check if sentence contains risk keywords
            if self.risk_pattern.search(sentence):
                risk_sentences.append(sentence)

        return risk_sentences

    def analyze_document(
        self, text: str, extract_guidance: bool = True, extract_risks: bool = True
    ) -> Dict[str, Any]:
        """
        Comprehensive document analysis including sentiment and extraction.

        Args:
            text: Document text to analyze
            extract_guidance: Whether to extract forward guidance (default: True)
            extract_risks: Whether to extract risk factors (default: True)

        Returns:
            Dictionary with complete analysis results
        """
        # Analyze sentiment
        sentiment_results = self.analyze_sentiment(text)

        # Extract forward guidance
        forward_guidance = []
        if extract_guidance:
            forward_guidance = self.extract_forward_guidance(text)

        # Extract risk factors
        risk_factors = []
        if extract_risks:
            risk_factors = self.extract_risk_factors(text)

        return {
            "sentiment": sentiment_results,
            "forward_guidance": forward_guidance,
            "forward_guidance_count": len(forward_guidance),
            "risk_factors": risk_factors,
            "risk_factors_count": len(risk_factors),
        }
