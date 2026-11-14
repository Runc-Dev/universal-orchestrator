# Durum dosyası ve repo haritası

Amaç: orkestratörün bağlamını küçük tutmak. Uzun sohbet geçmişi yerine diskteki kısa dosyaları oku ve güncelle.

## Konum

Hepsi çalışma ağacının dışında, Git ortak dizininde:

```text
<git rev-parse --git-common-dir>/orchestrator/
  repo-map.md            # kalıcı, koşular arasında yeniden kullanılır
  runs/<run-id>/
    state.json           # görevler, durumlar, kota kaydı
    <task-id>/           # run_agent.py --out dizini
```

## repo-map.md

Scout üretir, orkestratör okur. Obsidian uyumlu Markdown'dır (wikilink'ler Obsidian'da grafik olarak görünür), ama model için önemli olan kısa olmasıdır: hedef en fazla ~150 satır.

```markdown
---
base_sha: 1a2b3c4
generated_at: 2026-11-14T11:00:00Z
---
# Repo haritası

## Modüller
- [[api]] — `src/api/`: HTTP katmanı. Bağlı: [[db]], [[auth]]
- [[db]] — `src/db/`: şema ve migration'lar. Migration sırası kritik.
- [[ui]] — `web/`: React. Bağlı: [[api]] (yalnız `web/src/client.ts` üzerinden)

## Komutlar
- test: `npm test` (api), `npm --prefix web test` (ui)
- lint: `npm run lint`

## Riskli dosyalar
- `package-lock.json`, `src/db/migrations/*` — paralel görevlere bölme
```

Kurallar:

- `base_sha` ile `git rev-parse HEAD` arasındaki değişen dosyalar haritadaki modüllere dokunuyorsa yalnız o bölümleri scout'a güncellet; bütün haritayı baştan üretme.
- Modül bağlantıları (`Bağlı:` satırları) paralellik kararının girdisidir: bağlı modüllere dokunan görevleri aynı dalgaya koyma.
- Haritada kod gövdesi olmaz; yalnız yol, sorumluluk, bağımlılık ve komut.

## state.json

```json
{
  "run_id": "20261114-1100",
  "base_sha": "1a2b3c4",
  "goal": "Profil düzenleme",
  "out_of_scope": ["e-posta doğrulama"],
  "quota": {"claude": {"status": "unknown", "checked_at": null}},
  "tasks": [
    {"id": "API-01", "role": "coder", "goal": "PATCH /profile",
     "files": ["src/api/profile.ts", "src/api/profile.test.ts"],
     "depends_on": [], "worktree": "../orchestrator-worktrees/20261114-1100/api",
     "acceptance": ["400 geçersiz e-posta"], "verify": ["npm test -- profile"],
     "status": "running", "out": "runs/20261114-1100/API-01-1"}
  ]
}
```

Durumlar: `pending → ready → running → review → done`, ayrıca `blocked`, `failed`, `cancelled`.

Her karar turunda yalnız `state.json` ve yeni gelen `answer_preview`'lar okunur. Codex girişinde planner'a da sohbet geçmişi değil, bu dosya verilir.
