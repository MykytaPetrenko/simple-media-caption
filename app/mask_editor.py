#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Media Captioning Tool - Mask Editor
"""

import os
import tkinter as tk
from tkinter import ttk
import numpy as np
from PIL import Image, ImageTk, ImageDraw

class MaskEditor(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.mask = None
        self.mask_path = None
        self.media_path = None
        self.drawing = False
        self.last_x = 0
        self.last_y = 0
        
        # Initialize brush settings
        self.brush_size = 10
        self.brush_intensity = 255  # 0-255, where 255 is fully opaque
        
        # Create canvas for editing masks
        self.canvas_frame = ttk.Frame(self)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(self.canvas_frame, bg="black", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Bind mouse events
        self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_move)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        
        # Create status bar
        self.status_bar = ttk.Label(self, text="No mask loaded", anchor=tk.W)
        self.status_bar.pack(fill=tk.X, pady=(5, 0))
        
        # Bind resize event
        self.canvas.bind("<Configure>", self.on_resize)
    
    def create_mask(self, media_path, width, height):
        """Create a new empty (white) mask"""
        if not media_path:
            return
            
        # Create a white image (fully transparent mask)
        self.mask = Image.new('L', (width, height), 255)
        
        # Set media and mask paths
        self.media_path = media_path
        filename = os.path.basename(media_path)
        name, _ = os.path.splitext(filename)
        
        # Create the mask directory if it doesn't exist
        mask_dir = os.path.join(os.path.dirname(os.path.dirname(media_path)), "masks")
        os.makedirs(mask_dir, exist_ok=True)
        
        # Set the mask path
        self.mask_path = os.path.join(mask_dir, f"{name}.png")
        
        # Display the mask
        self.display_mask()
        
        # Update status bar
        self.status_bar.config(text=f"Created new mask: {os.path.basename(self.mask_path)}")
    
    def load_mask(self, media_path):
        """Load a mask for the given media"""
        if not media_path:
            self.clear()
            return
            
        self.media_path = media_path
        filename = os.path.basename(media_path)
        name, _ = os.path.splitext(filename)
        
        # Look for mask in the masks directory
        mask_dir = os.path.join(os.path.dirname(os.path.dirname(media_path)), "masks")
        self.mask_path = os.path.join(mask_dir, f"{name}.png")
        
        # Check if mask exists
        if os.path.isfile(self.mask_path):
            # Load existing mask
            self.mask = Image.open(self.mask_path).convert('L')
            self.status_bar.config(text=f"Loaded mask: {os.path.basename(self.mask_path)}")
        else:
            # Get media dimensions from the media viewer
            if hasattr(self.app, 'media_viewer') and self.app.media_viewer.media_width > 0:
                width = self.app.media_viewer.media_width
                height = self.app.media_viewer.media_height
                # Create a new mask
                self.create_mask(media_path, width, height)
            else:
                self.clear()
                self.status_bar.config(text="Could not determine media dimensions")
                return
        
        # Display the mask
        self.display_mask()
    
    def save_mask(self):
        """Save the current mask"""
        if not self.mask or not self.mask_path:
            return
            
        # Create masks directory if it doesn't exist
        os.makedirs(os.path.dirname(self.mask_path), exist_ok=True)
        
        # Save the mask
        self.mask.save(self.mask_path)
        self.status_bar.config(text=f"Saved mask: {os.path.basename(self.mask_path)}")
    
    def display_mask(self):
        """Display the current mask"""
        if not self.mask:
            self.clear()
            return
            
        # Create a copy for display with alpha channel
        # White (255) is transparent, Black (0) is opaque
        display_mask = Image.new('RGBA', self.mask.size, (0, 0, 0, 0))
        
        # Create mask array where white (255) becomes transparent (0) and black (0) becomes semi-opaque
        mask_array = np.array(self.mask)
        alpha_array = 255 - mask_array  # Invert so white (255) becomes 0 alpha
        
        # Create RGBA image with black color and alpha from mask
        rgba_array = np.zeros((mask_array.shape[0], mask_array.shape[1], 4), dtype=np.uint8)
        rgba_array[..., 3] = alpha_array
        
        # Convert back to PIL Image
        display_mask = Image.fromarray(rgba_array, 'RGBA')
        
        # Get canvas dimensions
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        if canvas_width <= 1 or canvas_height <= 1:
            # Canvas not yet properly sized, schedule for later
            self.after(100, self.display_mask)
            return
        
        # Calculate scaling factor to fit within canvas
        width_ratio = canvas_width / display_mask.width
        height_ratio = canvas_height / display_mask.height
        scale_factor = min(width_ratio, height_ratio)
        
        # Calculate new dimensions
        new_width = int(display_mask.width * scale_factor)
        new_height = int(display_mask.height * scale_factor)
        
        # Calculate position to center mask
        offset_x = (canvas_width - new_width) // 2
        offset_y = (canvas_height - new_height) // 2
        
        # Store scaling information for drawing
        self.scale_factor = scale_factor
        self.offset_x = offset_x
        self.offset_y = offset_y
        
        # Resize mask for display
        resized_mask = display_mask.resize((new_width, new_height), Image.LANCZOS)
        
        # Convert to PhotoImage and display
        self.tk_image = ImageTk.PhotoImage(resized_mask)
        
        # Clear canvas and display mask
        self.canvas.delete("all")
        self.canvas.create_image(offset_x, offset_y, anchor=tk.NW, image=self.tk_image)
    
    def clear(self):
        """Clear the canvas and reset state"""
        self.mask = None
        self.mask_path = None
        self.media_path = None
        self.canvas.delete("all")
        self.status_bar.config(text="No mask loaded")
    
    def on_resize(self, event):
        """Handle canvas resize event"""
        if self.mask:
            self.display_mask()
    
    def on_mouse_down(self, event):
        """Handle mouse button press"""
        if not self.mask:
            return
            
        self.drawing = True
        self.last_x = event.x
        self.last_y = event.y
        
        # Draw a single dot
        self.draw_on_mask(event.x, event.y, event.x, event.y)
    
    def on_mouse_move(self, event):
        """Handle mouse movement while button is pressed"""
        if not self.drawing or not self.mask:
            return
            
        # Draw line from last position to current
        self.draw_on_mask(self.last_x, self.last_y, event.x, event.y)
        
        # Update last position
        self.last_x = event.x
        self.last_y = event.y
    
    def on_mouse_up(self, event):
        """Handle mouse button release"""
        self.drawing = False
    
    def draw_on_mask(self, x1, y1, x2, y2):
        """Draw on the mask using the current brush settings"""
        if not self.mask:
            return
            
        # Convert canvas coordinates to mask coordinates
        mask_x1 = int((x1 - self.offset_x) / self.scale_factor)
        mask_y1 = int((y1 - self.offset_y) / self.scale_factor)
        mask_x2 = int((x2 - self.offset_x) / self.scale_factor)
        mask_y2 = int((y2 - self.offset_y) / self.scale_factor)
        
        # Ensure coordinates are within mask boundaries
        mask_width, mask_height = self.mask.size
        mask_x1 = max(0, min(mask_x1, mask_width - 1))
        mask_y1 = max(0, min(mask_y1, mask_height - 1))
        mask_x2 = max(0, min(mask_x2, mask_width - 1))
        mask_y2 = max(0, min(mask_y2, mask_height - 1))
        
        # Create a drawing context
        draw = ImageDraw.Draw(self.mask)
        
        # Calculate the intensity value (255 - intensity so 0 is black, 255 is white)
        intensity = 255 - self.brush_intensity
        
        # Draw line with the given brush size and intensity
        draw.line((mask_x1, mask_y1, mask_x2, mask_y2), fill=intensity, width=self.brush_size)
        
        # Update the display
        self.display_mask()
    
    def set_brush_size(self, size):
        """Set the brush size"""
        self.brush_size = int(size)
    
    def set_brush_intensity(self, intensity):
        """Set the brush intensity (0-255)"""
        self.brush_intensity = int(intensity) 