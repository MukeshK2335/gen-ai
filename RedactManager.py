from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine

analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()

class RedactManager:
    def pii_filter(self, txt: str) -> str:
        results = analyzer.analyze(
            text=txt,
            language="en",
            entities=["EMAIL_ADDRESS", "PHONE_NUMBER"],
            score_threshold=0.70
        )
        anonymized_result = anonymizer.anonymize(
            text=txt,
            analyzer_results=results
        )
        return anonymized_result.text