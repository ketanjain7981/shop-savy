# Archived

This repo has been archived. For a Pipecat client / server example, please checkout the [Simple Chatbot example](https://github.com/pipecat-ai/pipecat/tree/main/examples/simple-chatbot) in the `pipecat` repo.

# Pipecat Client Web UI


Some docs regarding how all this fits together: [here](/docs/)

## Getting setup


Install deps and build the UI:

```
mv env.example .env.development.local
yarn 
yarn run build

```

Navigate to https://localhost:5173

## Configuring your env

### Environment Variables

Only the following environment variables are required:

`VITE_APP_TITLE`

Name of your bot e.g. "Simple Chatbot" (shown in HTML and intro)

`VITE_SERVER_URL`

A server URL to trigger when starting a session (e.g. a Pipecat bot_runner) that instantiates a new agent at the specified room URL. Note: If this is not set, the app will assume you will manually start your bot at the same room URL (and show a warning on the config screen in dev mode.)

### Backend Configuration

All other configuration options are now managed through the backend `/config` endpoint. This provides a centralized way to configure the application without having to modify environment variables.

The following settings are now configured from the backend:

- `manual_room_entry` - Disable automatic room creation. User must enter a room URL to join or pass through `room_url` query string.
- `open_mic` - Can the user speak freely, or do they need to wait their turn?
- `user_video` - Does the app require the user's webcam?
- `show_splash` - Show an initial splash screen (Splash.tsx).
- `show_config` - Show demo config options first.
- `app_title` - Name of your bot (overrides VITE_APP_TITLE if provided).

To modify these settings, update the `/config` endpoint in the backend `main.py` file.

`VITE_SHOW_CONFIG`

Show app settings before device configuration, useful for debugging.

`VITE_OPEN_MIC`

Not currently in use

`VITE_USER_VIDEO`

Not currently in use


## What libraries does this use?

### Vite / React

We've used [Vite](https://vitejs.dev/) to simplify the development and build experience. 

### Tailwind CSS

We use [Tailwind](https://tailwindcss.com/) so the UI is easy to theme quickly, and reduce the number of CSS classes used throughout the project.

### Radix

For interactive components, we make use of [Radix](https://www.radix-ui.com/).

