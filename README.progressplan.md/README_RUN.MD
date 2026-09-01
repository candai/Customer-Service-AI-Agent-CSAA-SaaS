1. POSTGRESQL
   1. Luron_PostgreSQL port 5432
2. backend terminal
   1. **daphne -b 127.0.0.1 -p 8000 core.asgi:application**
   2. http://localhost:3000/
3. Terminal: Open local websockets to www
   1. **ngrok http http://localhost:8000**
4. Redis terminal
   1. **redis-server**
5. Celery terminals 3:
   1. **celery -A core worker -l info**
   2. celery beat: **celery -A core beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler**
   3. **celery -A core flower**
6. Frontend
   1. npm run dev

Libraries:

1. https://ui.shadcn.com/charts/line#charts
2. https://lucide.dev/icons/funnel-plus
3. https://elevenlabs.io/app/sign-in?redirect=%2Fapp%2Fsubscription
4. https://useautumn.com/
5. Twilio Console
   1. Manage Phone Numbers
      1. set webhooks
   2. Configure Whatsapp
      1. set webhooks
2.
