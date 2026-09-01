# ✅ Completed Phases

## ✅ Phase 1: Backend Foundation

**Backend:**

* Django project setup with PostgreSQL
* Custom User model with JWT authentication
* Organization, Agent, KnowledgeDocument, Conversation, Message models
* Complete REST APIs with Django Ninja
* Authentication, Agents, Conversations, Webhooks, Billing endpoints

**Frontend:** None (Backend only)

---

## ✅ Phase 2: Service Layer

**Backend:**

* OpenAI integration (GPT-4/GPT-3.5)
* Twilio service (WhatsApp, SMS, Voice)
* ElevenLabs text-to-speech
* Unified message processor
* Webhook handlers (tested & working)

**Frontend:** None (Skipped - not critical)

---

## ✅ Phase 3: WebSocket & Real-time Backend

**Backend (1 week):**

* **Django Channels Setup**

  python

  ```python
  # Complete WebSocket infrastructure
  - ASGI configuration
  - Redis channel layer setup
  - WebSocket routing
  ```
* **WebSocket Consumers**

  python

  ```python
  # Real-time conversation updates
  - ConversationConsumer
  - Authentication middleware
  - Organization-based rooms
  - Message broadcasting
  ```
* **Real-time Events**

  python

  ```python
  # Event types to implement
  - conversation.new_message
  - conversation.status_changed
  - conversation.agent_typing
  - agent.status_changed
  - organization.usage_update
  ```
* **Presence System**

  python

  ```python
  # Track online users
  - User online/offline status
  - Active conversations tracking
  - Agent availability
  ```

**Frontend:** None (Will implement WebSocket client in Phase 4)

---

## ✅ Phase 4: Frontend Foundation + WebSocket Client

**Backend (2-3 days):**

* API pagination
* Advanced filtering endpoints
* Bulk operations
* File upload optimization
* CORS fine-tuning

**Frontend (1.5 weeks):**

* **Project Setup**

  typescript

  ```typescript
  -Next.js14withAppRouter
  -TypeScript configuration
  -TailwindCSS+ shadcn/ui
  -Environment variables
  ```
* **Authentication System**

  typescript

  ```typescript
  -Login/Register pages
  -JWT token management
  -Protected routes
  -Auth context/hooks
  ```
* **Dashboard Layout**

  typescript

  ```typescript
  -Sidebar navigation
  -Headerwith user menu
  -Responsive design
  -Loading states
  ```
* **WebSocket Client**

  typescript

  ```typescript
  -WebSocket connection manager
  -Auto-reconnection
  -Event handlers
  -Real-time hooks
  ```

---

## ✅ Phase 5: Agent Management UI

**Backend (2-3 days):**

* Agent templates API
* Voice preview endpoint

**Frontend (2 weeks):**

**Agent Dashboard (Completed)**

* List view with cards
* Create/Edit/Delete
* Active/Inactive toggle
* Channel configuration

**Agent Testing (Partially Complated)**

* Test chat interface
* Test call button
* Voice preview
* Features implemented need to Integrate AI Service, Twilio Voice Call to complete

**Multi-tab Synchronization, Automatic Token Refresh, Smart Reconnection - WebSocket**

1. Automatic Token Refresh - Tokens are refreshed 5 minutes before expiry (currently tokens last 2 hours)
2. Smart Reconnection - WebSocket uses the latest token when reconnecting
3. Tab Visibility Handling - When returning to an inactive tab, the system checks if tokens need refreshing
4. Multi-tab Synchronization - Token updates in one tab are synchronized across all tabs
5. Request Queue Management - Multiple simultaneous 401 errors only trigger one refresh, preventing token refresh races

* Access tokens expire after 2 hours, refresh tokens after 7 days
* Tokens automatically refresh 5 minutes before expiry
* If a user returns to an idle tab, tokens are checked and refreshed if needed
* WebSocket automatically reconnects with fresh tokens
* Failed API calls due to expired tokens trigger automatic refresh and retry

The system now handles idle periods gracefully without keeping users connected indefinitely. When truly idle for extended periods (>2 hours), users will need to re-authenticate, which is a good security practice.

## ✅ Phase 6: Conversation Management UI

**Backend:**

1. Conversation search API (DONE)
2. Advanced analytics (DONE)
3. Export functionality (DONE)

