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


class MaskListPanel(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        
        # Create frame with title
        self.frame = ttk.LabelFrame(self, text="Masks")
        self.frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create listbox with scrollbar
        self.listbox_frame = ttk.Frame(self.frame)
        self.listbox_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.listbox = tk.Listbox(self.listbox_frame, selectmode=tk.SINGLE)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.scrollbar = ttk.Scrollbar(self.listbox_frame, orient=tk.VERTICAL, command=self.listbox.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.listbox.config(yscrollcommand=self.scrollbar.set)
        
        # Bind selection event to update button states
        self.listbox.bind("<<ListboxSelect>>", self.on_mask_select)
        
        # Create buttons
        self.button_frame = ttk.Frame(self.frame)
        self.button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.create_button = ttk.Button(self.button_frame, text="Create", command=self.on_create_mask)
        self.create_button.pack(side=tk.LEFT, padx=2)
        
        self.keyframe_button = ttk.Button(self.button_frame, text="Edit Frame", command=self.on_keyframe_mask, state=tk.DISABLED)
        self.keyframe_button.pack(side=tk.LEFT, padx=2)
        
        self.track_button = ttk.Button(self.button_frame, text="Track Mask", command=self.on_track_mask, state=tk.DISABLED)
        self.track_button.pack(side=tk.LEFT, padx=2)
        
        self.delete_button = ttk.Button(self.button_frame, text="Delete", command=self.on_delete_mask, state=tk.DISABLED)
        self.delete_button.pack(side=tk.LEFT, padx=2)
        
        # Create keyframe control buttons (initially hidden)
        self.keyframe_controls_frame = ttk.Frame(self.frame)
        
        self.apply_keyframe_button = ttk.Button(self.keyframe_controls_frame, text="Apply Keyframe", command=self.on_apply_keyframe)
        self.apply_keyframe_button.pack(side=tk.LEFT, padx=2)
        
        self.cancel_keyframe_button = ttk.Button(self.keyframe_controls_frame, text="Cancel", command=self.on_cancel_keyframe)
        self.cancel_keyframe_button.pack(side=tk.LEFT, padx=2)
        
        # Create style settings frame
        self.style_frame = ttk.LabelFrame(self.frame, text="Style")
        self.style_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Fill settings
        self.fill_frame = ttk.Frame(self.style_frame)
        self.fill_frame.pack(fill=tk.X, padx=5, pady=2)
        
        self.fill_var = tk.BooleanVar(value=True)
        self.fill_check = ttk.Checkbutton(self.fill_frame, text="Fill", variable=self.fill_var, command=self.on_fill_toggle)
        self.fill_check.pack(side=tk.LEFT)
        
        self.fill_color_button = ttk.Button(self.fill_frame, text="Color", width=6, command=self.on_fill_color)
        self.fill_color_button.pack(side=tk.LEFT, padx=5)
        
        self.fill_opacity_label = ttk.Label(self.fill_frame, text="Opacity:")
        self.fill_opacity_label.pack(side=tk.LEFT, padx=(5, 0))
        
        self.fill_opacity_var = tk.DoubleVar(value=0.3)
        self.fill_opacity_scale = ttk.Scale(self.fill_frame, from_=0.0, to=1.0, orient=tk.HORIZONTAL, 
                                           variable=self.fill_opacity_var, command=self.on_fill_opacity)
        self.fill_opacity_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Outline settings
        self.outline_frame = ttk.Frame(self.style_frame)
        self.outline_frame.pack(fill=tk.X, padx=5, pady=2)
        
        self.outline_var = tk.BooleanVar(value=True)
        self.outline_check = ttk.Checkbutton(self.outline_frame, text="Outline", variable=self.outline_var, command=self.on_outline_toggle)
        self.outline_check.pack(side=tk.LEFT)
        
        self.outline_color_button = ttk.Button(self.outline_frame, text="Color", width=6, command=self.on_outline_color)
        self.outline_color_button.pack(side=tk.LEFT, padx=5)
        
        self.outline_width_label = ttk.Label(self.outline_frame, text="Width:")
        self.outline_width_label.pack(side=tk.LEFT, padx=(5, 0))
        
        self.outline_width_var = tk.IntVar(value=2)
        self.outline_width_scale = ttk.Scale(self.outline_frame, from_=1, to=10, orient=tk.HORIZONTAL, 
                                            variable=self.outline_width_var, command=self.on_outline_width)
        self.outline_width_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Store mask list
        self.masks = []
        self.editing_mask = False
    
    def update_mask_list(self, masks):
        """Update the mask list with the given masks"""
        self.clear()
        
        self.masks = masks
        
        # Add to listbox
        for i, mask in enumerate(self.masks):
            self.listbox.insert(tk.END, f"Mask {i+1}")
        
        # Update UI state
        self.update_ui_state()
        
        # Update button states
        self.update_button_states()
    
    def on_mask_select(self, event):
        """Handle mask selection event"""
        self.update_button_states()
    
    def update_button_states(self):
        """Update button states based on selection"""
        if self.get_selected_mask():
            self.keyframe_button.config(state=tk.NORMAL)
            self.track_button.config(state=tk.NORMAL)
            self.delete_button.config(state=tk.NORMAL)
        else:
            self.keyframe_button.config(state=tk.DISABLED)
            self.track_button.config(state=tk.DISABLED)
            self.delete_button.config(state=tk.DISABLED)
    
    def get_selected_mask(self):
        """Get the currently selected mask"""
        selection = self.listbox.curselection()
        if not selection:
            return None
        
        index = selection[0]
        if 0 <= index < len(self.masks):
            return self.masks[index]
        
        return None
    
    def on_create_mask(self):
        """Handle create mask button click"""
        self.app.activate_create_mask_tool()
        self.set_editing_mode(True)
    
    def on_delete_mask(self):
        """Handle delete mask button click"""
        mask = self.get_selected_mask()
        if mask:
            self.app.delete_mask(mask['id'])
    
    def on_apply_edit(self):
        """Handle apply edit button click"""
        if hasattr(self.app, 'mask_manager'):
            self.app.mask_manager.apply_edit()
            self.set_editing_mode(False)
    
    def on_cancel_edit(self):
        """Handle cancel edit button click"""
        if hasattr(self.app, 'mask_manager'):
            self.app.mask_manager.cancel_current_operation()
            self.set_editing_mode(False)
    
    def set_editing_mode(self, editing):
        """Set the editing mode state"""
        self.editing_mask = editing
        self.update_ui_state()
    
    def update_ui_state(self):
        """Update UI state based on editing mode"""
        if self.editing_mask:
            # Show edit controls, hide normal controls
            self.button_frame.pack_forget()
            if hasattr(self.app, 'mask_manager') and self.app.mask_manager.active_tool == "keyframe":
                self.keyframe_controls_frame.pack(fill=tk.X, padx=5, pady=5)
            else:
                self.keyframe_controls_frame.pack_forget()
        else:
            # Show normal controls, hide edit controls
            self.keyframe_controls_frame.pack_forget()
            self.button_frame.pack(fill=tk.X, padx=5, pady=5)
            
            # Update button states
            self.update_button_states()
    
    def on_fill_toggle(self):
        """Handle fill toggle"""
        show_fill = self.fill_var.get()
        self.app.mask_manager.toggle_fill(show_fill)
        self.app.mask_manager.draw_all_masks()
    
    def on_fill_color(self):
        """Handle fill color button click"""
        color = colorchooser.askcolor(initialcolor=self.app.mask_manager.fill_color)
        if color[1]:
            self.app.mask_manager.set_fill_color(color[1])
            self.app.mask_manager.draw_all_masks()
    
    def on_fill_opacity(self, value):
        """Handle fill opacity change"""
        self.app.mask_manager.set_fill_opacity(float(value))
        self.app.mask_manager.draw_all_masks()
    
    def on_outline_toggle(self):
        """Handle outline toggle"""
        show_outline = self.outline_var.get()
        self.app.mask_manager.toggle_outline(show_outline)
        self.app.mask_manager.draw_all_masks()
    
    def on_outline_color(self):
        """Handle outline color button click"""
        color = colorchooser.askcolor(initialcolor=self.app.mask_manager.outline_color)
        if color[1]:
            self.app.mask_manager.set_outline_color(color[1])
            self.app.mask_manager.draw_all_masks()
    
    def on_outline_width(self, value):
        """Handle outline width change"""
        self.app.mask_manager.set_outline_width(int(float(value)))
        self.app.mask_manager.draw_all_masks()

    
    def on_keyframe_mask(self):
        """Handle keyframe mask button click"""
        mask = self.get_selected_mask()
        if mask:
            self.app.activate_keyframe_mask_tool(mask)
            self.set_keyframe_mode(True)
    
    def on_apply_keyframe(self):
        """Handle apply keyframe button click"""
        if hasattr(self.app, 'mask_manager'):
            self.app.mask_manager.apply_keyframe()
            self.set_keyframe_mode(False)
    
    def on_cancel_keyframe(self):
        """Handle cancel keyframe button click"""
        if hasattr(self.app, 'mask_manager'):
            self.app.mask_manager.cancel_current_operation()
            self.set_keyframe_mode(False)
    
    def on_track_mask(self):
        """Handle track mask button click"""
        mask = self.get_selected_mask()
        if mask:
            # Confirm tracking operation
            if tk.messagebox.askyesno("Track Mask", 
                                     "This will track the mask vertices across all frames and create keyframes. Continue?"):
                self.app.track_mask(mask['id'])
    
    def set_keyframe_mode(self, keyframing):
        """Set the keyframe mode state"""
        self.editing_mask = keyframing
        self.update_ui_state()
    
    def clear(self):
        """Clear the mask list"""
        self.listbox.delete(0, tk.END)
        self.masks = []
        self.editing_mask = False
        self.update_ui_state()


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