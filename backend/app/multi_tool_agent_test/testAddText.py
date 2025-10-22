import os
import logging
# from moviepy.editor import ColorClip # No longer needed

# Import the function to test
try:
    from addText import add_text_to_video
except ImportError:
    # Handle the case where the script is run directly
    from addText import add_text_to_video

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# create_dummy_video function removed as it's no longer needed

def test_add_text_local_video():
    """
    Tests the add_text_to_video function using a pre-existing local video.
    """
    logger = logging.getLogger(__name__)
    
    # Use the user's local video file. 
    # NOTE: Assumes .mp4 extension. Please change if incorrect.
    # This file must be in the same directory where the script is run 
    # (e.g., the 'wpromote-code-sprint/backend' directory if running as a module).
    input_file = "14561425081518715695_sample_0.mp4" 
    output_file = "edited_14561425081518715695_sample_0.mp4"
    
    # 1. Check if the local video exists before starting
    if not os.path.exists(input_file):
        logger.error(f"Test failed: Input video file not found at '{input_file}'.")
        logger.error("Please make sure the video is in the correct directory.")
        return

    # 2. Define test parameters
    test_params = {
        "input_video_path": input_file,
        "output_video_path": output_file,
        "text": "Hello, Local Video!",
        "start_time": 1,
        "duration": 3,
        "fontsize": 50,
        "color": "yellow",
        "position": "center"
    }
    
    logger.info(f"Testing add_text_to_video with params: {test_params}")
    
    try:
        # 3. Call the function
        result = add_text_to_video(**test_params)
        logger.info(f"Function result: {result}")
        
        # 4. Check if the output file was created
        if os.path.exists(output_file):
            logger.info(f"SUCCESS: Output file '{output_file}' was created.")
        else:
            logger.error(f"FAILURE: Output file '{output_file}' was NOT created.")
            logger.error(f"Function returned: {result}")
            
    except Exception as e:
        logger.error(f"Test crashed with an exception: {e}", exc_info=True)
        
    finally:
        # 5. Clean up ONLY the output file
        logger.info("Cleaning up test files...")
        # We no longer remove the input_file, as it's the user's local copy.
        if os.path.exists(output_file):
            os.remove(output_file)
            logger.info(f"Removed: {output_file}")

if __name__ == "__main__":
    # This allows you to run the test directly from the command line:
    # python -m app.multi_tool_agent.test_movie_tool
    # (Run from the 'backend' directory)
    # Or, if you cd into app/multi_tool_agent:
    # python test_movie_tool.py
    
    # Note: Ensure ImageMagick is installed if you haven't put it in your Docker container!
    test_add_text_local_video()