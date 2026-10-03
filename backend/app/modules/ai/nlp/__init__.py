"""
NLP module entrypoint.
"""
from app.modules.ai.nlp.classifier import disaster_nlp_classifier
from app.modules.ai.nlp.extractor import emergency_entity_extractor
from app.modules.ai.nlp.geocoder import disaster_geocoder
from app.modules.ai.nlp.ollama_extractor import ollama_disaster_extractor

__all__ = [
    "disaster_nlp_classifier",
    "emergency_entity_extractor",
    "disaster_geocoder",
    "ollama_disaster_extractor",
]
