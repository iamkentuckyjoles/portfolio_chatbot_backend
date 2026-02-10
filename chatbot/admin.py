from django import forms
from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from import_export.forms import ImportForm
from django.urls import reverse
from django.utils.html import format_html
from .models import KnowledgeItem
from .resources import KnowledgeItemResource


class CustomImportForm(ImportForm):
    custom_file_name = forms.CharField(
        required=False,
        label="Custom file name",
        
    )

@admin.register(KnowledgeItem)
class KnowledgeItemAdmin(ImportExportModelAdmin):
    resource_class = KnowledgeItemResource
    import_form_class = CustomImportForm   

    list_display = (
        "id",
        "category",
        "question",
        "answer",
        "uploaded_file_name",
        "uploaded_time",
        "row_actions",
    )
    search_fields = ("question", "answer", "category", "custom_file_name")
    list_filter = ("category", "uploaded_time")

    def row_actions(self, obj):
        edit_url = reverse("admin:chatbot_knowledgeitem_change", args=[obj.id])
        delete_url = reverse("admin:chatbot_knowledgeitem_delete", args=[obj.id])
        return format_html(
            '<a style="color:blue;" href="{}">Edit</a> &nbsp; '
            '<a style="color:red;" href="{}">Delete</a>',
            edit_url,
            delete_url,
        )
    row_actions.short_description = "Actions"

    def import_data(self, dataset, **kwargs):
        
        if "file_name" not in kwargs:
            kwargs["file_name"] = kwargs.get("custom_file_name") or dataset.title
        return super().import_data(dataset, **kwargs)

