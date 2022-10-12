class HardReset( Exception ):
    pass
class SoftReset( Exception ):
    pass
class ErrOpcode( Exception ):
    pass
class UnkownOpcode( Exception ):
    pass
class SessionInvalid( Exception ):
    pass
class notFound( AttributeError ):
    pass
