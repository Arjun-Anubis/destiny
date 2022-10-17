import pyogg


class OggSource( pyogg.OpusFileStream ):
    """Wrapper around  the internap file stream type, needs to implement, bytes per sample, get_buffer"""
    pass

encoder = pyogg.OpusEncoder()
encoder.set_application("voip")
encoder.set_sampling_frequency( 48000 )
encoder.set_channels( 2 )
