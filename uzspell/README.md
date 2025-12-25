# Uzbek Hunspell Spellchecker API

Bu katalogda Hunspell asosida o'zbek lotin va kirill imlo tekshiruvchisi uchun kodlar va lug'atlar bo'ladi.

## 1. Lug'atlarni yuklash

- Lotin va kirill uchun .dic va .aff fayllarni quyidagi manzildan yuklab oling:
  - https://github.com/tumaps/hunspell-uz

Fayllarni `uzspell/dict/latin/` va `uzspell/dict/cyrillic/` papkalarga joylashtiring:

```
uzspell/
  dict/
    latin/
      uz_UZ.dic
      uz_UZ.aff
    cyrillic/
      uz_UZ@cyrillic.dic
      uz_UZ@cyrillic.aff
```

## 2. Python kutubxonasini o'rnatish

- pyhunspell yoki pyenchant tavsiya etiladi:
  ```bash
  pip install hunspell
  # yoki
  pip install pyenchant
  ```

## 3. API yaratish

Keyingi bosqichda Flask/FastAPI kod namunasi va testlar qo'shiladi.
