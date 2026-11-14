# Değişiklik kaydı

Sürümler [SemVer](https://semver.org/lang/tr/) izler. Sürüm numarası `VERSION` dosyasında ve `run_agent.py --version` çıktısındadır.

## 2.0.0 — 2026-11-14

### Kırıcı değişiklikler
- `references/workflow.md` kaldırıldı; içerik `roles-and-quota.md`, `git.md`, `prompts.md`, `state-and-map.md` dosyalarına bölündü.
- `scout` rolünün varsayılan modeli sabit `gemini-3.8-flash-low` yerine `auto` oldu (`agy models` listesinden seçilir).

### Eklenenler
- `reviewer` rolü: agy + Gemini 4 Argon (high/medium) ile salt okuma diff ve test incelemesi.
- agy otomatik model seçimi: scout için Argon low/minimal → Flash low, reviewer için Argon high/medium → Argon → Pro. Seçim `request.json` → `model_selection` alanına yazılır.
- `doctor` artık agy model listesini ve otomatik seçimi gösteriyor.
- Her çalıştırma sonunda `answer.txt` (Claude/agy JSON çıktısından ayıklanır) ve kısa `answer_preview`; orkestratör ham logları okumak zorunda kalmıyor.
- Repo haritası (`repo-map.md`, Obsidian uyumlu) ve `state.json` biçimi: koşular arasında yeniden kullanılan, kısa bağlam.
- Kurucuda `--upgrade`: eski kurulum `.skill-backups/` altına taşınır (skill dizini dışında).
- `run_agent.py --version`.

### Değişenler
- `SKILL.md` ~11 KB'tan ~4 KB'a indi; ayrıntılar yalnız gerektiğinde okunan referanslarda.
- Skill başına "küçük iş kapısı": küçük işlerde orkestrasyon açılmaz.
- Rol kısıtlarının yalnız açık çağrıda ve iş bitene kadar geçerli olduğu yazıldı; iş bitince normal moda dönülür.
- Claude Code kopyasına kurucu `disable-model-invocation: true` ekler: skill yalnız `/universal-orchestrator` ile yüklenir.

## 1.0.0 — 2026-11-14
- İlk sürüm.
