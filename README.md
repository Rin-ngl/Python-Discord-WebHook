# Dishook

A dark-themed GUI application built with Python and CustomTkinter for sending messages to Discord channels via webhooks.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue) ![License](https://img.shields.io/badge/License-MIT-green) ![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)

## Features

*   **Dark UI:** Clean interface using CustomTkinter.
*   **Rich Embed Builder:** Full support for titles, descriptions, URLs, colors, authors, footers, and thumbnails.
*   **Color Picker:** Built-in visual color selector for embed accents.
*   **File Attachments:** Easily attach images or documents to your messages.
*   **Identity Override:** Custom bot usernames and avatars on a per-message basis.
*   **Auto-Save:** Automatically remembers your last 10 used Webhook URLs.
*   **Tabbed Interface:** Organize your workflow with separate tabs for Content, Embed Settings, and Fields.

## Installation

### Prerequisites
*   Python 3.8 or higher

### Setup
1.  **Clone or Download** this repository.
2.  **Install dependencies** using pip:

```bash
pip install customtkinter discord-webhook
```

## Usage

### 1. Get your Webhook URL
If you haven't created a webhook yet:
1.  Open Discord and go to your server.
2.  Right-click a channel ➞ **Edit Channel**.
3.  Select **Integrations** ➞ **Webhooks**.
4.  Click **New Webhook**.
5.  Click **Copy Webhook URL**.

### 2. Sending a Message
1.  **Launch the App:** Run the script (`python your_script_name.py`).
2.  **Configure:** Paste your Webhook URL in the top field (and click "Save URL" to keep it).
3.  **Compose:**
    *   **Message Content Tab:** Type a standard message or attach a file.
    *   **Embed Settings Tab:** Create rich content (Titles, Colors, Images).
    *   **Embed Fields Tab:** Add inline data fields (great for stats or lists).
4.  **Send:** Click **🚀 Send Message**.

## Configuration Details

| Feature | Description |
| :--- | :--- |
| **Bot Name** | Overrides the default name of the webhook for this specific message. |
| **Avatar URL** | Overrides the default avatar (link to a `.png` or `.jpg`). |
| **Colors** | Accepts Hex codes (e.g., `#FF0000`) or use the color picker button. |
| **Embed Fields** | Click `+ Add Field` to add dynamic rows of data. "In" checkbox makes them inline. |

## Troubleshooting

*   **App Freezes?** Check your damn internet connection.
*   **Error 404:** The Webhook URL is invalid or the webhook was deleted on Discord.
*   **Error 400:** The payload is malformed (e.g., sending an empty message without an attachment).
*   **"Missing Dependency"**: Ensure you ran the pip install command listed above.

## Contributing
Feel free to fork this project and submit pull requests. Suggestions for new features (like multi-webhook broadcasting) are welcome!

---
*Note: Keep your Webhook URL private! Anyone with the URL can send messages to your channel.*
