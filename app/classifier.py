"""Classifier function stub."""


def classify(data: str) -> dict:
    """
    Classify input data.
    
    Args:
        data: Input text to classify
        
    Returns:
        Classification result dictionary
    """
    # Placeholder implementation
    return {
        "result": "placeholder",
        "confidence": 0.0,
        "input": data[:50],  # Echo first 50 chars
    }
