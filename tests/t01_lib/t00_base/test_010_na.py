"""
@pyne
"""
from pynecore.lib import script, plot, bar_index, na, nz, fixnan


@script.indicator(title="Na", shorttitle="na")
def main():
    val = bar_index if bar_index % 2 == 0 else na(float)

    plot(val, "val")
    plot(0 if na(val) else 1, "na(val)")
    plot(nz(val), "nz(val)")
    plot(nz(val, 2), "nz(val, 2)")
    plot(fixnan(val), "fixnan(val)")


def __test_time__(csv_reader, runner, dict_comparator, log):
    """ NA """
    with csv_reader('na.csv', subdir="data") as cr:
        for i, (candle, _plot) in enumerate(runner(cr).run_iter()):
            dict_comparator(_plot, candle.extra_fields)
            if i > 300:
                break
