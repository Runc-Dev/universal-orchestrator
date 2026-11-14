---
name: universal-orchestrator
description: Coordinate delegated repository work in Codex or Claude Code using Opus 5.5 for planning, Codex GPT-6.1 Sol for implementation, agy for simple research and checks, and Fable 5.2 for advice, with separate Git worktrees and quota-aware parallelism. Use when this multi-CLI workflow is requested or already active.
---

# Universal Orchestrator

Bu skill aynı dosyalarla Codex ve Claude Code'da çalışır. Amaç: Opus karar verir, Codex kodlar, agy basit işleri yürütür, Fable gerektiğinde danışmanlık yapar. Skill'i hazırlamak veya açıklamak, bu workflow'u başlatmak değildir.

## Değişmeyen rol dağılımı

| Rol | CLI / model | Görev | Sınır |
| --- | --- | --- | --- |
| Ana orkestratör | Claude / `claude-opus-5-5` | Plan, görev bağımlılıkları, iş dağıtımı, sonuç değerlendirme, entegrasyon kararı | Uygulama kodu, test kodu, patch veya çözüm script'i yazmaz |
| Kodlama işçisi | Codex / `gpt-6.1-sol` | Kod, test, refactor, yapılandırma değişikliği, hata ve merge conflict düzeltme | Yalnız kendisine verilen kapsam |
| Basit işçi / scout | agy / keşfedilen uygun hafif model | Dosya keşfi, kısa araştırma, mevcut testleri çalıştırma, log özeti | Kaynak/test/yapılandırma kodu değiştirmez |
| Advisor | Claude / `claude-fable-5-2` | Mimari eleştiri, kritik risk, Opus'un çözemediği belirli karar | Araçsız; kod ve patch yazmaz; karar yetkisi Opus'ta |
| İsteğe bağlı yardımcı | Claude / `claude-sonnet-5-5`, gerekirse `claude-opus-5-5` | Bağımsız analiz, gereksinim veya plan incelemesi | Araçsız; kod yazmaz; aynı anda en fazla iki ek Claude yardımcısı |

Claude'a kodu ayrıntılı yazdırıp Codex'e kopyalatma. Opus hedefi, arayüzü ve kabul ölçütlerini tarif eder; çözümün kodunu Codex üretir. Orkestratörün görev metni, durum kaydı ve mekanik Git işlemleri bu kısıtın dışında kalır.

## Giriş ortamını doğru ele al

- **Claude Code'da:** etkin modelin Opus 5.5 olduğunu doğrula. Farklıysa mevcut oturumu değiştirmiş gibi davranma; Opus CLI planlayıcısını kullan veya desteklenen model seçimiyle geçiş yap.
- **Codex'te:** mevcut Codex modeli Opus'a dönüşmez. Codex ana oturumu taşıyıcıdır: bağlamı derler, Opus CLI'dan plan ve karar alır, bu kararları CLI işçilerine uygulatır ve raporları Opus'a geri verir. Planın mimari kararlarını kendisi devralmaz.
- **Bir işçi olarak çağrıldıysan:** `WORKFLOW_ROLE=worker` veya `WORKFLOW_ROLE=advisor` görev metnini uygula; bu skill ile yeniden orkestratör/işçi zinciri başlatma.

## Ön kontrol

İlk kullanımda [CLI ve çalışma referansını](references/workflow.md) oku. Paketle gelen `scripts/run_agent.py` CLI başlatma, süre sınırı ve kayıt içindir; kendi başına görev zamanlayıcısı değildir.

1. Repo talimatlarını (`AGENTS.md`, `CLAUDE.md` ve ilgili alt dizin kuralları), Git durumunu ve kullanılabilir CLI'ları kontrol et. `run_agent.py doctor` model çağrısı yapmadan sürümleri gösterir.
2. Tam model kimliklerini kullan; alias'ların doğru sürüme çözüleceğini varsayma. Opus 5.5 için Claude Code en az `2.1.280`; Fable 5.2 için en az `2.1.321`; Sonnet 5.5 için en az `2.1.284` gerekir. Daha yeni gereksinimi kurulu yardım veya resmi belgeyle karşılaştır.
3. `agy models` ile gerçekten sunulan modelleri gör. 14.11.2026 tarihli doğrulama ortamında `gemini-3.8-flash-low` listelendi; basit keşif için başlangıç tercihi bu. Zorlaşan salt okuma görevinde listelenen medium/high seçeneğine geç veya görevi küçült. Başka hesapta listeyi yeniden doğrula.
4. Model erişimi, yetki veya gerekli CLI yoksa aynı rolü sessizce başka modele verme. Bağımsız işleri sürdür, engellenen rolü açıkça bildir. CLI güncellemesi, yeni üyelik veya ücretli kullanım açmayı otomatik yapma.
5. Repo yoksa Git/worktree kurgulama veya kendiliğinden `git init` yapma. Dosya dışı analizleri bağımsız çalışma klasörlerinde yürüt; kodlama için hedef repoyu belirle.

