# Google OAuth Setup Guide

## Paso 1: Habilitar APIs en Google Cloud Console

1. Ve a [Google Cloud Console](https://console.cloud.google.com)
2. Selecciona tu proyecto: `proyecto-ai-campaign-manager`
3. Ve a **APIs & Services** > **Library**
4. Busca y habilita:
   - **Google Sheets API**
   - **Google Drive API**

## Paso 2: Crear Credenciales OAuth 2.0

1. Ve a **APIs & Services** > **Credentials**
2. Click en **+ CREATE CREDENTIALS** > **OAuth client ID**
3. Si te pide configurar la pantalla de consentimiento:
   - Click en **CONFIGURE CONSENT SCREEN**
   - Selecciona **External** (para testing)
   - Completa:
     - App name: `AI Campaign Manager`
     - User support email: tu email
     - Developer contact: tu email
   - Click **SAVE AND CONTINUE**
   - En **Scopes**, click **ADD OR REMOVE SCOPES** y agrega:
     - `https://www.googleapis.com/auth/spreadsheets`
     - `https://www.googleapis.com/auth/drive.file`
   - Click **SAVE AND CONTINUE**
   - En **Test users**, agrega tu email
   - Click **SAVE AND CONTINUE**

4. Vuelve a **Credentials** > **+ CREATE CREDENTIALS** > **OAuth client ID**
5. Selecciona:
   - Application type: **Web application**
   - Name: `Dashboard OAuth Client`
   - Authorized JavaScript origins:
     - `http://localhost:5173`
     - `http://localhost:8080`
   - Authorized redirect URIs:
     - `http://localhost:8080/api/auth/google/callback`
6. Click **CREATE**
7. **IMPORTANTE**: Descarga el JSON de credenciales
   - Guárdalo como `google_oauth_credentials.json` en:
     `/Users/francislock/Desktop/FLC - Antigravity/AI Campaign Manager/arbitrage-dashboard/backend/`

## Paso 3: Configurar Variables de Entorno

Agrega a tu archivo `.env`:

```bash
GOOGLE_OAUTH_CLIENT_ID=tu_client_id_aqui
GOOGLE_OAUTH_CLIENT_SECRET=tu_client_secret_aqui
GOOGLE_OAUTH_REDIRECT_URI=http://localhost:8080/api/auth/google/callback
```

## Paso 4: Verificación

Una vez completados estos pasos, avísame y continuaré con la implementación del código.

## Notas Importantes

- Durante el desarrollo, la app estará en modo "Testing"
- Solo los usuarios agregados en "Test users" podrán autenticarse
- Para producción, necesitarás solicitar verificación de Google
