# Vetal OTT Platform — "Pyzilla"

A curated dark-cinema streaming platform: a Netflix-style frontend serving a small, hand-picked library of psychological, cult-classic, and rare arthouse films, hosted on AWS EC2 with media delivered securely from S3.

## Architecture

```
Browser (movie grid / modal player)
        │
        ▼
EC2 instance (Node.js + Express, managed by PM2)
        │
        ├── GET /api/movies        → returns text metadata only
        ├── GET /api/stream/:id    → generates short-lived pre-signed S3 URLs
        │
        ▼
Private S3 bucket (movie/ prefix)
        - video files (.mp4)
        - poster images (.jpg)
```

- **EC2** runs the Express server, kept alive and auto-restarted via **PM2**
- **IAM role** attached to the EC2 instance grants `s3:GetObject` on the media bucket — no hardcoded AWS credentials anywhere in the app
- **S3 pre-signed URLs** are generated per-request with a short expiry (default 1 hour), so the bucket itself can stay fully private instead of being world-readable

## How this was implemented

- **Frontend built first as a static single-page site** (`public/index.html`) — a Netflix-style hero banner, movie grid, and modal video player, styled with a dark red/black theme and `Bebas Neue`/`DM Serif Display`/`Inter` fonts. Originally it referenced S3 object URLs directly by hardcoded path.
- **Metadata separated from media.** `data/movies.json` holds only text (title, year, rating, genre tags, description) plus the *filenames* of the corresponding poster/video objects in S3 — never the files themselves. This lets the backend and frontend both reference the same movie list without either one embedding copyrighted assets.
- **Pre-signed URL endpoint added** (`GET /api/stream/:movieId`) so the S3 bucket can be locked down to fully private, with access granted only per-request and only for a limited time window, using `@aws-sdk/s3-request-presigner`. This was the piece that turns "S3 bucket serving static files" into "secure media delivery."
- **IAM role over static credentials.** The EC2 instance is launched with an IAM role attached (rather than `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY` baked into the app), so the AWS SDK picks up temporary credentials automatically from the instance metadata service. `.env.example` documents this — credentials are only needed if running outside EC2.
- **PM2 instead of a raw `node server.js` process** so the app survives EC2 reboots, SSH disconnects, and crashes — configured via `ecosystem.config.js` with `autorestart: true` and a memory-based restart guard.

## Prerequisites

- An EC2 instance (Amazon Linux 2023 recommended) with Node.js 18+ installed
- An S3 bucket for media storage
- An IAM role attached to the EC2 instance with a policy granting `s3:GetObject` on the bucket (see below)
- Your own licensed movie files to upload

### Example IAM policy for the EC2 role

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:GetObject"],
      "Resource": "arn:aws:s3:::YOUR_BUCKET_NAME/movie/*"
    }
  ]
}
```

## Setup

```bash
git clone <this-repo-url>
cd vetal-ott-platform
npm install
cp .env.example .env
# edit .env with your bucket name and region
```

## Uploading your own media

Upload video and poster files directly to S3 (never through this repo):

```bash
aws s3 cp your-movie.mp4 s3://YOUR_BUCKET_NAME/movie/your-movie.mp4
aws s3 cp your-poster.jpg s3://YOUR_BUCKET_NAME/movie/your-poster.jpg
```

Then add a matching entry to `data/movies.json`:

```json
"your-movie-id": {
  "title": "Your Movie Title",
  "year": "2020",
  "rating": "★ 8.0",
  "match": "90% Match",
  "genre": ["Genre1", "Genre2"],
  "desc": "Short description.",
  "videoKey": "your-movie.mp4",
  "posterKey": "your-poster.jpg"
}
```

## Running locally

```bash
npm start
```

Visit `http://localhost:3000`.

## Running on EC2 with PM2

```bash
npm install -g pm2
npm install
pm2 start ecosystem.config.js
pm2 save
pm2 startup   # follow the printed command to enable PM2 on reboot
```

Useful PM2 commands:
```bash
pm2 status
pm2 logs pyzilla
pm2 restart pyzilla
```

## Project structure

```
vetal-ott-platform/
├── server.js               # Express server + pre-signed URL API
├── data/
│   └── movies.json          # Text metadata only — no media
├── public/
│   └── index.html            # Frontend (grid, hero, modal player)
├── ecosystem.config.js      # PM2 process config
├── package.json
├── .env.example
├── .gitignore                # Excludes node_modules, .env, and all media file types
└── README.md
```

## What this project demonstrates

| Concept | How it's shown |
|---|---|
| Secure, time-limited media delivery | S3 pre-signed URLs via `@aws-sdk/s3-request-presigner` |
| Credential-less AWS access from EC2 | IAM instance role instead of hardcoded keys |
| Process management / uptime | PM2 with auto-restart |
| Separating metadata from binary assets | `movies.json` (text) vs. S3 (media) |
| Static frontend + lightweight API backend | Express serving both `public/` and JSON endpoints |
