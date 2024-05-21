from tkinter import *
from discord_webhook import DiscordWebhook

def send_message(event=None):
    # Get message from entry box
    message = message_entry.get("1.0", END).strip()
    # Check if message is empty
    if not message:
        message_label.config(text="Message cannot be empty")
        return

    # Send message using webhook
    try:
        webhook = DiscordWebhook(url=webhook_url.get(), content=message)
        response = webhook.execute()
        if response.status_code == 200:
            message_entry.delete("1.0", END)  # Clear entry box
            message_label.config(text="Message sent successfully!")
        else:
            message_label.config(text=f"Failed to send message. Status code: {response.status_code}")
    except Exception as e:
        message_label.config(text=f"An error occurred: {e}")

def on_enter(event):
    send_message()
    return "break"  # Prevent default behavior

def on_shift_enter(event):
    message_entry.insert(INSERT, '\n')
    return "break"  # Prevent default behavior

# Create main window
window = Tk()
window.title("Discord Message Sender")
window.geometry("300x200")  # Set window size

# Create label for webhook URL
webhook_label = Label(window, text="Discord Webhook URL:")
webhook_label.pack()

# Create entry box for webhook URL
webhook_url = StringVar()
webhook_entry = Entry(window, textvariable=webhook_url, width=50)
webhook_entry.pack()

# Create label for message
message_label = Label(window, text="")
message_label.pack()

# Create entry box for message
message_entry = Text(window, width=100, height=5)
message_entry.pack()

# Bind key press events
message_entry.bind("<Return>", on_enter)
message_entry.bind("<Shift-Return>", on_shift_enter)

# Create button to send message
send_button = Button(window, text="Send", command=send_message)
send_button.pack()

window.mainloop()
