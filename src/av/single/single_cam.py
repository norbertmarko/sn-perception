import threading
import sys

from vimba import *
import cv2
import numpy as np

# sizes
# (w: 1280, h: 720)
# (w: 960  h: 380)

# parameters
orig_width: int = 1280
orig_height: int = 720
width: int = 680
height: int = 384
frame_is_recorded: bool = True
frame_name: str = "right.png"


def resize_img(cv_img: np.ndarray, width: int, height: int) -> np.ndarray:
	"""Resize an OpenCV image with the given parameters."""
	cv_img = cv2.resize(
		cv_img, (width, height), interpolation=cv2.INTER_AREA
	)
	# cv_img = cv_img[..., np.newaxis]
	return cv_img


def setup_camera(cam: Camera):
    """
    This function sets up the required pixel format
    for color frames in OpenCV. Exposure, White Balance
    and other features can be set here. Run 'list_features'
    from VimbaPython Examples to see a complete list.
    """
    with cam:
        # Set frame resolution
        try:
            cam.Width.set(orig_width)
            cam.Height.set(orig_height)

        except (AttributeError, VimbaFeatureError):
            pass

        # Enable white balancing
        try:
            cam.BalanceWhiteAuto.set('Continuous')

        except (AttributeError, VimbaFeatureError):
            pass

        # Enable auto exposure
        try:
            cam.ExposureAuto.set('Continuous')

        except (AttributeError, VimbaFeatureError):
            pass

        cv_fmts = intersect_pixel_formats(cam.get_pixel_formats(), OPENCV_PIXEL_FORMATS)
        color_fmts = intersect_pixel_formats(cv_fmts, COLOR_PIXEL_FORMATS)

        if color_fmts:
            cam.set_pixel_format(color_fmts[0])
            print('Camera set to color mode.')
        else:
            mono_fmts = intersect_pixel_formats(cv_fmts, MONO_PIXEL_FORMATS)
        
            if mono_fmts:
                cam.set_pixel_format(mono_fmts[0])
                print('Camera set to mono mode.')
            else:
                #TODO: Implement abort function.
                print('Camera does not support a OpenCV compatible format natively. Abort.')


class Handler:
    """
    This is the main callable class. The 'start_streaming'
    function takes an instance of it. With each acquired 
    frame by 'start_streaming', Handler is called and 
    provided with the new frame.
    """
    def __init__(self):
        self.shutdown_event = threading.Event()
        
    def __call__(self, cam: Camera, frame: Frame):
        ENTER_KEY_CODE = 13 # Unicode value of ENTER key.

        key = cv2.waitKey(1)
        
        if key == ENTER_KEY_CODE:
            self.shutdown_event.set()
            return
        
        elif frame.get_status() == FrameStatus.Complete:
            print('{} acquired {}'.format(cam, frame), flush=True)
      
        msg = 'Stream from \'{}\'. Press <Enter> to stop stream.'

        # code here  
        # separating numpy frame and the Frame provided to queue_frame 
        img = resize_img(frame.as_numpy_ndarray(), width, height)

        if frame_is_recorded:
            cv2.imwrite(frame_name, img)

        cv2.imshow(msg.format(cam.get_name()), img)

        # should be called last
        cam.queue_frame(frame)


def main():
    with Vimba.get_instance() as vimba:
        #TODO: Put this into a 'get_camera' function.
        cams = vimba.get_all_cameras()
        with cams[0] as cam:

            setup_camera(cam)
            handler = Handler()

            try:
                #TODO: Clear up 'buffer_count' purpose.
                cam.start_streaming(handler=handler, buffer_count=24)
                handler.shutdown_event.wait()

            finally:
                cam.stop_streaming()


if __name__ == '__main__':
    main()