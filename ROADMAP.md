# ロードマップ

## TODO

### ターミナル整列時のドロップシャドウ補正（透明キーボードで実装済み）
透明キーボード側で以下の影補正を実装した。即ランチャーの `_reposition_windows()` にも同じ補正を適用してほしい：

1. **右端の影を画面外に押し出す**: 右端ターミナルの配置開始位置を `sw + SHADOW_INSET` にする（SHADOW_INSET=7px）。影が画面外にはみ出し、ウィンドウ実体が画面右端にくっつく
2. **定数**: `SHADOW_INSET = 7`（ウィンドウ影の片側幅）

参考コード（透明キーボード `transparent_keyboard.py` の `_realign_all()`）:
```python
# ターミナルを右寄せで再配置（右の影を画面外に押し出す）
x = sw + SHADOW_INSET  # ← 元は x = sw
wt_positions = []
for i in range(n_wt - 1, -1, -1):
    x -= win_w
    if i < n_wt - 1:
        x += SHADOW_OVERLAP
    ...
```

## アイデアメモ
- （なし）
