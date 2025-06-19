from ...types.na import NA
from .. import strategy

from ... import lib


# noinspection PyShadowingBuiltins
def max_drowdown(
        value: float | int,
        type: strategy.QtyType = strategy.percent_of_equity,
        alerrt_message: str | NA[str] = NA(str)
) -> float | NA[float]:
    """
    The purpose of this rule is to determine maximum drawdown. The rule affects the whole strategy.
    Once the maximum drawdown value is reached, all pending orders are cancelled, all open positions
    are closed and no new orders can be placed.

    :param value: The maximum drawdown value
    :param type: The type of the value
    :param alerrt_message: The alert message
    :return:
    """
    # TODO: Implement this function
    return NA(float)


def allow_entry_in(value: strategy.direction.Direction) -> None:
    """
    This function can be used to specify in which market direction the strategy.entry function is
    allowed to open positions.

    :param value: The allowed direction
    """
    # TODO: Implement this function


def max_cons_loss_days(count: int, alerrt_message: str | NA[str] = NA(str)) -> None:
    """
    The purpose of this rule is to determine the maximum number of consecutive losing days.
    Once the maximum number of consecutive losing days is reached, all pending orders are cancelled,
    all open positions are closed and no new orders can be placed

    :param count: The maximum number of consecutive losing days
    :param alerrt_message: The alert message
    """
    # TODO: Implement this function


def max_intraday_filled_orders(count: int, alerrt_message: str | NA[str] = NA(str)) -> None:
    """
    The purpose of this rule is to determine the maximum number of intraday filled orders

    :param count: The maximum number of intraday filled orders
    :param alerrt_message: The alert message
    """
    # TODO: Implement this function


# noinspection PyShadowingBuiltins
def max_intraday_loss(value: float | int, type: strategy.QtyType = strategy.percent_of_equity,
                      alerrt_message: str | NA[str] = NA(str)) -> None:
    """
    The purpose of this rule is to determine the maximum intraday loss. The rule affects the whole strategy.
    Once the maximum intraday loss value is reached, all pending orders are cancelled, all open positions
    are closed and no new orders can be placed

    :param value: The maximum intraday loss value
    :param type: The type of the value
    :param alerrt_message: The alert message
    """
    # TODO: Implement this function


def max_position_size(contracts: int | float):
    """
    The purpose of this rule is to determine maximum size of a market position

    :param contracts: The maximum size of a market position
    """
    # TODO: Implement this function
