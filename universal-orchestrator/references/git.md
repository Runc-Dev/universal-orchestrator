# Worktree ve entegrasyon

Host'un worktree aracı varsa onu kullan. Yoksa (bash; PowerShell'de değişken sözdizimini uyarla):

```sh
repo=$(git rev-parse --show-toplevel)
base=$(git rev-parse HEAD)
common=$(git rev-parse --path-format=absolute --git-common-dir)
run=20261114-1100
runs="$common/orchestrator/runs/$run"
trees="$(dirname "$repo")/orchestrator-worktrees/$run"
mkdir -p "$runs" "$trees"
git worktree add -b "orch/$run/api" "$trees/api" "$base"
git worktree add -b "orch/$run/integration" "$trees/integration" "$base"
git worktree add --detach "$trees/review" "$base"   # scout/reviewer için
```

Her Git çıkışını kontrol et; başarısız adımın arkasından devam etme.

- Kullanıcının commit edilmemiş değişiklikleri HEAD'den açılan worktree'de yoktur. Görev onlara bağlıysa kullanıcıya nasıl taşınacağını sor.
- Bağımlı görev B, A doğrulanmadan başlamaz; B'nin `base_sha`'sı A'nın commit'ini içerir.
- Entegrasyonda yalnız henüz uygulanmamış görev commit'lerini, bağımlılık sırasıyla taşı. Yalnız incelenmiş açık dosya listesini stage et.
- Worktree ortam değişkenlerini, `node_modules`'ı ve untracked dosyaları taşımaz; bağımlılık kurulumunu görevde açıkça belirt.
- Worktree silmeden önce: yol beklenen `trees` altında mı, işçi bitti mi, değişiklikler taşındı mı, worktree temiz mi. `--force` yok.

## Çalıştırma

Önce `--dry-run` ile kontrol et, sonra aynı komutu çalıştır:

```sh
python scripts/run_agent.py run --role coder --worktree "$trees/api" \
  --prompt "$runs/API-01.txt" --out "$runs/API-01-1" --dry-run
```

`--out` mevcut olmamalı ve worktree dışında olmalı. Betik senkron çalışır; paralellik için host'un arka plan süreç aracını kullan.

Çıktılar: `request.json`, `prompt.txt`, `stdout.log`, `stderr.log`, `answer.txt`, `result.json`. Betik sonunda `answer_preview` (ilk 1500 karakter) ve `answer_chars` yazdırır; normalde yalnız bunu oku.
