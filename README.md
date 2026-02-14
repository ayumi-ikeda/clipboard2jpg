# clipboard2jpg

クリップボード内の画像をJPEGファイルとして保存するCLIツールです。
特に、AIエージェントにスクリーンショットや画像を確認してもらう際、クリップボードの内容をサッとファイル化して渡すのに便利です。
もちろん、画像ファイルを扱うあらゆるアプリケーションへの入力として汎用的に利用できます。

## 特徴

- **手軽な画像保存**: コマンド一発でクリップボードの画像をファイル化。
- **マルチプラットフォーム対応**: macOS, Linux (X11/Wayland), WSL2 をサポート。
- **ファイル名指定**: `-o` オプションで任意のファイル名を指定可能（拡張子自動補完あり）。
- **自動命名**: ファイル名を指定しない場合、タイムスタンプベースのユニークなファイル名で保存。
- **軽量**: Pythonスクリプトとして動作し、必要な依存関係も最小限。

## 必要要件

- **OS**: macOS, Linux (X11/Wayland), WSL2
- **Python**: 3.x
- **各環境のツール** (環境に応じて自動選択されます):
  - **Linux (X11)**: `xclip` または `xsel`
  - **Linux (Wayland)**: `wl-clipboard` (`wl-paste`)
  - **WSL2**: `powershell.exe` (Windows 側にインストール済み)
  - **macOS**: `pbpaste` / `osascript` (標準搭載)
- **Python Library**: `Pillow`

## インストール

1. **必要なパッケージのインストール (Ubuntu/Debian系の場合)**

   ```bash
   sudo apt install xclip
   ```

2. **Pythonライブラリのインストール**

   ```bash
   pip install -r requirements.txt
   ```

   ※環境に応じて仮想環境（venv）の使用を推奨します。

3. **実行権限の付与**

   ```bash
   chmod +x clipboard2jpg.py
   ```

## 使い方

### 基本的な使い方

クリップボードに画像が入っている状態で実行します。

```bash
./clipboard2jpg.py
```

成功すると、カレントディレクトリに `clipboard2jpg_YYYYMMDD_HHMMSS_xxxxxx.jpg` のようなファイル名で保存されます。

### ファイル名を指定して保存

```bash
./clipboard2jpg.py -o my_screenshot
```

拡張子を省略した場合、自動的に `.jpg` が付加され `my_screenshot.jpg` として保存されます。

### ヘルプとバージョン確認

```bash
./clipboard2jpg.py -h  # ヘルプ表示
./clipboard2jpg.py -v  # バージョン表示 (0.1.1)
```

## エラーメッセージ

- `error: no image`: クリップボードに画像データが含まれていない場合。
- `error : empty`: クリップボードが空、またはアクセスできない場合。
- `error: failed to save file: <reason>`: ファイルの書き込みに失敗した場合。詳細なエラー理由が表示されます。

## 終了コード

- `0`: 正常終了（画像が正常に保存された場合）。
- `1`: 異常終了（画像がない、クリップボードが空、または書き込みエラーなど）。
