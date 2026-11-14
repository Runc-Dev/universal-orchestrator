# İşçi prompt şablonları

Kısa tut: yalnız görevin ihtiyaç duyduğu bağlam. Sohbet geçmişi, bütün plan veya bütün repo haritası verme.

## coder (Codex)

```text
Görev: API-01
Hedef: ...
Base SHA / bağımlılıklar: ...
İzinli dosyalar: ...
Dokunma: ...
Kabul ölçütleri: ...
Doğrulama komutları: ...
Repo talimatlarını (AGENTS.md vb.) oku. Başka agent başlatma, push/deploy yapma.
Final raporu (en fazla 20 satır): özet; değişen dosyalar; komutlar ve exit kodları; risk/engel.
```

Commit'i host'a bırak; işçi commit yapacaksa görevde açıkça yaz.

## scout (agy)

```text
Görev: MAP-01 (salt okuma)
Soru: <tek, net soru> veya "repo-map.md'yi state-and-map.md biçiminde üret/güncelle: <değişen yollar>"
Dosya değiştirme. Yanıt en fazla 40 satır; yol + kısa açıklama, kod gövdesi yok.
```

## reviewer (agy)

```text
Görev: REV-API-01 (salt okuma)
Worktree'deki branch: orch/<run>/api, base: <sha>
Kabul ölçütleri: ...
Kontrol: `git diff <base>..HEAD` incele; doğrulama komutlarını çalıştır: ...
Dosya değiştirme. Yanıt: KABUL veya RED; en fazla 5 bulgu (dosya:satır + neden); çalıştırılan komutlar ve exit kodları.
```

## advisor / helper (Claude, araçsız)

```text
Karar: <tek soru>
Seçenekler: A) ... B) ...
Kanıt: <ilgili kod/diff parçaları, en fazla ~200 satır>
En fazla 5 bulgu; her biri için kanıt ve öneri. Kod veya patch yazma.
```

Araçsız oldukları için "git diff'e bak" gibi erişemeyecekleri referans verme.

## planner (yalnız Codex girişinde)

Codex ana oturumu taşıyıcıdır; plan ve kararları Opus'a `--role planner` ile yaptırır. Prompt'a `state.json` ve yeni `answer_preview`'ları koy; çıktıyı `state.json`'ı güncelleyen yapılandırılmış JSON olarak iste. Biçim bozuksa aynı Opus'a düzeltme isteği gönder; boşluğu kendi planınla doldurma.
