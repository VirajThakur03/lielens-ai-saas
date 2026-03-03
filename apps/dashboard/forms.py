from django import forms

from services.document_parser import ALLOWED_DOC_EXTENSIONS


class DashboardSubmissionForm(forms.Form):
    text = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 5}))
    document = forms.FileField(required=False)

    def clean(self):
        cleaned = super().clean()
        text = (cleaned.get("text") or "").strip()
        document = cleaned.get("document")

        if not text and not document:
            raise forms.ValidationError("Add text or upload a document.")
        if text and len(" ".join(text.split())) < 20:
            raise forms.ValidationError("Text should be at least 20 characters.")
        if document:
            name = document.name.lower()
            if not any(name.endswith(ext) for ext in ALLOWED_DOC_EXTENSIONS):
                raise forms.ValidationError("Only .txt, .md, .pdf, .docx files are supported.")
        return cleaned
