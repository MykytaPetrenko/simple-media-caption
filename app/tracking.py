import cv2
import numpy as np
import os

def track_points_with_lk_and_kalman(video_path, initial_points):
    """
    Track points using a combination of Lucas-Kanade optical flow with Kalman filtering
    for smoother, more stable tracking results.
    """
    cap = cv2.VideoCapture(video_path)
    ret, first_frame = cap.read()
    if not ret:
        cap.release()
        return []

    # Convert first frame to grayscale
    prev_gray = cv2.cvtColor(first_frame, cv2.COLOR_BGR2GRAY)
    
    # Convert initial points to numpy array for LK tracker
    initial_points = np.array(initial_points, dtype=np.float32).reshape(-1, 1, 2)
    
    # Parameters for Lucas-Kanade optical flow
    lk_params = dict(
        winSize=(21, 21),
        maxLevel=3,
        criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, 0.01)
    )
    
    # Initialize Kalman filters for each point
    kalman_filters = []
    for _ in range(len(initial_points)):
        kf = cv2.KalmanFilter(4, 2)
        kf.measurementMatrix = np.array([[1, 0, 0, 0], [0, 1, 0, 0]], np.float32)
        kf.transitionMatrix = np.array([
            [1, 0, 1, 0],
            [0, 1, 0, 1],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ], np.float32)
        kf.processNoiseCov = np.array([
            [1e-4, 0, 0, 0],
            [0, 1e-4, 0, 0],
            [0, 0, 1e-3, 0],
            [0, 0, 0, 1e-3]
        ], np.float32)
        kf.measurementNoiseCov = np.array([[1, 0], [0, 1]], np.float32) * 1e-3
        kalman_filters.append(kf)
    
    # Initialize Kalman states with initial positions
    for i, point in enumerate(initial_points):
        kalman_filters[i].statePost = np.array([[point[0][0]], [point[0][1]], [0], [0]], np.float32)
    
    # Store all tracked points
    tracked_points = [[tuple(p[0]) for p in initial_points.tolist()]]
    
    # Current points being tracked
    current_points = initial_points.copy()
    
    # Track through the video
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        # Convert current frame to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # If we have points to track
        if len(current_points) > 0:
            # Calculate optical flow
            next_points, status, _ = cv2.calcOpticalFlowPyrLK(
                prev_gray, gray, current_points, None, **lk_params
            )
            
            # Create a list for filtered points
            filtered_points = []
            
            # Process each point
            for i, (pt, st) in enumerate(zip(next_points, status)):
                if st[0] == 1:  # If point was found
                    if i < len(kalman_filters):
                        # Predict
                        predicted = kalman_filters[i].predict()
                        
                        # Update with measurement
                        measurement = np.array([[pt[0][0]], [pt[0][1]]], np.float32)
                        kalman_filters[i].correct(measurement)
                        
                        # Get filtered position
                        filtered_pos = kalman_filters[i].statePost[:2].flatten()
                        filtered_points.append((float(filtered_pos[0]), float(filtered_pos[1])))
                else:
                    # Point was lost, but we can still use Kalman prediction
                    if i < len(kalman_filters):
                        predicted = kalman_filters[i].predict()
                        filtered_pos = predicted[:2].flatten()
                        filtered_points.append((float(filtered_pos[0]), float(filtered_pos[1])))
            
            # Update points for next iteration
            current_points = np.array([[[p[0], p[1]]] for p in filtered_points], dtype=np.float32)
            
            # Save points for this frame
            tracked_points.append(filtered_points)
        else:
            # If all points are lost, add None for all points
            tracked_points.append([None] * len(initial_points))
        
        # Update previous frame
        prev_gray = gray.copy()
        
    cap.release()
    return tracked_points

def render_tracked_points(video_path, initial_points, output_path):
    """
    Track points in a video and render the results with trails for better visualization.
    """
    # Run the tracking function
    tracked_points = track_points_with_lk_and_kalman(video_path, initial_points)
    
    # Open the input video
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError("Cannot open the video file.")

    # Get video properties
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Define the codec and create VideoWriter object
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    # Store historical points for trail visualization
    history = [[] for _ in range(len(initial_points))]
    max_history = 20  # Number of frames to keep in history for trail visualization
    
    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_idx < len(tracked_points):
            # Update history with current points
            for i, pt in enumerate(tracked_points[frame_idx]):
                if pt is not None and i < len(history):
                    history[i].append((int(pt[0]), int(pt[1])))
                    # Keep only recent history
                    if len(history[i]) > max_history:
                        history[i] = history[i][-max_history:]
            
            # Draw trails with fading opacity
            for i, trail in enumerate(history):
                for j, pt in enumerate(trail):
                    # Calculate opacity based on recency (newer points are more opaque)
                    alpha = (j + 1) / len(trail)
                    # Main color for this point (can customize per point if needed)
                    color = (0, int(255 * alpha), int(255 * (1 - alpha)))
                    # Draw a small circle for each historical point with varying size
                    size = int(2 + 3 * (j / len(trail)))
                    cv2.circle(frame, pt, size, color, -1)
            
            # Draw current points with a larger, more visible circle
            for i, pt in enumerate(tracked_points[frame_idx]):
                if pt is not None and i < len(initial_points):
                    # Current point in bright green with larger size
                    cv2.circle(frame, (int(pt[0]), int(pt[1])), 7, (0, 255, 0), -1)
                    # Add a label if desired
                    cv2.putText(frame, f"Point {i+1}", (int(pt[0])+10, int(pt[1])), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        out.write(frame)
        frame_idx += 1

    cap.release()
    out.release()

    if os.path.exists(output_path):
        print(f"Output video saved at: {output_path}")
    else:
        print("Failed to save the output video.")

# Example usage
if __name__ == "__main__":
    input_video = 'mykyta__00001.mp4'  # Replace with your video path
    output_video = 'tracked_output.mp4'

    # Example initial points (replace with your own)
    initial_points = [(240, 360)]

    # Run the tracking
    render_tracked_points(input_video, initial_points, output_video)