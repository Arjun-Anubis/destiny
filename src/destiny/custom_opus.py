import ctypes

cdll = ctypes.cdll

opus = cdll.LoadLibrary( "libopus.so" )

err = ctypes.c_int

opus.opus_decoder_create(
