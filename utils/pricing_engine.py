from models.db_setup import load_settings, save_settings


PURITY_FACTORS = {
    "Gold 14k": 0.585,
    "Gold 18k": 0.75,
    "Platinum": 1.0,
}


def load_config():
    return load_settings()


def save_config(config):
    save_settings(config)


def get_metal_rate(metal_type, config):
    if metal_type == "Platinum":
        return float(config.get("platinum_rate", config.get("gold_rate", 0)))
    return float(config.get("gold_rate", 0))


def calculate_price(
    metal_type,
    metal_weight,
    diamond_weight,
    diamond_rate,
    diamond_pcs,
    labor_rate,
    setting_charge_per_pc,
    gold_loss,
    rhodium,
    extra_charges,
    margin,
):
    config = load_config()
    metal_weight = float(metal_weight)
    diamond_weight = float(diamond_weight)
    diamond_rate = float(diamond_rate)
    diamond_pcs = int(diamond_pcs)
    labor_rate = float(labor_rate)
    setting_charge_per_pc = float(setting_charge_per_pc)
    gold_loss_percent = float(gold_loss)
    rhodium = float(rhodium)
    extra_charges = float(extra_charges)
    margin = float(margin)

    if min(
        metal_weight,
        diamond_weight,
        diamond_rate,
        diamond_pcs,
        labor_rate,
        setting_charge_per_pc,
        gold_loss_percent,
        rhodium,
        extra_charges,
        margin,
    ) < 0:
        raise ValueError("Numeric values cannot be negative")

    purity_factor = PURITY_FACTORS.get(metal_type)
    if purity_factor is None:
        raise ValueError("Unsupported metal type")

    metal_price = metal_weight * get_metal_rate(metal_type, config) * purity_factor
    diamond_price = diamond_weight * diamond_rate
    labor_charge = metal_weight * labor_rate
    setting_charge = diamond_pcs * setting_charge_per_pc
    gold_loss_amount = metal_price * (gold_loss_percent / 100)
    making_total = labor_charge + setting_charge
    making_vat = making_total * 0.05
    total_cost = (
        metal_price
        + diamond_price
        + labor_charge
        + setting_charge
        + making_vat
        + gold_loss_amount
        + rhodium
        + extra_charges
    )
    final_price = total_cost * (1 + margin / 100)

    return {
        "metal_price": round(metal_price, 2),
        "diamond_price": round(diamond_price, 2),
        "labor_charge": round(labor_charge, 2),
        "setting_charge": round(setting_charge, 2),
        "making_total": round(making_total, 2),
        "making_vat": round(making_vat, 2),
        "gold_loss_percent": round(gold_loss_percent, 2),
        "gold_loss": round(gold_loss_amount, 2),
        "rhodium": round(rhodium, 2),
        "extra_charges": round(extra_charges, 2),
        "total_cost": round(total_cost, 2),
        "final_price": round(final_price, 2),
    }
