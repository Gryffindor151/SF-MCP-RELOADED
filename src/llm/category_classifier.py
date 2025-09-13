"""
Category classifier for analyzing user queries and determining tool categories
"""

import re
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

from .tool_registry import ToolCategory

logger = logging.getLogger(__name__)

@dataclass
class IntentAnalysis:
    """Result of query intent analysis"""
    primary_intent: str
    entities: List[str]
    action_words: List[str]
    complexity_indicators: List[str]
    category_scores: Dict[ToolCategory, float]
    confidence: float

class QueryIntent(Enum):
    """Types of user intents"""
    READ_DATA = "read_data"
    ANALYZE_DATA = "analyze_data"
    MODIFY_DATA = "modify_data"
    EXPLORE_SCHEMA = "explore_schema"
    MANAGE_SCHEMA = "manage_schema"
    DISCOVER_OBJECTS = "discover_objects"
    MANAGE_CODE = "manage_code"
    DEBUG_ISSUES = "debug_issues"

class CategoryClassifier:
    """Classifies user queries into tool categories"""
    
    def __init__(self):
        # Intent patterns for classification
        self.intent_patterns = {
            QueryIntent.READ_DATA: {
                "keywords": ["show", "get", "find", "list", "display", "retrieve", "fetch"],
                "patterns": [r"show me.*", r"get.*", r"find.*", r"list.*"],
                "categories": [ToolCategory.DATA_OPERATIONS, ToolCategory.OBJECT_DISCOVERY],
                "weight": 1.0
            },
            
            QueryIntent.ANALYZE_DATA: {
                "keywords": ["count", "sum", "average", "total", "how many", "statistics", "analyze"],
                "patterns": [r"how many.*", r"count.*", r"total.*", r"average.*"],
                "categories": [ToolCategory.DATA_OPERATIONS],
                "weight": 1.2
            },
            
            QueryIntent.MODIFY_DATA: {
                "keywords": ["create", "insert", "update", "delete", "modify", "change", "add", "remove"],
                "patterns": [r"create.*record", r"insert.*", r"update.*", r"delete.*"],
                "categories": [ToolCategory.DATA_OPERATIONS],
                "weight": 1.1
            },
            
            QueryIntent.EXPLORE_SCHEMA: {
                "keywords": ["describe", "fields", "structure", "schema", "what fields", "properties"],
                "patterns": [r"what fields.*", r"describe.*", r".*structure.*", r".*schema.*"],
                "categories": [ToolCategory.SCHEMA_MANAGEMENT],
                "weight": 1.3
            },
            
            QueryIntent.MANAGE_SCHEMA: {
                "keywords": ["create object", "add field", "manage", "permissions", "modify object"],
                "patterns": [r"create.*object", r"add.*field", r"manage.*", r".*permissions.*"],
                "categories": [ToolCategory.SCHEMA_MANAGEMENT],
                "weight": 1.4
            },
            
            QueryIntent.DISCOVER_OBJECTS: {
                "keywords": ["search objects", "find objects", "objects containing", "what objects"],
                "patterns": [r"search.*objects", r"find.*objects", r"objects.*containing"],
                "categories": [ToolCategory.OBJECT_DISCOVERY],
                "weight": 1.2
            },
            
            QueryIntent.MANAGE_CODE: {
                "keywords": ["apex", "trigger", "class", "execute", "run code", "deploy"],
                "patterns": [r".*apex.*", r".*trigger.*", r"execute.*code", r"run.*"],
                "categories": [ToolCategory.CODE_MANAGEMENT],
                "weight": 1.1
            },
            
            QueryIntent.DEBUG_ISSUES: {
                "keywords": ["debug", "logs", "error", "troubleshoot", "issue", "problem"],
                "patterns": [r"debug.*", r".*logs.*", r".*error.*", r"troubleshoot.*"],
                "categories": [ToolCategory.DEBUGGING],
                "weight": 1.3
            }
        }
        
        # Salesforce entity patterns
        self.entity_patterns = {
            "objects": [
                r"\b(account|accounts)\b", r"\b(contact|contacts)\b", 
                r"\b(opportunity|opportunities)\b", r"\b(case|cases)\b",
                r"\b(lead|leads)\b", r"\b(user|users)\b"
            ],
            "relationships": [r"with.*", r"including.*", r"and.*"],
            "conditions": [r"where.*", r"filter.*", r"condition.*"]
        }
        
        # Complexity indicators
        self.complexity_indicators = {
            "simple": ["show", "get", "list", "find"],
            "moderate": ["where", "filter", "condition", "with"],
            "complex": ["aggregate", "group by", "join", "relationship", "nested"],
            "advanced": ["create", "manage", "permissions", "deploy", "execute"]
        }
    
    def analyze_query(self, query: str) -> IntentAnalysis:
        """Analyze user query and determine intent and categories"""
        query_lower = query.lower().strip()
        
        # Extract entities
        entities = self._extract_entities(query_lower)
        
        # Extract action words
        action_words = self._extract_action_words(query_lower)
        
        # Detect complexity
        complexity_indicators = self._detect_complexity(query_lower)
        
        # Calculate category scores
        category_scores = self._calculate_category_scores(query_lower)
        
        # Determine primary intent
        primary_intent = self._determine_primary_intent(query_lower, category_scores)
        
        # Calculate overall confidence
        confidence = self._calculate_confidence(category_scores, action_words, entities)
        
        return IntentAnalysis(
            primary_intent=primary_intent,
            entities=entities,
            action_words=action_words,
            complexity_indicators=complexity_indicators,
            category_scores=category_scores,
            confidence=confidence
        )
    
    def _extract_entities(self, query: str) -> List[str]:
        """Extract Salesforce entities from query"""
        entities = []
        
        for entity_type, patterns in self.entity_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, query, re.IGNORECASE)
                entities.extend(matches)
        
        # Remove duplicates and clean up
        return list(set([e.strip() for e in entities if e.strip()]))
    
    def _extract_action_words(self, query: str) -> List[str]:
        """Extract action words from query"""
        action_words = []
        
        for intent, config in self.intent_patterns.items():
            for keyword in config["keywords"]:
                if keyword.lower() in query:
                    action_words.append(keyword)
        
        return list(set(action_words))
    
    def _detect_complexity(self, query: str) -> List[str]:
        """Detect complexity indicators in query"""
        indicators = []
        
        for complexity, keywords in self.complexity_indicators.items():
            for keyword in keywords:
                if keyword in query:
                    indicators.append(complexity)
        
        return list(set(indicators))
    
    def _calculate_category_scores(self, query: str) -> Dict[ToolCategory, float]:
        """Calculate relevance scores for each category"""
        scores = {category: 0.0 for category in ToolCategory}
        
        for intent, config in self.intent_patterns.items():
            intent_score = 0.0
            
            # Keyword matching
            for keyword in config["keywords"]:
                if keyword in query:
                    intent_score += 1.0
            
            # Pattern matching
            for pattern in config["patterns"]:
                if re.search(pattern, query, re.IGNORECASE):
                    intent_score += 1.5  # Patterns are more specific
            
            # Apply weight and distribute to categories
            weighted_score = intent_score * config["weight"]
            for category in config["categories"]:
                scores[category] += weighted_score / len(config["categories"])
        
        return scores
    
    def _determine_primary_intent(self, query: str, category_scores: Dict[ToolCategory, float]) -> str:
        """Determine the primary intent based on analysis"""
        # Find highest scoring category
        max_category = max(category_scores.items(), key=lambda x: x[1])
        
        # Map category back to intent
        category_to_intent = {
            ToolCategory.DATA_OPERATIONS: "data_operations",
            ToolCategory.SCHEMA_MANAGEMENT: "schema_exploration",
            ToolCategory.OBJECT_DISCOVERY: "object_discovery",
            ToolCategory.CODE_MANAGEMENT: "code_operations",
            ToolCategory.DEBUGGING: "troubleshooting"
        }
        
        return category_to_intent.get(max_category[0], "general_query")
    
    def _calculate_confidence(self, category_scores: Dict[ToolCategory, float], 
                            action_words: List[str], entities: List[str]) -> float:
        """Calculate overall confidence in the analysis"""
        max_score = max(category_scores.values()) if category_scores.values() else 0
        
        # Base confidence from category scoring
        confidence = min(max_score / 3.0, 1.0)  # Normalize to 0-1
        
        # Boost confidence if we found clear indicators
        if action_words:
            confidence += 0.1 * len(action_words)
        
        if entities:
            confidence += 0.1 * len(entities)
        
        # Cap at 1.0
        return min(confidence, 1.0)
    
    def get_ranked_categories(self, analysis: IntentAnalysis, 
                            min_score: float = 0.1) -> List[Tuple[ToolCategory, float]]:
        """Get categories ranked by relevance score"""
        filtered_scores = {
            category: score 
            for category, score in analysis.category_scores.items() 
            if score >= min_score
        }
        
        return sorted(filtered_scores.items(), key=lambda x: x[1], reverse=True) 