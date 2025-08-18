from ninja import NinjaAPI
from apps.accounts.api import router as accounts_router
from apps.agents.api import router as agents_router
from apps.conversations.api import router as conversations_router
from apps.webhooks.api import router as webhooks_router
from apps.billing.api import router as billing_router
from apps.analytics.api import router as analytics_router
from apps.accounts.api import router as accounts_router, JWTAuth


# Create main API instance
luron_ninja_api = NinjaAPI(
    title="Luron API Documentation",
    version="1.0.0",
    description="Luron API for managing conversations, agents, and more."
)

# Add routers
luron_ninja_api.add_router("/auth/", accounts_router, tags=["Authentication"])
luron_ninja_api.add_router("/agents/", agents_router, tags=["Agents"])
luron_ninja_api.add_router("/conversations/", conversations_router, tags=["Conversations"])
luron_ninja_api.add_router("/analytics/", analytics_router, tags=["Analytics"])

luron_ninja_api.add_router("/billing/", billing_router, tags=["Billing"])

luron_ninja_api.add_router("/webhooks/", webhooks_router, tags=["Webhooks"])
