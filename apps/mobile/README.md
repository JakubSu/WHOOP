# WHOOP mobile (v0.1)

Expo React Native companion app. The signed-in experience is a single Today screen with WHOOP recovery, sleep, and strain rings above today's planned workout and its exercises.

## Run locally

1. Install dependencies with `npm install` from this directory.
2. Set `EXPO_PUBLIC_API_BASE_URL` to the API origin reachable from the device, ending in `/api/v1`.
   - iOS simulator: `http://localhost:8000/api/v1`
   - Android emulator: `http://10.0.2.2:8000/api/v1`
   - Physical device: use your development machine's LAN address, or a reachable HTTPS API.
3. Start the API, then run `npx expo run:ios` or `npx expo run:android`.

The app uses a custom `whoopmobile://` callback scheme for WHOOP OAuth. OAuth requires a development/native build; the callback deep link is not configured for Expo Go. The Django setting `WHOOP_FRONTEND_ALLOWED_ORIGINS` must include `whoopmobile://connect-whoop` (the default local setting and `.env.example` include it). Configure the same allowlist entry in deployed environments before connecting WHOOP there.

Session access and refresh tokens are stored in Expo SecureStore. The app sends the refresh token in the request body, so mobile session refresh does not depend on browser cookies.
