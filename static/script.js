const purityFactors = {
  "Gold 14k": 0.585,
  "Gold 18k": 0.75,
  "Platinum": 1
};

function money(value) {
  const symbol = window.APP_CONFIG?.currency_symbol || "$";
  return `${symbol}${Number(value || 0).toFixed(2)}`;
}

function getMetalRate(metalType) {
  if (metalType === "Platinum") {
    return Number(window.APP_CONFIG?.platinum_rate || window.APP_CONFIG?.gold_rate || 0);
  }
  return Number(window.APP_CONFIG?.gold_rate || 0);
}

function numberFrom(form, name) {
  return Number(form.elements[name]?.value || 0);
}

function updatePricePreview(form) {
  const metalType = form.elements.metal_type?.value;
  const metalWeight = numberFrom(form, "metal_weight");
  const diamondWeight = numberFrom(form, "diamond_weight");
  const diamondPcs = numberFrom(form, "diamond_pcs");
  const diamondRate = numberFrom(form, "diamond_rate");
  const laborRate = numberFrom(form, "labor_rate");
  const settingChargePerPc = numberFrom(form, "setting_charge_per_pc");
  const goldLossPercent = numberFrom(form, "gold_loss");
  const rhodium = numberFrom(form, "rhodium");
  const extraCharges = numberFrom(form, "extra_charges");
  const margin = numberFrom(form, "margin");

  const metalPrice = metalWeight * getMetalRate(metalType) * (purityFactors[metalType] || 0);
  const diamondPrice = diamondWeight * diamondRate;
  const laborCharge = metalWeight * laborRate;
  const settingCharge = diamondPcs * settingChargePerPc;
  const makingVat = (laborCharge + settingCharge) * 0.05;
  const goldLoss = metalPrice * (goldLossPercent / 100);
  const totalCost = metalPrice + diamondPrice + laborCharge + settingCharge + makingVat + goldLoss + rhodium + extraCharges;
  const finalPrice = totalCost * (1 + margin / 100);

  form.querySelector("[data-metal-price]").textContent = money(metalPrice);
  form.querySelector("[data-diamond-price]").textContent = money(diamondPrice);
  form.querySelector("[data-labor-charge]").textContent = money(laborCharge);
  form.querySelector("[data-setting-charge]").textContent = money(settingCharge);
  form.querySelector("[data-making-vat]").textContent = money(makingVat);
  form.querySelector("[data-gold-loss]").textContent = money(goldLoss);
  form.querySelector("[data-rhodium]").textContent = money(rhodium);
  form.querySelector("[data-extra-charges]").textContent = money(extraCharges);
  form.querySelector("[data-total-cost]").textContent = money(totalCost);
  form.querySelector("[data-final-price]").textContent = money(finalPrice);
}

document.querySelectorAll("[data-price-form]").forEach((form) => {
  form.addEventListener("input", () => updatePricePreview(form));
  form.addEventListener("change", () => updatePricePreview(form));
  updatePricePreview(form);
});

document.querySelectorAll("form[data-confirm]").forEach((form) => {
  form.addEventListener("submit", (event) => {
    if (!window.confirm(form.dataset.confirm)) {
      event.preventDefault();
    }
  });
});
