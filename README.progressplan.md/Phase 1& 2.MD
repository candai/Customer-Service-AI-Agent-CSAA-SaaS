## Implementation Instructions for Claude Code

### Step-by-Step Implementation Order:

1. **Start with Backend Foundation**
   * Create Django project structure
   * Set up models for accounts, agents, conversations
   * Configure Django settings with CORS, Channels, JWT
2. **Implement Authentication**
   * Create auth endpoints with Django Ninja
   * Set up JWT token generation
   * Create registration flow with organization creation
3. **Build Core Services**
   * Implement AIService for OpenAI integration
   * Create TwilioService for WhatsApp/SMS/Voice
   * Build MessageProcessor for unified message handling
4. **Create Webhook Endpoints**
   * Set up Twilio webhook handlers
   * Implement message processing pipeline
   * Add WebSocket consumers for real-time updates
5. **Develop Frontend**
   * Set up Next.js with TypeScript
   * Create authentication flow
   * Build agent creation form
   * Implement conversation dashboard with WebSocket
6. **Testing & Deployment**
   * Test each component individually
   * Set up Railway deployment
   * Configure environment variables
   * Deploy and test end-to-end

### Key Implementation Notes:

1. **Database** : Use PostgreSQL with Django ORM. The models use UUIDs for IDs and JSONField for flexible data storage.
2. **Real-time Updates** : Django Channels with Redis enables WebSocket connections for live conversation updates.
3. **Message Flow** :

* Incoming: Twilio → Webhook → MessageProcessor → AI → Response
* WebSocket updates keep dashboard in sync

1. **Security** : JWT tokens for API auth, CORS configuration for frontend, webhook signature verification.
2. **File Uploads** : Knowledge documents are processed and stored as text for AI context.
3. **Async Processing** : Use async/await for non-blocking operations, especially for AI and external API calls.

This specification provides a complete, production-ready B2B SaaS platform for AI-powered customer service agents with WhatsApp, SMS, and voice capabilities


# Luron Backend Phases

## Phase 1: Backend Foundation ✅

**Phase 1.1: Django Project Setup**

1. ✅ **Project Structure** - Organized Django project with separate apps
2. ✅ **Settings Configuration** - Base settings with CORS, JWT, Channels setup
3. ✅ **Database Configuration** - PostgreSQL setup
4. ✅ **Custom User Model** - Email-based authentication

**Phase 1.2: Data Models**

1. ✅ **Organization Model** - Multi-tenant support with subscription tiers
2. ✅ **User Model** - Custom user with roles (owner, admin, member)
3. ✅ **Agent Model** - AI agent configuration with personality, prompts, channels
4. ✅ **KnowledgeDocument Model** - Knowledge base storage for agents
5. ✅ **Conversation Model** - Track customer conversations across channels
6. ✅ **Message Model** - Individual messages with metadata
7. ✅ **UsageLog Model** - Track usage for billing

**Phase 1.3: API Endpoints with Django Ninja**

1. ✅ **Authentication API**
   * Login endpoint with JWT tokens
   * Register endpoint with organization creation
   * Token refresh endpoint
   * User profile management
   * Password change functionality
2. ✅ **Agents API**
   * Create, Read, Update, Delete agents
   * Knowledge document upload (PDF, CSV, JSON, TXT)
   * List agents with filtering
   * Test agent with dry-run messages
   * Agent activation/deactivation
3. ✅ **Conversations API**
   * List conversations with filters
   * Get conversation details with messages
   * Send messages (for human agents)
   * End conversations
   * Hand off to human agent
   * Add tags to conversations
   * Conversation statistics
4. ✅ **Webhooks API**
   * WhatsApp webhook endpoint
   * SMS webhook endpoint
   * Voice webhook endpoint
   * Health check endpoint
5. ✅ **Billing API**
   * Usage summary and details
   * Subscription management
   * Usage tracking

**Key Features Implemented:**

* ✅ **JWT Authentication** - Stateless API authentication
* ✅ **Multi-tenancy** - Organization-based data isolation
* ✅ **File Upload** - Knowledge base document processing
* ✅ **Admin Interface** - Django admin for data management
* ✅ **CORS Support** - Cross-origin requests for frontend
* ✅ **Proper Permissions** - Role-based access control

## Phase 2: Service Layer Implementation ✅

**Phase 2.1: Core Services**

1. ✅ **AI Service (OpenAI Integration)**
   * Generate contextual AI responses
   * System prompt building with personality
   * Knowledge base integration
   * Conversation history context
   * Sentiment analysis
   * Intent extraction
   * Token usage tracking for billing
   * Fallback to GPT-3.5 when rate limited
2. ✅ **Twilio Service**
   * WhatsApp message sending/receiving
   * SMS message handling
   * Voice call management with TwiML
   * Phone number provisioning
   * Webhook validation
   * Message status tracking
3. ✅ **ElevenLabs Service**
   * Text-to-speech conversion
   * Voice selection
   * Audio file storage
   * Usage tracking for billing
   * Voice listing endpoint
4. ✅ **Message Processor (Unified Handler)**
   * Channel-agnostic message processing
   * Conversation management
   * Message storage and retrieval
   * Response delivery across channels
   * Metrics tracking
   * Real-time WebSocket updates
   * Welcome message handling

**Phase 2.2: Integration Features**

1. ✅ **Webhook Processing**
   * Twilio signature validation
   * Async message processing
   * Error handling and logging
   * Status callbacks
   * Voice call flow with speech recognition
2. ✅ **Real-time Updates**
   * WebSocket broadcasting setup
   * Conversation updates to dashboard
   * Organization-based channels
3. ✅ **Logging & Monitoring**
   * Comprehensive logging configuration
   * Error tracking
   * Service-level logging
4. ✅ **Environment Configuration**
   * Environment variables for all services
   * Secure API key management
   * Configurable webhook URLs
