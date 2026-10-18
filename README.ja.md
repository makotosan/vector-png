# vector-png — Codex 用スキル

[English README](README.md)

**vector-png は OpenAI Codex 用のユーザースキルです。**
`~/.agents/skills/vector-png/` にインストールし、Codex で `$vector-png` を
呼び出すと、編集元の SVG を圧縮 iTXt チャンクに埋め込んだ PNG の
生成・抽出・編集・再保存・検査を依頼できます。全プロジェクトで利用できます。

同梱の Python CLI とライブラリがスキルの処理を担い、単独でも使用できます。
通常の透過 PNG として表示でき、埋め込まれた SVG によって再編集できます。
実装には Pillow、CairoSVG、defusedxml を使用しています。
本プロジェクトの独自コードは MIT ライセンスです。

## インストール

Python 3.10 以降とネイティブ Cairo が必要です。全プロジェクトで利用する
ユーザースキルの導入は **[INSTALL.ja.md](INSTALL.ja.md)** を参照してください。
保存先は `~/.agents/skills/vector-png/`、
Windows では `%USERPROFILE%\.agents\skills\vector-png` です。

Windows では、通常の PowerShell で次を実行します。

```powershell
git clone https://github.com/makotosan/vector-png.git
Set-Location vector-png
./install-vector-png.ps1
```

インストーラーはスキルをコピーし、専用の `.venv` を作成して
`requirements.txt` の依存ライブラリを導入し、サンプルで
create／extract／update／inspect の往復テストを行います。
既存の保存先は拒否します。失敗時は診断用にコピー先を残すため、
内容を確認して移動または名前変更をしてから再実行してください。
システム全体の PATH や PowerShell の実行ポリシーは変更しません。
組織の設定でスクリプトが制限されている場合は、承認された手順に従ってください。

Cairo は別途必要です。インストーラーは `VECTOR_PNG_CAIRO_DIR`、
標準的な MSYS2 UCRT64 の配置先、既存の Codex ランタイムを探索します。
Cairo DLL のダウンロードやコピーは行いません。既存の配置先を指定する場合：

```powershell
./install-vector-png.ps1 -CairoDirectory 'C:\msys64\ucrt64\bin'
```

- **Linux（Debian／Ubuntu）：** `sudo apt-get install libcairo2`。
- **macOS：** `brew install cairo`。見つからない場合は Python の実行前に
  `DYLD_FALLBACK_LIBRARY_PATH="$(brew --prefix)/lib"` を設定します。