**Frontend:**

**Conversation Interface**

1. Split-view layout
2. Real-time messages (using Phase 3 WebSocket)
3. Message input
4. ~~Media support~~

**Human Agent Message Handling**

**Flow:**

* User types and sends message
* Message appears immediately (optimistic)
* Backend saves to DB and sends via Twilio
* Frontend updates with real message ID
* If sending fails, message is removed and user is notified

**Human Agent - AI agent Handoff Capability:**

* ✅ **Warning dialog** when first human message is sent
* ✅ **Clear status indicators** showing who's in control
* ✅ **Take Full Control** button to handoff conversation
* ✅ **Return to AI** button to give control back
* ✅ **Visual badges** on messages sent during human control
* ✅ **Info messages** explaining the current state
* ✅ **Different placeholder text** based on control status

The flow is now:

1. AI is active initially
2. Human types first message → Warning dialog appears
3. User chooses to take control → Conversation handed off
4. All future messages from human, AI won't respond
5. Human can click "Return to AI" to re-enable AI responses

* ✅ Human Handoff minor bug fix

---

### ✅Phase 6.5: POSTGRESQL transition (Local) & CELERY

* ✅PostgreSQL integration completed (same as PROD)
* ✅Welcome message + SPEECH (handled by ELEVENLABS)
* ✅ELEVENLABS media files are stored locally at the moment at backend/media
  * For Twilio to access these files, ngrok is used asd.ngrok.com/media/asdb.mp3 which directs to localhost
  * NOTE: Will be fixed with the integration of Amazon S3 storage for media/audo files

---

## Phase 6.6: Test Chat agent (MID)

* ✅Test Voice: Voice selection dropdown, preview
* 🅿️Test Voice Call: Receive a phone call feature
* ✅Test Chat
* 🅿️ End chat button (when can we say the chat is done? After a few hours? Never ends from the same ? Manual end by the user?)

---

## Phase 7: Analytics DASHBOARD (NEED DEBUGGING)

**Backend:**

* ✅Metrics aggregation
* ✅Time-series data
* 🅿️Export APIs
* ✅CELERY SCHEDULER installed, tasks configured:
  * Hourly metrics (Analytics & Billing) ✅
  * Daily Metrics (Analytics & Billing) ✅
* ✅FAKE Data generated for a better view


**Frontend:**

* **✅Analytics Dashboard**

  * Overview metrics ✅
  * Charts and graphs ✅
  * Channel distribution ✅
  * Agent performance ✅

---

## Phase 8: Phone Number Purchase & Call Transfer

Backend

* Twilio API updates:
  * search_available_numbers (Voice/SMS & Whatsapp)
  * purchase_number
  * configure_webhooks
  * release_number
  * update_webhook_urls

Frontend

* Phone Number Management UI

  * List view of all organization's numbers
  * Status Badges (available/assigned)
  * Assign/Unassign buttons
  * Release number option (with confirmation)
  * Search and filter based on channel
* Phone Number Purchase Modal

  * AreaCodeSelector (with popular cities dropdown)
  * NumberTypeSelector (Local, Toll-free, Mobile)
  * CapabilitiesFilter (Voice, SMS, MMS checkboxes)
  * SearchResults list with "Buy" button
  * PurchaseConfirmation with monthly cost display
* **Modified Agent Creation Flow**

  * Step 2: Instead of manual input, show dropdown of available numbers
  * Add "Buy New Number" button that opens purchase modal
  * Validate at least one number selected
  * Show which capabilities the number supports

Phase 9: Warm Transfer & Call Management

Backend:

* Transfer Service Layer
  **-** check_business_hours**(**organization**)**
  **-** generate_call_summary**(**conversation_id**)**
  **-** initiate_warm_transfer**(**call_sid**,** transfer_to**)**
  **-** send_context_to_agent**(**phone_number**,** summary**)**
  **-** create_conference_room**(**call_sid**)**
  **-** add_participant_to_conference**(**conference_sid**,** phone_number**)**
  **-** handle_transfer_failure**(**call_sid**)**
* CallSession & CallTransfer Models
* Business Hours Checker

  * AvailabilityService:
    **-** is_within_business_hours**(**organization**)**
    **-** get_next_available_time**(**organization**)**
    **-** get_on_call_number**(**organization**)**
    **-** handle_after_hours**(**conversation**)**
