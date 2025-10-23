"""
Risk Assessment Module for BerkAI Professional
Analyzes messages for crisis, self-harm, and suicide risk
"""

import re
from typing import Dict, List, Tuple

# Crisis keywords - Türkçe
SUICIDE_KEYWORDS = [
    "intihar", "kendimi öldür", "ölmek istiyorum", "yaşamak istemiyorum",
    "hayattan bıktım", "son vermek", "kendime zarar", "öldürmek istiyorum"
]

SELF_HARM_KEYWORDS = [
    "kendime zarar", "kesiyorum", "kendimi kesiyorum", "kendimi yaralıyorum",
    "acı çekmek istiyorum", "kendimi incitiyorum"
]

HIGH_RISK_KEYWORDS = [
    "plan yaptım", "silah", "ilaç içeceğim", "atlamak", "kendimi astım",
    "bugün son gün", "veda", "elveda", "affet beni"
]

CRISIS_KEYWORDS = [
    "panik", "dayanamıyorum", "çöküyorum", "kontrolü kaybettim",
    "çaresizim", "yalnızım", "umutsuzum"
]

def analyze_message_risk(message: str) -> Dict:
    """
    Analyze a message for risk indicators
    Returns risk assessment dict
    """
    message_lower = message.lower()
    
    # Initialize risk assessment
    risk = {
        "risk_level": 0,
        "risk_category": "low",
        "suicide_risk": False,
        "self_harm_risk": False,
        "crisis_detected": False,
        "risk_indicators": []
    }
    
    # Check suicide keywords
    for keyword in SUICIDE_KEYWORDS:
        if keyword in message_lower:
            risk["suicide_risk"] = True
            risk["risk_indicators"].append(f"İntihar göstergesi: '{keyword}'")
            risk["risk_level"] += 4
    
    # Check self-harm keywords
    for keyword in SELF_HARM_KEYWORDS:
        if keyword in message_lower:
            risk["self_harm_risk"] = True
            risk["risk_indicators"].append(f"Kendine zarar göstergesi: '{keyword}'")
            risk["risk_level"] += 3
    
    # Check high risk keywords
    for keyword in HIGH_RISK_KEYWORDS:
        if keyword in message_lower:
            risk["risk_indicators"].append(f"Yüksek risk göstergesi: '{keyword}'")
            risk["risk_level"] += 5
    
    # Check crisis keywords
    for keyword in CRISIS_KEYWORDS:
        if keyword in message_lower:
            risk["crisis_detected"] = True
            risk["risk_indicators"].append(f"Kriz göstergesi: '{keyword}'")
            risk["risk_level"] += 2
    
    # Negative emotion patterns
    negative_patterns = [
        r'hiçbir\s+şey',
        r'kimse\s+anlamıyor',
        r'artık\s+yok',
        r'sonsuza\s+kadar'
    ]
    
    for pattern in negative_patterns:
        if re.search(pattern, message_lower):
            risk["risk_level"] += 1
    
    # Cap risk level at 10
    risk["risk_level"] = min(risk["risk_level"], 10)
    
    # Determine risk category
    if risk["risk_level"] >= 8 or risk["suicide_risk"]:
        risk["risk_category"] = "critical"
    elif risk["risk_level"] >= 5 or risk["self_harm_risk"]:
        risk["risk_category"] = "high"
    elif risk["risk_level"] >= 3 or risk["crisis_detected"]:
        risk["risk_category"] = "medium"
    else:
        risk["risk_category"] = "low"
    
    return risk


def should_notify_doctor(risk: Dict) -> bool:
    """Determine if doctor should be notified"""
    return risk["risk_category"] in ["critical", "high"] or risk["suicide_risk"]


def generate_crisis_response() -> str:
    """Generate appropriate crisis response"""
    return """
🚨 Zor bir dönemden geçtiğinizi anlıyorum. Lütfen profesyonel destek alın:

📞 **Acil Yardım Hatları:**
• 112 - Acil Yardım
• 182 - Psikolojik Destek Hattı
• Ankara Kriz Merkezi: 0312 310 2565

💚 **Atanmış doktorunuz bilgilendirildi ve en kısa sürede sizinle iletişime geçecek.**

Lütfen güvende olun. Hayatınız değerli!
"""
