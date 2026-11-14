# Universal Orchestrator

**Sürüm 2.0.0** · [Değişiklik kaydı](CHANGELOG.md)

A shared skill for **Codex and Claude Code**: Opus 5.5 plans, Codex GPT-6.1 Sol implements, agy (Gemini 4 Argon / Flash) scouts and reviews, and Fable 5.2 advises. Workers use separate Git worktrees with quota-aware concurrency.

Ortak bir skill ile **Opus planlasın, Codex kodlasın, agy Argon incelesin, Fable danışman olsun**. Claude modellerine uygulama veya test kodu yazdırmadan, bağımsız işleri ayrı worktree'lerde paralel yürütün.

## Roller

| Rol | CLI / model | Sorumluluk |
| --- | --- | --- |
| Orkestratör | Claude / `claude-opus-5-5` | Planlama, görev dağıtımı, bağımlılıklar ve sonuç değerlendirme |
| Kodlama işçisi | Codex / `gpt-6.1-sol` | Kod, test, refactor, hata ve conflict düzeltme |
| Keşif (scout) | agy / `auto`: Argon low/minimal, yoksa Flash low | Salt okuma keşif, repo haritası, test çalıştırma, log özeti |
| İnceleme (reviewer) | agy / `auto`: Argon high/medium | Salt okuma diff incelemesi ve kabul kontrolü |
| Advisor | Claude / `claude-fable-5-2` | Gerektiğinde araçsız mimari ve risk değerlendirmesi |
| Ek analiz yardımcısı | Sonnet 5.5 veya Opus 5.5 | Yeterli kota ve bağımsız iş varsa en fazla 1–2 yardımcı |

agy modelleri `agy models` listesinden otomatik seçilir; Argon hesabında yoksa Flash'a düşer ve bu seçim kayda geçer. Coder, planner ve advisor modelleri sabittir; erişim olmadığında başka modele sessizce geçilmez.

## v2'de token tasarrufu

