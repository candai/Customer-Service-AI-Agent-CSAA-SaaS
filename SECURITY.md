# Security Policy

## ⚠️ CRITICAL: Environment Variables & Secrets

This repository contains sensitive configuration. Please follow these guidelines:

### Setup Instructions

#### Backend Setup
1. Copy `backend/.env.example` to `backend/.env`
   ```bash
   cp backend/.env.example backend/.env
   ```
2. Fill in all the values with your actual credentials
3. **NEVER** commit `backend/.env` to version control

#### Frontend Setup
1. Copy `frontend/.env.example` to `frontend/.env.local`
   ```bash
   cp frontend/.env.example frontend/.env.local
   ```
2. Fill in all the values with your actual configuration
3. **NEVER** commit `frontend/.env.local` to version control

### Environment Variables Required

**Backend (.env):**
- `SECRET_KEY` - Django secret key (generate a new one with Django's `get_random_secret_key()`)
- `DEBUG` - Set to `False` in production
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `OPENAI_API_KEY` - OpenAI API key
- `TWILIO_ACCOUNT_SID` - Twilio account SID
- `TWILIO_AUTH_TOKEN` - Twilio auth token
- `ELEVENLABS_API_KEY` - ElevenLabs API key
- `AWS_ACCESS_KEY_ID` - AWS access key (if using S3)
- `AWS_SECRET_ACCESS_KEY` - AWS secret key (if using S3)

**Frontend (.env.local):**
- `NEXT_PUBLIC_API_URL` - Backend API URL
- `NEXT_PUBLIC_WS_URL` - Backend WebSocket URL

### ✅ Best Practices

1. **Never hardcode secrets** in source code
2. **Use `.gitignore`** to exclude `.env` files from version control
3. **Use `.env.example`** files as templates for team members
4. **Rotate credentials regularly** especially if exposed
5. **Use a secrets manager** for production (e.g., AWS Secrets Manager, HashiCorp Vault)
6. **Limit API key scope** - rotate keys, set expiration dates where possible
7. **Use environment-specific files** (`.env.local`, `.env.production`, etc.)

### Secrets Manager Recommendations

For production deployments:
- **AWS**: AWS Secrets Manager or AWS Systems Manager Parameter Store
- **Heroku/Railway**: Built-in environment variable management
- **Docker**: Use Docker secrets
- **Kubernetes**: Use Kubernetes secrets
- **General**: HashiCorp Vault, Doppler, or similar

### Git History Cleanup

If secrets were accidentally committed, remove them from history:

```bash
# Using BFG (recommended)
bfg --delete-files backend/.env

# Or using git-filter-branch
git filter-branch --tree-filter 'rm -f backend/.env' HEAD
```

### Reporting Security Issues

If you discover a security vulnerability, please:
1. **DO NOT** open a public GitHub issue
2. Email security details to: [add your security contact]
3. Include description and reproduction steps
4. Allow time for a fix before public disclosure

### Checklist for Contributors

- [ ] Copy `.env.example` files to `.env` or `.env.local`
- [ ] Fill in your local configuration
- [ ] **Never** commit `.env` files
- [ ] Run `git status` before committing to ensure no `.env` files are staged
- [ ] If you accidentally commit a secret, rotate it immediately

---

**Last Updated**: 2026-09-01
