#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Media Captioning Tool - UI Components
"""

import os
import tkinter as tk
from tkinter import ttk, colorchooser, messagebox

class FileListPanel(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        
        # Create frame with title
        self.frame = ttk.LabelFrame(self, text="Media Files")
        self.frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create listbox with scrollbar
        self.listbox_frame = ttk.Frame(self.frame)
        self.listbox_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.listbox = tk.Listbox(self.listbox_frame, selectmode=tk.SINGLE)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.scrollbar = ttk.Scrollbar(self.listbox_frame, orient=tk.VERTICAL, command=self.listbox.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.listbox.config(yscrollcommand=self.scrollbar.set)
        
        # Bind selection event
        self.listbox.bind("<<ListboxSelect>>", self.on_file_select)
        
        # Store file list
        self.files = []
    
    def load_files(self, directory):
        """Load media files from the given directory"""
        self.clear()
        
        if not directory or not os.path.isdir(directory):
            return
        
        # Get all files in the directory
        all_files = os.listdir(directory)
        
        # Filter for image and video files
        media_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.mp4', '.avi', '.mov', '.mkv']
        self.files = [f for f in all_files if os.path.splitext(f.lower())[1] in media_extensions]
        
        # Sort files
        self.files.sort()
        
        # Add to listbox
        for file in self.files:
            self.listbox.insert(tk.END, file)
    
    def on_file_select(self, event):
        """Handle file selection event"""
        selection = self.listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        if 0 <= index < len(self.files):
            self.app.select_media(self.files[index])
    
    def clear(self):
        """Clear the file list"""
        self.listbox.delete(0, tk.END)
        self.files = []


class ControlPanel(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        
        # Create frame
        self.frame = ttk.Frame(self)
        self.frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Create video controls
        self.prev_button = ttk.Button(self.frame, text="<", width=3, command=self.on_prev_frame)
        self.prev_button.pack(side=tk.LEFT, padx=2)
        
        self.play_pause_button = ttk.Button(self.frame, text="▶", width=3, command=self.on_play_pause)
        self.play_pause_button.pack(side=tk.LEFT, padx=2)
        
        self.next_button = ttk.Button(self.frame, text=">", width=3, command=self.on_next_frame)
        self.next_button.pack(side=tk.LEFT, padx=2)
        
        # Create frame slider
        self.slider_var = tk.IntVar(value=0)
        self.slider = ttk.Scale(self.frame, from_=0, to=100, orient=tk.HORIZONTAL, 
                               variable=self.slider_var, command=self.on_slider_change)
        self.slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Create frame counter
        self.frame_counter = ttk.Label(self.frame, text="0/0")
        self.frame_counter.pack(side=tk.LEFT, padx=5)
        
        # Playing state
        self.playing = False
        
        # Update timer
        self.update_timer()
    
    def on_prev_frame(self):
        """Handle previous frame button click"""
        self.app.media_viewer.prev_frame()
        self.update_ui()
    
    def on_next_frame(self):
        """Handle next frame button click"""
        self.app.media_viewer.next_frame()
        self.update_ui()
    
    def on_play_pause(self):
        """Handle play/pause button click"""
        if self.app.media_viewer.is_video:
            if self.app.media_viewer.playing:
                self.app.media_viewer.pause_video()
                self.play_pause_button.config(text="▶")
            else:
                self.app.media_viewer.play_video()
                self.play_pause_button.config(text="⏸")
    
    def on_slider_change(self, value):
        """Handle slider change"""
        if self.app.media_viewer.is_video and self.app.media_viewer.total_frames > 0:
            frame_index = int(float(value) / 100 * (self.app.media_viewer.total_frames - 1))
            self.app.media_viewer.seek_video(frame_index)
    
    def update_ui(self):
        """Update UI state based on current media"""
        if not hasattr(self.app, 'media_viewer'):
            return
            
        if self.app.media_viewer.is_video:
            # Update play/pause button
            if self.app.media_viewer.playing:
                self.play_pause_button.config(text="⏸")
            else:
                self.play_pause_button.config(text="▶")
            
            # Update slider
            if self.app.media_viewer.total_frames > 0:
                progress = self.app.media_viewer.current_frame_index / (self.app.media_viewer.total_frames - 1) * 100
                self.slider_var.set(progress)
            
            # Update frame counter
            self.frame_counter.config(
                text=f"{self.app.media_viewer.current_frame_index + 1}/{self.app.media_viewer.total_frames}"
            )
            
            # Enable controls
            self.prev_button.config(state=tk.NORMAL)
            self.play_pause_button.config(state=tk.NORMAL)
            self.next_button.config(state=tk.NORMAL)
            self.slider.config(state=tk.NORMAL)
        else:
            # Disable controls for images
            self.prev_button.config(state=tk.DISABLED)
            self.play_pause_button.config(state=tk.DISABLED)
            self.next_button.config(state=tk.DISABLED)
            self.slider.config(state=tk.DISABLED)
            self.frame_counter.config(text="0/0")
    
    def update_timer(self):
        """Update UI periodically"""
        self.update_ui()
        
        # Schedule next update
        self.after(100, self.update_timer) 