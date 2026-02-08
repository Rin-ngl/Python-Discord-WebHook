import customtkinter as ctk
from tkinter import filedialog, messagebox, colorchooser
import json
import os
import threading
from datetime import datetime
from typing import List, Dict

# Check for discord_webhook library
try:
    from discord_webhook import DiscordWebhook, DiscordEmbed
    WEBHOOK_AVAILABLE = True
except ImportError:
    WEBHOOK_AVAILABLE = False

class DiscordWebhookSender:
    def __init__(self, root):
        self.root = root
        self.root.title("Dishook")
        self.root.geometry("900x800")
        
        # Check dependency
        if not WEBHOOK_AVAILABLE:
            self.show_dependency_error()
            return
        
        # Theme Setup
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # State Variables
        self.config_file = "webhook_config.json"
        self.attachment_path = None
        self.saved_webhooks = []
        self.embed_fields_data = [] # Stores references to field widgets
        
        # Initialize UI
        self.load_config()
        self.setup_ui()
        
    def show_dependency_error(self):
        frame = ctk.CTkFrame(self.root)
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        ctk.CTkLabel(frame, text="Missing Dependency: discord-webhook", 
                     font=("Arial", 20, "bold"), text_color="red").pack(pady=20)
        ctk.CTkLabel(frame, text="Please run: pip install discord-webhook").pack()
        
    def setup_ui(self):
        # --- Top Section: Configuration ---
        config_frame = ctk.CTkFrame(self.root)
        config_frame.pack(fill="x", padx=10, pady=10)
        
        # Webhook URL
        url_frame = ctk.CTkFrame(config_frame, fg_color="transparent")
        url_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(url_frame, text="Webhook URL:").pack(side="left", padx=5)
        
        self.webhook_var = ctk.StringVar(value=self.saved_webhooks[-1] if self.saved_webhooks else "")
        self.webhook_combo = ctk.CTkComboBox(
            url_frame, variable=self.webhook_var, values=self.saved_webhooks, width=500
        )
        self.webhook_combo.pack(side="left", fill="x", expand=True, padx=5)
        ctk.CTkButton(url_frame, text="Save URL", width=80, command=self.save_config).pack(side="left")

        # Identity Row (Username/Avatar)
        id_frame = ctk.CTkFrame(config_frame, fg_color="transparent")
        id_frame.pack(fill="x", padx=10, pady=5)
        
        self.username_var = ctk.StringVar()
        self.avatar_var = ctk.StringVar()
        
        ctk.CTkLabel(id_frame, text="Bot Name:").pack(side="left", padx=5)
        ctk.CTkEntry(id_frame, textvariable=self.username_var, width=200, placeholder_text="Overwrites bot name").pack(side="left", padx=5)
        
        ctk.CTkLabel(id_frame, text="Avatar URL:").pack(side="left", padx=5)
        ctk.CTkEntry(id_frame, textvariable=self.avatar_var, width=200, placeholder_text="http://...").pack(side="left", padx=5)

        # --- Middle Section: Tabs ---
        self.tab_view = ctk.CTkTabview(self.root)
        self.tab_view.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.tab_content = self.tab_view.add("Message Content")
        self.tab_embed = self.tab_view.add("Embed Settings")
        self.tab_fields = self.tab_view.add("Embed Fields")
        
        self.setup_content_tab()
        self.setup_embed_tab()
        self.setup_fields_tab()
        
        # --- Bottom Section: Actions ---
        action_frame = ctk.CTkFrame(self.root)
        action_frame.pack(fill="x", padx=10, pady=10)
        
        self.status_label = ctk.CTkLabel(action_frame, text="Ready", text_color="gray")
        self.status_label.pack(side="left", padx=15)
        
        ctk.CTkButton(action_frame, text="Clear All", fg_color="#555555", hover_color="#333333", 
                      command=self.clear_all).pack(side="right", padx=5)
        
        self.send_btn = ctk.CTkButton(action_frame, text="🚀 Send Message", font=("Arial", 14, "bold"), 
                                      height=40, command=self.start_send_thread)
        self.send_btn.pack(side="right", padx=5)

    def setup_content_tab(self):
        """Setup standard text message and file attachments"""
        # Text Content
        ctk.CTkLabel(self.tab_content, text="Message Body (Optional if using Embed):", anchor="w").pack(fill="x", padx=10, pady=5)
        self.message_text = ctk.CTkTextbox(self.tab_content, height=150)
        self.message_text.pack(fill="x", padx=10, pady=5)
        
        # Char Counter
        self.char_count_label = ctk.CTkLabel(self.tab_content, text="0 / 2000", text_color="gray")
        self.char_count_label.pack(anchor="e", padx=10)
        self.message_text.bind('<KeyRelease>', self.update_char_count)
        
        # Attachments
        file_frame = ctk.CTkFrame(self.tab_content)
        file_frame.pack(fill="x", padx=10, pady=20)
        
        ctk.CTkButton(file_frame, text="📎 Attach File", command=self.attach_file).pack(side="left", padx=10, pady=10)
        self.file_label = ctk.CTkLabel(file_frame, text="No file selected", text_color="gray")
        self.file_label.pack(side="left", padx=10)
        ctk.CTkButton(file_frame, text="✕", width=30, fg_color="transparent", border_width=1, 
                      command=self.remove_file).pack(side="right", padx=10)

    def setup_embed_tab(self):
        """Setup Main Embed Properties"""
        scroll = ctk.CTkScrollableFrame(self.tab_embed)
        scroll.pack(fill="both", expand=True)
        
        # Helper to create rows
        def create_row(parent, label, variable, placeholder=""):
            f = ctk.CTkFrame(parent, fg_color="transparent")
            f.pack(fill="x", pady=2)
            ctk.CTkLabel(f, text=label, width=100, anchor="w").pack(side="left", padx=5)
            ctk.CTkEntry(f, textvariable=variable, placeholder_text=placeholder).pack(side="left", fill="x", expand=True, padx=5)

        # Variables
        self.embed_title = ctk.StringVar()
        self.embed_url = ctk.StringVar()
        self.embed_color = ctk.StringVar(value="#5865F2")
        self.embed_author_name = ctk.StringVar()
        self.embed_author_url = ctk.StringVar()
        self.embed_author_icon = ctk.StringVar()
        self.embed_image = ctk.StringVar()
        self.embed_thumbnail = ctk.StringVar()
        self.embed_footer = ctk.StringVar()
        self.embed_footer_icon = ctk.StringVar()
        self.use_timestamp = ctk.BooleanVar(value=True)

        # Basic Info
        ctk.CTkLabel(scroll, text="Main Info", font=("Arial", 14, "bold")).pack(anchor="w", padx=5, pady=5)
        create_row(scroll, "Title:", self.embed_title)
        create_row(scroll, "Title URL:", self.embed_url)
        
        # Color Picker
        color_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        color_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(color_frame, text="Color:", width=100, anchor="w").pack(side="left", padx=5)
        self.color_entry = ctk.CTkEntry(color_frame, textvariable=self.embed_color, width=100)
        self.color_entry.pack(side="left", padx=5)
        self.color_preview = ctk.CTkButton(color_frame, text="", width=30, fg_color=self.embed_color.get(), 
                                           command=self.pick_color)
        self.color_preview.pack(side="left", padx=5)
        ctk.CTkCheckBox(color_frame, text="Timestamp", variable=self.use_timestamp).pack(side="left", padx=20)

        # Description
        ctk.CTkLabel(scroll, text="Description:", anchor="w").pack(fill="x", padx=10, pady=(10,0))
        self.embed_desc = ctk.CTkTextbox(scroll, height=80)
        self.embed_desc.pack(fill="x", padx=5, pady=5)

        # Author
        ctk.CTkLabel(scroll, text="Author", font=("Arial", 14, "bold")).pack(anchor="w", padx=5, pady=(10,5))
        create_row(scroll, "Name:", self.embed_author_name)
        create_row(scroll, "URL:", self.embed_author_url)
        create_row(scroll, "Icon URL:", self.embed_author_icon)

        # Images
        ctk.CTkLabel(scroll, text="Images", font=("Arial", 14, "bold")).pack(anchor="w", padx=5, pady=(10,5))
        create_row(scroll, "Big Image URL:", self.embed_image)
        create_row(scroll, "Thumbnail URL:", self.embed_thumbnail)

        # Footer
        ctk.CTkLabel(scroll, text="Footer", font=("Arial", 14, "bold")).pack(anchor="w", padx=5, pady=(10,5))
        create_row(scroll, "Text:", self.embed_footer)
        create_row(scroll, "Icon URL:", self.embed_footer_icon)

    def setup_fields_tab(self):
        """Dynamic Embed Fields"""
        ctk.CTkButton(self.tab_fields, text="+ Add Field", command=self.add_field).pack(pady=10)
        
        self.fields_container = ctk.CTkScrollableFrame(self.tab_fields)
        self.fields_container.pack(fill="both", expand=True, padx=5, pady=5)

    def pick_color(self):
        color = colorchooser.askcolor(title="Choose Embed Color")[1]
        if color:
            self.embed_color.set(color)
            self.color_preview.configure(fg_color=color)

    def add_field(self):
        frame = ctk.CTkFrame(self.fields_container)
        frame.pack(fill="x", pady=2)
        
        name_var = ctk.StringVar()
        val_var = ctk.StringVar()
        inline_var = ctk.BooleanVar(value=True)
        
        # Layout
        ctk.CTkEntry(frame, textvariable=name_var, placeholder_text="Name", width=150).pack(side="left", padx=2)
        ctk.CTkEntry(frame, textvariable=val_var, placeholder_text="Value", width=250).pack(side="left", fill="x", expand=True, padx=2)
        ctk.CTkCheckBox(frame, text="In", width=40, variable=inline_var).pack(side="left", padx=5)
        
        # Use a closure to capture the specific frame and list object
        btn = ctk.CTkButton(frame, text="✕", width=30, fg_color="#CC0000", hover_color="#990000")
        btn.pack(side="right", padx=2)
        
        field_obj = {
            "frame": frame,
            "name": name_var,
            "value": val_var,
            "inline": inline_var
        }
        
        # Configure button command after creating the object reference
        btn.configure(command=lambda: self.remove_field(field_obj))
        
        self.embed_fields_data.append(field_obj)

    def remove_field(self, field_obj):
        field_obj["frame"].destroy()
        if field_obj in self.embed_fields_data:
            self.embed_fields_data.remove(field_obj)

    def update_char_count(self, _=None):
        text = self.message_text.get("1.0", "end-1c")
        count = len(text)
        self.char_count_label.configure(text=f"{count} / 2000", text_color="red" if count > 2000 else "gray")

    def attach_file(self):
        path = filedialog.askopenfilename()
        if path:
            self.attachment_path = path
            self.file_label.configure(text=os.path.basename(path), text_color="white")

    def remove_file(self):
        self.attachment_path = None
        self.file_label.configure(text="No file selected", text_color="gray")

    def save_config(self):
        url = self.webhook_var.get().strip()
        if url and url not in self.saved_webhooks:
            self.saved_webhooks.append(url)
            self.saved_webhooks = self.saved_webhooks[-10:] # Keep last 10
            self.webhook_combo.configure(values=self.saved_webhooks)
            
            try:
                with open(self.config_file, 'w') as f:
                    json.dump({'webhooks': self.saved_webhooks}, f)
                messagebox.showinfo("Saved", "Webhook URL saved!")
            except Exception as e:
                print(e)

    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    self.saved_webhooks = data.get('webhooks', [])
            except:
                pass

    def start_send_thread(self):
        """Entry point for the Send button"""
        url = self.webhook_var.get().strip()
        if not url:
            messagebox.showerror("Error", "Webhook URL is required!")
            return

        # Disable button
        self.send_btn.configure(state="disabled", text="Sending...")
        self.status_label.configure(text="Sending...", text_color="yellow")
        
        # Start thread
        threading.Thread(target=self.run_send_logic, args=(url,), daemon=True).start()

    def run_send_logic(self, url):
        """Background thread logic"""
        try:
            webhook = DiscordWebhook(url=url)
            
            # Identity
            if self.username_var.get():
                webhook.username = self.username_var.get()
            if self.avatar_var.get():
                webhook.avatar_url = self.avatar_var.get()

            # Content
            content_text = self.message_text.get("1.0", "end-1c").strip()
            if content_text:
                webhook.content = content_text

            # Embed Construction
            embed_obj = DiscordEmbed()
            has_embed_data = False
            
            # Check if any embed data exists
            if self.embed_title.get(): 
                embed_obj.title = self.embed_title.get()
                has_embed_data = True
            if self.embed_desc.get("1.0", "end-1c").strip():
                embed_obj.description = self.embed_desc.get("1.0", "end-1c")
                has_embed_data = True
            
            # Color processing
            try:
                c = self.embed_color.get().replace("#", "")
                embed_obj.color = int(c, 16)
            except:
                pass # Default color

            if self.embed_url.get(): embed_obj.url = self.embed_url.get()
            if self.embed_image.get(): 
                embed_obj.set_image(url=self.embed_image.get())
                has_embed_data = True
            if self.embed_thumbnail.get(): 
                embed_obj.set_thumbnail(url=self.embed_thumbnail.get())
                has_embed_data = True
            
            # Author & Footer
            if self.embed_author_name.get():
                embed_obj.set_author(
                    name=self.embed_author_name.get(),
                    url=self.embed_author_url.get() or None,
                    icon_url=self.embed_author_icon.get() or None
                )
                has_embed_data = True
                
            if self.embed_footer.get():
                embed_obj.set_footer(
                    text=self.embed_footer.get(),
                    icon_url=self.embed_footer_icon_var.get() or None if hasattr(self, 'embed_footer_icon_var') else None
                )
                has_embed_data = True

            if self.use_timestamp.get():
                embed_obj.set_timestamp()

            # Fields
            for field in self.embed_fields_data:
                n = field['name'].get().strip()
                v = field['value'].get().strip()
                if n and v:
                    embed_obj.add_embed_field(name=n, value=v, inline=field['inline'].get())
                    has_embed_data = True

            # Add Embed if it has data
            if has_embed_data:
                webhook.add_embed(embed_obj)

            # File
            if self.attachment_path and os.path.exists(self.attachment_path):
                with open(self.attachment_path, "rb") as f:
                    webhook.add_file(file=f.read(), filename=os.path.basename(self.attachment_path))
            elif not content_text and not has_embed_data:
                self.root.after(0, lambda: messagebox.showwarning("Warning", "Message is empty!"))
                self.reset_ui_state()
                return

            # Execute
            response = webhook.execute()
            
            # UI Update needs to be on main thread
            self.root.after(0, lambda: self.handle_response(response))

        except Exception as e:
            self.root.after(0, lambda: self.handle_error(str(e)))

    def handle_response(self, response):
        self.reset_ui_state()
        if response.status_code in [200, 204]:
            self.status_label.configure(text=f"Sent at {datetime.now().strftime('%H:%M:%S')}", text_color="green")
        else:
            self.status_label.configure(text=f"Failed: {response.status_code}", text_color="red")
            messagebox.showerror("Failed", f"Discord API returned status: {response.status_code}")

    def handle_error(self, error_msg):
        self.reset_ui_state()
        self.status_label.configure(text="Error", text_color="red")
        messagebox.showerror("Error", f"An error occurred:\n{error_msg}")

    def reset_ui_state(self):
        self.send_btn.configure(state="normal", text="🚀 Send Message")

    def clear_all(self):
        self.message_text.delete("1.0", "end")
        self.embed_title.set("")
        self.embed_desc.delete("1.0", "end")
        # Clear fields (Iterate copy to avoid modification issues)
        for field in list(self.embed_fields_data):
            self.remove_field(field)
        self.embed_image.set("")
        self.embed_thumbnail.set("")
        self.embed_author_name.set("")
        self.embed_author_url.set("")
        self.embed_author_icon.set("")
        self.embed_footer.set("")
        self.remove_file()
        self.status_label.configure(text="Cleared", text_color="gray")

if __name__ == "__main__":
    root = ctk.CTk()
    app = DiscordWebhookSender(root)
    root.mainloop()
