from django.contrib import admin
from .models import Dashboard, Widget


class WidgetInline(admin.TabularInline):
    model  = Widget
    extra  = 0
    fields = ['type_widget', 'titre', 'variable_x', 'variable_y', 'position']


@admin.register(Dashboard)
class DashboardAdmin(admin.ModelAdmin):
    list_display    = ['titre', 'dataset_nom', 'nb_widgets', 'updated_at']
    search_fields   = ['titre', 'dataset_nom']
    readonly_fields = ['id', 'share_token', 'created_at', 'updated_at']
    inlines         = [WidgetInline]


@admin.register(Widget)
class WidgetAdmin(admin.ModelAdmin):
    list_display  = ['titre', 'type_widget', 'dashboard', 'variable_x', 'position']
    list_filter   = ['type_widget']
    search_fields = ['titre', 'dashboard__titre']