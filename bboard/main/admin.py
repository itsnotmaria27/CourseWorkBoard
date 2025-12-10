from django.contrib import admin
from .models import AdvUser, SuperRubric, SubRubric, Bb, AdditionalImage, Comment, Rating

# ---------- AdvUser ----------
@admin.register(AdvUser)
class AdvUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'is_activated', 'send_messages', 'date_joined')
    list_filter = ('is_activated', 'send_messages', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email')
    fields = (
        ('username', 'email'),
        ('first_name', 'last_name'),
        ('is_activated', 'send_messages'),
        ('is_staff', 'is_superuser', 'is_active'),
        'groups',
        'user_permissions',
        'last_login',
        'date_joined'
    )
    readonly_fields = ('last_login', 'date_joined')
    save_on_top = True


# ---------- Rubrics ----------
class SubRubricInline(admin.TabularInline):
    model = SubRubric
    extra = 1

@admin.register(SuperRubric)
class SuperRubricAdmin(admin.ModelAdmin):
    inlines = (SubRubricInline,)

@admin.register(SubRubric)
class SubRubricAdmin(admin.ModelAdmin):
    list_display = ('name', 'super_rubric', 'order')
    list_filter = ('super_rubric',)
    search_fields = ('name',)
    fields = ('super_rubric', 'name', 'order')


# ---------- AdditionalImage (встроенный редактор для Bb) ----------
class AdditionalImageInline(admin.TabularInline):
    model = AdditionalImage
    extra = 1


# ---------- Bb ----------
@admin.register(Bb)
class BbAdmin(admin.ModelAdmin):
    list_display = ('title', 'rubric', 'author', 'price', 'is_active', 'created_at')
    list_display_links = ('title',)
    list_filter = ('is_active', 'rubric', 'author', 'created_at')
    search_fields = ('title', 'content')
    fields = (
        ('title', 'price'),
        'content',
        'contacts',
        ('rubric', 'author'),
        'image',
        'is_active',
        'created_at'
    )
    readonly_fields = ('created_at',)
    inlines = (AdditionalImageInline,)
    save_on_top = True
    date_hierarchy = 'created_at'


# ---------- Comment ----------
@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'bb', 'created_at', 'is_active')
    list_filter = ('is_active', 'created_at')
    search_fields = ('author', 'content')
    fields = ('bb', 'author', 'content', 'is_active', 'created_at')
    readonly_fields = ('created_at',)


# ---------- Rating ----------
@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('user', 'bb', 'score', 'created_at')
    list_filter = ('score', 'created_at')
    search_fields = ('user__username', 'bb__title')
    readonly_fields = ('created_at',)