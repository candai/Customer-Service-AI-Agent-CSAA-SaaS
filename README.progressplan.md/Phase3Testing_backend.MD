### Phase 3 Testing

#### 3 Terminals

1. **python manage.py runserver**
2. **redis-server**
   1. localhost:6379
3. **ngrok http 8000**
   1. **NOTE: Ngrok url changes every run, update twilio webhook URLs accordingly!!!!!**
4. **python -m http.server 3000 ** desktop terminal
   1. move the test_websocket_send_whatsapp.html to desktop
   2. load it in browser
   3. send a whatsapp message
   4. voice call twilio number

#### Tested:

1. Voice
2. Whatsapp


Success:

Backend is completed with webhooks
