# Paibot

Paibot is a Discord bot built with the `discord.py` library. It includes features such as responding to messages with specific keywords, sending scheduled announcements, and various other tools tailored for programming communities.

---

## Features

- **Automated Responses**: The bot detects keywords in messages and replies with customizable responses.
- **Scheduled Tasks**: Sends announcements in specified channels at scheduled times.
- **Image Support**: Replies can include images based on configurations.
- **Cooldown Control**: Prevents repetitive responses to the same user in a short time frame.
- **Extensible**: Easily add new commands and events.
- **Dockerized**: Simple setup with Docker for running in isolated environments.

---

## Installation

### Prerequisites

Make sure you have Python 3.8+ and Docker (optional) installed on your machine.

### Environment Variables

Create a `.env` file in the project's root directory with the following variables:

```bash
cat .env_example > .env
```

The .env file should contain:

```bash
CLIENT_ID=
TOKEN=
IMG_PATH=./assets/
ANNOUNCE_CHANNEL_ID=
```

- `CLIENT_ID`: The Discord application's client ID.
- `TOKEN`: The bot's token.
- `IMG_PATH`: The path to the directory containing images.
- `ANNOUNCE_CHANNEL_ID`: The ID of the channel where announcements will be sent.

Installing Dependencies

Use the pip package manager to install the required dependencies:

```bash
pip install -r requirements.txt
```

### Docker

Alternatively, you can use Docker to run the bot in an isolated environment:

```bash
docker compose up
```

Usage

To run the bot locally, execute:

```bash
python bot.py
```

Available Commands

- Custom Commands: Add keywords and automated responses via configuration files.
- Scheduled Task Management: Control message delivery at predefined time intervals.
- !http <status_code>: Returns the description of an HTTP status code.
- Additional Commands: Easily extend functionalities with new extensions and cogs.