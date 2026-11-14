# CLI uygulaması ve görev sözleşmesi

Bu referansı ilk workflow kurulurken oku. Komutları mevcut `--help` çıktısıyla karşılaştır; yeni sürüm farklıysa doğrulanmış seçenekleri kullan. Ortak giriş dosyası yalnız standart `name` ve `description` frontmatter alanlarına dayanır; Claude'a özgü `context: fork` veya model alanlarını ortak frontmatter'a koyma.

## Kurulum ve çağırma

Aynı `universal-orchestrator` klasörünü iki yere kopyala:

| Kapsam | Codex | Claude Code |
| --- | --- | --- |
| Proje | `.agents/skills/universal-orchestrator/` | `.claude/skills/universal-orchestrator/` |
| Kullanıcı | `~/.agents/skills/universal-orchestrator/` | `~/.claude/skills/universal-orchestrator/` |

Bazı eski/özelleştirilmiş Codex ortamları `~/.codex/skills` kullanır; etkin skill dizinini kontrol et, aynı adı birden fazla keşfedilen dizine kurma. Claude'un özel yapılandırma kökü varsa onu kullan.

Codex: `$universal-orchestrator Bu repoda ... işini tamamla.`

Claude Code: `/universal-orchestrator Bu repoda ... işini tamamla.`

Model seçimi skill frontmatter'ıyla evrensel biçimde zorlanamaz. Claude Code'u Opus 5.5 ile başlatmak için:

```powershell
claude --model claude-opus-5-5
```

Yeni skill'in keşfedilmesi için gerekirse oturumu yeniden aç. `agents/openai.yaml` yalnız Codex UI metadatasıdır; Claude ortak `SKILL.md` ve destek dosyalarını kullanır.

## CLI yardımcı script'i

Python 3.10+ kullanılır; ek Python paketi gerekmez. `scripts/run_agent.py` CLI'ları shell üzerinden metin birleştirmeden başlatır. Windows'ta npm `.ps1` shim'leri için PowerShell 7.3+ adaptörü kullanılır; native executable için bu gerekmez. Görev stdin'den aktarılır. Ortamın mevcut yetki/hook ayarları korunur.

Önce, skill klasöründeyken:

```powershell
python scripts/run_agent.py doctor
agy models
```

`doctor` kota veya hesap erişimi ölçmez. `run` senkron çalışır; host bağımsız çağrıları kendi background/process araçlarıyla eşzamanlı başlatır ve süreç kimliklerini kaydeder. Cmd.exe'de de aynı Python komutları çalışır; PowerShell'e özgü aşağıdaki Git örnekleri için PowerShell kullan.

Önce komutu yan etkisiz kontrol et:

```powershell
python scripts/run_agent.py run --role coder --worktree 'C:/worktrees/run-a/api' --prompt 'C:/runs/run-a/api-task.txt' --out 'C:/runs/run-a/api' --dry-run
```

Ardından aynı komutu `--dry-run` olmadan çalıştır. `--out` mevcut olmayan bir dizin olmalıdır; kayıtlar üstüne yazılmaz. Log konumu worktree dışında olmalıdır. Her aktif işçi için ayrı `--out` ve ayrı `--worktree` kullan.

Desteklenen roller:

| `--role` | Model | Uygulama |
| --- | --- | --- |
| `planner` | `claude-opus-5-5` | Codex taşıyıcısı için araçsız plan / sonraki karar |
| `coder` | `gpt-6.1-sol` | Kodlama; `workspace-write` sandbox |
| `scout` | `gemini-3.8-flash-low` | agy plan modu; listedeki modeli `--model` ile seç |
| `advisor` | `claude-fable-5-2` | Araçsız Fable görüşü |
| `helper` | `claude-sonnet-5-5` | Araçsız ek analiz; gerekirse `--model claude-opus-5-5` |

`--model` yalnız scout ve helper için değiştirilebilir. Varsayılan timeout 900 saniyedir; görev karmaşıklığına göre `--timeout` belirle. API kullanıcısı ek bir üst sınır isterse Claude rolleri için `--max-budget-usd` verebilir. Script limit politikasını kendisi ölçüp uygulamaz; dalga ve kota kararını Opus/host verir.

Script her çağrıda ilgili CLI sürümünü kontrol eder. Model sunucusuna erişimi önceden kanıtlamaz. Claude rolleri gerekli minimum sürümün altındaysa model çağrısından önce durur. Güncelleme ihtiyacını kullanıcıya bildir; skill'i kurmak otomatik CLI yükseltmesi değildir.

Claude alt süreçleri `--tools ""`, boş MCP yapılandırması ve `--disable-slash-commands` ile çalışır: dosya veya terminal aracı kullanamaz, bağlamları prompt'ta verilmelidir. Bu, ana Claude oturumunun araç izinlerini değiştirmez. agy plan modu bir OS sandbox garantisi değildir; salt okuma kapsamı ve mevcut izinler korunmalıdır. Codex'in sandbox'ı platformda desteklenmiyorsa izin atlama bayrağı ekleme; hatayı bildir.

Claude içinden `claude -p` çağrısı kurulu sürümde nested-session hatası verirse bunu kaydet. Guard değişkenlerini gizlice kaldırma. Host'un desteklediği salt okuma Claude subagent/background agent yolunu aynı sabit modelle kullanabiliyorsan kullan; aksi halde sadece o rolü engelli bırak. Bu fallback ana süreçten sınırsız fan-out izni vermez.

