##  System Architecture Diagram

                ┌──────────────────────────────┐
                │        User / Admin          │
                │ (Uploads Image or via API)   │
                └────────────┬─────────────────┘
                             │
                             ▼
                ┌──────────────────────────────────────┐
                │        app (Django)                  │
                │ 1. Save FaceProfile Model            │
                │ 2. Trigger Signal → Celery Task      │
                └────────────┬─────────────────────────┘
                             │
                             ▼
                ┌──────────────────────────────┐
                │       Redis Broker           │
                │ (Queue stores task info)     │
                └────────────┬─────────────────┘
                             │
                             ▼
                ┌──────────────────────────────────────┐
                │      Celery Worker                   │
                │ 1. Pulls task from Redis             │
                │ 2. Loads image from media_files      │
                │ 3. Calculates face embedding         │
                │ 4. Updates Postgres DB               │
                └────────────┬─────────────────────────┘
                             │
                             ▼
                ┌──────────────────────────────┐
                │        Postgres DB           │
                │ (Stores embeddings, profiles)│
                └────────────┬─────────────────┘
                             │
                             ▼
                ┌──────────────────────────────┐
                │      media_files Volume      │
                │ (Shared between app & worker)│
                └──────────────────────────────┘

────────────────────────────────────────────────────────────

                [ LIVE RECOGNITION FLOW ]

────────────────────────────────────────────────────────────

                ┌──────────────────────────────┐
                │     Frontend (Browser)       │
                │ (Sends camera stream frames) │
                └────────────┬─────────────────┘
                             │
                             ▼
                ┌──────────────────────────────────────┐
                │       app (Django)                   │
                │ 1. Receives video frames             │
                │ 2. Detects faces & computes embeds   │
                │ 3. Compares with DB embeddings       │
                │ 4. Logs result in AccessLog          │
                │ 5. Sends recognition result          │
                └────────────┬─────────────────────────┘
                             │
                             ▼
                ┌──────────────────────────────┐
                │        Postgres DB           │
                │ (Profiles + Access Logs)     │
                └────────────┬─────────────────┘
                             │
                             ▼
                ┌──────────────────────────────┐
                │       Frontend (Browser)     │
                │ (Displays boxes & names)     │
                └──────────────────────────────┘
