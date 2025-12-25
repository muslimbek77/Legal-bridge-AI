// src/features/contracts/contracts.constants.ts

export const CONTRACT_TYPES = [
  { value: "", label: "Barcha turlar" },
  { value: "service", label: "Xizmat ko'rsatish" },
  { value: "supply", label: "Yetkazib berish" },
  { value: "lease", label: "Ijara" },
  { value: "employment", label: "Mehnat" },
  { value: "loan", label: "Kredit" },
  { value: "other", label: "Boshqa" },
];

export const STATUS_OPTIONS = [
  { value: "", label: "Barcha statuslar" },
  { value: "uploaded", label: "Qoralama" },
  { value: "processing", label: "Tahlil qilinmoqda" },
  { value: "analyzed", label: "Tahlil qilindi" },
  { value: "approved", label: "Tasdiqlandi" },
  { value: "rejected", label: "Rad etildi" },
];

export const ANALYZABLE_STATUSES = ["pending", "draft"];