Çıktılar: `request.json`, `prompt.txt`, `stdout.log`, `stderr.log`, `result.json`; Codex için ayrıca `answer.txt`. `result.json` süreç ve exit durumudur, görev kabul kararı değildir. JSON çıktısındaki `is_error`, model bilgisi, limit ve tool-denied sonuçlarını ayrıca incele. Gerçekte kullanılan model istenenden farklıysa bunu kaydet; sürüm eşleşmiş sayma.

## Worktree hazırlığı

Host'ta worktree oluşturma aracı varsa onu öncele. Yoksa temiz ve uygun bir repoda örnek:

```powershell
$repoPath = (git rev-parse --show-toplevel).Trim()
$baseSha = (git rev-parse HEAD).Trim()
$gitCommonPath = (git rev-parse --path-format=absolute --git-common-dir).Trim()
$runId = '20261114-1100'
$runRoot = Join-Path $gitCommonPath "orchestrator-runs/$runId"
$treeRoot = Join-Path (Split-Path $repoPath -Parent) "orchestrator-worktrees/$runId"
New-Item -ItemType Directory -Path $runRoot, $treeRoot | Out-Null
git worktree add -b "orch/$runId/api" (Join-Path $treeRoot 'api') $baseSha
git worktree add -b "orch/$runId/ui" (Join-Path $treeRoot 'ui') $baseSha
git worktree add --detach (Join-Path $treeRoot 'advisor') $baseSha
git worktree add -b "orch/$runId/integration" (Join-Path $treeRoot 'integration') $baseSha
```

İsimleri gerçek koşuya göre benzersiz seç; her Git çıkışını kontrol et, başarısız adımın arkasından devam etme. Worktree silerken önce yolun beklenen treeRoot altında olduğunu, işçinin bittiğini, değişikliklerin taşındığını ve worktree'nin temiz olduğunu doğrula.

Bağımlı görev B, A'nın kodunu gerektiriyorsa B'yi A doğrulanmadan başlatma. B için kaydedilen `base_sha`, gereken A commit'ini içermelidir. Entegrasyonda yalnız henüz uygulanmamış görev commit'lerini bağımlılık sırasıyla taşı. Salt branch adından hangi commit'lerin yeni olduğunu tahmin etme.

Kullanıcının ana çalışma ağacını workflow kayıtları veya worker çıktılarıyla doldurma. Kayıtlar prompt ve kod içerebilir; kimlik bilgisi koyma, uzak yere kendiliğinden yükleme.

## İşçi prompt sözleşmesi

```text
WORKFLOW_ROLE=worker
Görev: API-01
Rol/model: coder / gpt-6.1-sol
Hedef: ...
Base SHA / bağımlılıklar: ...
İzinli dosyalar: ...
Değiştirilmeyecek alanlar: ...
Gerekli bağlam / kabul ölçütleri: ...
Doğrulama komutları: ...
Süre sınırı: ...
Bu görev dışında agent başlatma, push/deploy yapma veya yetki kapsamını genişletme.
Repo ve ilgili alt dizin talimatlarını oku. Başka işçinin dosyalarını düzenleme.
Final raporu: özet; dosyalar; test komutları ve exit kodları; risk/engel.
```

Commit oluşturmayı host'a bırakmak Codex'in ortak `.git` dizinine sandbox dışından yazma ihtiyacını azaltır. İşçi commit yapacaksa bu görevde açıkça belirtilmeli ve yalnız kendi dosyaları olmalıdır. Test üretmek veya kod içeren dokümantasyon örneğini değiştirmek de coder rolüne gider.

Advisor için `WORKFLOW_ROLE=advisor`, belirli soru, kısa plan, ilgili kod/diff parçaları ve seçenekler ver. "Kod/patch yazma; en fazla 5 önemli bulgu; kabul/itiraz gerekçesi ve kanıt" iste. Araçsız olduğu için "git diff'e bak" gibi erişemeyeceği bağlam referansları verme.

Codex girişinde `planner` prompt'u ayrıca görev bağımlılıkları, sahiplik, model, kabul ölçütleri ve sonraki kararları yapılandırılmış JSON olarak istesin. Host biçim veya rol ihlali varsa aynı Opus'a düzeltme isteği döndürsün; kendi planıyla boşluğu doldurmasın. Bir sonraki Opus çağrısına önceki onaylı planı, açık kararları, güncel limit kaydını ve kısa işçi raporlarını ekle. Script oturumlar arası belleğe güvenmez.

## Doğrulama kaynakları

14.11.2026 tarihinde resmi kaynaklar ve yerel `--help`/`agy models` kontrol edildi. Model/CLI uyumluluğu ve dizinler zamanla değişebilir.

- [Codex skills ve keşif dizinleri](https://learn.chatgpt.com/docs/build-skills)
- [Codex CLI komutları](https://learn.chatgpt.com/docs/developer-commands?surface=cli)
- [GPT-6.1 Sol model kimliği](https://developers.openai.com/api/docs/models/gpt-6.1-sol)
- [Claude Code skills](https://code.claude.com/docs/en/skills)
- [Claude Code CLI](https://code.claude.com/docs/en/cli-reference)
- [Claude modelleri ve minimum sürümler](https://code.claude.com/docs/en/model-config)
- [Claude kullanım verisi](https://code.claude.com/docs/en/costs)

agy için bu makinede kurulu `agy --help`, `agy --version`, `agy models` çıktıları esas alındı; başka sürümün internetteki flag'leri doğrulanmadan kullanılmadı.
