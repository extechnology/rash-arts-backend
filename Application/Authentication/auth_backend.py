from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import (
    ReadOnlyPasswordHashField,
    AdminPasswordChangeForm,
)
from django import forms
from django.urls import path, reverse
from django.shortcuts import render, redirect
from django.utils.translation import gettext_lazy as _

from .auth_models import User


class UserCreationForm(forms.ModelForm):
    password1 = forms.CharField(
        label=_("Password"),
        widget=forms.PasswordInput
    )
    password2 = forms.CharField(
        label=_("Confirm Password"),
        widget=forms.PasswordInput
    )

    class Meta:
        model = User
        fields = ("username", "email", "phone")

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(_("Passwords don't match."))

        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])

        if commit:
            user.save()

        return user


# ---------------------------------------------------
# User Change Form
# ---------------------------------------------------

class UserChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = User
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance.pk:
            self.fields[
                "password"
            ].help_text = _(
                'Raw passwords are not stored, so there is no way to see '
                'this user’s password, but you can '
                f'<a href="{reverse("admin:user_change_password", args=[self.instance.pk])}">'
                'change the password using this form</a>.'
            )

    def clean_password(self):
        return self.initial["password"]


# ---------------------------------------------------
# User Admin
# ---------------------------------------------------

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm

    list_display = (
        "id",
        "unique_id",
        "username",
        "email",
        "phone",
        "is_active",
        "is_staff",
        "is_email_verified",
        "is_phone_verified",
    )

    list_display_links = ("username",)

    list_filter = (
        "is_active",
        "is_staff",
        "is_superuser",
        "is_email_verified",
        "is_phone_verified",
    )

    search_fields = (
        "username",
        "email",
        "phone",
    )

    ordering = ("id",)

    readonly_fields = (
        "id",
        "unique_id",
        "date_joined",
        "updated_at",
        "last_login",
    )

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "username",
                    "fullname",
                    "email",
                    "phone",
                    "password",
                )
            },
        ),
        (
            _("Verification"),
            {
                "fields": (
                    "is_email_verified",
                    "is_phone_verified",
                )
            },
        ),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (
            _("Important dates"),
            {
                "fields": (
                    "last_login",
                    "date_joined",
                    "updated_at",
                )
            },
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "fullname",
                    "email",
                    "phone",
                    "password1",
                    "password2",
                    "is_active",
                    "is_staff",
                    "is_email_verified",
                    "is_phone_verified",
                ),
            },
        ),
    )

    # ---------------------------------------------------
    # Password Change View
    # ---------------------------------------------------

    def get_urls(self):
        urls = super().get_urls()

        custom_urls = [
            path(
                "<int:id>/password/",
                self.admin_site.admin_view(self.user_change_password),
                name="user_change_password",
            ),
        ]

        return custom_urls + urls

    def user_change_password(self, request, id):
        user = self.get_object(request, id)

        if user is None:
            return redirect("../")

        if request.method == "POST":
            form = AdminPasswordChangeForm(user, request.POST)

            if form.is_valid():
                form.save()
                messages.success(
                    request,
                    _("Password changed successfully."),
                )
                return redirect("../../")

        else:
            form = AdminPasswordChangeForm(user)

        context = {
            **self.admin_site.each_context(request),
            "title": _("Change password"),
            "form": form,
            "opts": self.model._meta,
            "original": user,
        }

        return render(
            request,
            "admin/auth/user/change_password.html",
            context,
        )