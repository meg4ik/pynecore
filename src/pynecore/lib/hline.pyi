from ..core.callable_module import CallableModule
from ..types.hline import HLineEnum


#
# Module object
#

class HLineModule(CallableModule):
    #
    # Constants
    #

    style_solid = HLineEnum()
    style_dotted = HLineEnum()
    style_dashed = HLineEnum()


CallableModule(__name__)