## Workflow'u aç

İşi gerçekten başlatırken hedefi, başarı ölçütünü, kapsam dışını ve kısa planı kullanıcıya göster. Host'un plan/görev görünümü varsa kullan; yoksa kalıcı görev tablosu oluştur. Yeni Codex sohbeti açmak veya otomasyon kurmak gerekmez.

Opus her görev için şunları belirler:

```text
id, rol, model, hedef, gerekli_baglam, base_sha,
bagimliliklar, worktree, branch, izinli_dosyalar,
kabul_olcutleri, dogrulama, sure_siniri, durum
```

Durumlar: `pending -> ready -> running -> review -> done`; ayrıca `blocked`, `failed`, `cancelled`. `done` yalnız doğrulama kanıtı ve entegrasyon sonucu mevcutsa kullanılır. Çıkış kodu 0 veya işçinin başarı iddiası yeterli değildir.

Önce kısa bir agy keşfiyle gereken dosyaları ve mevcut doğrulama komutlarını bul; Opus'un bütün repoyu okumasına gerek bırakma. Sadece eksik bağlamı getir. Fable'a tüm konuşma yerine belirli karar, seçenekler ve ilgili kanıtı ver.

## Paralel çalışma ve worktree sahipliği

- Sabit bir başlangıç commit'i kaydet. Kullanıcının commit edilmemiş değişikliklerini silme, stash etme veya kendiliğinden commit etme. Görev bu değişikliklere bağlıysa worktree tabanını nasıl taşıyacağını netleştir; HEAD'den açılan worktree'nin onları içerdiğini varsayma.
- Her aktif işçiye ayrı worktree ve tek görev ver. Okuma işçileri/advisor için detached worktree, kodlama için ayrı branch uygundur. Önceden bulunan uygun bir worktree'yi ancak başka işçi kullanmıyorsa kullan.
- Host worktree araçları sağlıyorsa onları kullan; yoksa referanstaki Git komutlarını kullan. Worktree'leri repo dışında tut; run kayıtlarını Git ortak dizini altına veya repo dışındaki bir klasöre yaz.
- Yalnız bağımsız ve dosya sahipliği çakışmayan görevleri paralelleştir. Aynı dosyayı, lockfile'ı, şemayı veya migration sırasını etkileyen görevleri sırala. Git worktree ortak Git metadatasını paylaşır; bu tam güvenlik izolasyonu değildir.
- Başlangıç sınırı: aynı anda en fazla **3 dış CLI işçisi**. Fable ve ek Claude yardımcıları da bu sayıya dahildir; ana host dahil değildir. Önce 2 Codex + 1 agy gibi gerçek ihtiyaca göre dağıt; boş kontenjanı doldurmak için işçi açma.
- İşçiler başka agent çağırmaz; paket yükleme, ortak servis/port, veritabanı ve cache gibi paylaşılan yan etkileri görevde açıkça ayır. Worktree ortam değişkenlerini, bağımlılıkları ve untracked dosyaları otomatik taşımaz.

## Limit ve bütçe kararı

Başlangıçta, her yeni paralel dalgadan önce, Fable/ek Claude çağrısından önce ve limit hatasından sonra sağlayıcı kullanımını kontrol et. Ana oturum ve aynı hesaptaki yardımcılar ortak kotayı tüketebilir; yeni agent açmak kota yenilemez.