* TwiML Responses for Transfer APIs:

  /api/calls/transfer/initiate

  - Creates conference room
  - Plays hold music to customer
  - Calls human agent with whisper

  /api/calls/transfer/connect

  - Bridges calls in conference
  - Starts recording if enabled

  /api/calls/transfer/fallback

  - Handles failed transfers
  - Offers callback or voicemail

- **Transfer Configuration in Settings**
  Update Organization Settings:

```javascript
EscalationSettings:
-Primary contact number
-Backup contact numbers[]
-After-hours message
-Transfer greeting template
-Auto-summary enabled:Boolean
-Include transcript:Boolean
```

* Real-time Call Status Updates

WebSocket events for:

* call.started
* call.transferring
* call.transferred
* call.completed
* transfer.failed

Call Summary Component

**CallSummaryPanel**:
Customer info
Call duration
AI confidence score
Key topics discussed
Reason **for** transfer

Suggested actions

Frontend:

**1. Live Call Dashboard Updates**
Add to existing conversation view:

* "Transfer Call" button (only shows during active calls)
* Transfer modal with options:
  * Transfer to: Dropdown of escalation contacts
  * Transfer type: Warm/Cold toggle
  * Reason: Quick select + custom input
  * Include summary: Checkbox
* Transfer status indicator
* Call duration timer

## Testing Checklist

**Day 1 Tests:**

* [ ] Can search for numbers by area code
* [ ] Can purchase a number
* [ ] Number appears in available list
* [ ] Can assign number to agent
* [ ] Webhooks properly configured
* [ ] Incoming calls route correctly

**Day 2 Tests:**

* [ ] Transfer button appears during call
* [ ] Business hours properly checked
* [ ] Call summary generated
* [ ] Human agent receives context (SMS/screen)
* [ ] Conference bridge successful
* [ ] Fallback works if transfer fails

---

Phase USAGE & Billing

Backend:

* EXPORT APIs (whole application)
* STRIPE INTEGRATION

Frontend:

* **🅿️Usage & Billing**
  * Current usage
  * Cost breakdown
  * Invoice history

🅿️Deltas for dashboard metrics needs to be updated in /overview api

🅿️FRONTEND Reusable delta component (name: )


## Phase : S3 Bucket for Audio Files + Vector Embedding Storage?

- Audio file write, get, delete
- Knowledge Base processing-> vector embedding save, retrieve, delete
- 

---

## Phase : Knowledge Base

**Backend (1 week):**

* Vector embeddings
* Semantic search
* Intent classification
* Conversation summarization
* Multi-language support

**Frontend (1 week):**

**Knowledge Base**

* Drag-drop file upload
* Document management
* Processing status
* Search documents

**AI Configuration**

* Advanced prompt editor
* Model selection
* Parameter tuning
* Training interface

---

## Phase : Registration Page

Flow:

* Page 1: Fill in basic company information
* Page 2: Upload Knowledge Base
* Page 3: Configure Agent
* Page 4: Test and Confirm
* Page 5: Ready to go dashboard

---

## Phase : Team & Collaboration

**Backend (4-5 days):**

* Team invitation system
* Role permissions
* Activity logging
* Audit trail

**Frontend (1 week):**

* **Team Management**
  * Invite members
  * Role assignment
  * Activity feed
  * Permissions UI

---

## Phase :

* Report generation
* Send emails reporting:
  * Weekly usage & analytics
  * Usage warnings

---

## Phase  : Production Optimization

**Backend (1 week):**

* Query optimization
* Caching layer (REDIS DONE)
* Rate limiting
* Error handling

**Frontend (1 week):**

* Code splitting
* Performance optimization
* PWA features

---

## Phase LAST : Deployment

**Backend (3-4 days):**

* Deployment setup

**Frontend (2 weeks):**

* CI/CD pipeline
* Production deployment
* Monitoring setup

---

---



# Future considerations:

## Phase 1: Integrations

**Backend (1.5 weeks):**

* CRM connectors
* Slack integration
* Email channel
* Zapier webhooks
* Public API

**Frontend (1 week):**

* Integration marketplace
* OAuth flows
* Webhook management
* API documentation

---
