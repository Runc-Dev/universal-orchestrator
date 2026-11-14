---
name: universal-orchestrator
description: Multi-CLI repo workflow (v2) - Opus plans, Codex GPT-6.1 Sol codes, agy (Gemini Argon/Flash) scouts and reviews, Fable 5.2 advises, each in its own Git worktree. Use only when the user explicitly invokes universal-orchestrator; never for ordinary coding questions.
---

# Universal Orchestrator v2

Bu talimatlar yalnız kullanıcı skill'i açıkça çağırdığında ve yalnız o iş bitene kadar geçerlidir. İş kapandığında (veya kullanıcı "normal moda dön" dediğinde) rol kısıtları biter; normal asistan gibi davran. Skill'i açıklamak veya düzenlemek workflow başlatmak değildir.

## 0. Önce kapı: orkestrasyon gerekli mi?

Kullanıcı açıkça çağırmış olsa bile önce işin boyutunu tahmin et:

- **Küçük iş** (tek dosya, kısa düzeltme, soru, açıklama): orkestrasyon açma. Kullanıcıya "bu iş için doğrudan yapmak daha ucuz" de ve onay alırsan normal modda kendin yap.
- **Büyük iş** (birden çok bağımsız parça, birden çok dosya grubu): aşağıdaki akışı aç.

Bu kapı token tasarrufunun en büyük kaynağıdır; her işte zorunlu çok-agent akışı açma.

## 1. Roller

| Rol | `run_agent.py --role` | Model | Sınır |
| --- | --- | --- | --- |
| Orkestratör | (ana oturum) | `claude-opus-5-5` | Plan, dağıtım, kabul kararı. Uygulama/test kodu yazmaz |
| Kodlama | `coder` | Codex `gpt-6.1-sol` | Yalnız verilen dosya kapsamı |
| Keşif | `scout` | agy, `auto`: Argon low/minimal, yoksa Flash low | Salt okuma: dosya bulma, test çalıştırma, log özeti |
| İnceleme | `reviewer` | agy, `auto`: Argon (medium/high) | Salt okuma: diff incelemesi, test/kabul kontrolü |
| Advisor | `advisor` | `claude-fable-5-2` | Araçsız, en fazla 5 bulgu, kod yazmaz |
| Yardımcı | `helper` | `claude-sonnet-5-5` (gerekirse Opus) | Araçsız analiz, isteğe bağlı |

agy modelleri `auto` iken `agy models` listesinden seçilir ve seçim `request.json`'a yazılır. Listede uygun model yoksa rol engellenir; coder/planner/advisor asla sessizce değişmez. Ayrıntı: [roles-and-quota.md](references/roles-and-quota.md).

## 2. Akış

1. **Ön kontrol:** `python scripts/run_agent.py doctor` (sürümler + agy model seçimi). Repo talimatlarını (`CLAUDE.md`, `AGENTS.md`) ve `git status`u oku.
2. **Repo haritası:** `<git-common-dir>/orchestrator/repo-map.md` varsa ve `base_sha` güncelse onu oku; yoksa scout'a üret. Bütün repoyu kendin okuma. Biçim: [state-and-map.md](references/state-and-map.md).
3. **Plan:** Görevleri `state.json`'a yaz (id, rol, hedef, izinli dosyalar, bağımlılık, kabul ölçütü, doğrulama, durum). Kullanıcıya hedefi, kapsam dışını ve kısa planı göster.
4. **Dağıt:** Bağımsız ve dosya çakışmasız görevleri ayrı worktree'lerde, aynı anda en fazla 3 dış CLI işçisiyle çalıştır. Git komutları: [git.md](references/git.md). Prompt şablonu: [prompts.md](references/prompts.md).
5. **Değerlendir:** Yalnız betiğin yazdırdığı `answer_preview`'u ve gerekiyorsa `answer.txt`'yi oku; `stdout.log`/`stderr.log`'u yalnız hata ayıklarken aç. Diff'i `reviewer`'a inceletmek Opus bağlamından ucuzdur.
6. **Düzelt / entegre et:** Düzeltmeler Codex'e döner. Entegrasyon ayrı worktree'de, bağımlılık sırasıyla; birleşmiş sonuçta test/lint/build çalışır.
7. **Kapat:** Sonuç, doğrulama kanıtı, branch/worktree konumu, engeller. Ardından normal moda dön.

## 3. Değişmez kurallar

- `done` = doğrulama kanıtı + entegrasyon. Exit 0 veya işçinin "bitti" demesi yetmez.
- Kullanıcının commit edilmemiş değişikliklerini silme, stash etme, commit etme. `git add -A`, `--force` temizlik, push, deploy yok (kullanıcı istemedikçe).
- Erişim/CLI/model yoksa rolü başka modele kaydırma; engeli bildir, bağımsız işleri sürdür.
- Kota: ölçülemiyorsa `unknown` say ve en fazla 2 işçi çalıştır. Eşikler: [roles-and-quota.md](references/roles-and-quota.md).
- İşçi olarak çağrıldıysan (`WORKFLOW_ROLE=worker|advisor`) bu skill'le yeni zincir başlatma.
