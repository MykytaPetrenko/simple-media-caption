#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Media Captioning Tool - Media Viewer
"""

import os
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import cv2
import threading
import time

class MediaViewer(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.media_path = None
        self.is_video = False
        self.video_capture = None
        self.current_frame = None
        self.playing = False
        self.total_frames = 0
        self.current_frame_index = 0
        self.video_thread = None
        self.stop_video_thread = False
        
        # Media dimensions and scaling
        self.media_width = 0
        self.media_height = 0
        self.scale_factor = 1.0
        self.offset_x = 0
        self.offset_y = 0
        
        # Create canvas for displaying media
        self.canvas_frame = ttk.Frame(self)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(self.canvas_frame, bg="black", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Create status bar
        self.status_bar = ttk.Label(self, text="No media loaded", anchor=tk.W)
        self.status_bar.pack(fill=tk.X, pady=(5, 0))
        
        # Bind resize event
        self.canvas.bind("<Configure>", self.on_resize)
    
    def load_media(self, media_path):
        """Load media (image or video) from the given path"""
        if not media_path or not os.path.isfile(media_path):
            self.clear()
            self.status_bar.config(text="Media file not found")
            return
        
        # Stop any running video
        self.stop_video()
        
        self.media_path = media_path
        
        # Check if it's a video or image
        _, ext = os.path.splitext(media_path.lower())
        self.is_video = ext in ['.mp4', '.avi', '.mov', '.mkv']
        
        if self.is_video:
            self.load_video()
        else:
            self.load_image()
    
    def load_image(self):
        """Load and display an image"""
        try:
            # Open image with PIL
            image = Image.open(self.media_path)
            
            # Resize to fit canvas
            self.resize_and_display_image(image)
            
            # Update status bar
            filename = os.path.basename(self.media_path)
            width, height = image.size
            self.status_bar.config(text=f"{filename} ({width}x{height})")
        
        except Exception as e:
            self.clear()
            self.status_bar.config(text=f"Error loading image: {str(e)}")
    
    def load_video(self):
        """Load and display a video"""
        try:
            # Open video with OpenCV
            self.video_capture = cv2.VideoCapture(self.media_path)
            
            if not self.video_capture.isOpened():
                raise ValueError("Could not open video file")
            
            # Get video properties
            self.total_frames = int(self.video_capture.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = self.video_capture.get(cv2.CAP_PROP_FPS)
            width = int(self.video_capture.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self.video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # Read first frame
            ret, frame = self.video_capture.read()
            if not ret:
                raise ValueError("Could not read video frame")
            
            # Convert frame from BGR to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Convert to PIL Image
            image = Image.fromarray(frame_rgb)
            
            # Resize and display
            self.resize_and_display_image(image)
            
            # Update status bar
            filename = os.path.basename(self.media_path)
            duration = self.total_frames / fps if fps > 0 else 0
            self.status_bar.config(
                text=f"{filename} ({width}x{height}, {fps:.2f} fps, {duration:.2f} sec)"
            )
            
            # Set to first frame and pause by default
            self.current_frame_index = 0
            self.playing = False
            
            # Start video thread (paused)
            self.start_video_thread()
        
        except Exception as e:
            self.clear()
            self.status_bar.config(text=f"Error loading video: {str(e)}")
    
    def start_video_thread(self):
        """Start the video playback thread (even if paused)"""
        if not self.is_video or not self.video_capture:
            return
        
        self.stop_video_thread = False
        
        # Start video thread if not already running
        if not self.video_thread or not self.video_thread.is_alive():
            self.video_thread = threading.Thread(target=self.video_playback_thread)
            self.video_thread.daemon = True
            self.video_thread.start()
    
    def play_video(self):
        """Start video playback"""
        if not self.is_video or not self.video_capture:
            return
        
        self.playing = True
        
        # Start thread if not already running
        if not self.video_thread or not self.video_thread.is_alive():
            self.start_video_thread()
    
    def pause_video(self):
        """Pause video playback"""
        self.playing = False
    
    def stop_video(self):
        """Stop video playback and release resources"""
        self.playing = False
        self.stop_video_thread = True
        
        # Wait for thread to finish
        if self.video_thread and self.video_thread.is_alive():
            self.video_thread.join(timeout=1.0)
        
        # Release video capture
        if self.video_capture:
            self.video_capture.release()
            self.video_capture = None
    
    def seek_video(self, frame_index):
        """Seek to a specific frame in the video"""
        if not self.is_video or not self.video_capture:
            return
        
        # Ensure frame index is within bounds
        frame_index = max(0, min(frame_index, self.total_frames - 1))
        
        # Seek to frame
        self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
        self.current_frame_index = frame_index
        
        # Read and display frame
        ret, frame = self.video_capture.read()
    
    def next_frame(self):
        """Go to next frame in video"""
        if self.is_video and self.video_capture:
            self.pause_video()
            self.seek_video(self.current_frame_index + 1)
    
    def prev_frame(self):
        """Go to previous frame in video"""
        if self.is_video and self.video_capture:
            self.pause_video()
            self.seek_video(self.current_frame_index - 1)
    
    def video_playback_thread(self):
        """Thread function for video playback"""
        while not self.stop_video_thread:
            if self.playing and self.video_capture:
                # Read next frame
                ret, frame = self.video_capture.read()
                
                if not ret:
                    # End of video, loop back to beginning
                    self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    self.current_frame_index = 0
                    continue
                
                # Update current frame index
                self.current_frame_index += 1
                
                # Convert frame from BGR to RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Convert to PIL Image
                image = Image.fromarray(frame_rgb)
                
                # Schedule UI update in main thread
                self.after(0, lambda img=image: self.update_frame(img))
                
                # Sleep to maintain frame rate
                time.sleep(0.03)  # ~30 fps
            else:
                # Not playing, sleep to avoid busy waiting
                time.sleep(0.1)
    
    def resize_and_display_image(self, image):
        """Resize image to fit canvas and display it"""
        if not image:
            return
        
        # Store original media dimensions
        self.media_width, self.media_height = image.size
        
        # Get canvas dimensions
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        if canvas_width <= 1 or canvas_height <= 1:
            # Canvas not yet properly sized, schedule for later
            self.after(100, lambda img=image: self.resize_and_display_image(img))
            return
        
        # Calculate scaling factor to fit image within canvas
        width_ratio = canvas_width / self.media_width
        height_ratio = canvas_height / self.media_height
        self.scale_factor = min(width_ratio, height_ratio)
        
        # Calculate new dimensions
        new_width = int(self.media_width * self.scale_factor)
        new_height = int(self.media_height * self.scale_factor)
        
        # Calculate position to center image (offset)
        self.offset_x = (canvas_width - new_width) // 2
        self.offset_y = (canvas_height - new_height) // 2
        
        # Resize image
        resized_image = image.resize((new_width, new_height), Image.LANCZOS)
        
        # Convert to PhotoImage
        photo_image = ImageTk.PhotoImage(resized_image)
        
        # Store reference to prevent garbage collection
        self.current_frame = photo_image
        
        # Clear canvas and display image
        self.canvas.delete("all")
        
        self.canvas.create_image(self.offset_x, self.offset_y, anchor=tk.NW, image=photo_image)
    
    def canvas_to_media_coords(self, x, y):
        """Convert canvas coordinates to media coordinates"""
        if self.scale_factor == 0:
            return (0, 0)
            
        media_x = (x - self.offset_x) / self.scale_factor
        media_y = (y - self.offset_y) / self.scale_factor
        return (media_x, media_y)
    
    def media_to_canvas_coords(self, x, y):
        """Convert media coordinates to canvas coordinates"""
        canvas_x = (x * self.scale_factor) + self.offset_x
        canvas_y = (y * self.scale_factor) + self.offset_y
        return (canvas_x, canvas_y)
    
    def on_resize(self, event):
        """Handle canvas resize event"""
        if self.media_path and self.current_frame:
            # Store current editing state
            editing_state = None
            
            # If we have a video, get the current frame
            if self.is_video and self.video_capture and not self.playing:
                # Save current position
                current_pos = self.current_frame_index
                
                # Seek to current position
                self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, current_pos)
                
                # Read frame
                ret, frame = self.video_capture.read()
                if ret:
                    # Convert frame from BGR to RGB
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    
                    # Convert to PIL Image
                    image = Image.fromarray(frame_rgb)
                    
                    # Resize and display
                    self.resize_and_display_image(image)
    
    def clear(self):
        """Clear the canvas and reset state"""
        self.stop_video()
        self.media_path = None
        self.is_video = False
        self.current_frame = None
        self.canvas.delete("all")
        self.status_bar.config(text="No media loaded") 