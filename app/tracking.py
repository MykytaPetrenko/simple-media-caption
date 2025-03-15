import cv2
import numpy as np
import os

def track_points_with_lk_and_kalman(video_path, initial_points):
    """
    Track points using a combination of Lucas-Kanade optical flow with Kalman filtering
    for smoother, more stable tracking results.
    """
    # Use the improved tracking algorithm instead
    return track_points_with_consensus(video_path, initial_points)

def track_points_with_consensus(video_path, initial_points, use_shifted_points=True, 
                               shift_value=5, window_sizes=None, filter_method="consensus"):
    """
    Enhanced tracking algorithm that uses multiple sample points around each vertex
    and consensus-based filtering for more reliable tracking.
    
    Parameters:
    -----------
    video_path : str
        Path to the video file
    initial_points : list
        List of initial points to track
    use_shifted_points : bool
        Whether to use additional sample points around each vertex
    shift_value : int
        Offset distance for additional sample points
    window_sizes : list
        List of window sizes for Lucas-Kanade optical flow
    filter_method : str
        Method for filtering results ('average' or 'consensus')
    """
    cap = cv2.VideoCapture(video_path)
    ret, first_frame = cap.read()
    if not ret:
        cap.release()
        return []

    # Convert first frame to grayscale
    prev_gray = cv2.cvtColor(first_frame, cv2.COLOR_BGR2GRAY)
    
    # Set default window sizes if not provided
    if window_sizes is None or len(window_sizes) == 0:
        window_sizes = [21]
    
    # Generate sample points around each vertex
    sample_points = []
    sample_offsets = []  # Store offsets for each sample point
    
    for point in initial_points:
        x, y = point
        # Center point
        sample_points.append((x, y))
        sample_offsets.append((0, 0))
        
        # Add shifted points if enabled
        if use_shifted_points:
            # Up, down, left, right
            sample_points.append((x, y - shift_value))  # Up
            sample_offsets.append((0, -shift_value))
            
            sample_points.append((x, y + shift_value))  # Down
            sample_offsets.append((0, shift_value))
            
            sample_points.append((x - shift_value, y))  # Left
            sample_offsets.append((-shift_value, 0))
            
            sample_points.append((x + shift_value, y))  # Right
            sample_offsets.append((shift_value, 0))
    
    # Convert sample points to numpy array for LK tracker
    np_sample_points = np.array(sample_points, dtype=np.float32).reshape(-1, 1, 2)
    
    # Create a list of Lucas-Kanade parameter sets for each window size
    lk_params_list = []
    for win_size in window_sizes:
        lk_params_list.append(dict(
            winSize=(win_size, win_size),
            maxLevel=3,
            criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, 0.01)
        ))
    
    # Initialize Kalman filters for each sample point
    kalman_filters = []
    for _ in range(len(np_sample_points)):
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
    for i, point in enumerate(np_sample_points):
        kalman_filters[i].statePost = np.array([[point[0][0]], [point[0][1]], [0], [0]], np.float32)
    
    # Store all tracked points (only the original vertices, not the sample points)
    tracked_points = [[tuple(p) for p in initial_points]]
    
    # Current sample points being tracked
    current_sample_points = np_sample_points.copy()
    
    # Calculate points per vertex (1 if not using shifted points, 5 if using)
    points_per_vertex = 5 if use_shifted_points else 1
    
    # Track through the video
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        # Convert current frame to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # If we have points to track
        if len(current_sample_points) > 0:
            # Process each window size
            all_next_points = []
            all_statuses = []
            
            for lk_params in lk_params_list:
                # Calculate optical flow for this window size
                next_points, status, _ = cv2.calcOpticalFlowPyrLK(
                    prev_gray, gray, current_sample_points, None, **lk_params
                )
                all_next_points.append(next_points)
                all_statuses.append(status)
            
            # Process each original vertex
            filtered_vertices = []
            
            for i in range(len(initial_points)):
                # Collect valid tracked samples from all window sizes
                valid_samples = []
                
                # Process each window size
                for w_idx, (next_points, status) in enumerate(zip(all_next_points, all_statuses)):
                    # Get the sample points for this vertex
                    start_idx = i * points_per_vertex
                    end_idx = start_idx + points_per_vertex
                    
                    # Process each sample point
                    for j in range(start_idx, min(end_idx, len(next_points))):
                        if j < len(status) and status[j][0] == 1:
                            # Apply Kalman filter
                            predicted = kalman_filters[j].predict()
                            measurement = np.array([[next_points[j][0][0]], [next_points[j][0][1]]], np.float32)
                            kalman_filters[j].correct(measurement)
                            filtered_pos = kalman_filters[j].statePost[:2].flatten()
                            
                            # Get the offset for this sample point
                            sample_offset = sample_offsets[j % len(sample_offsets)]
                            
                            # Adjust position by removing the offset
                            adjusted_pos = (
                                float(filtered_pos[0]) - sample_offset[0],
                                float(filtered_pos[1]) - sample_offset[1]
                            )
                            
                            # Add to valid samples with window size info
                            valid_samples.append((adjusted_pos, w_idx))
                
                # If we have valid samples, apply filtering
                if valid_samples:
                    # Extract positions (without window size info)
                    positions = [pos for pos, _ in valid_samples]
                    
                    if filter_method == "consensus" and len(positions) >= 3:
                        # Calculate movement vectors for each sample
                        original_pos = initial_points[i]
                        movement_vectors = []
                        
                        for pos in positions:
                            dx = pos[0] - original_pos[0]
                            dy = pos[1] - original_pos[1]
                            movement_vectors.append((dx, dy))
                        
                        # Calculate median movement
                        median_dx = np.median([v[0] for v in movement_vectors])
                        median_dy = np.median([v[1] for v in movement_vectors])
                        
                        # Identify outliers
                        threshold = 10  # Threshold for outlier detection
                        consensus_samples = []
                        
                        for j, (dx, dy) in enumerate(movement_vectors):
                            if (abs(dx - median_dx) < threshold and 
                                abs(dy - median_dy) < threshold):
                                consensus_samples.append(positions[j])
                        
                        # Calculate average position from consensus samples
                        if consensus_samples:
                            avg_x = sum(p[0] for p in consensus_samples) / len(consensus_samples)
                            avg_y = sum(p[1] for p in consensus_samples) / len(consensus_samples)
                            filtered_vertices.append((avg_x, avg_y))
                        else:
                            # If no consensus, use the original position plus median movement
                            filtered_vertices.append((
                                original_pos[0] + median_dx,
                                original_pos[1] + median_dy
                            ))
                    else:
                        # Use simple average
                        avg_x = sum(p[0] for p in positions) / len(positions)
                        avg_y = sum(p[1] for p in positions) / len(positions)
                        filtered_vertices.append((avg_x, avg_y))
                else:
                    # No valid samples, use Kalman prediction for the center point
                    center_idx = i * points_per_vertex  # Index of the center point
                    if center_idx < len(kalman_filters):
                        predicted = kalman_filters[center_idx].predict()
                        filtered_pos = predicted[:2].flatten()
                        filtered_vertices.append((float(filtered_pos[0]), float(filtered_pos[1])))
                    else:
                        # If all else fails, use the last known position
                        if len(tracked_points) > 0 and i < len(tracked_points[-1]):
                            filtered_vertices.append(tracked_points[-1][i])
                        else:
                            filtered_vertices.append(None)
            
            # Save vertices for this frame
            tracked_points.append(filtered_vertices)
            
            # Update sample points for next iteration
            new_sample_points = []
            new_sample_offsets = []
            
            for i, vertex in enumerate(filtered_vertices):
                if vertex is not None:
                    x, y = vertex
                    # Center point
                    new_sample_points.append([x, y])
                    new_sample_offsets.append((0, 0))
                    
                    # Add shifted points if enabled
                    if use_shifted_points:
                        new_sample_points.append([x, y - shift_value])  # Up
                        new_sample_offsets.append((0, -shift_value))
                        
                        new_sample_points.append([x, y + shift_value])  # Down
                        new_sample_offsets.append((0, shift_value))
                        
                        new_sample_points.append([x - shift_value, y])  # Left
                        new_sample_offsets.append((-shift_value, 0))
                        
                        new_sample_points.append([x + shift_value, y])  # Right
                        new_sample_offsets.append((shift_value, 0))
            
            if new_sample_points:
                current_sample_points = np.array(new_sample_points, dtype=np.float32).reshape(-1, 1, 2)
                sample_offsets = new_sample_offsets
            else:
                current_sample_points = np.array([], dtype=np.float32)
                sample_offsets = []
        else:
            # If all points are lost, add None for all vertices
            tracked_points.append([None] * len(initial_points))
        
        # Update previous frame
        prev_gray = gray.copy()
        
    cap.release()
    return tracked_points

def render_tracked_points(video_path, initial_points, output_path, use_shifted_points=True, 
                          shift_value=5, window_sizes=None, filter_method="consensus"):
    """
    Track points in a video and render the results with trails for better visualization.
    
    Parameters:
    -----------
    video_path : str
        Path to the video file
    initial_points : list
        List of initial points to track
    output_path : str
        Path to save the output video
    use_shifted_points : bool
        Whether to use additional sample points around each vertex
    shift_value : int
        Offset distance for additional sample points
    window_sizes : list
        List of window sizes for Lucas-Kanade optical flow
    filter_method : str
        Method for filtering results ('average' or 'consensus')
    """
    # Run the tracking function
    tracked_points = track_points_with_consensus(
        video_path, 
        initial_points, 
        use_shifted_points=use_shifted_points,
        shift_value=shift_value,
        window_sizes=window_sizes,
        filter_method=filter_method
    )
    
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

    # Run the tracking with custom parameters
    render_tracked_points(
        input_video, 
        initial_points, 
        output_video,
        use_shifted_points=True,
        shift_value=5,
        window_sizes=[21, 31],
        filter_method="consensus"
    )