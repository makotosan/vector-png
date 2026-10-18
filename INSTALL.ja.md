# vector-png を Codex ユーザースキルとしてインストールする

[English installation guide](INSTALL.md) · [日本語 README](README.ja.md)

保存先は **`~/.agents/skills/vector-png/`** です。全プロジェクトで利用できます。
Python 3.10 以降とネイティブ Cairo が必要です。既存の同名スキルは上書きしません。

## Windows（PowerShell）

通常の PowerShell で次を実行します。

```powershell
git clone https://github.com/makotosan/vector-png.git
Set-Location vector-png
./install-vector-png.ps1
```

既にクローン済みの場合は、そのリポジトリを最新にしてからスクリプトを実行してください。

インストーラーは次の処理を行います。

1. `skills/vector-png` をユーザースキルの保存先へコピー
2. スキル内に専用の Python 仮想環境 `.venv` を作成
3. `requirements.txt` の依存ライブラリを導入
4. create／extract／update／inspect の既存 PNG 4 コマンドで往復テストを実施

システム全体の PATH は変更しません。失敗時は診断用にコピー先を残します。
再実行すると既存フォルダーとして拒否されるため、内容を確認し、必要に応じて
移動または名前変更をしてから再実行してください。

### Cairo の準備

インストーラーは、環境変数 `VECTOR_PNG_CAIRO_DIR`、標準的な MSYS2 UCRT64 の
配置先、既存の Codex ランタイムから Cairo を探索します。Cairo DLL 自体の
ダウンロードやコピーは行いません。既存のライブラリの場所を指定することもできます。

```powershell
./install-vector-png.ps1 -CairoDirectory 'C:\msys64\ucrt64\bin'
```

Cairo がない場合は [MSYS2](https://www.msys2.org/) を導入し、そのターミナルで
次を実行します。

```sh
pacman -S mingw-w64-ucrt-x86_64-cairo
```

Python と Cairo は 64 ビット同士など、アーキテクチャを合わせてください。
選択したディレクトリはスキル内の `cairo-path.txt` に記録され、描画プロセスが
参照します。PowerShell の実行ポリシーは変更しません。スクリプトが組織の設定で
制限されている場合は、その組織の承認された手順に従ってください。

## macOS／Linux

まず Cairo を導入します。

- macOS：`brew install cairo`
- Debian／Ubuntu：`sudo apt-get install libcairo2`

リポジトリを取得し、ルートディレクトリへ移動します。

```sh
git clone https://github.com/makotosan/vector-png.git
cd vector-png
```

次のコピー処理を実行します。保存先が既に存在する場合は停止します。

```sh
python - <<'PY'
from pathlib import Path
import shutil
target = Path.home() / '.agents/skills/vector-png'
if target.exists():
    raise SystemExit(f'Existing skill was not overwritten: {target}')
target.parent.mkdir(parents=True, exist_ok=True)
shutil.copytree('skills/vector-png', target)
print(target)
PY
```

**コピーが成功したことを確認してから**、仮想環境の作成と依存導入を行います。
途中でエラーになった場合は、それ以降のコマンドを実行しないでください。

```sh
python -m venv "$HOME/.agents/skills/vector-png/.venv"
"$HOME/.agents/skills/vector-png/.venv/bin/python" -m pip install -r "$HOME/.agents/skills/vector-png/requirements.txt"
"$HOME/.agents/skills/vector-png/.venv/bin/python" "$HOME/.agents/skills/vector-png/scripts/roundtrip_check.py" --output-dir "$(mktemp -d)"
```

環境に応じて `python` を `python3` に置き換えてください。macOS で Cairo が
見つからない場合は、Python の実行前に次を設定します。

```sh
export DYLD_FALLBACK_LIBRARY_PATH="$(brew --prefix)/lib"
```

## 任意の正規化対応

Windows で normalize／convert を有効にした新しいスキルを導入する場合：

```powershell
./install-vector-png.ps1 -WithNormalization
```

requirements-normalization.txt の導入、固定した Playwright Chromium の取得、
normalization_check.py の実行を追加します。既存スキルは引き続き拒否します。
既存スキルはローカル設定を確認して保持・名前変更した後、新しいコピーを導入してください。
唯一のコピーを消したり、異なる版の補助モジュールを混在させたりしないでください。

コピー済みの macOS／Linux のスキルでは、専用の Python で任意の依存先を導入します。

```sh
"$HOME/.agents/skills/vector-png/.venv/bin/python" -m pip install -r "$HOME/.agents/skills/vector-png/requirements-normalization.txt"
"$HOME/.agents/skills/vector-png/.venv/bin/python" -m playwright install chromium
"$HOME/.agents/skills/vector-png/.venv/bin/python" "$HOME/.agents/skills/vector-png/scripts/normalization_check.py" --output-dir "$(mktemp -d)"
```

Linux でシステム依存先が不足する場合は、ブラウザー導入のコマンドに --with-deps を追加できます。
管理者権限が必要な場合があります。各手順の成功確認は維持してください。
PLAYWRIGHT_BROWSERS_PATH でブラウザーのキャッシュ配置先を指定でき、導入とスキルの呼び出しで
同じ設定を使います。任意の依存先・ブラウザーがなくても、既存の 4 コマンドは動作し、
正規化は安全に失敗します。対応範囲とレポートは [NORMALIZATION.ja.md](NORMALIZATION.ja.md) を参照してください。

## 導入結果と Codex での利用確認

1. 往復テストの出力が `"roundtrip": "passed"` になっていることを確認します。
   PNG の生成、SVG の完全一致での抽出、編集、再保存、画像との整合性を検証します。
2. Codex で `$vector-png` を呼び出します。既存チャットでも、スキルが認識されて
   いれば利用できます。認識されない場合は Codex を再起動し、チャットを開き直してください。
3. 簡単な SVG から PNG を作成し、inspect するよう依頼します。
   正常時の JSON には `"raster_matches_svg": true` が含まれます。

スキルは専用の `.venv` があれば、その Python を使用するよう案内します。
補助スクリプトを絶対パスで指定すれば、どのプロジェクトからでも実行できます。
CLI のテスト成功と、Codex がスキルを認識していることは、別々に確認してください。

## 自動テスト

開発用リポジトリのルートで実行する場合：

```sh
python -m pip install -e ".[test]"
python -m pytest -q
```

インストール済みスキルをテストする場合は、スキルのディレクトリへ移動し、
その `.venv` の Python で `-m pytest -q` を実行します。

`VECTOR_PNG_TEST_TMP_ROOT` を指定すると、テスト用ファイルの保存先を
書き込み可能な作業フォルダーに変更できます。

[English installation guide に戻る](INSTALL.md)

