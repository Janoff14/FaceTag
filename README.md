# FaceTag

Office entrance kiosk that loops promo videos and greets registered people by name using on-device face recognition.

## Setup

1. Create and activate a Python 3.11+ virtual environment.
2. Install the pinned dependencies:

   ```powershell
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```

3. Copy the safe config template and fill local-only values:

   ```powershell
   Copy-Item config.yaml.example config.yaml
   ```

   Edit `config.yaml` and replace `PASTE_BOT_TOKEN_HERE` with your Telegram bot token. Real tokens and admin chat IDs belong in `config.yaml` only — it is gitignored and must never be committed.

4. Copy the tracked seed promo into the local playlist folder before running the player locally:

   ```powershell
   Copy-Item tests\assets\seed-promo.mp4 videos\seed-promo.mp4
   ```

5. Run the app entry point:

   ```powershell
   python run.py
   ```

## Architecture

```text
run.py supervisor
|-- player process: fullscreen looping videos from videos/
|-- recognition worker: camera frames -> face embeddings -> greeting queue
`-- Telegram bot subprocess: admin commands -> shared local writers
```

The MVP keeps all face photos and biometric embeddings on the demo machine. The only planned outbound network path is Telegram API access by the admin bot.

## Selection Strategy

When multiple registered people are visible, the planned selection rule is largest face wins. This chooses the person closest to the camera and keeps the greeting behavior predictable for a lobby display.

## Threading Model

Recognition work runs outside the Qt player loop. The planned architecture uses a separate recognition process so dlib CPU work cannot stall fullscreen video playback, while the player receives only greeting events through a queue.

## Benchmark Results

Pending Story 4.3. The final README will include the latest `benchmark.py` output with p50/p95 recognition latency, true-positive rate, false-positive rate, tolerance, and seed-set details.
