# 引き継ぎメモ

## 現在の状況
- GitHubリポジトリ: https://github.com/nock-in-mook/terminal_copy
- Mac版: GC問題修正済み、メニューバーアイコン追加済み、安定動作中
- Windows版: マウスフック完全軽量化済み（セッション019）

## 今回の変更（セッション019）
### 修正: Windows版フック内の全処理を排除
- デスクトップダブルクリック時にPCがカクカクになり即ランチャーが落ちる問題（018で直したはずが再発）
- **原因**: 018でSendMessageWは別スレッドに移動したが、フック内にまだ重い処理が残っていた
  - `root.after()` — tkinterへのクロススレッド通信（GILロック待ち）
  - `threading.Thread().start()` — スレッド生成コスト（~1ms）
  - Windowsはlow-levelフックに約300ms制限、超えると無言でフック解除
- **対策**: フック内は座標記録とフラグセットのみ（関数呼び出しゼロ）。メインスレッドの30msポーリングでフラグを拾って処理（Orchisと同じ設計思想）

## Mac版の構成
- `folder_launcher.py` — メイン（NSApplication + NSEvent + NSMenu + NSStatusItem）
- `hammerspoon_init.lua` — Hammerspoon設定（グローバル変数でGC対策済み）
- `install_mac.sh` — Mac版インストールスクリプト

## Windows版の構成
- `folder_launcher_win.pyw` — メイン（pystray + tkinter + WH_MOUSE_LL）
- `即ランチャー.exe` — pythonw.exeコピー+アイコン・バージョン情報書き換え済み
- `一発更新_即ランチャー.bat` — 1クリックセットアップ
- ショートカットは .pyw を引数で渡す方式なので、コード修正だけで反映される

## 次のアクション
- Windows側で一発更新バッチを実行して透明キーボードEXEを再ビルド（前回からの持ち越し）
- フック軽量化後の動作確認（ダブルクリックでカクカクしないか）
