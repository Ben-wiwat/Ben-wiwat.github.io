# Publication statistics

The citation total, h-index, i10-index and ten-year citation chart in
`index.html` and `publications.html` are updated together from values entered
manually. The other publication counts are maintained separately.

1. Open the [Google Scholar profile](https://scholar.google.com/citations?user=td86cJcAAAAJ&hl=en)
   and note the **All** values for citations, h-index and i10-index, and the
   citation counts for ten consecutive years.
2. From the repository root, run:

   ```sh
   python3 scripts/update_scholar.py
   ```

3. Enter the three all-time values, the first year of the ten-year chart, and
   the ten annual counts in order, separated by commas. For example, entering
   `2016` and `9, 0, 0, 0, 0, 0, 0, 80, 170, 200` supplies counts for
   2016 through 2025. Include `0` for a year with no citations.
4. Review the changes to both HTML pages, then commit and publish them as usual.

The command requires Python 3 but makes no network requests. Invalid or
incomplete input is rejected before either page is changed. Updates are manual;
there is no scheduled workflow.

Run the updater tests with `python3 -m unittest discover -s tests`.