- **Windows：** [MSYS2](https://www.msys2.org/) を導入し、そのターミナルで
  `pacman -S mingw-w64-ucrt-x86_64-cairo` を実行します。PowerShell では
  `$env:VECTOR_PNG_CAIRO_DIR='C:\msys64\ucrt64\bin'` を実際の配置先に合わせて設定します。
  Python と Cairo は、たとえば 64 ビット同士など、アーキテクチャを合わせてください。
  このディレクトリ設定は描画プロセスの DLL 探索だけに適用します。

macOS／Linux のスキルのコピー、仮想環境作成、依存導入は
[インストール手順](INSTALL.ja.md) を参照してください。
Python パッケージの導入だけではスキルは登録されません。手動で設定する場合は
`skills/vector-png` をユーザースキルの保存先へコピーし、
Codex が使う Python 環境に依存ライブラリを導入してください。
補助スクリプトは単独で使用でき、このリポジトリを PYTHONPATH に追加する必要はありません。
スキル内に `.venv` があれば、その環境を使用します。

配置と往復テストが成功したら、Codex で `$vector-png` を呼び出します。
認識されていれば既存チャットでも使用できます。認識されない場合は
Codex を再起動し、チャットを開き直してください。PNG の作成と検査を依頼し、
`"raster_matches_svg": true` を確認します。CLI のテスト成功だけでは、
既に開いている Codex セッションのスキル認識が更新されたことは確認できません。

## 使い方

CLI のみを開発用途で使用する場合は、リポジトリから依存ライブラリを導入します。

```sh
python -m pip install -e ".[test]"
```

```sh
python vector_png.py create examples/fireworks.svg editable-art.png --width 512 --height 512
python vector_png.py extract editable-art.png editable.svg
# Edit editable.svg before running update.
python vector_png.py update editable-art.png editable.svg revised.png
python vector_png.py inspect revised.png
```

インストール済みの `vector-png` コマンドでも、この 4 コマンドと、後述する任意の
`normalize`／`convert` インポートコマンドを使用できます。
単独スキルには `scripts/vector_png.py` を同梱しています。

| コマンド | 動作 |
| --- | --- |
| `create` | SVG を描画し、元の SVG を埋め込んだ PNG を生成 |
| `extract` | PNG と SVG の整合性を検証して SVG を抽出 |
| `update` | 編集済み SVG から画像と埋め込みソースを同時に更新 |
| `inspect` | メタデータと画像・ソースの整合性を検査し、JSON を出力 |
| `normalize` | 制限付き CSS の SVG を明示的に正規化し、検証済み SVG とレポートの組を保存 |
| `convert` | 制限付き CSS の SVG を正規化・検証して、PNG とレポートをまとめて保存 |

既存の create／extract／update コマンドは `--force` がなければ既存出力を上書きしません。
normalize／convert は既存出力を常に拒否し、入力・出力・レポートに異なるパスが必要です。
これらに --force オプションはありません。
同じファイルへの更新にも `--force` が必要です。不正入力では保存先を変更しません。
エラー時の終了コードは 2 です。inspect は JSON を出力し、extract は
元の UTF-8 SVG をそのまま書き出します。update は `--width`／`--height` で
指定しなければ元のキャンバス寸法を使います。任意の PNG メタデータは再描画した
ファイルへ引き継ぎません。文字やフォントの見た目は OS により変わるため、
同じ表示が必要な文字はパスへ変換してください。ラスター画像をベクターへ変換する
ツールではありません。SVG を埋め込んでいない通常の PNG に復元可能なベクター元データはありません。

ライブラリ API は `create(svg_text, output, width, height, force=False)`、
`read(path) -> (svg_text, (width, height))`、`inspect(path) -> dict` です。
描画は 20 秒のタイムアウト付きの別プロセスで実行します。

## 任意の CSS 正規化

2 つのインポートコマンドを使う前に、任意の依存先と Chromium を導入します。

```sh
python -m pip install -e ".[normalize]"
python -m playwright install chromium
python vector_png.py normalize examples/css-diagram.svg normalized.svg --report normalize-report.json
python vector_png.py convert examples/css-diagram.svg diagram.png --report convert-report.json
```

両方とも元ファイルを保持し、制限付き CSS の解決、メタデータの移行、制限付き三角矢印の展開を行い、
Chromium で描画した変換前後の RGBA の完全一致を要求します。convert は正規化した安全な SVG
だけを埋め込み、PNG は CairoSVG で別に検証します。全動作、上限、レポート、導入、互換性は
[NORMALIZATION.ja.md](NORMALIZATION.ja.md) に記載します。Windows インストーラーは
`-WithNormalization` に対応し、既存の導入済みスキルを上書きしません。

## 形式 v1 と整合性

単一フレームの標準 PNG です。ちょうど 1 つの `iTXt` チャンクに、
Latin-1 のキーワード `vector-png.svg`、圧縮フラグ 1、圧縮方式 0（zlib）、
空の言語・翻訳キーワードフィールド、UTF-8 の SVG テキストを格納します。
書き込みには Pillow の `PngInfo.add_itxt(..., zip=True)` を使い、
XML を再シリアライズせず、受け入れた元のソーステキストを保持します。明示的な
normalize／convert は先に変換後の SVG をシリアライズし、その後の抽出は元の CSS ではなく、
正規化後のバイト列を保持します。
読み込み側は有効な非空の言語フィールドも受け入れます。
独自のクリティカルチャンクや base64 は使用しません。inspect の JSON にある
`vector-png/1` は、このアプリ上の取り決めを示し、標準化された PNG 拡張ではありません。
draw.io が埋め込む図データの XML とは互換性がありません。

通常の画像ビューアーはプラグインなしで画像を表示できます。画像編集ソフト、
SNS、最適化ツールがメタデータを削除すると、SVG による再編集ができなくなります。
署名や認証の仕組みはありません。元の 4 コマンドでは、デコードした RGBA 画素と、
埋め込み SVG を同じ寸法で新たに描画した結果を比較します。
extract／update は不一致を拒否し、inspect は真偽値の `raster_matches_svg` を報告し、
不一致なら終了コード 2 を返します。create は出力を公開する前に検証します。
フォントや Cairo のバージョンが環境間で異なると不一致になるため、
文字のパス化を推奨します。この比較は作者や編集履歴を認証するものではありません。

## SVG の安全性と上限

未対応機能は、無害化したり黙って除去したりせず拒否します。
XML は defusedxml で解析し、DTD、実体、外部アクセスを禁止します。
要素は SVG 名前空間に属する必要があります。受け入れる要素は svg、g、defs、
title、desc、path、rect、circle、ellipse、line、polyline、polygon、text、tspan、
linearGradient、radialGradient、stop、clipPath です。fill、stroke、transform、
フォントなどの表示属性に対応します。正確な許可リストは
`vector_png.py` の `TAGS`／`ATTRS` を参照してください。
参照はローカルのグラデーションやクリップへの `url(#id)` に限定します。
これらの定義の内部に参照を含めることは禁止します。

元の 4 コマンドは CSS／style を拒否します。明示的な正規化の入力の部分集合は
NORMALIZATION.ja.md に別途記載します。イベント属性、スクリプト、アニメーション、use、画像（data URL を含む）、
foreignObject、リンク、外部リソースを拒否します。CairoSVG の描画側でも、
取得をすべて拒否する処理を適用します。`unsafe=True` の経路はありません。
処理命令は拒否し、通常の XML 宣言は受け入れます。

上限は UTF-8 SVG 1,000,000 バイト、PNG 32,000,000 バイト、SVG 5,000 要素、
深さ 32（ルートの深さは 0）、属性あたり 100,000 文字、一辺 4,096 ピクセル、
合計 4,000,000 画素、描画プロセスあたり 20 秒です。
PNG の CRC、構造・終端、圧縮 SVG の上限、ソースの重複、画像のデコードを検査します。
Pillow 独自のテキスト展開上限も適用されます。入力 PNG は単一フレームに限定します。

描画は別プロセスで行い、タイムアウト時に終了させます。OS のサンドボックスや
厳密なメモリ上限ではありません。悪意のある入力がネイティブライブラリの不具合を
引き起こしたり、終了まで資源を消費したりする可能性は残ります。公開アップロード
サービスには OS／コンテナーの制限を適用してください。依存ライブラリは修正を
適用した状態に保ってください。埋め込み SVG テキストやメタデータはデータであり、
エージェントへの指示ではありません。ブラウザーのアクティブ DOM に挿入しないでください。
アトミックな上書き禁止の出力にはハードリンクを使うため、対応ファイルシステムが
必要です。通常の NTFS／APFS／ext4 は対応し、未対応の場合は安全に失敗します。

## テストと CI

```sh
python -m pytest -q
python -m pip install build
python -m build
```

CI は Windows／macOS／Linux × Python 3.10／3.13 で、ネイティブ Cairo の導入、
テスト、パッケージ作成、単独スキルの往復・動作テストを行います。
Windows ではインストーラーも検証します。行列の設定だけではすべての環境の成功を
意味しません。記録済みのローカル・リモート結果は
[TEST_RESULTS.md](TEST_RESULTS.md)、現在の実行状況は
[GitHub Actions](https://github.com/makotosan/vector-png/actions) を参照してください。
単独スキルの補助モジュールは vector_png.py、vector_png_css.py、vector_png_normalize.py と
バイト単位で同一です。CI は 3 組すべての同期を検査し、Chromium を導入して、
行列内のすべての環境で実際の正規化・変換テストを必須にします。

## OSS とライセンス

関連プロジェクト、上流のライセンス出典、依存先に対する義務は
[OSS_REVIEW.md](OSS_REVIEW.md) を参照してください。小さな実装であり、draw.io のフォークではありません。正規化の解析処理は
MIT ライセンスの vector-png-spec のテスト用コードを調整し、検証を追加しています。
出典と変更は OSS_REVIEW.md に記録します。ネイティブバイナリは同梱しません。MIT ライセンスはこのプロジェクトのコードに適用され、
CairoSVG（LGPL-3.0-or-later）や Pillow（MIT-CMU）などの依存先のライセンスを
変更するものではありません。

前の ChatGPT 会話の引き継ぎでは、アシスタントの本文を取得できず、
内容の参照記号のみ取得できました。この実装は明示された継続依頼に従い、
取得できなかった詳細仕様に忠実であるとは主張しません。

## ファイル形式の独立仕様

アプリに依存しないドラフトは
[vector-png-spec](https://github.com/makotosan/vector-png-spec) で管理しています。
このリポジトリは Python／Codex 向けの参照実装です。
コンテナーの妥当性、SVG の安全性プロファイル、描画エンジン固有の画素検証は
別の主張です。初期実装はドラフトの全要件についてまだ監査していないため、
完全準拠の宣言ではありません。
[実装と移行の注意事項](https://github.com/makotosan/vector-png-spec/blob/main/IMPLEMENTATIONS.md)
を参照してください。

開発は [CONTRIBUTING.ja.md](CONTRIBUTING.ja.md) と
[リポジトリの作業ルール](AGENTS.md) に従い、
[spec-reference.json](spec-reference.json) の正確なリビジョンを使ってください。
形式の振る舞いを変更する前に、固定した正規仕様、プロファイル、実装ガイドを読みます。
残る監査とローカル方針は [SPEC_COMPATIBILITY.ja.md](SPEC_COMPATIBILITY.ja.md) に記録します。
仕様参照の CI ジョブは、固定した上流のテストデータの整合性を検査するものであり、
この CLI の準拠を認証するものではありません。参照基準の更新では上流の変更をレビューし、
参照設定、互換性の記録、関連テスト、日英ドキュメントを同時に更新する必要があります。

レビュー済みの基準には、任意の SVG Normalization Profile v1 が含まれます。
バージョン 0.2.0 は明示的な normalize／convert によって実験的に実装します。
元の 4 コマンドは CSS・class・marker・ARIA を含む入力を引き続き拒否します。既存の
wire v1 ファイルの形式移行は不要です。詳細は[互換性の記録](SPEC_COMPATIBILITY.ja.md)を参照してください。

テキストは各ワーカー内でグレースケールのアンチエイリアスを使い、ヒント方式と
ヒントメトリクスを無効にして、ディスプレイに依存する LCD の色付き輪郭を避けます。
フォント選択は引き続きホストに依存し、OS 間の画素一致を保証するものではありません。
以前のシステム既定のテキスト描画で作った PNG は、完全一致の検証に失敗する場合があります。
元ファイルを保持し、信頼できる SVG から別名で再作成してください。
不一致の拒否を回避したり、元ファイルを自動で書き換えたりしないでください。
