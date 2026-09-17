# fireguard-frontend

The frontend application for the FireGuardAI platform, built with React, TypeScript, Vite, and Tailwind CSS.

## Prerequisites

### For local development

Install:

- Node.js
- npm
- Git

Verify the installation:

```bash
node --version
npm --version
git --version
```

### For Docker

Install and start:

- Docker Desktop

Verify Docker:

```bash
docker --version
docker compose version
```

## Environment Configuration

Create a `.env` file in the project root.

```env
VITE_API_BASE_URL=http://localhost:8020
```

`VITE_API_BASE_URL` is the URL of the FireGuardAI backend API.

Do not commit `.env` files containing environment-specific values or secrets.

The repository includes `.env.example` as the environment configuration template.

## Run Locally

Clone the repository:

```bash
git clone https://github.com/FireGuardAI/fireguard-frontend.git
cd fireguard-frontend
```

Switch to the development branch if required:

```bash
git switch dev
```

Install the exact dependencies from the lock file:

```bash
npm ci
```

Create the environment file:

```powershell
Copy-Item .env.example .env
```

Start the development server:

```bash
npm run dev
```

The application will normally be available at:

```text
http://localhost:5173
```

### Available Routes

Login:

```text
http://localhost:5173/login
```

Dashboard:

```text
http://localhost:5173/dashboard
```

The root path redirects to the login page:

```text
http://localhost:5173/
```

Stop the development server with:

```text
Ctrl + C
```

## Build the Application

Create a production build:

```bash
npm run build
```

The generated production files are placed in:

```text
dist/
```

Preview the production build locally:

```bash
npm run preview
```

## Run with Docker

Make sure Docker Desktop is running.

Create the environment file:

```powershell
Copy-Item .env.example .env
```

Build the Docker image and start the container:

```bash
docker compose up -d --build
```

The Dockerized frontend will be available at:

```text
http://localhost:3000
```

### Test the Docker Application

Open:

```text
http://localhost:3000
```

Login page:

```text
http://localhost:3000/login
```

Dashboard:

```text
http://localhost:3000/dashboard
```

### Check the Container

```bash
docker ps
```

The frontend container should appear as:

```text
fireguard-frontend-app
```

### View Container Logs

```bash
docker compose logs -f frontend
```

Press `Ctrl + C` to stop following the logs.

### Stop the Container

```bash
docker compose down
```

### Restart the Container

```bash
docker compose up -d
```

### Rebuild After Code Changes

When frontend code or dependencies change:

```bash
docker compose down
docker compose up -d --build
```

## Docker Configuration

The frontend uses a multi-stage Docker build:

1. Node.js builds the React/Vite application.
2. Nginx serves the generated production files.

The Docker container exposes port `80` internally and maps it to port `3000` on the host.

```text
Host
3000
  |
  v
Docker
80
  |
  v
Nginx
  |
  v
React application
```

## Project Structure

```text
src/
├── common/
│   ├── components/
│   ├── config/
│   ├── hooks/
│   ├── layouts/
│   ├── services/
│   ├── types/
│   └── utils/
│
├── modules/
│   ├── auth/
│   │   └── pages/
│   │       └── LoginPage.tsx
│   │
│   └── dashboard/
│       └── pages/
│           └── DashboardPage.tsx
│
├── App.tsx
├── index.css
└── main.tsx
```

## Technology Stack

- React
- TypeScript
- Vite
- Tailwind CSS
- React Router
- Nginx
- Docker

## Git Development

Development work is performed on the `dev` branch.

Check the current branch:

```bash
git branch --show-current
```

Check changes:

```bash
git status
```

Pull the latest changes:

```bash
git pull
```

Stage changes:

```bash
git add .
```

Create a commit:

```bash
git commit -m "feat: describe your change"
```

Push changes:

```bash
git push
```

## Ports

| Service | Port |
|---|---:|
| Frontend development server | `5173` |
| Frontend Docker container | `3000` |
| FireGuardAI backend API | `8020` |

## Quick Start with Docker

For a quick Docker setup:

```powershell
git clone https://github.com/FireGuardAI/fireguard-frontend.git
cd fireguard-frontend
Copy-Item .env.example .env
docker compose up -d --build
```

Then open:

```text
http://localhost:3000
```

To stop:

```bash
docker compose down
```
