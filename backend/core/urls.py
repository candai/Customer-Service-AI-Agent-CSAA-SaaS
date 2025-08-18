from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from apps.accounts.api import router as accounts_router
from apps.agents.api import router as agents_router
from apps.conversations.api import router as conversations_router
from apps.webhooks.api import router as webhooks_router
from apps.billing.api import router as billing_router
from core.api import luron_ninja_api
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", luron_ninja_api.urls)

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)