- Claude'un erişilebilir `/usage` ekranı veya desteklenen kullanım verisi; Codex'in erişilebilir `/status`/sağlayıcı verisi; agy'nin gerçekten sunduğu kullanım verisini kullan. Slash komutlarını doğrulamadan `claude -p /usage`, `codex usage` gibi shell komutlarına dönüştürme.
- Her sağlayıcı için `source`, `checked_at`, varsa oturum/haftalık/model bazlı `remaining_percent`, `reset_at`, `status` kaydet. Birden çok pencere varsa en kısıtlayıcı ilgili pencereyi esas al. 15 dakikadan eski veya reset zamanı geçmiş ölçümü yeniden kontrol et; alınamıyorsa `unknown` yaz.
- **Kalan > %40:** normal paralellik; ancak gerçek bağımsız iş varsa 1–2 ek Sonnet/Opus analiz yardımcısı kullanılabilir. Sonnet'i öncele, Opus'u zor plan ayrışmasına ayır.
- **Kalan %20–40:** en fazla 2 işçi; ek Claude yardımcısı açma; Fable'ı yalnız kritik ve belirli bir karara ayır.
- **Kalan < %20:** etkilenen sağlayıcıda en fazla 1 işçi; ek Claude/Fable açma; bağımsız işleri mevcut yetkili diğer sağlayıcılara yönlendir. Codex kodlama modelini değiştirme.
- **Limit bilinmiyor:** en fazla 2 işçi; isteğe bağlı Claude yardımcılarını açma. Gerekli bir Fable incelemesi en fazla bir kısa çağrı olabilir; görünür limit uyarısı varsa onu da başlatma. Devamı için ölçüm topla.
- **Limit dolu / 429:** etkilenen sağlayıcıda yeni iş başlatma; bildirilen reset veya Retry-After'a uy. Sadece geçici hata ise ve süre sınırı elveriyorsa en fazla bir yeniden deneme yap. Aynı hesaba yeni agent açarak döngüye girme.

Yüzde eşikleri bu workflow'un ayarlanabilir tercihidir; sağlayıcı garantisi değildir. Token sayısı, API dolar maliyeti ve kalan abonelik kotası ayrı verilerdir. `--max-budget-usd` abonelikte kalan yüzdeyi ölçmez. Sağlayıcılar arasında limit yüzdelerini toplama.

"Limit az gidiyor" ifadesini **tüketim düşük ve kalan kapasite yeterli** olarak yorumla. Kalan limit azaldığında ek Opus açma. Kullanıcı başka bir bütçe kuralı verirse onu uygula.

## Advisor ve geri bildirim

Önemli kodlama işinde, kota elveriyorsa plan kararlı hale gelirken **bir Fable 5.2 advisor** çağır. Basit ve belirli bir düzeltmede veya düşük kotada atlanabilir; sebebini kaydet. Fable'dan en fazla beş önemli bulgu, kanıtı ve önerdiği kararları iste. Her küçük adımda yeniden çağırma. İkinci çağrı ancak yeni kritik risk veya Opus'un çözemediği belirli bir anlaşmazlık için yapılır.

Fable ve ek Claude yardımcılarını `run_agent.py` ile araçsız başlat; gereken dosya parçalarını görev metnine koy. Opus görüşleri değerlendirir; kabul edilen değişiklikleri Codex'e görev olarak geri gönderir.

## Entegrasyon ve kapanış

İşçi raporu şunları içersin: özet, değişen dosyalar, commit varsa SHA, çalıştırılan komutlar ve sonuçları, kalan risk, engel ve sonraki bağımlılık. Kaynak dosyaları ve raporu ayrı tut; işçiye genel sohbet geçmişini yığma.

Opus sonuçları kabul eder veya kapsamı belirli yeni görev verir. Mekanik Git stage/commit/cherry-pick işlemlerini host yapabilir; kaynak, test ve conflict düzeltmesini Codex yapar. Yalnız incelenmiş açık dosya listesini stage et; `git add -A` ile kullanıcı dosyalarını toplama.

Entegrasyonu ayrı bir worktree/branch üzerinde bağımlılık sırasıyla yap. İlgili test, lint ve build kontrollerini birleşmiş sonuç üzerinde çalıştır. Başarısızlıkları Codex'e döndür; çalışan işçilerin ortak tabanını sessizce değiştirme. Kullanıcı istemedikçe push, deploy veya uzak merge yapma.

Durumu ve aktif süreçleri aralarda kısa güncellemelerle bildir. Süre aşımı veya iptalde ilgili süreç ağacını durdur; yarım kalan dosyaları başarı sayma. Tamamlanan değişiklikler güvenle taşınmadan branch/worktree silme; `--force` temizlik yapma. Host'un yönettiği worktree'leri yine host aracıyla arşivle.

Son mesajda sonucu, doğrulama kanıtını, branch/worktree konumunu, varsa limit/model engelini ve kalan işi belirt. Workflow'u kapatmak için her zorunlu görev doğrulanmış veya açıkça engellenmiş olmalıdır; engellenen işi tamamlandı olarak sunma.
