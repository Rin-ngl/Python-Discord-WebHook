import customtkinter as ctk
from tkinter import filedialog, messagebox
import json
import os
from datetime import datetime
from PIL import Image
import requests
from io import BytesIO

# Check for discord_webhook library
try:
    from discord_webhook import DiscordWebhook, DiscordEmbed
    WEBHOOK_AVAILABLE = True
except ImportError:
    WEBHOOK_AVAILABLE = False
    print("Error: discord-webhook library not found!")
    print("Please install it with: pip install discord-webhook")

class DiscordWebhookSender:
    def __init__(self, root):
        self.root = root
        self.root.title("Discord Webhook Sender Pro")
        self.root.geometry("800x900")
        
        # Check if library is available
        if not WEBHOOK_AVAILABLE:
            messagebox.showerror(
                "Missing Dependency", 
                "discord-webhook library not found!\n\n"
                "Please install it with:\n"
                "pip install discord-webhook"
            )
            self.root.destroy()
            return
        
        # Set theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Config file for saving webhook URL
        self.config_file = "webhook_config.json"
        self.load_config()
        
        # Store file paths
        self.attachment_path = None
        self.avatar_url = None
        
        self.setup_ui()
        
    def load_config(self):
        """Load saved webhook URLs from config file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.saved_webhooks = config.get('webhooks', [])
            else:
                self.saved_webhooks = []
        except Exception:
            self.saved_webhooks = []
    
    def save_config(self):
        """Save webhook URLs to config file"""
        try:
            webhook_url = self.webhook_var.get()
            if webhook_url and webhook_url not in self.saved_webhooks:
                self.saved_webhooks.append(webhook_url)
                # Keep only last 10 webhooks
                self.saved_webhooks = self.saved_webhooks[-10:]
                self.webhook_combo.configure(values=self.saved_webhooks)
            
            with open(self.config_file, 'w') as f:
                json.dump({'webhooks': self.saved_webhooks}, f)
        except Exception as e:
            print(f"Failed to save config: {e}")
    
    def setup_ui(self):
        """Create and layout all UI elements"""
        # Create scrollable frame
        self.main_frame = ctk.CTkScrollableFrame(self.root)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Webhook Configuration Section
        webhook_frame = ctk.CTkFrame(self.main_frame)
        webhook_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(webhook_frame, text="Webhook URL:", font=("Arial", 14, "bold")).pack(anchor="w", padx=10, pady=(10, 5))
        
        webhook_input_frame = ctk.CTkFrame(webhook_frame)
        webhook_input_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        self.webhook_var = ctk.StringVar(value=self.saved_webhooks[-1] if self.saved_webhooks else "")
        self.webhook_combo = ctk.CTkComboBox(
            webhook_input_frame, 
            variable=self.webhook_var,
            values=self.saved_webhooks,
            width=500
        )
        self.webhook_combo.pack(side="left", padx=(0, 10), fill="x", expand=True)
        
        ctk.CTkButton(webhook_input_frame, text="Save", command=self.save_config, width=80).pack(side="left")
        
        # Bot Settings Section
        bot_frame = ctk.CTkFrame(self.main_frame)
        bot_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(bot_frame, text="Bot Settings:", font=("Arial", 14, "bold")).pack(anchor="w", padx=10, pady=(10, 5))
        
        bot_input_frame = ctk.CTkFrame(bot_frame)
        bot_input_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        ctk.CTkLabel(bot_input_frame, text="Username:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.username_var = ctk.StringVar()
        ctk.CTkEntry(bot_input_frame, textvariable=self.username_var, width=200).grid(row=0, column=1, padx=10, pady=5)
        
        ctk.CTkLabel(bot_input_frame, text="Avatar URL:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.avatar_var = ctk.StringVar()
        ctk.CTkEntry(bot_input_frame, textvariable=self.avatar_var, width=200).grid(row=1, column=1, padx=10, pady=5)
        
        # Message Type Selection
        message_type_frame = ctk.CTkFrame(self.main_frame)
        message_type_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(message_type_frame, text="Message Type:", font=("Arial", 14, "bold")).pack(anchor="w", padx=10, pady=(10, 5))
        
        self.message_type = ctk.StringVar(value="simple")
        
        type_buttons = ctk.CTkFrame(message_type_frame)
        type_buttons.pack(fill="x", padx=10, pady=(0, 10))
        
        ctk.CTkRadioButton(type_buttons, text="Simple Message", variable=self.message_type, 
                          value="simple", command=self.toggle_message_type).pack(side="left", padx=10)
        ctk.CTkRadioButton(type_buttons, text="Embed Message", variable=self.message_type, 
                          value="embed", command=self.toggle_message_type).pack(side="left", padx=10)
        
        # Simple Message Section
        self.simple_frame = ctk.CTkFrame(self.main_frame)
        self.simple_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(self.simple_frame, text="Message Content:", font=("Arial", 14, "bold")).pack(anchor="w", padx=10, pady=(10, 5))
        
        self.message_text = ctk.CTkTextbox(self.simple_frame, height=150, wrap="word")
        self.message_text.pack(fill="both", expand=True, padx=10, pady=(0, 5))
        self.message_text.bind('<KeyRelease>', self.update_char_count)
        
        self.char_count_label = ctk.CTkLabel(self.simple_frame, text="0 / 2000 characters", text_color="gray")
        self.char_count_label.pack(anchor="e", padx=10, pady=(0, 10))
        
        # Embed Message Section
        self.embed_frame = ctk.CTkFrame(self.main_frame)
        
        ctk.CTkLabel(self.embed_frame, text="Embed Configuration:", font=("Arial", 14, "bold")).pack(anchor="w", padx=10, pady=(10, 5))
        
        # Embed fields in grid
        embed_grid = ctk.CTkFrame(self.embed_frame)
        embed_grid.pack(fill="x", padx=10, pady=(0, 10))
        
        # Row 0: Title
        ctk.CTkLabel(embed_grid, text="Title:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.embed_title_var = ctk.StringVar()
        ctk.CTkEntry(embed_grid, textvariable=self.embed_title_var, width=300).grid(row=0, column=1, padx=10, pady=5, columnspan=2, sticky="ew")
        
        # Row 1: URL
        ctk.CTkLabel(embed_grid, text="Title URL:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.embed_url_var = ctk.StringVar()
        ctk.CTkEntry(embed_grid, textvariable=self.embed_url_var, width=300).grid(row=1, column=1, padx=10, pady=5, columnspan=2, sticky="ew")
        
        # Row 2: Color and Timestamp
        ctk.CTkLabel(embed_grid, text="Color (hex):").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.embed_color_var = ctk.StringVar(value="#5865F2")
        ctk.CTkEntry(embed_grid, textvariable=self.embed_color_var, width=120).grid(row=2, column=1, padx=10, pady=5, sticky="w")
        
        self.timestamp_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(embed_grid, text="Add Timestamp", variable=self.timestamp_var).grid(row=2, column=2, padx=10, pady=5, sticky="w")
        
        # Row 3: Description
        ctk.CTkLabel(embed_grid, text="Description:").grid(row=3, column=0, padx=10, pady=5, sticky="nw")
        self.embed_desc_text = ctk.CTkTextbox(embed_grid, height=100, width=300)
        self.embed_desc_text.grid(row=3, column=1, padx=10, pady=5, columnspan=2, sticky="ew")
        
        # Row 4: Author
        ctk.CTkLabel(embed_grid, text="Author Name:").grid(row=4, column=0, padx=10, pady=5, sticky="w")
        self.embed_author_var = ctk.StringVar()
        ctk.CTkEntry(embed_grid, textvariable=self.embed_author_var, width=300).grid(row=4, column=1, padx=10, pady=5, columnspan=2, sticky="ew")
        
        # Row 5: Author URL and Icon
        ctk.CTkLabel(embed_grid, text="Author URL:").grid(row=5, column=0, padx=10, pady=5, sticky="w")
        self.embed_author_url_var = ctk.StringVar()
        ctk.CTkEntry(embed_grid, textvariable=self.embed_author_url_var, width=150).grid(row=5, column=1, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(embed_grid, text="Icon URL:").grid(row=5, column=2, padx=10, pady=5, sticky="w")
        self.embed_author_icon_var = ctk.StringVar()
        ctk.CTkEntry(embed_grid, textvariable=self.embed_author_icon_var, width=150).grid(row=5, column=3, padx=10, pady=5, sticky="ew")
        
        # Row 6: Footer
        ctk.CTkLabel(embed_grid, text="Footer Text:").grid(row=6, column=0, padx=10, pady=5, sticky="w")
        self.embed_footer_var = ctk.StringVar()
        ctk.CTkEntry(embed_grid, textvariable=self.embed_footer_var, width=150).grid(row=6, column=1, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(embed_grid, text="Footer Icon:").grid(row=6, column=2, padx=10, pady=5, sticky="w")
        self.embed_footer_icon_var = ctk.StringVar()
        ctk.CTkEntry(embed_grid, textvariable=self.embed_footer_icon_var, width=150).grid(row=6, column=3, padx=10, pady=5, sticky="ew")
        
        # Row 7: Image and Thumbnail
        ctk.CTkLabel(embed_grid, text="Image URL:").grid(row=7, column=0, padx=10, pady=5, sticky="w")
        self.embed_image_var = ctk.StringVar()
        ctk.CTkEntry(embed_grid, textvariable=self.embed_image_var, width=150).grid(row=7, column=1, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(embed_grid, text="Thumbnail URL:").grid(row=7, column=2, padx=10, pady=5, sticky="w")
        self.embed_thumbnail_var = ctk.StringVar()
        ctk.CTkEntry(embed_grid, textvariable=self.embed_thumbnail_var, width=150).grid(row=7, column=3, padx=10, pady=5, sticky="ew")
        
        # Embed Fields
        ctk.CTkLabel(self.embed_frame, text="Embed Fields:", font=("Arial", 12, "bold")).pack(anchor="w", padx=10, pady=(10, 5))
        
        self.fields_frame = ctk.CTkFrame(self.embed_frame)
        self.fields_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        self.embed_fields = []
        
        ctk.CTkButton(self.embed_frame, text="+ Add Field", command=self.add_embed_field).pack(padx=10, pady=(0, 10))
        
        embed_grid.columnconfigure(1, weight=1)
        embed_grid.columnconfigure(3, weight=1)
        
        # File Attachment Section
        file_frame = ctk.CTkFrame(self.main_frame)
        file_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(file_frame, text="Attachments:", font=("Arial", 14, "bold")).pack(anchor="w", padx=10, pady=(10, 5))
        
        file_buttons = ctk.CTkFrame(file_frame)
        file_buttons.pack(fill="x", padx=10, pady=(0, 10))
        
        ctk.CTkButton(file_buttons, text="📎 Attach File", command=self.attach_file).pack(side="left", padx=5)
        ctk.CTkButton(file_buttons, text="🗑️ Remove File", command=self.remove_file).pack(side="left", padx=5)
        
        self.file_label = ctk.CTkLabel(file_frame, text="No file attached", text_color="gray")
        self.file_label.pack(anchor="w", padx=10, pady=(0, 10))
        
        # Status Label
        self.status_label = ctk.CTkLabel(self.main_frame, text="Ready", text_color="gray")
        self.status_label.pack(anchor="w", padx=20, pady=5)
        
        # Send Button
        button_frame = ctk.CTkFrame(self.main_frame)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        self.send_btn = ctk.CTkButton(button_frame, text="🚀 Send Message", command=self.send_message, 
                                      height=40, font=("Arial", 14, "bold"))
        self.send_btn.pack(side="right", padx=10)
        
        ctk.CTkButton(button_frame, text="Clear All", command=self.clear_all, 
                     fg_color="gray", hover_color="darkgray").pack(side="right", padx=5)
        
        # Hide embed frame initially
        self.toggle_message_type()
    
    def toggle_message_type(self):
        """Toggle between simple and embed message types"""
        if self.message_type.get() == "simple":
            self.simple_frame.pack(fill="both", expand=True, padx=10, pady=10)
            self.embed_frame.pack_forget()
        else:
            self.simple_frame.pack_forget()
            self.embed_frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    def add_embed_field(self):
        """Add a new embed field"""
        field_frame = ctk.CTkFrame(self.fields_frame)
        field_frame.pack(fill="x", pady=5)
        
        name_var = ctk.StringVar()
        value_var = ctk.StringVar()
        inline_var = ctk.BooleanVar(value=True)
        
        ctk.CTkLabel(field_frame, text="Name:").grid(row=0, column=0, padx=5, pady=5)
        ctk.CTkEntry(field_frame, textvariable=name_var, width=150).grid(row=0, column=1, padx=5, pady=5)
        
        ctk.CTkLabel(field_frame, text="Value:").grid(row=0, column=2, padx=5, pady=5)
        ctk.CTkEntry(field_frame, textvariable=value_var, width=200).grid(row=0, column=3, padx=5, pady=5)
        
        ctk.CTkCheckBox(field_frame, text="Inline", variable=inline_var).grid(row=0, column=4, padx=5, pady=5)
        
        remove_btn = ctk.CTkButton(field_frame, text="✕", width=30, 
                                    command=lambda: self.remove_embed_field(field_frame, field_data))
        remove_btn.grid(row=0, column=5, padx=5, pady=5)
        
        field_data = {
            'frame': field_frame,
            'name': name_var,
            'value': value_var,
            'inline': inline_var
        }
        
        self.embed_fields.append(field_data)
    
    def remove_embed_field(self, frame, field_data):
        """Remove an embed field"""
        frame.destroy()
        self.embed_fields.remove(field_data)
    
    def attach_file(self):
        """Attach a file to the message"""
        filename = filedialog.askopenfilename(
            title="Select a file",
            filetypes=[("All files", "*.*"), ("Images", "*.png *.jpg *.jpeg *.gif"), ("Text files", "*.txt")]
        )
        if filename:
            self.attachment_path = filename
            self.file_label.configure(text=f"📎 {os.path.basename(filename)}", text_color="lightblue")
    
    def remove_file(self):
        """Remove attached file"""
        self.attachment_path = None
        self.file_label.configure(text="No file attached", text_color="gray")
    
    def update_char_count(self, event=None):
        """Update character counter"""
        content = self.message_text.get("1.0", "end-1c")
        char_count = len(content)
        self.char_count_label.configure(text=f"{char_count} / 2000 characters")
        
        if char_count > 2000:
            self.char_count_label.configure(text_color="red")
        else:
            self.char_count_label.configure(text_color="gray")
    
    def update_status(self, message, color="gray"):
        """Update status label"""
        self.status_label.configure(text=message, text_color=color)
        self.root.update_idletasks()
    
    def clear_all(self):
        """Clear all fields"""
        self.message_text.delete("1.0", "end")
        self.username_var.set("")
        self.avatar_var.set("")
        self.embed_title_var.set("")
        self.embed_url_var.set("")
        self.embed_desc_text.delete("1.0", "end")
        self.embed_author_var.set("")
        self.embed_author_url_var.set("")
        self.embed_author_icon_var.set("")
        self.embed_footer_var.set("")
        self.embed_footer_icon_var.set("")
        self.embed_image_var.set("")
        self.embed_thumbnail_var.set("")
        
        for field in self.embed_fields:
            field['frame'].destroy()
        self.embed_fields = []
        
        self.remove_file()
        self.update_char_count()
    
    def hex_to_int(self, hex_color):
        """Convert hex color to integer"""
        try:
            hex_color = hex_color.lstrip('#')
            return int(hex_color, 16)
        except:
            return 0x5865F2
    
    def send_message(self):
        """Send message through Discord webhook"""
        webhook_url = self.webhook_var.get().strip()
        
        if not webhook_url:
            messagebox.showerror("Error", "Please enter a webhook URL")
            return
        
        self.send_btn.configure(state='disabled')
        self.update_status("Sending...", "yellow")
        
        try:
            # Create webhook
            webhook = DiscordWebhook(url=webhook_url)
            
            # Set username and avatar
            if self.username_var.get():
                webhook.username = self.username_var.get()
            if self.avatar_var.get():
                webhook.avatar_url = self.avatar_var.get()
            
            # Add content or embed based on message type
            if self.message_type.get() == "simple":
                message = self.message_text.get("1.0", "end-1c").strip()
                if not message and not self.attachment_path:
                    messagebox.showerror("Error", "Message cannot be empty")
                    self.send_btn.configure(state='normal')
                    self.update_status("Ready", "gray")
                    return
                
                if len(message) > 2000:
                    messagebox.showerror("Error", "Message exceeds 2000 character limit")
                    self.send_btn.configure(state='normal')
                    self.update_status("Ready", "gray")
                    return
                
                webhook.content = message
            else:
                # Create embed
                embed = DiscordEmbed()
                
                if self.embed_title_var.get():
                    embed.title = self.embed_title_var.get()
                if self.embed_url_var.get():
                    embed.url = self.embed_url_var.get()
                if self.embed_desc_text.get("1.0", "end-1c").strip():
                    embed.description = self.embed_desc_text.get("1.0", "end-1c").strip()
                
                embed.color = self.hex_to_int(self.embed_color_var.get())
                
                if self.embed_author_var.get():
                    embed.set_author(
                        name=self.embed_author_var.get(),
                        url=self.embed_author_url_var.get() or None,
                        icon_url=self.embed_author_icon_var.get() or None
                    )
                
                if self.embed_footer_var.get():
                    embed.set_footer(
                        text=self.embed_footer_var.get(),
                        icon_url=self.embed_footer_icon_var.get() or None
                    )
                
                if self.embed_image_var.get():
                    embed.set_image(url=self.embed_image_var.get())
                
                if self.embed_thumbnail_var.get():
                    embed.set_thumbnail(url=self.embed_thumbnail_var.get())
                
                if self.timestamp_var.get():
                    embed.set_timestamp()
                
                # Add fields
                for field in self.embed_fields:
                    name = field['name'].get().strip()
                    value = field['value'].get().strip()
                    if name and value:
                        embed.add_embed_field(
                            name=name,
                            value=value,
                            inline=field['inline'].get()
                        )
                
                webhook.add_embed(embed)
            
            # Add file attachment
            if self.attachment_path:
                with open(self.attachment_path, "rb") as f:
                    webhook.add_file(file=f.read(), filename=os.path.basename(self.attachment_path))
            
            # Send webhook
            response = webhook.execute()
            
            if response.status_code in [200, 204]:
                self.update_status(f"✓ Message sent successfully at {datetime.now().strftime('%H:%M:%S')}", "lightgreen")
                self.save_config()
            else:
                self.update_status(f"✗ Failed: Status {response.status_code}", "red")
                messagebox.showerror("Error", f"Failed to send message.\nStatus code: {response.status_code}")
                
        except Exception as e:
            self.update_status("✗ Error occurred", "red")
            messagebox.showerror("Error", f"An error occurred:\n{str(e)}")
        
        finally:
            self.send_btn.configure(state='normal')

def main():
    root = ctk.CTk()
    app = DiscordWebhookSender(root)
    root.mainloop()

if __name__ == "__main__":
    main()
