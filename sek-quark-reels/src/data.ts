// Doğrulanmış ürün verisi. Kaynaklar: KAYNAKLAR.md
// SEK Protein Quark (Sade) 165 g — 100 g başına değerler.
// Migros (migros.com.tr) ve Şok (sokmarket.com.tr) ürün sayfalarında birebir aynı.
export const PRODUCT = {
  brand: "SEK",
  name: "Protein Quark",
  variant: "Sade",
  netG: 165,
  per100: {
    kcal: 84,
    protein: 12,
    carb: 4,
    sugar: 1.2,
    fat: 2,
    satFat: 1.3,
    salt: 0.1,
  },
  ingredients: ["Pastörize inek sütü", "Peynir kültürü"],
  allergen: "Süt ve süt ürünleri (laktoz) içerir.",
  packClaim: "20g PROTEIN",
};

// Paket başına hesap (165 g): 12 × 1,65 = 19,8 g
export const perPack = (v: number) => Math.round(v * (PRODUCT.netG / 100) * 10) / 10;

// Türkçe ondalık biçimi: 1.2 -> "1,2"
export const tr = (v: number, digits = 1) =>
  Number.isInteger(v) ? String(v) : v.toFixed(digits).replace(".", ",");
