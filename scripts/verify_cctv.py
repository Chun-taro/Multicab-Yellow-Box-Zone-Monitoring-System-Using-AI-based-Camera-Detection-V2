import cv2
import sys

def test_rtsp_stream(url):
    print(f"Attempting to connect to: {url}")
    print("Press 'q' to quit the test window.")
    
    # Create the video capture object
    cap = cv2.VideoCapture(url)
    
    # Check if the stream was opened successfully
    if not cap.isOpened():
        print("Error: Could not open the video stream. Please check:")
        print("1. Your RJ45 cable connection.")
        print("2. The camera's IP address and port.")
        print("3. Your username and password in the URL.")
        return

    # Try to read the first frame
    ret, frame = cap.read()
    if not ret:
        print("Error: Successfully connected, but could not read frames.")
        cap.release()
        return

    print("Success! Stream is working. Opening window...")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Lost stream connection.")
            break
            
        # Display the frame
        cv2.imshow("CCTV Test Feed", frame)
        
        # Check for 'q' key to quit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("Test connection closed.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        rtsp_url = sys.argv[1]
    else:
        print("Please enter your camera's RTSP URL:")
        rtsp_url = input("> ")
    
    test_rtsp_stream(rtsp_url)
