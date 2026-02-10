from import_export import resources, fields
from .models import KnowledgeItem
import os
from django.core.exceptions import ValidationError

class KnowledgeItemResource(resources.ModelResource):
    category = fields.Field(attribute="category", column_name="category")
    question = fields.Field(attribute="question", column_name="question")
    answer = fields.Field(attribute="answer", column_name="answer")

    class Meta:
        model = KnowledgeItem
        import_id_fields = [] 
        fields = ("category", "question", "answer")  

    def before_import(self, dataset, **kwargs):
        # Validate headers
        expected_headers = {"category", "question", "answer"}
        if set(dataset.headers) != expected_headers:
            raise ValidationError("Invalid file headers. Must be: category, question, answer")

        # Validate file type
        file_name = kwargs.get("file_name", "")
        ext = os.path.splitext(file_name)[1].lower()
        if ext not in [".csv", ".json", ".txt"]:
            raise ValidationError("Invalid file type. Only .csv, .json, or .txt files are allowed.")

        # Enforce row limit
        if len(dataset) > 50:
            raise ValidationError("Bulk upload limit exceeded. Maximum 50 rows allowed per file.")

    def before_import_row(self, row, row_number=None, **kwargs):
        # Inject filename into each row before saving
        file_name = kwargs.get("file_name", "")
        if file_name:
            row["uploaded_file_name"] = os.path.basename(file_name)