- `SKILL.md` ~11 KB'tan ~4 KB'a indi; Git, kota, prompt ve durum ayrıntıları ayrı referanslarda, yalnız gerektiğinde okunur.
- **Küçük iş kapısı:** tek dosyalık işlerde orkestrasyon açılmaz.
- **Repo haritası:** scout bir kez `repo-map.md` üretir (Obsidian uyumlu wikilink'lerle); sonraki koşular yalnız değişen modülleri günceller.
- **`state.json`:** orkestratör sohbet geçmişi yerine kısa durum dosyasını okur.
- **`answer_preview`:** betik yalnız işçinin son yanıtını kısaltılmış yazdırır; ham JSON loglar okunmaz.
- **Reviewer:** diff incelemesi Opus yerine agy Argon'da yapılır.

## İndir ve kur

[Son sürümü indir](https://github.com/Runc-Dev/universal-orchestrator/releases/latest) veya repoyu klonla:

```sh
git clone https://github.com/Runc-Dev/universal-orchestrator.git
cd universal-orchestrator
```

İndirdiğin ZIP'i açtıysan `install-skill.py` dosyasının bulunduğu klasörde terminal aç. Mevcut proje yolunu ver:

```sh
python install-skill.py --project "YOUR_PROJECT_PATH" --dry-run
python install-skill.py --project "YOUR_PROJECT_PATH"
```

Sisteminde Python komutu `python3` ise onu kullan. Kurucu aynı skill'i iki yere kopyalar:

```text
YOUR_PROJECT_PATH/
  .agents/skills/universal-orchestrator/    # Codex
  .claude/skills/universal-orchestrator/    # Claude Code
```

Mevcut skill kurulumunun üzerine yazılmaz. v1'den yükseltmek için `--upgrade` ekle; eski kopya `YOUR_PROJECT_PATH/.skill-backups/` altına taşınır. Kurucu yalnız proje içine dosya kopyalar; CLI kurmaz, hesaplara giriş yapmaz veya model çağırmaz.

Claude Code kopyasına `disable-model-invocation: true` eklenir: skill yalnız `/universal-orchestrator` yazdığında yüklenir, Claude onu kendiliğinden devreye sokmaz. Elle kurulumda bu satırı Claude kopyasının frontmatter'ına kendin ekle.

Tüm projeler için elle kurulum: `universal-orchestrator/` klasörünü Codex'in etkin kullanıcı skill dizinine (güncel varsayılan `~/.agents/skills/`) ve Claude'un etkin kullanıcı skill dizinine (`~/.claude/skills/`) kopyala. Özel/eski Codex ortamında `~/.codex/skills/` kullanılıyor olabilir; aynı skill'i birden çok keşfedilen dizine kurma. [Codex skill dizinleri](https://learn.chatgpt.com/docs/build-skills), [Claude skill dizinleri](https://code.claude.com/docs/en/skills).

## Kullan

Claude Code'u Opus 5.5 ile aç:

```sh
claude --model claude-opus-5-5
```

Claude Code'da:

```text
/universal-orchestrator Bu repoda kullanıcı profil düzenleme özelliğini tamamla.
```

Codex'te:

```text
$universal-orchestrator Bu repoda kullanıcı profil düzenleme özelliğini tamamla.
```

Codex girişinde ana Codex oturumu taşıyıcı olarak çalışır: plan ve sonraki kararları CLI üzerinden Opus'a hazırlatır, işçileri başlatır ve raporları geri iletir. Skill mevcut Codex modelini Opus'a dönüştürmez. Gerekirse yeni skill'in keşfedilmesi için oturumu yeniden aç.

## Gereksinimler

- Python **3.10+** ve Git.
- Kurulu ve kendi hesabınla yetkilendirilmiş `codex`, `claude`, `agy` CLI'ları; hedef modellere hesap/sağlayıcı erişimi.
- Claude Code **2.1.321+**: Fable 5.2 için minimum sürüm. Opus 5.5 minimumu `2.1.280`, Sonnet 5.5 minimumu `2.1.284`. [Resmi model uyumluluğu](https://code.claude.com/docs/en/model-config).
- Windows'ta npm `.ps1` başlatıcıları için PowerShell **7.3+**. Native executable yolunda PowerShell adaptörü gerekmez.

Model kimlikleri ve minimum sürümler 14 Kasım 2026 tarihinde kontrol edildi. Kullandığın sürümün `--help` çıktısını ve sağlayıcı erişimini yeniden doğrula.

Skill klasöründeki ön kontrol:

```sh
python universal-orchestrator/scripts/run_agent.py doctor
agy models
```

`doctor` kurulu sürümleri kontrol eder; canlı kota veya model erişimi ölçmez. Gerekli CLI/sürüm eksikse çıkış kodu `2` ve `workflow_ready: false` döndürür.

## Workflow

1. agy kısa bir keşif yapar; Opus görevleri ve kabul ölçütlerini belirler.
2. Gerekiyorsa Fable belirli bir plan veya risk hakkında görüş verir.
3. Bağımsız görevler ayrı worktree ve dosya sahipliğiyle CLI işçilerine verilir.
4. Opus sonuçları değerlendirir; düzeltmeler Codex'e döner.
5. Entegrasyon ayrı worktree'de yapılır; birleşmiş sonuç doğrulanır.

Varsayılan üst sınır aynı anda 3 dış CLI işçisidir. Limit azaldıkça paralellik azaltılır. Bilinmeyen kota `unknown` olarak kaydedilir; yeni agent açmak ortak hesap kotasını yenilemez.

`run_agent.py` tek çağrıyı yürütür, süre sınırı ve ayrı kayıtlar tutar. Bağımsız scheduler veya otomatik kota sorgulayıcı değildir; planlama ve kota kararlarını skill'i kullanan ana agent verir. Claude alt süreçleri araçsız çalışır ve ihtiyaç duydukları bağlamı prompt'tan alır. Ana oturumun rol sınırları skill talimatıdır; bütün host davranışlarını zorlayan bir güvenlik hook'u değildir.

## Doğrulama

```sh
python -m unittest discover -s tests -v
```

v2'de 13 test Linux'ta geçti (v1'in 9 testi Windows'ta da geçmişti): argüman/stdin aktarımı, kayıtların korunması, sabit model rolleri, sürüm kontrolü, timeout ve alt süreçlerin durdurulması, iki host'a kurulum ve yükseltme, agy otomatik model seçimi, yanıt ayıklama. Testler yapay CLI kullanır; model çağrısı yapmaz.

Tam modeller arası workflow ve canlı kota sorgusu bu sürümde uçtan uca doğrulanmadı. v2 Windows ve macOS'ta henüz çalıştırılmadı. Ayrıntılar: [VALIDATION.md](VALIDATION.md).

- [Ortak skill](universal-orchestrator/SKILL.md)
- [Roller, agy model seçimi ve kota](universal-orchestrator/references/roles-and-quota.md)
- [Repo haritası ve durum dosyası](universal-orchestrator/references/state-and-map.md)
- [Worktree ve entegrasyon](universal-orchestrator/references/git.md)
- [İşçi prompt şablonları](universal-orchestrator/references/prompts.md)

## Lisans

[MIT](LICENSE). Kullanabilir, değiştirebilir ve lisans koşullarıyla paylaşabilirsin.
