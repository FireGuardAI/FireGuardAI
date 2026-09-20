const API_BASE_URL = import.meta.env.VITE_API_BASE_URL

// Vite inlines VITE_* variables at BUILD time, not at container start time.
// If this is missing, every fetch call below would otherwise fall back to a
// same-origin relative request — which, behind the frontend's own nginx
// container, surfaces as a confusing "405 Not Allowed" instead of a clear
// "can't reach the API" error. Log it loudly here so it's obvious in devtools.
if (!API_BASE_URL) {
  console.error(
    '[fireguard-frontend] VITE_API_BASE_URL is not set. Create fireguard-frontend/.env from ' +
      '.env.example and rebuild the Docker image (docker compose up -d --build) — a plain ' +
      '"up -d" reuses the already-built image with the missing value baked in.',
  )
}

export const env = {
  apiBaseUrl: API_BASE_URL ?? '',
}