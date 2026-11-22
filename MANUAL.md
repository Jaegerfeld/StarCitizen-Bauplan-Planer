# SC Blueprint Planner – Manual

## Quick guide

The Blueprint Planner lists all craftable Star Citizen blueprints with recipe and source. You pick blueprints and get a procurement list with the total material needs.

### Areas

- **Header:** language **DE | EN**, **Light / Dark**, **What’s new?** (changelog), **Import owned (SCDL)** and **Load latest build (GitHub)**.
- **Catalog** (right): one tile per blueprint with image, subcategory, size · grade · class, recipe chips (quantity × material, **Q≥** = minimum quality) and source (up to three contracts with drop chance).
- **Filter bar:** search field (name, material, category, size such as `s2`), plus **all categories**, **all subcategories**, **all sizes**, **all grades**, **all classes**. Each field opens a checkbox list, and you can tick several values. With nothing ticked, "all" applies.
- **all / owned only / not owned only:** works only after an SCDL import or after loading a state that contains owned blueprints.
- **Name A–Z / fewest materials:** sort order of the catalog.
- **selected only:** shows only your selected blueprints. The other filters still apply.
- **Selection bar** (above the catalog): your selected blueprints with **−**, **+** and **✕**.
- **Procurement list** (top left): **Material** and **need**. Once you enter stock, the column **left** is added.
- **Available resources** (bottom left): enter what you already own. **reset** sets everything back to 0.

### Frequent actions

- Select a blueprint: enter the quantity in the field at the bottom of the tile, then click **+**.
- Share the list: **📋 Copy**, **⬇ .txt** or **⬇ .csv**.
- Keep selection and stock: under **Selection & stock** click **💾 Save** (JSON file), and bring it back later with **📂 Load**.
- More results: click **… show N more** at the bottom of the catalog.

### Data and storage

- Recipes and sources come from [star-head.de](https://star-head.de), the categories from the item type table of the SC-Deutsch-Launcher. The data depends on the patch, so check it in game.
- Images come from the [Star Citizen Wiki](https://starcitizen.tools/) and are loaded from there when you view them. Offline, the tiles show no images.
- The page also works as an offline copy (`SC_Bauplan_Planer.html`) with the data built in.
- **Load latest build (GitHub)** fetches the data set that is built every day. If you already have it, the page tells you.
- Selection, stock, owned blueprints, language, light/dark and the **selected only** toggle are stored only in your browser (localStorage). Search and filters are not stored.

## Tutorial: Plan materials

Goal: you want to craft two armor pieces and find out which materials you still need.

1. Open the planner. On a phone, tap the **Catalog** tab at the top.
2. Click **all categories** and tick **Armor**. Click next to the list to close it.
3. Narrow it down further with **all subcategories** if you like, for example to **Light armor**.
4. Type the name of the piece into the search field. The number of results is shown on the right of the filter bar.
5. Enter the quantity at the bottom of the tile (default is 1) and click **+**. The blueprint appears in the selection bar above the catalog.
6. Repeat this for the second piece. Use **−** and **+** in the selection bar to change the quantity, and **✕** to remove a blueprint.
7. Look at the **Procurement list** on the left. It adds up **Material** and **need** across all selected blueprints. The same material with different minimum qualities gets separate rows.
8. Under **Available resources**, enter what you already own. Materials your selection needs are highlighted there.
9. The procurement list now shows the column **left**. A **✓** means your stock is enough.
10. Click **📋 Copy** to put the list on the clipboard, or download it with **⬇ .txt** or **⬇ .csv**.

### Tips

- With **selected only**, the catalog shows just your selection. If other filters hide selected blueprints, the catalog offers **Reset filters**.
- Materials are refined commodities. Buy them at refineries or the TDD, or refine them yourself.
- The .csv file has the columns Material, MinQuality, Need, Stock and Left.

## Tutorial: Owned blueprints

Goal: you want to see which blueprints you are still missing and continue on another device.

1. In the SC-Deutsch-Launcher, export your completed blueprints as `sc_bp_erledigt.json`.
2. In the header, click **📥 Import owned (SCDL)** and choose the file.
3. A short message at the bottom shows how many owned blueprints were detected and how many are not in the catalog.
4. Owned blueprints now carry the badge **✓ owned** and a green left edge.
5. The **all** field in the filter bar is now active. Choose **not owned only**. On a phone you find it under **More filters**.
6. Combine it with category, size or grade to look for missing blueprints. The source line on the tile names the contracts that drop the blueprint.
7. Under **Selection & stock**, click **💾 Save**. You get the file `SC_Bauplan_Zustand.json` with selection, stock and owned blueprints.
8. Open the planner on the other device or in another browser and click **📂 Load**. Choose the saved file.
9. Selection, stock and owned blueprints are back.

### Tips

- Blueprints that everyone has from the start always count as owned.
- A new SCDL import replaces the previous list of owned blueprints.
- **📂 Load** replaces your current selection and stock with the content of the file.
- If a selected blueprint is no longer in the catalog after a data update, it is struck through in the selection bar and not counted in the totals.

## FAQ

### Why do some tiles have no image?

Not every item has an image in the wiki. Offline, no images are loaded at all.

### Why is the "all" (owned) field greyed out?

It becomes active only after you import via **📥 Import owned (SCDL)** or load a state that contains owned blueprints.

### Why is **selected only** locked?

You have not selected any blueprint yet. When the last selection is removed, the toggle switches itself off.

### Are the recipes correct?

The data comes from star-head.de and depends on the patch. Check quantities and sources in game.

### Do I lose my selection if I clear the browser storage?

Yes. Save it as a file with **💾 Save** first.
