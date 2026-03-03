from rest_framework import serializers

from apps.analysis.models import AnalysisResult, TextSubmission


class TextSubmissionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TextSubmission
        fields = ("id", "text", "document", "status", "created_at")
        read_only_fields = ("id", "status", "created_at")

    def validate_text(self, value: str) -> str:
        return " ".join(value.strip().split())

    def validate(self, attrs):
        text = attrs.get("text", "")
        document = attrs.get("document")
        if not text and not document:
            raise serializers.ValidationError("Provide text or upload a document.")
        if text and len(text) < 20:
            raise serializers.ValidationError("Text must be at least 20 characters.")
        return attrs


class AnalysisResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalysisResult
        fields = (
            "confidence_score",
            "exaggeration_score",
            "credibility_score",
            "emotional_intensity",
            "final_risk_score",
            "ml_probability",
            "feature_snapshot",
            "annotation_data",
            "contribution_breakdown",
            "ai_summary",
            "recommendations",
            "rewritten_text",
            "rewrite_method",
            "rewrite_changes",
            "report_file",
            "created_at",
        )


class SubmissionStatusSerializer(serializers.ModelSerializer):
    result = AnalysisResultSerializer(read_only=True)

    class Meta:
        model = TextSubmission
        fields = ("id", "status", "text", "document", "created_at", "result")
