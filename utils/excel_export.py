from pathlib import Path
from tempfile import NamedTemporaryFile

import pandas as pd

from utils.pricing_engine import calculate_price


def export_products_to_excel(products):
    rows = []
    for product in products:
        breakdown = calculate_price(
            product["metal_type"],
            product["metal_weight"],
            product["diamond_weight"],
            product["diamond_rate"],
            product["diamond_pcs"],
            product["labor_rate"],
            product["setting_charge_per_pc"],
            product["gold_loss"],
            product["rhodium"],
            product["extra_charges"],
            product["margin"],
        )
        rows.append(
            {
                "Product ID": product["product_code"],
                "Client Name": product["client_name"],
                "Category": product["category"],
                "Metal Type": product["metal_type"],
                "Metal Weight (g)": product["metal_weight"],
                "Diamond Weight (ct)": product["diamond_weight"],
                "Diamond Pcs": product["diamond_pcs"],
                "Diamond Rate": product["diamond_rate"],
                "Labor Rate/g": product["labor_rate"],
                "Labor Charge": breakdown["labor_charge"],
                "Setting Charge/pc": product["setting_charge_per_pc"],
                "Setting Charge": breakdown["setting_charge"],
                "Making VAT 5%": breakdown["making_vat"],
                "Metal Price": breakdown["metal_price"],
                "Diamond Price": breakdown["diamond_price"],
                "Gold Loss (%)": product["gold_loss"],
                "Gold Loss Amount": breakdown["gold_loss"],
                "Rhodium": product["rhodium"],
                "Extra Charges": product["extra_charges"],
                "Margin (%)": product["margin"],
                "Total Cost": breakdown["total_cost"],
                "Final Price": product["final_price"],
                "Created At": product["created_at"],
            }
        )

    df = pd.DataFrame(rows)
    temp_file = NamedTemporaryFile(delete=False, suffix=".xlsx")
    temp_path = Path(temp_file.name)
    temp_file.close()

    with pd.ExcelWriter(temp_path, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Products", index=False)
        worksheet = writer.sheets["Products"]
        for column_cells in worksheet.columns:
            max_length = max(len(str(cell.value or "")) for cell in column_cells)
            worksheet.column_dimensions[column_cells[0].column_letter].width = min(max_length + 2, 28)

    return temp_path
