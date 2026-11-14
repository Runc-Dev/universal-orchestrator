# Roller, modeller ve kota

Bu dosyayı ön kontrolde ve her yeni paralel dalgadan önce oku.

## Sabit ve otomatik modeller

| `--role` | CLI | Model | Değiştirilebilir mi |
| --- | --- | --- | --- |
| `planner` | claude | `claude-opus-5-5` (Claude Code >= 2.1.280) | Hayır |
| `coder` | codex | `gpt-6.1-sol`, `workspace-write` sandbox | Hayır |
| `advisor` | claude | `claude-fable-5-2` (>= 2.1.321) | Hayır |
| `helper` | claude | `claude-sonnet-5-5` (>= 2.1.284), `--model claude-opus-5-5` | Yalnız bu iki model |
| `scout` | agy | `auto` | `--model <agy models listesinden>` |
| `reviewer` | agy | `auto` | `--model <agy models listesinden>` |

### agy `auto` seçimi

`run_agent.py`, `agy models` çıktısındaki kimlikleri sırayla şu tercihlere göre eşler (ilk eşleşen kazanır):

- **scout:** `argon` + `minimal|low` → `flash` + `low` → herhangi bir `flash`
- **reviewer:** `argon` + `high|medium` → herhangi bir `argon` → `pro` + `high|medium`

Gemini 4 Argon her hesapta yoktur (Ultra / bazı Enterprise hesaplarında listelenir). Listede yoksa tercih listesi bir sonraki modele geçer ve bu, `request.json` içindeki `model_selection` alanında kayıtlıdır. Hiçbiri yoksa rol engellenir. Tercih listesini değiştirmek için `run_agent.py` içindeki `AGY_PREFERENCES`'ı düzenle.

agy yalnız `--mode plan` ile çalışır; salt okuma bir talimattır, OS sandbox'ı değildir. agy'ye kod yazdırmak (ikinci coder) bu sürümde yok: agy'nin yazma kipi bayrakları doğrulanmadan eklenmedi.

## Claude alt süreçleri

`--tools ""`, boş MCP yapılandırması ve `--disable-slash-commands` ile çalışır: dosya okuyamaz, bağlamı prompt'tan alır. Gerekli kod parçalarını prompt'a koy. Claude Code içinden `claude -p` nested-session hatası verirse kaydet ve rolü engelli bırak; guard değişkenlerini kaldırma.

## Kota kararı

Her sağlayıcı için `source`, `checked_at`, `remaining_percent`, `reset_at`, `status` kaydını `state.json`'a yaz. 15 dakikadan eski ölçümü yenile; ölçülemiyorsa `unknown`. Slash komutlarını (`/usage`, `/status`) shell komutu varsayma.

| Kalan | Davranış |
| --- | --- |
| > %40 | En fazla 3 işçi; bağımsız iş varsa 1–2 helper (Sonnet öncelikli) |
| %20–40 | En fazla 2 işçi; helper yok; Fable yalnız kritik karar |
| < %20 | O sağlayıcıda en fazla 1 işçi; helper/Fable yok |
| unknown | En fazla 2 işçi; helper yok; Fable en fazla bir kısa çağrı |
| dolu / 429 | O sağlayıcıda yeni iş yok; Retry-After'a uy; en fazla bir yeniden deneme |

Eşikler bu workflow'un tercihidir, sağlayıcı garantisi değildir. Yeni agent açmak kotayı yenilemez. Sağlayıcı yüzdelerini toplama.

## Advisor

Önemli kodlama işinde, kota elveriyorsa plan oturunca bir Fable çağrısı. Belirli soru + seçenekler + ilgili kod parçası ver; en fazla 5 bulgu iste. İkinci çağrı yalnız yeni kritik risk için.
