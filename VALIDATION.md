# Doğrulama kaydı — 14.11.2026

Skill Creator `quick_validate.py`: başarılı.

CLI başlatıcısı ve kurucu için gerçek yerel süreçlerle 9 test geçti. Testlerde yapay CLI kullanıldı; ücretli model çağrısı yapılmadı.

1. Kodlama işçisinde Türkçe stdin, boşluk ve `&` içeren yollar; loglar ve son yanıt dosyası.
2. Advisor'da boş `--tools` argümanının Windows PowerShell üzerinden korunması.
3. Mevcut çıktı dizininin üzerine yazılmaması.
4. Eski Claude sürümünde model çağrısından önce durulması.
5. Dry-run sırasında run dosyası oluşturulmaması.
6. Sabit coder/planner/advisor modellerinin sessizce değiştirilememesi.
7. Run kayıtlarının işçi worktree'sinin içine yazılmasının reddedilmesi.
8. Timeout sırasında işçi ve onun başlattığı alt sürecin durdurulması.
9. Kurucunun iki host dizinine aynı skill'i kopyalaması ve var olan kurulumu ezmemesi.

Gerçek CLI `--version` / `--help` kontrolleri ve `agy models` sorgusu yapıldı. Başlatıcı PATH'te seçilen npm Codex sürümünü kullanıyor: `0.163.0`. Claude Code `2.1.206`; son agy kontrolü `1.5.9`.

Tam workflow bu makinede henüz çalıştırılmadı: kurulu Claude Code hedef modellerin minimum sürümünü karşılamıyor. Gerçek model erişimi, canlı abonelik kotası, Linux/macOS çalıştırması ve proje entegrasyonu bu testlerle kanıtlanmış değildir. `doctor` bu nedenle `workflow_ready: false`, `quota_status: unknown` bildiriyor.
