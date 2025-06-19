from ..types.base import IntEnum


class AlignEnum(IntEnum):
    ...


class FormatEnum(IntEnum):
    ...


class WrapEnum(IntEnum):
    ...


# Text alignment constants
align_left = AlignEnum()
align_center = AlignEnum()
align_right = AlignEnum()
align_top = AlignEnum()
align_bottom = AlignEnum()

# Text format constants
format_bold = FormatEnum()
format_italic = FormatEnum()
format_none = FormatEnum()

# Text wrap constants
wrap_auto = WrapEnum()
wrap_none = WrapEnum()
